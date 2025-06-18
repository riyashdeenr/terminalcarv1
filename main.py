#!/usr/bin/env python3
"""
Secure Car Rental Management System
Educational Implementation with AI Integration
"""
import hashlib
import secrets
import base64
import re
import sqlite3
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote, unquote
import threading
from contextlib import contextmanager
from security import SecurityUtils  # Add this import

# Minimal web server implementation
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs

# Importing components
from auth import AuthenticationManager
from database import DatabaseManager
from car_manager import CarManager
from booking_manager import BookingManager
from admin_functions import AdminManager
from gemini import get_ai_response

def save_encrypted_terms():
    """Save encrypted terms and conditions file"""
    terms_content = """
    SECURE CAR RENTAL TERMS AND CONDITIONS
    
    1. RENTAL AGREEMENT
    This agreement constitutes the entire rental contract between the customer and Secure Car Rental.
    
    2. DRIVER REQUIREMENTS
    - Must be at least 21 years of age
    - Valid driver's license required
    - Clean driving record preferred
    
    3. VEHICLE CONDITION
    - Vehicle must be returned in same condition as received
    - Interior and exterior cleaning required
    - Fuel level must match pickup level
    
    4. SECURITY DEPOSIT
    - Required for all rentals
    - Refunded upon satisfactory vehicle return
    - May be used for damages or violations
    
    5. INSURANCE COVERAGE
    - Basic coverage included
    - Additional coverage available
    - Customer responsible for deductibles
    
    6. PROHIBITED USES
    - No smoking in vehicles
    - No pets without prior approval
    - No off-road driving
    - No racing or competitive events
    
    7. CANCELLATION POLICY
    - 24-hour advance notice required
    - Fees may apply for late cancellations
    - Emergency cancellations considered case-by-case
    
    8. LIABILITY
    - Customer liable for traffic violations
    - Customer liable for parking tickets
    - Customer liable for vehicle damage
    
    9. LATE RETURNS
    - Grace period: 30 minutes
    - Late fees apply after grace period
    - Daily rate charged for overnight delays
    
    10. AGREEMENT ACCEPTANCE
    By booking a vehicle, customer agrees to all terms and conditions herein.
    """
    
    # Encrypt and save
    key = "SecureCarRental2024"
    encrypted_terms = SecurityUtils.encrypt_data(terms_content, key)
    
    with open("terms_conditions.enc", "w") as f:
        f.write(encrypted_terms)
    
    print("✅ Encrypted terms and conditions saved to terms_conditions.enc")

def display_terms_and_conditions():
    """Display decrypted terms and conditions"""
    try:
        # Read encrypted terms
        with open("terms_conditions.enc", "r") as f:
            encrypted_terms = f.read()
        
        # Decrypt terms using the same key used for encryption
        key = "SecureCarRental2024"
        decrypted_terms = SecurityUtils.decrypt_data(encrypted_terms, key)
        
        print("\n=== TERMS AND CONDITIONS ===")
        print(decrypted_terms)
        print("\nPress Enter to continue...")
        input()
    except FileNotFoundError:
        print("Terms and conditions file not found.")
    except Exception as e:
        print(f"Error displaying terms and conditions: {str(e)}")

def display_admin_menu(admin_manager: AdminManager, car_manager: CarManager):
    """Display admin management options"""
    while True:
        print("\n=== Admin Management Menu ===")
        print("1. User Management")
        print("2. Car Management")
        print("3. Booking Management")
        print("4. Asset Management")
        print("5. Revenue Analytics")
        print("6. Back to Main Menu")
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            display_user_management_menu(admin_manager)
        elif choice == "2":
            display_car_management_menu(admin_manager, car_manager)
        elif choice == "3":
            display_booking_management_menu(admin_manager)
        elif choice == "4":
            display_asset_management_menu(admin_manager, car_manager)
        elif choice == "5":
            display_revenue_menu(admin_manager)
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")

