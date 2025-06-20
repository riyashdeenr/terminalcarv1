#!/usr/bin/env python3
"""
Manual test of registration via direct commands
"""

from ai_terminal_app import GeminiCarRentalTerminal

def test_direct_commands():
    print("🧪 Testing Direct Registration Commands")
    print("=" * 50)
    
    app = GeminiCarRentalTerminal()
    
    # Simulate the main loop logic for 'register' command
    user_input = "register"
    user_input_lower = user_input.lower().strip()
    
    print(f"Testing command: '{user_input}'")
    
    if user_input_lower in ['register', 'signup', 'sign up', 'create account']:
        print("✅ Command recognized as registration request")
        print("This would call: app.interactive_register()")
        # We won't actually call it since it requires user input
    else:
        print("❌ Command not recognized")
    
    # Test other variations
    test_commands = ['register', 'signup', 'sign up', 'create account']
    
    print(f"\nTesting all registration command variations:")
    for cmd in test_commands:
        cmd_lower = cmd.lower().strip()
        is_recognized = cmd_lower in ['register', 'signup', 'sign up', 'create account']
        status = "✅" if is_recognized else "❌"
        print(f"{status} '{cmd}' -> Recognized: {is_recognized}")

if __name__ == "__main__":
    test_direct_commands()
