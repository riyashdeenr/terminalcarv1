#!/usr/bin/env python3
"""
Quick test for the booking cancellation key error fix
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_terminal_app import GeminiCarRentalTerminal

def quick_test():
    """Quick test of the cancellation"""
    print("🔧 Quick test of cancellation fix...")
    
    app = GeminiCarRentalTerminal()
    
    # Login first
    app.login_user("admin@carental.com", "Admin@2025")
    
    # Test the cancel_booking function directly with a booking ID
    print("\n🔹 Testing cancel_booking function directly:")
    try:
        # This should NOT cause the 'id' key error anymore
        result = app.cancel_booking("24")
        print(f"✅ Result: {result[:100]}...")
    except Exception as e:
        if "'id'" in str(e):
            print("❌ Still has the 'id' key error!")
        else:
            print(f"ℹ️ Different error (this might be expected): {e}")
    
    # Test with empty booking ID
    print("\n🔹 Testing with empty booking ID:")
    try:
        result = app.cancel_booking("")
        print(f"✅ Result: {result[:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()