def display_user_management_menu(admin_manager):
    """Display user management options"""
    while True:
        print("\n=== User Management Menu ===")
        print("1. View All Users")
        print("2. Search Bookings by Username")
        print("3. Back to Admin Menu")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == "1":
            users = admin_manager.view_all_users()
            print("\nAll Users:")
            for user in users:
                print(f"ID: {user['id']}, Email: {user['email']}, Role: {user['role']}")
        
        elif choice == "2":
            username = input("Enter username (email): ")
            bookings = admin_manager.search_bookings_by_username(username)
            print("\nUser Bookings:")
            for booking in bookings:
                print(f"Booking ID: {booking['id']}")
                print(f"Car: {booking['make']} {booking['model']}")
                print(f"Period: {booking['start_date']} to {booking['end_date']}\n")
        
        elif choice == "3":
            break
        else:
            print("Invalid choice. Please try again.")

def display_car_management_menu(admin_manager, car_manager):
    """Display car management options"""
    while True:
        print("\n=== Car Management Menu ===")
        print("1. View Car Status")
        print("2. Search Car by License Plate")
        print("3. Search Cars by Make/Model")
        print("4. Set Car Maintenance Status")
        print("5. Back to Admin Menu")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == "1":
            status = admin_manager.view_car_status()
            print("\nAvailable Cars:")
            for car in status['available']:
                print(f"{car['make']} {car['model']} ({car['license_plate']})")
            print("\nBooked Cars:")
            for car in status['not_available']:
                print(f"{car['make']} {car['model']} ({car['license_plate']}) - Booked by: {car['booked_by']}")
        
        elif choice == "2":
            plate = input("Enter license plate: ")
            car = admin_manager.search_car_by_plate(plate)
            if car:
                print(f"\nCar Details:")
                print(f"Make/Model: {car['make']} {car['model']}")
                print(f"Year: {car['year']}")
                print(f"Status: {'Available' if car['is_available'] else 'Not Available'}")
                if car['booked_by']:
                    print(f"Booked by: {car['booked_by']}")
            else:
                print("Car not found.")
        
        elif choice == "3":
            make = input("Enter make: ")
            model = input("Enter model: ")
            cars = admin_manager.search_cars_by_make_model(make, model)
            print("\nSearch Results:")
            for car in cars:
                print(f"{car['make']} {car['model']} ({car['license_plate']})")
                print(f"Status: {'Available' if car['is_available'] else 'Not Available'}")
                if car['booked_by']:
                    print(f"Booked by: {car['booked_by']}")
                print()  # Add a blank line between cars
        
        elif choice == "4":
            car_id = input("Enter Car ID (press Enter to cancel): ").strip()
            if not car_id:  # If empty input, return to menu
                print("Operation cancelled.")
                continue
            try:
                car_id = int(car_id)
                status = input("Set to maintenance (yes/no)? ").lower().strip()
                if not status:  # If empty input, return to menu
                    print("Operation cancelled.")
                    continue
                status = status == 'yes'
                success, msg = car_manager.set_maintenance_status(car_id, status, 1)  # 1 is admin user_id
                print(msg)
            except ValueError:
                print("Invalid car ID. Please enter a valid number.")
        
        elif choice == "5":
            break
        else:
            print("Invalid choice. Please try again.")

