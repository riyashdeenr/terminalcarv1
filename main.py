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
from terms_manager import read_and_decrypt_terms


def display_terms_and_conditions():
    """Display decrypted terms and conditions"""
    try:     
        print("\n=== TERMS AND CONDITIONS ===")
        decrypted_tNc = read_and_decrypt_terms()
        print(decrypted_tNc)
        print("\nPress Enter to continue...")
        input()
    except FileNotFoundError:
        print("Terms and conditions file not found.")
    except Exception as e:
        print(f"Error displaying terms and conditions: {str(e)}")

def display_admin_menu(admin_manager: AdminManager, car_manager: CarManager):
    """Display admin management options"""
    while True:
        try:
            print("\n=== Admin Management Menu ===")
            print("1. User Management")
            print("2. Car Management")
            print("3. Booking Management")
            print("4. Asset Management")
            print("5. Revenue Analytics")
            print("6. Logout")
            choice = SecurityUtils.sanitize_input(input("Enter your choice (1-6): "))
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
                return True  # Return True to indicate logout
            else:
                print("Invalid choice. Please try again.")
        except Exception as e:
            print(f"Error in admin menu: {str(e)}")

def display_user_management_menu(admin_manager):
    """Display user management options"""
    while True:
        try:
            print("\n=== User Management Menu ===")
            print("1. View All Users")
            print("2. Search Bookings by Username")
            print("3. Back to Admin Menu")
            choice = SecurityUtils.sanitize_input(input("Enter your choice (1-3): "))
            if choice == "1":
                users = admin_manager.view_all_users()
                print("\nAll Users:")
                for user in users:
                    print(f"ID: {user['id']}, Email: {user['email']}, Role: {user['role']}")
            elif choice == "2":
                username = SecurityUtils.sanitize_input(input("Enter username (email): "))
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
        except Exception as e:
            print(f"Error in user management menu: {str(e)}")

def display_car_management_menu(admin_manager, car_manager):
    """Display car management options"""
    while True:
        try:
            print("\n=== Car Management Menu ===")
            print("1. View Car Status")
            print("2. Search Car by License Plate")
            print("3. Search Cars by Make/Model")
            print("4. Set Car Maintenance Status")
            print("5. Back to Admin Menu")
            choice = SecurityUtils.sanitize_input(input("Enter your choice (1-5): "))
            if choice == "1":
                print("\n=== Car Status Overview ===")
                cars = car_manager.show_car_status()
                if not cars:
                    print("No cars found in the system.")
                    continue
                categories = {}
                for car in cars:
                    cat = car['category']
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append(car)
                for category in sorted(categories.keys()):
                    print(f"\n{category.upper()} CARS:")
                    print("-" * 100)
                    print(f"{'ID':4} {'Make':12} {'Model':12} {'Year':6} {'License':10} {'Rate':8} {'Status':15} {'Booking Period':25} {'Booked By'}")
                    print("-" * 100)
                    for car in categories[category]:
                        booking_period = ""
                        if car['booking_start'] and car['booking_end']:
                            booking_period = f"{car['booking_start']} to {car['booking_end']}"
                        print(f"{car['id']:<4} {car['make']:<12} {car['model']:<12} {car['year']:<6} "
                              f"{car['license_plate']:<10} ${car['daily_rate']:<7.2f} {car['status']:<15} "
                              f"{booking_period:<25} {car['booked_by'] if car['booked_by'] else ''}")
                input("\nPress Enter to continue...")
            elif choice == "2":
                license_plate = SecurityUtils.sanitize_input(input("\nEnter license plate to search: ")).strip().upper()
                car = admin_manager.search_car_by_plate(license_plate)
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
                make = SecurityUtils.sanitize_input(input("Enter make: "))
                model = SecurityUtils.sanitize_input(input("Enter model: "))
                cars = admin_manager.search_cars_by_make_model(make, model)
                print("\nSearch Results:")
                for car in cars:
                    print(f"{car['make']} {car['model']} ({car['license_plate']})")
                    print(f"Status: {'Available' if car['is_available'] else 'Not Available'}")
                    if car['booked_by']:
                        print(f"Booked by: {car['booked_by']}")
                    print()  # Add a blank line between cars
            elif choice == "4":
                car_id = SecurityUtils.sanitize_input(input("Enter Car ID (press Enter to cancel): ")).strip()
                if not car_id:  # If empty input, return to menu
                    print("Operation cancelled.")
                    continue
                try:
                    car_id = int(car_id)
                    status = SecurityUtils.sanitize_input(input("Set to maintenance (yes/no)? ")).lower().strip()
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
        except Exception as e:
            print(f"Error in car management menu: {str(e)}")

