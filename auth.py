from security import SecurityUtils
from database import DatabaseManager


class AuthenticationManager:
    """Handle user authentication and session management"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.active_sessions = {}
    
    def register_user(self, email: str, password: str, national_id: str, role: str = 'user') -> Tuple[bool, str]:
        """Register a new user"""
        email = SecurityUtils.sanitize_input(email)
        
        if not SecurityUtils.validate_email(email):
            return False, "Invalid email format"
        
        is_strong, msg = SecurityUtils.check_password_strength(password)
        if not is_strong:
            return False, msg
        
        # Hash password
        password_hash, salt = SecurityUtils.hash_password(password)
        
        # Encrypt national ID
        encrypted_national_id = SecurityUtils.encrypt_data(national_id, password)
        
        try:
            with self.db.get_connection() as conn:
                # Insert user
                cursor = conn.execute("""
                    INSERT INTO users (email, password_hash, password_salt, role)
                    VALUES (?, ?, ?, ?)
                """, (email, password_hash, salt, role))
                
                user_id = cursor.lastrowid
                
                # Insert identity
                conn.execute("""
                    INSERT INTO user_identity (user_id, national_id_encrypted)
                    VALUES (?, ?)
                """, (user_id, encrypted_national_id))
                
                conn.commit()
                
                # Log registration
                self.log_action(user_id, "USER_REGISTERED", f"User {email} registered")
                
                return True, "User registered successfully"
        
        except sqlite3.IntegrityError:
            return False, "Email already exists"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate user login"""
        email = SecurityUtils.sanitize_input(email)
        
        with self.db.get_connection() as conn:
            user = conn.execute("""
                SELECT id, email, password_hash, password_salt, role, is_active,
                       failed_attempts, locked_until
                FROM users WHERE email = ?
            """, (email,)).fetchone()
            
            if not user:
                self.log_action(None, "LOGIN_FAILED", f"Login attempt for non-existent user: {email}")
                return False, "Invalid credentials", None
            
            # Check if account is locked
            if user['locked_until'] and datetime.now() < datetime.fromisoformat(user['locked_until']):
                return False, "Account is temporarily locked. Please try again later.", None
            
            if not user['is_active']:
                return False, "Account is disabled", None
            
            # Verify password
            if not SecurityUtils.verify_password(password, user['password_hash'], user['password_salt']):
                # Increment failed attempts
                failed_attempts = user['failed_attempts'] + 1
                locked_until = None
                
                if failed_attempts >= 5:
                    locked_until = (datetime.now() + timedelta(minutes=30)).isoformat()
                
                conn.execute("""
                    UPDATE users SET failed_attempts = ?, locked_until = ?
                    WHERE id = ?
                """, (failed_attempts, locked_until, user['id']))
                conn.commit()
                
                self.log_action(user['id'], "LOGIN_FAILED", f"Failed login attempt for {email}")
                return False, "Invalid credentials", None
            
            # Reset failed attempts on successful login
            conn.execute("""
                UPDATE users SET failed_attempts = 0, locked_until = NULL, last_login = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), user['id']))
            
            # Create session
            session_token = SecurityUtils.generate_session_token()
            expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
            
            conn.execute("""
                INSERT INTO sessions (user_id, session_token, expires_at)
                VALUES (?, ?, ?)
            """, (user['id'], session_token, expires_at))
            
            conn.commit()
            
            # Store in memory for quick access
            self.active_sessions[session_token] = {
                'user_id': user['id'],
                'email': user['email'],
                'role': user['role'],
                'expires_at': expires_at
            }
            
            self.log_action(user['id'], "LOGIN_SUCCESS", f"User {email} logged in")
            
            return True, "Login successful", {
                'session_token': session_token,
                'user_id': user['id'],
                'email': user['email'],
                'role': user['role']
            }
    
    def logout(self, session_token: str) -> bool:
        """Logout user and invalidate session"""
        if session_token in self.active_sessions:
            user_info = self.active_sessions[session_token]
            del self.active_sessions[session_token]
            
            with self.db.get_connection() as conn:
                conn.execute("""
                    UPDATE sessions SET is_active = 0 WHERE session_token = ?
                """, (session_token,))
                conn.commit()
            
            self.log_action(user_info['user_id'], "LOGOUT", "User logged out")
            return True
        
        return False
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate session token and return user info"""
        if not session_token:
            return None
        
        # Check memory cache first
        if session_token in self.active_sessions:
            session_info = self.active_sessions[session_token]
            if datetime.now().isoformat() < session_info['expires_at']:
                return session_info
            else:
                # Session expired
                del self.active_sessions[session_token]
        
        # Check database
        with self.db.get_connection() as conn:
            session = conn.execute("""
                SELECT s.user_id, s.expires_at, u.email, u.role
                FROM sessions s
                JOIN users u ON s.user_id = u.id
                WHERE s.session_token = ? AND s.is_active = 1
            """, (session_token,)).fetchone()
            
            if session and datetime.now().isoformat() < session['expires_at']:
                session_info = {
                    'user_id': session['user_id'],
                    'email': session['email'],
                    'role': session['role'],
                    'expires_at': session['expires_at']
                }
                self.active_sessions[session_token] = session_info
                return session_info
        
        return None
    
    def reset_password(self, email: str, new_password: str, admin_user_id: int = None) -> Tuple[bool, str]:
        """Reset user password (admin function)"""
        email = SecurityUtils.sanitize_input(email)
        
        is_strong, msg = SecurityUtils.check_password_strength(new_password)
        if not is_strong:
            return False, msg
        
        password_hash, salt = SecurityUtils.hash_password(new_password)
        
        with self.db.get_connection() as conn:
            user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if not user:
                return False, "User not found"
            
            conn.execute("""
                UPDATE users SET password_hash = ?, password_salt = ?, failed_attempts = 0, locked_until = NULL
                WHERE email = ?
            """, (password_hash, salt, email))
            conn.commit()
            
            self.log_action(admin_user_id, "PASSWORD_RESET", f"Password reset for user {email}")
            return True, "Password reset successfully"
    
    def log_action(self, user_id: Optional[int], action: str, details: str, ip_address: str = None):
        """Log user action for audit trail"""
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO audit_log (user_id, action, details, ip_address)
                VALUES (?, ?, ?, ?)
            """, (user_id, action, details, ip_address))
            conn.commit()