def display_booking_management_menu(admin_manager):
    """Display booking management options"""
    while True:
        print("\n=== Booking Management Menu ===")
        print("1. View All Bookings")
        print("2. Search Booking by ID")
        print("3. View User Bookings")
        print("4. Back to Admin Menu")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == "1":
            bookings = admin_manager.view_user_bookings()
            print("\nAll Bookings:")
            for booking in bookings:
                print(f"Booking ID: {booking['id']}")
                print(f"User: {booking['user_email']}")
                print(f"Car: {booking['make']} {booking['model']}")
                print(f"Period: {booking['start_date']} to {booking['end_date']}\n")
        
        elif choice == "2":
            booking_id = input("Enter Booking ID: ")
            booking = admin_manager.search_booking_by_id(booking_id)
            if booking:
                print(f"\nBooking Details:")
                print(f"User: {booking['user_email']}")
                print(f"Car: {booking['make']} {booking['model']}")
                print(f"Period: {booking['start_date']} to {booking['end_date']}")
            else:
                print("Booking not found.")
        
        elif choice == "3":
            user_id = input("Enter User ID: ")
            bookings = admin_manager.view_user_bookings(int(user_id))
            print("\nUser Bookings:")
            for booking in bookings:
                print(f"Booking ID: {booking['id']}")
                print(f"Car: {booking['make']} {booking['model']}")
                print(f"Period: {booking['start_date']} to {booking['end_date']}\n")
        
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")

def display_asset_management_menu(admin_manager, car_manager):
    """Display asset management options"""
    while True:
        print("\n=== Asset Management Menu ===")
        print("1. View Asset Summary")
        print("2. View Car Asset Details")
        print("3. Update Car Asset Information")
        print("4. View Expiring Documents")
        print("5. Update Maintenance Record")
        print("6. Generate Asset Report")
        print("7. Back to Admin Menu")
        
        choice = input("Enter your choice (1-7): ")
        
        if choice == "1":
            summary = admin_manager.view_asset_summary()
            print("\nFleet Summary:")
            print(f"Total Cars: {summary['fleet_value']['total_cars']}")
            print(f"Fleet Value: ${summary['fleet_value']['fleet_value']:,.2f}")
            print(f"Total Maintenance Cost: ${summary['fleet_value']['total_maintenance']:,.2f}")
            print("\nExpiring Soon:")
            print(f"Road Tax: {summary['expiring_soon']['road_tax_expiring']} cars")
            print(f"Insurance: {summary['expiring_soon']['insurance_expiring']} cars")
            print(f"Maintenance: {summary['expiring_soon']['maintenance_due']} cars")
        
        elif choice == "2":
            car_id = input("Enter Car ID: ")
            details = admin_manager.get_asset_details(int(car_id))
            if details:
                print("\nCar Asset Details:")
                print(f"Make/Model: {details['make']} {details['model']}")
                print(f"Purchase Price: ${details.get('purchase_price', 'N/A'):,.2f}")
                print(f"Total Rentals: {details['total_bookings']}")
                print(f"Total Rental Days: {details['total_rental_days']}")
            else:
                print("Car not found.")
        
        elif choice == "3":
            car_id = input("Enter Car ID: ")
            asset_data = {
                'purchase_date': input("Purchase Date (YYYY-MM-DD): "),
                'purchase_price': float(input("Purchase Price: ")),
                'road_tax_expiry': input("Road Tax Expiry (YYYY-MM-DD): "),
                'road_tax_amount': float(input("Road Tax Amount: ")),
                'insurance_expiry': input("Insurance Expiry (YYYY-MM-DD): "),
                'insurance_provider': input("Insurance Provider: "),
                'insurance_policy_number': input("Insurance Policy Number: "),
                'insurance_amount': float(input("Insurance Amount: "))
            }
            success, msg = car_manager.update_car_assets(int(car_id), asset_data, 1)  # 1 is admin user_id
            print(msg)
        
        elif choice == "4":
            days = int(input("Check documents expiring within days (default 30): ") or 30)
            expiring = car_manager.get_expiring_assets(days)
            
            print("\nRoad Tax Expiring:")
            for car in expiring['road_tax_expiring']:
                print(f"{car['make']} {car['model']} ({car['license_plate']}) - Expires: {car['road_tax_expiry']}")
            
            print("\nInsurance Expiring:")
            for car in expiring['insurance_expiring']:
                print(f"{car['make']} {car['model']} ({car['license_plate']}) - Expires: {car['insurance_expiry']}")
        
        elif choice == "5":
            car_id = input("Enter Car ID: ")
            maintenance_data = {
                'maintenance_date': input("Maintenance Date (YYYY-MM-DD): "),
                'next_maintenance_date': input("Next Maintenance Due (YYYY-MM-DD): "),
                'cost': float(input("Maintenance Cost: ")),
                'mileage': int(input("Current Mileage: "))
            }
            success, msg = car_manager.update_maintenance_record(int(car_id), maintenance_data, 1)  # 1 is admin user_id
            print(msg)
        
        elif choice == "6":
            start_date = input("Start Date (YYYY-MM-DD) or press Enter for this month: ")
            end_date = input("End Date (YYYY-MM-DD) or press Enter for today: ")
            report = admin_manager.generate_asset_report(start_date, end_date)
            
            print("\nAsset Report:")
            print(f"Period: {report['period']['start']} to {report['period']['end']}")
            print(f"\nFinancial Summary:")
            print(f"Total Investment: ${report['financials']['total_investment']:,.2f}")
            print(f"Total Maintenance: ${report['financials']['total_maintenance']:,.2f}")
            print(f"Total Road Tax: ${report['financials']['total_road_tax']:,.2f}")
            print(f"Total Insurance: ${report['financials']['total_insurance']:,.2f}")
            
            print(f"\nRental Summary:")
            print(f"Total Bookings: {report['rentals']['total_bookings']}")
            print(f"Total Rental Days: {report['rentals']['total_rental_days']}")
            print(f"Cars Rented: {report['rentals']['cars_rented']}")
        
        elif choice == "7":
            break
        else:
            print("Invalid choice. Please try again.")

