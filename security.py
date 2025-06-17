import hashlib
import secrets
import base64
import re
import string
from typing import Optional, Dict, Tuple
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os


DEFAULT_ITERATIONS = 600000  # OWASP recommended iterations for PBKDF2

class SecurityUtils:
    """Cryptographic and security utilities"""
    
    @staticmethod
    def generate_salt(length: int = 32) -> str:
        """Generate cryptographically secure salt"""
        return secrets.token_hex(length)
    
    
    
    @staticmethod
    def hash_password(password: str) -> Tuple[str, str]:
        """Hash password using PBKDF2 with a random salt"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=DEFAULT_ITERATIONS,
            backend=default_backend()
        )
        password_hash = base64.b64encode(kdf.derive(password.encode())).decode()
        salt_hex = base64.b64encode(salt).decode()
        return password_hash, salt_hex

    
    @staticmethod
    def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
        """Verify password against stored hash"""
        salt = base64.b64decode(stored_salt.encode())
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=DEFAULT_ITERATIONS,
            backend=default_backend()
        )
        password_hash = base64.b64encode(kdf.derive(password.encode())).decode()
        return password_hash == stored_hash

    @staticmethod
    def generate_session_token() -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    
    @staticmethod
    def encrypt_data(data: str, master_key: str) -> str:
        """Encrypt data using AES CBC mode with cryptography library"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=DEFAULT_ITERATIONS,
            backend=default_backend()
        )
        key = kdf.derive(master_key.encode())
        iv = os.urandom(16)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ct = encryptor.update(padded_data) + encryptor.finalize()
        # Store salt + iv + ciphertext, all base64 encoded
        return base64.b64encode(salt + iv + ct).decode()

    @staticmethod
    def decrypt_data(encrypted_data: str, master_key: str) -> str:
        """Decrypt data using AES CBC mode with cryptography library"""
        try:
            raw = base64.b64decode(encrypted_data)
            salt = raw[:16]
            iv = raw[16:32]
            ct = raw[32:]
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=DEFAULT_ITERATIONS,
                backend=default_backend()
            )
            key = kdf.derive(master_key.encode())
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ct) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()
            return data.decode()
        except Exception as e:
            return f"Decryption error: {str(e)}"

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
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"
        
        if not any(c in string.punctuation for c in password):
            return False, "Password must contain at least one special character"
        
        # Check against common passwords
        common_passwords = [
            'password', '123456', 'password123', 'admin', 'qwerty',
            'letmein', 'welcome', 'monkey', '1234567890', 'abc123'
        ]
        
        if password.lower() in common_passwords:
            return False, "Password is too common. Please choose a stronger password"
        
        return True, "Password meets security requirements"
