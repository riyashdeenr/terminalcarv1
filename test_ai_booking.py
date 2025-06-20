#!/usr/bin/env python3
"""
Test script for AI booking functionality
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_terminal_app import GeminiCarRentalTerminal

def test_booking_flow():
    """Test the booking flow with various inputs"""
    print("🧪 Testing AI Booking Flow...")
    
    # Initialize the app (it will use the hardcoded API key)
    app = GeminiCarRentalTerminal()
    
    # Test cases for booking flow
    test_cases = [
        "i want to book a car for 3 days",
        "book car ID 1", 
        "1",  # Just a car ID
        "book car ID 1 for 3 days starting 2026-08-01",
        "2026-08-01",  # Just a date
        "ID 1 for 3 days",
        "show me available cars"
    ]
    
    print("\n📋 Testing various booking inputs:")
    print("=" * 50)
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n🔹 Test {i}: '{test_input}'")
        print("-" * 30)
        
        try:
            response = app.process_user_input(test_input)
            print(f"Response: {response}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()

    print("🎯 Test complete!")

if __name__ == "__main__":
    test_booking_flow()