def display_revenue_menu(admin_manager):
    """Display revenue analytics options"""
    while True:
        print("\n=== Revenue Analytics Menu ===")
        print("1. Overall Revenue Statistics")
        print("2. Car Revenue Details")
        print("3. Revenue Alerts")
        print("4. Back to Admin Menu")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == "1":
            start_date = input("Start Date (YYYY-MM-DD) or press Enter for this month: ")
            end_date = input("End Date (YYYY-MM-DD) or press Enter for today: ")
            stats = admin_manager.get_revenue_statistics(start_date, end_date)
            
            print("\nOverall Revenue Statistics:")
            print(f"Period: {stats['period']['start']} to {stats['period']['end']}")
            print(f"Total Bookings: {stats['overall']['total_bookings']}")
            print(f"Total Revenue: ${stats['overall']['total_revenue']:,.2f}")
            print(f"Average Booking Value: ${stats['overall']['average_booking_value']:,.2f}")
            
            print("\nRevenue by Category:")
            for cat in stats['by_category']:
                print(f"{cat['category']}: ${cat['revenue']:,.2f} ({cat['bookings']} bookings)")
            
            print("\nTop Performing Cars:")
            for car in stats['top_cars']:
                print(f"{car['make']} {car['model']}: ${car['total_revenue']:,.2f}")
        
        elif choice == "2":
            car_id = input("Enter Car ID: ")
            start_date = input("Start Date (YYYY-MM-DD) or press Enter for this month: ")
            end_date = input("End Date (YYYY-MM-DD) or press Enter for today: ")
            
            details = admin_manager.get_car_revenue_details(int(car_id), start_date, end_date)
            if details:
                car = details['car_details']
                print(f"\nCar Revenue Details - {car['make']} {car['model']}:")
                print(f"Total Revenue: ${car['total_revenue']:,.2f}")
                print(f"Total Bookings: {car['total_bookings']}")
                print(f"Average Revenue per Booking: ${car['avg_revenue_per_booking']:,.2f}")
                if 'roi' in car:
                    print(f"ROI: {car['roi']:.1f}%")
                
                print("\nMonthly Revenue:")
                for month in details['monthly_revenue']:
                    print(f"{month['month']}: ${month['revenue']:,.2f}")
            else:
                print("Car not found.")
        
        elif choice == "3":
            alerts = admin_manager.get_revenue_alerts()
            print("\nRevenue Performance Alerts:")
            for alert in alerts:
                print(f"\n{alert['make']} {alert['model']} ({alert['license_plate']}):")
                print(f"Category: {alert['category']}")
                print(f"Average Revenue: ${alert['car_avg_revenue']:,.2f}")
                print(f"Category Average: ${alert['category_avg_revenue']:,.2f}")
                print(f"Performance: {(alert['car_avg_revenue']/alert['category_avg_revenue']*100):.1f}% of category average")
        
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")

