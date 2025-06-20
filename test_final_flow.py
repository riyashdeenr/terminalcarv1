#!/usr/bin/env python3
"""
Final test for complete AI booking flow with correct admin credentials
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_terminal_app import GeminiCarRentalTerminal

def test_final_booking_flow():
    """Test the complete booking flow with correct admin credentials"""
    print("🧪 Final Test: AI Booking Flow with Correct Admin Credentials...")
    
    # Initialize the app
    app = GeminiCarRentalTerminal()
    
    # Use the correct admin credentials
    print("\n1️⃣ Testing admin login...")
    login_response = app.login_user("admin@carental.com", "Admin@2025")
    print(f"Login: {login_response}")
    
    # Now test booking scenarios while logged in
    booking_test_cases = [
        "i want to book a car for 3 days",
        "book car ID 1", 
        "1",  # Just a car ID
        "book car ID 1 for 3 days starting 2026-08-01",
        "2026-08-01",  # Just a date
        "ID 1 for 3 days",
    ]
    
    print("\n2️⃣ Testing booking flows while logged in:")
    print("=" * 60)
    
    for i, test_input in enumerate(booking_test_cases, 1):
        print(f"\n🔹 Booking Test {i}: '{test_input}'")
        print("-" * 40)
        
        try:
            response = app.process_user_input(test_input)
            # Show first 500 chars to see the full message flow
            response_short = response[:500] + "..." if len(response) > 500 else response
            print(f"Response: {response_short}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()

    print("🎯 Final test finished!")
    print("\n✅ Summary: The AI should now:")
    print("   - Always call booking function for any booking request")
    print("   - Guide users through missing information step by step") 
    print("   - Provide context-aware prompts instead of generic responses")
    print("   - Handle partial booking information intelligently")

if __name__ == "__main__":
    test_final_booking_flow()
