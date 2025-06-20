#!/usr/bin/env python3
"""
Test script for AI-powered admin/statistics flows
Tests the enhanced admin functions in ai_terminal_app.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_terminal_app import GeminiCarRentalTerminal
    from admin_functions import AdminManager
    from database import DatabaseManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)

def test_admin_ai_functions():
    """Test the AI-powered admin functions"""
    print("🧪 Testing AI-Powered Admin/Statistics Functions")
    print("=" * 60)
    
    # Initialize the application
    try:
        app = GeminiCarRentalTerminal()
        print("✅ Application initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize application: {e}")
        return
    
    # Create an admin user for testing
    print("\n📝 Setting up test admin user...")
    try:
        # Create admin user manually for testing
        app.current_user = {"email": "admin@test.com", "national_id": "123456789", "role": "admin"}
        app.is_admin = True
        print("✅ Admin user set up for testing")
    except Exception as e:
        print(f"❌ Failed to set up admin user: {e}")
        return
    
    # Test 1: Get Asset Details
    print("\n🔍 Test 1: Asset Details Function")
    print("-" * 40)
    try:
        # Test with no car ID (should prompt)
        result = app.get_asset_details("")
        print("Result for empty car ID:")
        print(result)
        print()
        
        # Test with a specific car ID
        result = app.get_asset_details("1")
        print("Result for car ID '1':")
        print(result)
        print()
    except Exception as e:
        print(f"❌ Asset details test failed: {e}")
    
    # Test 2: Revenue Statistics
    print("\n💰 Test 2: Revenue Statistics Function")
    print("-" * 40)
    try:
        # Test with no dates (should use defaults)
        result = app.get_revenue_stats("", "")
        print("Result for empty dates:")
        print(result)
        print()
        
        # Test with specific dates
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        result = app.get_revenue_stats(start_date, end_date)
        print(f"Result for dates {start_date} to {end_date}:")
        print(result)
        print()
    except Exception as e:
        print(f"❌ Revenue statistics test failed: {e}")
    
    # Test 3: Asset Report Generation
    print("\n📊 Test 3: Asset Report Generation")
    print("-" * 40)
    try:
        # Test with no dates (should use defaults)
        result = app.generate_asset_report("", "")
        print("Result for empty dates:")
        print(result)
        print()
        
        # Test with specific dates
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        result = app.generate_asset_report(start_date, end_date)
        print(f"Result for dates {start_date} to {end_date}:")
        print(result)
        print()
    except Exception as e:
        print(f"❌ Asset report test failed: {e}")
    
    # Test 4: Car Revenue Details
    print("\n🚗 Test 4: Car Revenue Details")
    print("-" * 40)
    try:
        # Test with no parameters (should prompt)
        result = app.get_car_revenue_details("", "", "")
        print("Result for empty parameters:")
        print(result)
        print()
        
        # Test with car ID only
        result = app.get_car_revenue_details("1", "", "")
        print("Result for car ID '1' with empty dates:")
        print(result)
        print()
        
        # Test with full parameters
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        result = app.get_car_revenue_details("1", start_date, end_date)
        print(f"Result for car ID '1' with dates {start_date} to {end_date}:")
        print(result)
        print()
    except Exception as e:
        print(f"❌ Car revenue details test failed: {e}")
    
    # Test 5: Function Schema Validation
    print("\n🔧 Test 5: Function Schema Validation")
    print("-" * 40)
    try:
        functions = app._define_functions()
        admin_functions = [
            'get_asset_details', 
            'generate_asset_report', 
            'get_car_revenue_details', 
            'get_revenue_stats'
        ]
        
        for func_name in admin_functions:
            if func_name in functions:
                print(f"✅ {func_name}: Schema defined")
                # Check if it has proper parameters
                params = functions[func_name].get('parameters', {})
                if params:
                    print(f"   Parameters: {list(params.keys())}")
                else:
                    print("   No parameters defined")
            else:
                print(f"❌ {func_name}: Schema missing")
        print()
    except Exception as e:
        print(f"❌ Function schema validation failed: {e}")
    
    # Test 6: Function Call Mapping
    print("\n🔗 Test 6: Function Call Mapping")
    print("-" * 40)
    try:
        # Test the call_tool method with admin functions
        test_calls = [
            ("get_asset_details", {"car_id": "1"}),
            ("get_revenue_stats", {"start_date": "", "end_date": ""}),
            ("generate_asset_report", {"start_date": "", "end_date": ""}),
            ("get_car_revenue_details", {"car_id": "1", "start_date": "", "end_date": ""})
        ]
        
        for func_name, args in test_calls:
            try:
                result = app.call_tool(func_name, args)
                print(f"✅ {func_name}: Function call successful")
                print(f"   Result length: {len(result)} characters")
            except Exception as e:
                print(f"❌ {func_name}: Function call failed - {e}")
        print()
    except Exception as e:
        print(f"❌ Function call mapping test failed: {e}")

def test_database_content():
    """Check if we have test data in the database"""
    print("\n🗄️ Database Content Check")
    print("-" * 40)
    
    try:
        db = DatabaseManager()
        
        # Check cars
        cars_query = "SELECT car_id, make, model, year, daily_rate FROM cars LIMIT 5"
        cars = db.execute_query(cars_query)
        print(f"Cars in database: {len(cars) if cars else 0}")
        if cars:
            for car in cars[:3]:  # Show first 3
                print(f"  Car {car[0]}: {car[1]} {car[2]} ({car[3]}) - ${car[4]}/day")
        
        # Check bookings
        bookings_query = "SELECT COUNT(*) FROM bookings"
        booking_count = db.execute_query(bookings_query)
        print(f"Bookings in database: {booking_count[0][0] if booking_count else 0}")
        
        # Check users
        users_query = "SELECT COUNT(*) FROM users"
        user_count = db.execute_query(users_query)
        print(f"Users in database: {user_count[0][0] if user_count else 0}")
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Admin AI Function Tests")
    print("=" * 60)
    
    # First check database content
    test_database_content()
    
    # Then test admin functions
    test_admin_ai_functions()
    
    print("\n✅ All tests completed!")
    print("Check the output above to verify that admin functions are working correctly.")
