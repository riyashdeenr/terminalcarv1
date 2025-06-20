#!/usr/bin/env python3
"""
Test script to verify login functionality
"""

from ai_terminal_app import GeminiCarRentalTerminal

def test_login():
    """Test login with correct admin credentials"""
    print("Testing login functionality...")
    
    # Initialize the app
    app = GeminiCarRentalTerminal()
    
    # Test admin login with correct credentials from database.py
    admin_email = "admin@carental.com"
    admin_password = "Admin@2025"
    
    print(f"\nTesting login with:")
    print(f"Email: {admin_email}")
    print(f"Password: {admin_password}")
    
    # Call login_user method directly
    result = app.login_user(admin_email, admin_password)
    print(f"\nLogin result: {result}")
    
    # Check session state
    print(f"\nSession state after login:")
    print(f"Current user: {app.current_user}")
    print(f"Is admin: {app.is_admin}")
    print(f"Session token: {app.session_token}")
    
    # Test a normal user login
    print("\n" + "="*50)
    print("Testing normal user login...")
    
    # Reset session
    app.current_user = None
    app.is_admin = False
    app.session_token = None
    
    user_email = "user1@example.com"
    user_password = "User1@2024"
    
    print(f"\nTesting login with:")
    print(f"Email: {user_email}")
    print(f"Password: {user_password}")
    
    result = app.login_user(user_email, user_password)
    print(f"\nLogin result: {result}")
    
    # Check session state
    print(f"\nSession state after login:")
    print(f"Current user: {app.current_user}")
    print(f"Is admin: {app.is_admin}")
    print(f"Session token: {app.session_token}")

if __name__ == "__main__":
    test_login()
