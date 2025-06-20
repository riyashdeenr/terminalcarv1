#!/usr/bin/env python3
"""
Quick test for the specific issue mentioned by user
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_terminal_app import GeminiCarRentalTerminal

def test_user_scenario():
    """Test the exact scenario mentioned by the user"""
    print("🎯 Testing the exact user scenario...")
    
    app = GeminiCarRentalTerminal()
    
    # Login first 
    print("1️⃣ Logging in...")
    login_response = app.login_user("admin@carental.com", "Admin@2025")
    print(f"✅ {login_response[:50]}...")
    
    # Test the user's exact inputs
    test_inputs = [
        "i want to book a car for 3 days",
        "1",  # Car ID selection
        "book car ID 1",
        "2026-08-01",  # Date input  
        "ID 1 for 3 days"
    ]
    
    print("\n2️⃣ Testing user scenario:")
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n🔸 User input {i}: '{user_input}'")
        try:
            response = app.process_user_input(user_input)
            # Show key parts of response
            if "Available Cars" in response:
                print("✅ Shows available cars with booking guidance")
            elif "I see you want to book" in response or "Please specify" in response:
                print("✅ Provides intelligent guidance for missing info")
            elif "Booking Confirmed" in response:
                print("✅ Successfully created booking!")
            else:
                print(f"📝 Response: {response[:100]}...")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_user_scenario()
