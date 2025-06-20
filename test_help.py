#!/usr/bin/env python3
"""
Test the help command functionality
"""

from ai_terminal_app import GeminiCarRentalTerminal

def test_help_command():
    """Test help command"""
    print("Testing help command functionality...")
    
    app = GeminiCarRentalTerminal()
    
    # Test help command when not logged in
    print("\n" + "="*60)
    print("TEST 1: Help command when NOT logged in")
    print("="*60)
    help_result = app.show_help()
    print(help_result)
    
    # Test help command when logged in as regular user
    print("\n" + "="*60)
    print("TEST 2: Help command when logged in as USER")
    print("="*60)
    
    # Simulate login as regular user
    app.current_user = {'email': 'user1@example.com', 'user_id': 2}
    app.is_admin = False
    app.session_token = "test_token"
    
    help_result = app.show_help()
    print(help_result)
    
    # Test help command when logged in as admin
    print("\n" + "="*60)
    print("TEST 3: Help command when logged in as ADMIN")
    print("="*60)
    
    # Simulate login as admin
    app.current_user = {'email': 'admin@carental.com', 'user_id': 1}
    app.is_admin = True
    app.session_token = "admin_token"
    
    help_result = app.show_help()
    print(help_result)
    
    print("\n✅ Help command test completed!")

if __name__ == "__main__":
    test_help_command()
