#!/usr/bin/env python3
"""
Test registration command recognition
"""

from ai_terminal_app import GeminiCarRentalTerminal

def test_registration_recognition():
    print("🧪 Testing Registration Command Recognition")
    print("=" * 50)
    
    app = GeminiCarRentalTerminal()
    
    # Test cases
    test_inputs = [
        "register",
        "register new account", 
        "create account",
        "sign up",
        "I want to register",
        "help me create an account"
    ]
    
    keywords = ['register', 'signup', 'sign up', 'create account', 'register account', 'new account', 'register new account', 'create new account']
    
    for user_input in test_inputs:
        user_input_lower = user_input.lower().strip()
        is_direct = user_input_lower in keywords
        
        print(f"\nInput: '{user_input}'")
        if is_direct:
            print("✅ Direct command -> interactive_register()")
        else:
            print("❌ Goes to AI -> should call user_register function")
            # Test what AI would do
            result = app.call_tool('user_register', {})
            print(f"   AI response: {result}")

if __name__ == "__main__":
    test_registration_recognition()
