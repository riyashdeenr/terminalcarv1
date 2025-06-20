#!/usr/bin/env python3
"""
Test script to verify the login fix in the AI terminal app
"""

from ai_terminal_app import GeminiCarRentalTerminal

def test_login_functionality():
    """Test the login functionality with explicit credentials"""
    print("🧪 Testing AI Terminal App Login Fix")
    print("=" * 50)
    
    # Initialize the app
    app = GeminiCarRentalTerminal()
    
    # Test 1: Check initial state
    print("Test 1: Initial State")
    print(f"Current user: {app.current_user}")
    print(f"Is admin: {app.is_admin}")
    print(f"Session token: {app.session_token}")
    print()
      # Test 2: Test login prompt processing (simulated Gemini response)
    print("Test 2: Testing login with admin credentials")
    
    # Simulate direct login call - Using the correct admin email from database
    login_result = app.login_user("admin@carental.com", "admin123")
    print(f"Login result: {login_result}")
    print(f"Current user after login: {app.current_user}")
    print(f"Is admin after login: {app.is_admin}")
    print(f"Session token after login: {app.session_token}")
    print()
    
    # Test 3: Test function calling with login
    print("Test 3: Testing AI function calling")
    
    # Test the call_tool method directly
    function_args = {
        "email": "abc@123.com", 
        "password": "123"
    }
    
    # Reset session first
    app.current_user = None
    app.is_admin = False
    app.session_token = None
    
    tool_result = app.call_tool("user_login", function_args)
    print(f"Tool call result: {tool_result}")
    print(f"Current user after tool call: {app.current_user}")
    print(f"Is admin after tool call: {app.is_admin}")
    print()
      # Test 4: Test admin functions
    print("Test 4: Testing admin access")
    
    # Login as admin - using correct credentials
    app.login_user("admin@carental.com", "admin123")
    admin_result = app.call_tool("get_all_users", {})
    print(f"Admin function result: {admin_result[:200]}...")
    print()
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    test_login_functionality()
