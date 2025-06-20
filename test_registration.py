#!/usr/bin/env python3
"""
Test script for registration functionality
"""

from ai_terminal_app import GeminiCarRentalTerminal

def test_registration():
    print("🧪 Testing Registration Functionality")
    print("=" * 50)
    
    app = GeminiCarRentalTerminal()
    
    # Test 1: Direct function call
    print("\n1. Testing direct registration function:")
    result = app.register_user("test1@example.com", "TestPass123!", "TEST001") 
    print(f"Result: {result}")
    
    # Test 2: Call tool routing
    print("\n2. Testing call_tool routing:")
    result = app.call_tool("user_register", {
        "email": "test2@example.com",
        "password": "TestPass456!",
        "national_id": "TEST002"
    })
    print(f"Result: {result}")
    
    # Test 3: Function schema check
    print("\n3. Checking function schema:")
    print(f"user_register in functions: {'user_register' in app.functions}")
    
    # Test 4: Interactive registration (simulate)
    print("\n4. Testing interactive registration method exists:")
    print(f"interactive_register method exists: {hasattr(app, 'interactive_register')}")
    
    print("\n✅ All registration tests completed!")

if __name__ == "__main__":
    test_registration()
