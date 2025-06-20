#!/usr/bin/env python3
"""
Test script for complete AI booking flow with login (using strong password)
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_terminal_app import GeminiCarRentalTerminal

def test_complete_booking_flow():
    """Test the complete booking flow including login"""
    print("🧪 Testing Complete AI Booking Flow (with proper credentials)...")
    
    # Initialize the app
    app = GeminiCarRentalTerminal()
    
    # Use the admin credentials that should already exist
    print("\n1️⃣ Testing admin login...")
    login_response = app.login_user("admin@example.com", "AdminPass123!")
    print(f"Login: {login_response}")
    
    # Now test booking scenarios while logged in
    booking_test_cases = [
        "i want to book a car for 3 days",
        "book car ID 1", 
        "1",  # Just a car ID
        "book car ID 1 for 3 days starting 2026-08-01",
        "2026-08-01",  # Just a date
        "ID 1 for 3 days",
        "show me available cars"
    ]
    
    print("\n2️⃣ Testing booking flows while logged in:")
    print("=" * 50)
    
    for i, test_input in enumerate(booking_test_cases, 1):
        print(f"\n🔹 Booking Test {i}: '{test_input}'")
        print("-" * 40)
        
        try:
            response = app.process_user_input(test_input)
            # Show only first 300 chars to keep output manageable
            response_short = response[:300] + "..." if len(response) > 300 else response
            print(f"Response: {response_short}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()

    print("🎯 Complete test finished!")

if __name__ == "__main__":
    test_complete_booking_flow()
