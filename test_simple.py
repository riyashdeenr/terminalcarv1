#!/usr/bin/env python3
"""
Simple test to verify function calling works
"""

from ai_terminal_app import GeminiCarRentalTerminal

def test_simple():
    """Simple test"""
    print("Starting simple test...")
    
    app = GeminiCarRentalTerminal()
    
    # Test if AI can call get_available_cars function
    print("\nTesting: 'show me available cars'")
    result = app.process_user_input("show me available cars")
    print(f"Result: {result}")

if __name__ == "__main__":
    test_simple()
