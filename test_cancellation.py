#!/usr/bin/env python3
"""
Test the booking cancellation fix
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_terminal_app import GeminiCarRentalTerminal

def test_cancellation():
    """Test the cancellation functionality"""
    print("🧪 Testing Booking Cancellation Fix...")
    
    app = GeminiCarRentalTerminal()
    
    # Login with admin credentials
    print("1️⃣ Logging in...")
    login_response = app.login_user("admin@carental.com", "Admin@2025")
    print(f"✅ {login_response[:50]}...")
    
    # Test cancellation scenarios
    test_inputs = [
        "view my bookings",
        "cancel this booking",
        "cancel booking ID 24"
    ]
    
    print("\n2️⃣ Testing cancellation scenarios:")
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n🔸 Test {i}: '{user_input}'")
        try:
            response = app.process_user_input(user_input)
            # Show relevant parts
            if "Your Bookings" in response:
                print("✅ Shows user bookings")
            elif "specify which booking" in response:
                print("✅ Asks user to specify booking ID when missing")
            elif "cancelled successfully" in response:
                print("✅ Successfully cancelled booking!")
            elif "Error cancelling booking: 'id'" in response:
                print("❌ Still has the 'id' key error!")
            else:
                print(f"📝 Response: {response[:150]}...")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_cancellation()