def display_booking_management_menu(admin_manager):
    """Display booking management options"""
    while True:
        try:
            print("\n=== Booking Management Menu ===")
            print("1. View All Bookings")
            print("2. Search Booking by ID")
            print("3. View User Bookings")
            print("4. Back to Admin Menu")
            choice = SecurityUtils.sanitize_input(input("Enter your choice (1-4): "))
            if choice == "1":
                bookings = admin_manager.view_user_bookings()
                print("\nAll Bookings:")
                for booking in bookings:
                    print(f"Booking ID: {booking['id']}")
                    print(f"User: {booking['user_email']}")
                    print(f"Car: {booking['make']} {booking['model']}")
                    print(f"Period: {booking['start_date']} to {booking['end_date']}\n")
            elif choice == "2":
                booking_id = SecurityUtils.sanitize_input(input("Enter Booking ID: "))
                booking = admin_manager.search_booking_by_id(booking_id)
                if booking:
                    print(f"\nBooking Details:")
                    print(f"User: {booking['user_email']}")
                    print(f"Car: {booking['make']} {booking['model']}")
                    print(f"Period: {booking['start_date']} to {booking['end_date']}")
                else:
                    print("Booking not found.")
            elif choice == "3":
                user_id = SecurityUtils.sanitize_input(input("Enter User ID or Email: "))
                bookings = admin_manager.view_user_bookings(user_id)
                if not bookings:
                    print("No bookings found for this user.")
                    continue
                print("\nUser Bookings:")
                for booking in bookings:
                    # Calculate number of days and total cost
                    start_date = datetime.strptime(booking['start_date'], '%Y-%m-%d')
                    end_date = datetime.strptime(booking['end_date'], '%Y-%m-%d')
                    days = (end_date - start_date).days
                    daily_rate = booking.get('daily_rate', 0)
                    total_cost = daily_rate * days
                    print(f"\nBooking ID: {booking['id']}")
                    print(f"User: {booking['user_email']}")
                    print(f"Car: {booking['make']} {booking['model']}")
                    print(f"Period: {booking['start_date']} to {booking['end_date']}")
                    print(f"Duration: {days} days")
                    print(f"Daily Rate: ${daily_rate:.2f}")
                    print(f"Total Cost: ${total_cost:.2f}")
                    print(f"Status: {booking['status'].upper()}")
                    print("-" * 30)
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please try again.")
        except Exception as e:
            print(f"Error in booking management menu: {str(e)}")

def format_currency(value):
    """Format currency values with proper handling of None"""
    try:
        if value is None:
            return "$0.00"
        return f"${float(value):,.2f}"
    except Exception as e:
        print(f"Error formatting currency: {str(e)}")
        return "$0.00"

def format_date(value):
    """Format date values with proper handling of None"""
    try:
        return value if value else "Not set"
    except Exception as e:
        print(f"Error formatting date: {str(e)}")
        return "Not set"

def format_number(value):
    """Format integer values with proper NULL handling"""
    try:
        return f"{int(value or 0):,}"
    except (TypeError, ValueError) as e:
        print(f"Error formatting number: {str(e)}")
        return "0"
    except Exception as e:
        print(f"Unexpected error formatting number: {str(e)}")
        return "0"

