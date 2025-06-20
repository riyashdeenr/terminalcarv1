#!/usr/bin/env python3
"""Test script to check booking functionality in ai_terminal_app.py"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ai_terminal_app import GeminiCarRentalTerminal

def test_booking_flow():
    """Test the booking flow"""
    app = GeminiCarRentalTerminal()
    
    # Test 1: Check if booking functions are properly mapped
    print("=== Testing Function Mapping ===")
    functions = app.functions
    print(f"Available functions: {list(functions.keys())}")
    
    # Check for booking-related functions
    booking_funcs = [func for func in functions.keys() if 'booking' in func.lower() or 'book' in func.lower()]
    print(f"Booking-related functions: {booking_funcs}")
    
    # Test 2: Test view_user_bookings directly
    print("\n=== Testing view_user_bookings (not logged in) ===")
    try:
        result = app.view_user_bookings()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Test if function is callable through call_tool
    print("\n=== Testing call_tool mapping ===")
    try:
        result = app.call_tool("get_user_bookings", {})
        print(f"call_tool result: {result}")
    except Exception as e:
        print(f"call_tool error: {e}")

if __name__ == "__main__":
    test_booking_flow()
