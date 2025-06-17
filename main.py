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

def display_admin_menu(admin_manager: AdminManager):
    while True:
        print("\n=== Admin Menu ===")
        print("1. View All Users")
        print("2. View All Bookings")
        print("3. View Car Status")
        print("4. Search Bookings")
        print("5. Search Cars")
        print("6. Return to Main Menu")
        print("7. Exit System")
        
        choice = input("Choose an option: ").strip()
        
        if choice == "1":
            users = admin_manager.view_all_users()
            print("\n=== User List ===")
            for user in users:
                print(f"ID: {user['id']}, Email: {user['email']}, Role: {user['role']}")
                print(f"Created: {user['created_at']}, Last Login: {user['last_login']}")
                print("-" * 50)
        
        elif choice == "2":
            bookings = admin_manager.view_user_bookings()
            print("\n=== All Bookings ===")
            for booking in bookings:
                print(f"Booking ID: {booking['id']}")
                print(f"User: {booking['user_email']}")
                print(f"Car: {booking['make']} {booking['model']} ({booking['license_plate']})")
                print(f"Period: {booking['start_date']} to {booking['end_date']}")
                print("-" * 50)
        
        elif choice == "3":
            print("\nCar Status Options:")
            print("1. View Available Cars")
            print("2. View Booked Cars")
            print("3. View All Cars")
            
            status_choice = input("Choose an option: ").strip()
            status = admin_manager.view_car_status()
            
            if status_choice == "1":
                print("\n=== Available Cars ===")
                for car in status['available']:
                    print(f"{car['make']} {car['model']} ({car['license_plate']})")
                    print(f"Daily Rate: ${car['daily_rate']}/day")
                    print(f"Category: {car['category']}")
                    print("-" * 30)
            
            elif status_choice == "2":
                print("\n=== Booked Cars ===")
                for car in status['not_available']:
                    print(f"{car['make']} {car['model']} ({car['license_plate']})")
                    print(f"Booked by: {car['booked_by']}")
                    print(f"Period: {car['start_date']} to {car['end_date']}")
                    print("-" * 30)
            
            elif status_choice == "3":
                print("\n=== All Cars Status ===")
                print("\nAvailable Cars:")
                for car in status['available']:
                    print(f"{car['make']} {car['model']} ({car['license_plate']}) - ${car['daily_rate']}/day")
                
                print("\nBooked Cars:")
                for car in status['not_available']:
                    print(f"{car['make']} {car['model']} ({car['license_plate']})")
                    print(f"Booked by: {car['booked_by']}")
                    print(f"Period: {car['start_date']} to {car['end_date']}")
                    print("-" * 30)
        
        elif choice == "4":
            print("\nSearch Bookings by:")
            print("1. Booking ID")
            print("2. Username")
            search_choice = input("Choose search option: ").strip()
            
            if search_choice == "1":
                booking_id = input("Enter Booking ID: ").strip()
                booking = admin_manager.search_booking_by_id(booking_id)
                if booking:
                    print("\n=== Booking Details ===")
                    print(f"Booking ID: {booking['id']}")
                    print(f"User: {booking['user_email']}")
                    print(f"Car: {booking['make']} {booking['model']} ({booking['license_plate']})")
                    print(f"Period: {booking['start_date']} to {booking['end_date']}")
                else:
                    print("Booking not found.")
            
            elif search_choice == "2":
                username = input("Enter username (email): ").strip()
                bookings = admin_manager.search_bookings_by_username(username)
                if bookings:
                    print("\n=== Bookings Found ===")
                    for booking in bookings:
                        print(f"Booking ID: {booking['id']}")
                        print(f"Car: {booking['make']} {booking['model']} ({booking['license_plate']})")
                        print(f"Period: {booking['start_date']} to {booking['end_date']}")
                        print("-" * 30)
                else:
                    print("No bookings found for this user.")
        
        elif choice == "5":
            print("\nSearch Cars by:")
            print("1. License Plate")
            print("2. Make and Model")
            search_choice = input("Choose search option: ").strip()
            
            if search_choice == "1":
                license_plate = input("Enter License Plate: ").strip()
                car = admin_manager.search_car_by_plate(license_plate)
                if car:
                    print("\n=== Car Details ===")
                    print(f"Make: {car['make']}")
                    print(f"Model: {car['model']}")
                    print(f"License Plate: {car['license_plate']}")
                    print(f"Daily Rate: ${car['daily_rate']}")
                    print(f"Status: {'Available' if car['is_available'] else 'Booked'}")
                else:
                    print("Car not found.")
            
            elif search_choice == "2":
                make = input("Enter Make: ").strip()
                model = input("Enter Model: ").strip()
                cars = admin_manager.search_cars_by_make_model(make, model)
                if cars:
                    print("\n=== Cars Found ===")
                    for car in cars:
                        print(f"Make: {car['make']}")
                        print(f"Model: {car['model']}")
                        print(f"License Plate: {car['license_plate']}")
                        print(f"Daily Rate: ${car['daily_rate']}")
                        print(f"Status: {'Available' if car['is_available'] else 'Booked'}")
                        print("-" * 30)
                else:
                    print("No cars found matching the criteria.")
        
        elif choice == "6":
            break
        
        elif choice == "7":
            print("Goodbye!")
            exit(0)

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
                display_admin_menu(admin_manager)
            else:
                print("\n=== User Menu ===")
                print("1. Book a car")
                print("2. View my bookings")
                print("3. View Terms and Conditions")
                print("4. Logout")
                print("5. Exit")
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
                
                elif choice == "2":
                    bookings = booking_manager.get_user_bookings(user_id)
                    print("\nYour Bookings:")
                    for booking in bookings:
                        print(f"Booking ID: {booking['id']}")
                        print(f"Start Date: {booking['start_date']}")
                        print(f"End Date: {booking['end_date']}")
                        print("-" * 30)
                
                elif choice == "3":
                    display_terms_and_conditions()
                
                elif choice == "4":
                    if auth_manager.logout(session_token):
                        print("Logged out successfully.")
                    else:
                        print("Logout failed.")
                    session_token = None
                    user_id = None
                    is_admin = False
                
                elif choice == "5":
                    print("Goodbye!")
                    break

if __name__ == "__main__":
    # Save encrypted terms and conditions
    save_encrypted_terms()
    main()