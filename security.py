import hashlib
import secrets
import base64
import re
from typing import Optional, Dict, Tuple
from Crypto.Cipher import AES

DEFAULT_ITERATIONS = 600000  # Updated from 100,000 to meet OWASP recommendations

class SecurityUtils:
    """Cryptographic and security utilities"""
    
    @staticmethod
    def generate_salt(length: int = 32) -> str:
        """Generate cryptographically secure salt"""
        return secrets.token_hex(length)
    
    
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        if salt is None:
            salt = SecurityUtils.generate_salt()
        key = hashlib.pbkdf2_hmac('sha256', 
                                password.encode('utf-8'), 
                                salt.encode('utf-8'), 
                                DEFAULT_ITERATIONS)
        return base64.b64encode(key).decode('utf-8'), salt

    
    @staticmethod
    def verify_password(password: str, hash_value: str, salt: str) -> bool:
        """Verify password against stored hash"""
        test_hash, _ = SecurityUtils.hash_password(password, salt)
        return secrets.compare_digest(test_hash, hash_value)
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    
    @staticmethod
    def encrypt_data(data: str, master_key: str) -> str:
        """Improved encryption using SHA256 key derivation"""
        key = hashlib.sha256(master_key.encode()).digest()
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())
        return base64.b64encode(cipher.nonce + tag + ciphertext).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: str) -> str:
        """Decrypt XOR encrypted data"""
        try:
            data = base64.b64decode(encrypted_data).decode()
            key_bytes = hashlib.sha256(key.encode()).digest()
            decrypted = []
            for i, char in enumerate(data):
                decrypted.append(chr(ord(char) ^ key_bytes[i % len(key_bytes)]))
            return ''.join(decrypted)
        except:
            return ""
    
    @staticmethod
    def sanitize_input(user_input: str) -> str:
        """Sanitize user input to prevent injection attacks"""
        # Remove dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`', '$']
        sanitized = user_input
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def check_password_strength(password: str) -> Tuple[bool, str]:
        """Check password strength and dictionary attacks"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        # Check against common passwords
        common_passwords = [
            'password', '123456', 'password123', 'admin', 'qwerty',
            'letmein', 'welcome', 'monkey', '1234567890', 'abc123'
        ]
        
        if password.lower() in common_passwords:
            return False, "Password is too common. Please choose a stronger password"
        
        return True, "Password is strong"