def format_money(value):
    """Format monetary values with proper NULL handling"""
    try:
        return f"${float(value or 0):,.2f}"
    except (TypeError, ValueError) as e:
        print(f"Error formatting money: {str(e)}")
        return "$0.00"
    except Exception as e:
        print(f"Unexpected error formatting money: {str(e)}")
        return "$0.00"

def format_value(value, prefix="", suffix="", default="Not set"):
    """Format values with proper NULL handling"""
    try:
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return f"{prefix}{float(value):,.2f}{suffix}"
        return f"{value}"
    except Exception as e:
        print(f"Error formatting value: {str(e)}")
        return default

def display_asset_management_menu(admin_manager, car_manager):
    """Display asset management options"""
    while True:
        try:
            print("\n=== Asset Management Menu ===")
            print("1. View Asset Summary")
            print("2. View Car Asset Details")
            print("3. Update Car Asset Information")
            print("4. View Expiring Documents")
            print("5. Update Maintenance Record")
            print("6. Generate Asset Report")
            print("7. Back to Admin Menu")
            choice = SecurityUtils.sanitize_input(input("Enter your choice (1-7): "))
            if choice == "1":
                summary = admin_manager.view_asset_summary()
                if not summary:
                    print("No asset summary data available.")
                    continue
                fleet_value = summary.get('fleet_value', {})
                total_cars = fleet_value.get('total_cars') or 0
                fleet_value_amount = fleet_value.get('fleet_value') or 0
                total_maintenance = fleet_value.get('total_maintenance') or 0
                expiring = summary.get('expiring_soon', {})
                road_tax = expiring.get('road_tax_expiring') or 0
                insurance = expiring.get('insurance_expiring') or 0
                maintenance_due = expiring.get('maintenance_due') or 0
                print("\nFleet Summary:")
                print(f"Total Cars: {total_cars}")
                print(f"Fleet Value: {format_money(fleet_value_amount)}")
                print(f"Total Maintenance Cost: {format_money(total_maintenance)}")
                print("\nExpiring Soon:")
                print(f"Road Tax: {road_tax} cars")
                print(f"Insurance: {insurance} cars")
                print(f"Maintenance Due: {maintenance_due} cars")
            elif choice == "2":
                car_id = SecurityUtils.sanitize_input(input("Enter Car ID: "))
                try:
                    car_id = int(car_id)
                    details = admin_manager.get_asset_details(car_id)
                    if details:
                        print("\nCar Asset Details:")
                        print(f"Make/Model: {details['make']} {details['model']}")
                        print(f"Purchase Price: {format_money(details['purchase_price'])}")
                        print(f"Purchase Date: {details.get('purchase_date', 'Not set')}")
                        print(f"Road Tax Expiry: {details.get('road_tax_expiry', 'Not set')}")
                        print(f"Road Tax Amount: {format_money(details['road_tax_amount'])}")
                        print(f"Insurance Provider: {details.get('insurance_provider', 'Not set')}")
                        print(f"Insurance Expiry: {details.get('insurance_expiry', 'Not set')}")
                        print(f"Insurance Amount: {format_money(details['insurance_amount'])}")
                        print(f"Last Maintenance: {details.get('last_maintenance_date', 'Not set')}")
                        print(f"Next Maintenance: {details.get('next_maintenance_date', 'Not set')}")
                        print(f"Total Maintenance Cost: {format_money(details['total_maintenance_cost'])}")
                        print(f"Current Mileage: {format_number(details['mileage'])} km")
                        print(f"Total Bookings: {format_number(details['total_bookings'])}")
                        print(f"Total Rental Days: {format_number(details['total_rental_days'])}")
                    else:
                        print("Car not found.")
                except ValueError:
                    print("Invalid car ID. Please enter a number.")
                except Exception as e:
                    print(f"Error retrieving car details: {str(e)}")
            elif choice == "3":
                try:
                    car_id = SecurityUtils.sanitize_input(input("Enter Car ID: "))
                    asset_data = {
                        'purchase_date': SecurityUtils.sanitize_input(input("Purchase Date (YYYY-MM-DD): ")),
                        'purchase_price': float(SecurityUtils.sanitize_input(input("Purchase Price: "))),
                        'road_tax_expiry': SecurityUtils.sanitize_input(input("Road Tax Expiry (YYYY-MM-DD): ")),
                        'road_tax_amount': float(SecurityUtils.sanitize_input(input("Road Tax Amount: "))),
                        'insurance_expiry': SecurityUtils.sanitize_input(input("Insurance Expiry (YYYY-MM-DD): ")),
                        'insurance_provider': SecurityUtils.sanitize_input(input("Insurance Provider: ")),
                        'insurance_policy_number': SecurityUtils.sanitize_input(input("Insurance Policy Number: ")),
                        'insurance_amount': float(SecurityUtils.sanitize_input(input("Insurance Amount: ")))
                    }
                    success, msg = car_manager.update_car_assets(int(car_id), asset_data, 1)  # 1 is admin user_id
                    maintenance_data = {
                        'maintenance_date': SecurityUtils.sanitize_input(input("Maintenance Date (YYYY-MM-DD): ")),
                        'next_maintenance_date': SecurityUtils.sanitize_input(input("Next Maintenance Due (YYYY-MM-DD): ")),
                        'cost': float(SecurityUtils.sanitize_input(input("Maintenance Cost: "))),
                        'mileage': int(SecurityUtils.sanitize_input(input("Current Mileage: ")))
                    }
                    success, msg = car_manager.update_maintenance_record(int(car_id), maintenance_data, 1)  # 1 is admin user_id
                    print(msg)
                except Exception as e:
                    print(f"Error updating car asset information: {str(e)}")
            elif choice == "6":
                try:
                    start_date = SecurityUtils.sanitize_input(input("Start Date (YYYY-MM-DD) or press Enter for this month: "))
                    end_date = SecurityUtils.sanitize_input(input("End Date (YYYY-MM-DD) or press Enter for today: "))
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
                except Exception as e:
                    print(f"Error generating asset report: {str(e)}")
            elif choice == "7":
                break
            else:
                print("Invalid choice. Please try again.")
        except Exception as e:
            print(f"Error in asset management menu: {str(e)}")

