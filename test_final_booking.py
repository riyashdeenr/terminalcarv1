#!/usr/bin/env python3
"""Final test to verify all booking functionality works correctly"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ai_terminal_app import GeminiCarRentalTerminal

def test_booking_functionality():
    """Test all booking-related functionality"""
    app = GeminiCarRentalTerminal()
    
    print("🚗 **FINAL BOOKING FUNCTIONALITY TEST**")
    print("=" * 60)
    
    # Test 1: Login as regular user (user1@example.com)
    print("\n1️⃣ **Testing Regular User Login & Bookings**")
    print("-" * 40)
    
    # Login as user1 who should have bookings
    result = app.login_user("user1@example.com", "password123")
    print(f"Login result: {result}")
    
    if app.current_user:
        print(f"Logged in as: {app.current_user.get('email')} (ID: {app.current_user.get('user_id')})")
        
        # Test user bookings
        result = app.view_user_bookings()
        print(f"\nUser bookings:\n{result}")
        
        # Test show available cars
        print("\n2️⃣ **Testing Available Cars**")
        print("-" * 40)
        result = app.show_available_cars()
        print(f"Available cars:\n{result}")
        
        # Test booking creation
        print("\n3️⃣ **Testing Car Booking**")
        print("-" * 40)
        result = app.book_car(car_id=1, start_date="2025-07-15", duration=3)
        print(f"Booking result:\n{result}")
    
    # Test 2: Login as admin and test admin functions
    print("\n\n4️⃣ **Testing Admin Functions**")
    print("-" * 40)
    
    result = app.login_user("admin@carental.com", "Admin@2025")
    print(f"Admin login result: {result}")
    
    if app.is_admin:
        # Test admin functions through call_tool (simulating Gemini AI calls)
        print("\n🔧 Testing admin functions via call_tool:")
        
        functions_to_test = [
            ("get_all_users", {}),
            ("get_all_bookings", {}),
            ("get_car_status", {}),
            ("get_revenue_stats", {}),
            ("execute_sql", {"query": "SELECT COUNT(*) as total_bookings FROM bookings"})
        ]
        
        for func_name, args in functions_to_test:
            print(f"\n📋 Testing {func_name}:")
            try:
                result = app.call_tool(func_name, args)
                # Show first 200 characters to avoid too much output
                print(f"✅ Success: {result[:200]}{'...' if len(result) > 200 else ''}")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print("\n\n🎉 **TEST COMPLETE**")
    print("=" * 60)

if __name__ == "__main__":
    test_booking_functionality()
