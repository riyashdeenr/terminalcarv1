#!/usr/bin/env python3
"""Test script to check booking functionality when logged in"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from ai_terminal_app import GeminiCarRentalTerminal

def test_login_and_bookings():
    """Test login and booking functionality"""
    app = GeminiCarRentalTerminal()
    
    # Test 1: Login as admin
    print("=== Testing Admin Login ===")
    try:
        result = app.login_user("admin@carental.com", "Admin@2025")
        print(f"Login result: {result}")
        print(f"Current user: {app.current_user}")
        print(f"Is admin: {app.is_admin}")
    except Exception as e:
        print(f"Login error: {e}")
    
    # Test 2: Test view_user_bookings when logged in
    print("\n=== Testing view_user_bookings (logged in) ===")
    try:
        result = app.view_user_bookings()
        print(f"Bookings result: {result}")
    except Exception as e:
        print(f"Bookings error: {e}")
    
    # Test 3: Test admin functions
    print("\n=== Testing Admin Functions ===")
    try:
        # Test get_all_users
        result = app.get_all_users()
        print(f"All users: {result}")
        print("\n" + "="*50 + "\n")
        
        # Test get_all_bookings
        result = app.get_all_bookings()
        print(f"All bookings: {result}")
        print("\n" + "="*50 + "\n")
        
        # Test get_car_status
        result = app.get_car_status()
        print(f"Car status: {result}")
        print("\n" + "="*50 + "\n")
        
        # Test get_revenue_stats
        result = app.get_revenue_stats()
        print(f"Revenue stats: {result}")
        
    except Exception as e:
        print(f"Admin functions error: {e}")

if __name__ == "__main__":
    test_login_and_bookings()
