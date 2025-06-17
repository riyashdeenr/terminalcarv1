from security import SecurityUtils
from database import DatabaseManager
from typing import Optional, Dict, Tuple
import sqlite3
from datetime import datetime, timedelta
from google import genai

# Importing components
from database import DatabaseManager   
from auth import AuthenticationManager
from car_manager import CarManager
from booking_manager import BookingManager
# from gemini import GeminiIntegration   
from web import WebInterfacez
from security import SecurityUtils


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
    



class CarRentalApp:
    """Main application class"""
    
    def __init__(self):
        # Initialize components
        self.db = DatabaseManager()
        self.auth = AuthenticationManager(self.db)
        self.car_manager = CarManager(self.db)
        self.booking_manager = BookingManager(self.db)
        # self.gemini = GeminiIntegration(self.car_manager, self.booking_manager)
        self.web_interface = WebInterfacez(self)
        
        # Insert sample data
        self.db.insert_sample_data()
        
        # Create default superuser
        self.create_default_users()
    
    def create_default_users(self):
        """Create default users for testing"""
        # Create superuser
        self.auth.register_user("admin@carental.com", "Admin123!", "000000000", "superuser")
        
        # Create admin
        self.auth.register_user("staff@carental.com", "Staff123!", "111111111", "admin")
        
        # Create regular user
        self.auth.register_user("user@carental.com", "User123!", "222222222", "user")
    
    def user_auth_menu(self, username, password):
        while True:
            print("\n1. Register\n2. Login\n3. Exit")
            choice = input("Choose an option: ")
            if choice == "1":
                username = input("Enter new username: ")
                password = input("Enter new password: ")
                if AuthenticationManager().register_user(username, password):
                    print("Registration successful!")
                else:
                    print("Registration failed. Username may already exist.")
            elif choice == "2":
                username = input("Enter username: ")
                password = input("Enter password: ")
                if AuthenticationManager().login(username, password):
                    print("Login successful!")
                else:
                    print("Login failed. Check your credentials.")
            elif choice == "3":
                print("Goodbye!")
                break
            else:
                print("Invalid option. Try again.")

if __name__ == "__main__":
    while True:
        print("\nWelcome to the Car Rental App!")
        car = CarRentalApp()
        car.create_default_users()
        car.user_auth_menu()