def display_revenue_menu(admin_manager):
    """Display revenue analytics options"""
    while True:
        try:
            print("\n=== Revenue Analytics Menu ===")
            print("1. Overall Revenue Statistics")
            print("2. Car Revenue Details")
            print("3. Revenue Alerts")
            print("4. Back to Admin Menu")
            choice = SecurityUtils.sanitize_input(input("Enter your choice (1-4): "))
            if choice == "1":
                start_date = SecurityUtils.sanitize_input(input("Start Date (YYYY-MM-DD) or press Enter for this month: "))
                end_date = SecurityUtils.sanitize_input(input("End Date (YYYY-MM-DD) or press Enter for today: "))
                stats = admin_manager.get_revenue_statistics(start_date, end_date)
                print("\nOverall Revenue Statistics:")
                period = stats.get('period', {})
                print(f"Period: {period.get('start', 'Not set')} to {period.get('end', 'Not set')}")
                overall = stats.get('overall', {})
                print(f"Total Bookings: {format_number(overall.get('total_bookings'))}")
                print(f"Total Revenue: {format_money(overall.get('total_revenue'))}")
                print(f"Average Booking Value: {format_money(overall.get('average_booking_value'))}")
                print("\nRevenue by Category:")
                for cat in stats.get('by_category', []):
                    print(f"{cat.get('category', 'Unknown')}: {format_money(cat.get('revenue'))} ({format_number(cat.get('bookings'))} bookings)")
                print("\nTop Performing Cars:")
                for car in stats.get('top_cars', []):
                    print(f"{car.get('make', 'Unknown')} {car.get('model', '')}: {format_money(car.get('total_revenue'))}")
            elif choice == "2":
                car_id = SecurityUtils.sanitize_input(input("Enter Car ID: "))
                start_date = SecurityUtils.sanitize_input(input("Start Date (YYYY-MM-DD) or press Enter for this month: "))
                end_date = SecurityUtils.sanitize_input(input("End Date (YYYY-MM-DD) or press Enter for today: "))
                try:
                    car_id = int(car_id)
                    details = admin_manager.get_car_revenue_details(car_id, start_date, end_date)
                    if details:
                        car = details.get('car_details', {})
                        print(f"\nCar Revenue Details - {car.get('make')} {car.get('model')}:" )
                        print(f"Total Revenue: {format_money(car.get('total_revenue', 0))}")
                        print(f"Total Bookings: {format_number(car.get('total_bookings', 0))}")
                        print(f"Average Revenue per Booking: {format_money(car.get('avg_revenue_per_booking', 0))}")
                        print(f"ROI: {car.get('roi', 0):.1f}%")
                        monthly_revenue = details.get('monthly_revenue', [])
                        if monthly_revenue:
                            print("\nMonthly Revenue:")
                            for month in monthly_revenue:
                                print(f"{month.get('month', 'Unknown')}: {format_money(month.get('revenue', 0))}")
                        else:
                            print("\nNo monthly revenue data available.")
                    else:
                        print("Car not found.")
                except ValueError:
                    print("Invalid car ID. Please enter a number.")
                except Exception as e:
                    print(f"Error retrieving car details: {str(e)}")
            elif choice == "3":
                try:
                    alerts = admin_manager.get_revenue_alerts()
                    print("\nRevenue Performance Alerts:")
                    for alert in alerts:
                        car_avg = float(alert.get('car_avg_revenue', 0))
                        cat_avg = float(alert.get('category_avg_revenue', 0))
                        performance = (car_avg / cat_avg * 100) if cat_avg > 0 else 0
                        print(f"\n{alert.get('make', 'Unknown')} {alert.get('model', '')} ({alert.get('license_plate', '')}:")
                        print(f"Category: {alert.get('category', 'Unknown')}")
                        print(f"Average Revenue: {format_money(car_avg)}")
                        print(f"Category Average: {format_money(cat_avg)}")
                        print(f"Performance: {performance:.1f}% of category average")
                except Exception as e:
                    print(f"Error retrieving revenue alerts: {str(e)}")
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please try again.")
        except Exception as e:
            print(f"Error in revenue analytics menu: {str(e)}")