def calculate_total_cost(daily_rate: float, duration: int) -> float:
    """Calculate total cost for the booking duration"""
    return daily_rate * duration

def get_valid_date_input(prompt: str) -> str:
    """Get and validate date input from user"""
    while True:
        date_str = input(prompt).strip()
        try:
            # Validate date format
            date = datetime.strptime(date_str, '%Y-%m-%d')
            if date.date() < datetime.now().date():
                print("Date cannot be in the past. Please enter a future date.")
                continue
            return date_str
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD format.")

def display_user_menu(user_id: int, booking_manager, car_manager):
    """Display user menu options"""
    while True:
        print("\n=== User Menu ===")
        print("1. Book a car")
        print("2. View my bookings")
        print("3. Cancel a booking")
        print("4. View Terms and Conditions")
        print("5. Logout")
        
        choice = input("Choose an option: ").strip()
        
        if choice == "1":  # Book a car
            cars = car_manager.show_available_cars()
            if not cars:
                print("\nNo cars available for booking.")
                continue
            
            print("\nAvailable Cars:")
            for car in cars:
                print(f"\nCar ID: {car['id']}")
                print(f"Make/Model: {car['make']} {car['model']}")
                print(f"Category: {car['category']}")
                print(f"Daily Rate: ${car['daily_rate']}/day")
                print("-" * 30)
            
            while True:
                try:
                    car_id = int(input("\nEnter Car ID to book (0 to cancel): ").strip())
                    if car_id == 0:
                        print("Booking cancelled.")
                        break
                    
                    selected_car = next((car for car in cars if car['id'] == car_id), None)
                    if not selected_car:
                        print("Invalid Car ID. Please try again.")
                        continue
                    
                    # Get booking dates
                    print("\nEnter booking details (format: YYYY-MM-DD)")
                    start_date = get_valid_date_input("Start Date: ")
                    
                    while True:
                        try:
                            duration = int(input("Number of days to rent: ").strip())
                            if duration <= 0:
                                print("Duration must be at least 1 day.")
                                continue
                            if duration > 30:
                                print("Maximum rental duration is 30 days.")
                                continue
                            break
                        except ValueError:
                            print("Please enter a valid number of days.")
                    
                    # Calculate end date and total cost
                    end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=duration)).strftime('%Y-%m-%d')
                    total_cost = calculate_total_cost(selected_car['daily_rate'], duration)
                    
                    # Show booking summary
                    print("\n=== Booking Summary ===")
                    print(f"Car: {selected_car['make']} {selected_car['model']}")
                    print(f"Category: {selected_car['category']}")
                    print(f"Start Date: {start_date}")
                    print(f"End Date: {end_date}")
                    print(f"Duration: {duration} days")
                    print(f"Daily Rate: ${selected_car['daily_rate']}")
                    print(f"Total Cost: ${total_cost:.2f}")
                    print("\nTerms and Conditions apply.")
                    
                    # Get confirmation
                    confirm = input("\nConfirm booking? (yes/no): ").strip().lower()
                    if confirm == 'yes':
                        success, message = booking_manager.create_booking(
                            user_id=user_id,
                            car_id=car_id,
                            start_date=start_date,
                            end_date=end_date
                        )
                        print(message)
                        if success:
                            print(f"\nTotal amount to pay: ${total_cost:.2f}")
                            print("Thank you for your booking!")
                    else:
                        print("Booking cancelled.")
                    break
                
                except ValueError:
                    print("Invalid input. Please enter a valid Car ID.")
        
        elif choice == "2":  # View bookings
            bookings = booking_manager.get_user_bookings(user_id)
            if not bookings:
                print("\nYou have no bookings.")
                continue
                
            print("\nYour Bookings:")
            for booking in bookings:
                print(f"\nBooking ID: {booking['id']}")
                print(f"Car: {booking['make']} {booking['model']}")
                print(f"Start Date: {booking['start_date']}")
                print(f"End Date: {booking['end_date']}")
                print(f"Total Amount: ${booking['total_amount']:.2f}")
                print(f"Status: {booking['status']}")
                print("-" * 30)
        
        elif choice == "3":  # Cancel booking
            bookings = booking_manager.get_user_bookings(user_id)
            if not bookings:
                print("\nYou have no bookings to cancel.")
                continue
            
            print("\nYour Bookings:")
            for booking in bookings:
                print(f"\nBooking ID: {booking['id']}")
                print(f"Car: {booking['make']} {booking['model']}")
                print(f"Start Date: {booking['start_date']}")
                print(f"End Date: {booking['end_date']}")
                print(f"Total Amount: ${booking['total_amount']:.2f}")
                print(f"Status: {booking['status']}")
                print("-" * 30)
            
            booking_id = input("\nEnter Booking ID to cancel (press Enter to cancel): ").strip()
            if not booking_id:
                print("Operation cancelled.")
                continue
            
            try:
                booking_id = int(booking_id)
                if not any(b['id'] == booking_id for b in bookings):
                    print("Invalid Booking ID.")
                    continue
                
                confirm = input("Are you sure you want to cancel this booking? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    success, msg = booking_manager.cancel_booking(booking_id, user_id)
                    print(msg)
                else:
                    print("Cancellation aborted.")
            except ValueError:
                print("Invalid Booking ID. Please enter a number.")
        
        elif choice == "4":  # View Terms
            display_terms_and_conditions()
        
        elif choice == "5":  # Logout
            return True  # Return True to indicate logout
        
        else:
            print("Invalid choice. Please try again.")

def main():
    db_manager = DatabaseManager()
    auth_manager = AuthenticationManager(db_manager)
    car_manager = CarManager(db_manager)
    booking_manager = BookingManager(db_manager)
    admin_manager = AdminManager(db_manager)
    session_token = None
    user_id = None
    is_admin = False

    print("\n=== Car Rental System ===")
    print("(Admin credentials will be displayed during first run)")

    while True:
        if not session_token:
            print("\n1. Register")
            print("2. Login")
            print("3. Exit")
            choice = input("Choose an option: ").strip()
            
            if choice == "1":
                email = input("Email: ").strip()
                password = input("Password: ").strip()
                national_id = input("National ID: ").strip()
                success, msg = auth_manager.register_user(email, password, national_id)
                print(msg)
            
            elif choice == "2":
                email = input("Email: ").strip()
                password = input("Password: ").strip()
                success, msg, user_info = auth_manager.login(email, password)
                print(msg)
                if success:
                    session_token = user_info['session_token']
                    user_id = user_info['user_id']
                    is_admin = user_info['role'] == 'admin'
            
            elif choice == "3":
                print("Goodbye!")
                break
        
        else:
            if is_admin:
                display_admin_menu(admin_manager, car_manager)
            else:
                if display_user_menu(user_id, booking_manager, car_manager):
                    # Logout successful
                    session_token = None
                    user_id = None
                    is_admin = False

if __name__ == "__main__":
    # Save encrypted terms and conditions
    save_encrypted_terms()
    main()