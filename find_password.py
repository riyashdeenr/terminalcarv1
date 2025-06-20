#!/usr/bin/env python3
"""
Find the admin password by trying common passwords
"""

from auth import AuthenticationManager
from database import DatabaseManager

def find_admin_password():
    """Try to find the admin password"""
    db = DatabaseManager()
    auth = AuthenticationManager(db)
    
    # Common passwords to try
    passwords = ["admin", "admin123", "password", "123456", "carental", "admin@carental.com"]
    
    admin_email = "admin@carental.com"
    
    print(f"Trying to login as {admin_email} with common passwords...")
    
    for password in passwords:
        try:
            success, message, user_info = auth.login(admin_email, password)
            if success:
                print(f"✅ SUCCESS! Password: '{password}'")
                print(f"User info: {user_info}")
                return password
            else:
                print(f"❌ Failed with password '{password}': {message}")
        except Exception as e:
            print(f"❌ Error with password '{password}': {str(e)}")
    
    print("❌ Could not find the admin password")
    return None

if __name__ == "__main__":
    find_admin_password()