def calculate_total_cost(daily_rate: float, duration: int) -> float:
    """Calculate total cost for the booking duration"""
    try:
        return daily_rate * duration
    except Exception as e:
        print(f"Error calculating total cost: {str(e)}")
        return 0.0

def get_valid_date_input(prompt: str) -> str:
    """Get and validate date input from user"""
    while True:
        try:
            date_str = SecurityUtils.sanitize_input(input(prompt).strip())
            # Validate date format
            date = datetime.strptime(date_str, '%Y-%m-%d')
            if date.date() < datetime.now().date():
                print("Date cannot be in the past. Please enter a future date.")
                continue
            return date_str
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD format.")
        except Exception as e:
            print(f"Error validating date input: {str(e)}")

def display_user_menu(user_id: int, booking_manager, car_manager):
    """Display user menu options"""
    while True:
        try:
            print("\n=== User Menu ===")
            print("1. Book a car")
            print("2. View my bookings")
            print("3. Cancel a booking")
            print("4. View Terms and Conditions")
            print("5. Logout")
            choice = SecurityUtils.sanitize_input(input("Choose an option: ").strip())
            if choice == "1":  # Book a car
                try:
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
                            car_id = int(SecurityUtils.sanitize_input(input("\nEnter Car ID to book (0 to cancel): ").strip()))
                            if car_id == 0:
                                print("Booking cancelled.")
                                break
                            selected_car = next((car for car in cars if car['id'] == car_id), None)
                            if not selected_car:
                                print("Invalid Car ID. Please try again.")
                                continue
                            print("\nEnter booking details (format: YYYY-MM-DD)")
                            start_date = get_valid_date_input("Start Date: ")
                            while True:
                                try:
                                    duration = int(SecurityUtils.sanitize_input(input("Number of days to rent: ").strip()))
                                    if duration <= 0:
                                        print("Duration must be at least 1 day.")
                                        continue
                                    if duration > 30:
                                        print("Maximum rental duration is 30 days.")
                                        continue
                                    break
                                except ValueError:
                                    print("Please enter a valid number of days.")
                            end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=duration)).strftime('%Y-%m-%d')
                            total_cost = calculate_total_cost(selected_car['daily_rate'], duration)
                            print("\n=== Booking Summary ===")
                            print(f"Car: {selected_car['make']} {selected_car['model']}")
                            print(f"Category: {selected_car['category']}")
                            print(f"Start Date: {start_date}")
                            print(f"End Date: {end_date}")
                            print(f"Duration: {duration} days")
                            print(f"Daily Rate: ${selected_car['daily_rate']}")
                            print(f"Total Cost: ${total_cost:.2f}")
                            print("\nTerms and Conditions apply.")
                            confirm = SecurityUtils.sanitize_input(input("\nConfirm booking? (yes/no): ").strip().lower())
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
                        except Exception as e:
                            print(f"Error booking car: {str(e)}")
                except Exception as e:
                    print(f"Unexpected error during car booking: {str(e)}")
            elif choice == "2":  # View bookings
                try:
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
                except Exception as e:
                    print(f"Error viewing bookings: {str(e)}")
            elif choice == "3":  # Cancel booking
                try:
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
                    booking_id = SecurityUtils.sanitize_input(input("\nEnter Booking ID to cancel (press Enter to cancel): ").strip())
                    if not booking_id:
                        print("Operation cancelled.")
                        continue
                    try:
                        booking_id = int(booking_id)
                        if not any(b['id'] == booking_id for b in bookings):
                            print("Invalid Booking ID.")
                            continue
                        confirm = SecurityUtils.sanitize_input(input("Are you sure you want to cancel this booking? (yes/no): ").strip().lower())
                        if confirm == 'yes':
                            success, msg = booking_manager.cancel_booking(booking_id, user_id)
                            print(msg)
                        else:
                            print("Cancellation aborted.")
                    except ValueError:
                        print("Invalid Booking ID. Please enter a number.")
                    except Exception as e:
                        print(f"Error cancelling booking: {str(e)}")
                except Exception as e:
                    print(f"Error retrieving bookings: {str(e)}")
            elif choice == "4":  # View Terms
                try:
                    display_terms_and_conditions()
                except Exception as e:
                    print(f"Error displaying terms and conditions: {str(e)}")
            elif choice == "5":  # Logout
                return True  # Return True to indicate logout
            else:
                print("Invalid choice. Please try again.")
        except Exception as e:
            print(f"Error in user menu: {str(e)}")

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
                if display_admin_menu(admin_manager, car_manager):
                    if auth_manager.logout(session_token):
                        print("Logged out successfully.")
                    else:
                        print("Logout failed.")
                    session_token = None
                    user_id = None
                    is_admin = False
            else:
                if display_user_menu(user_id, booking_manager, car_manager):
                    # Logout successful
                    session_token = None
                    user_id = None
                    is_admin = False

if __name__ == "__main__":
    main()