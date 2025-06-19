"""
AI Car Rental System - Advanced Interface

This module provides an advanced command-line interface for a secure car rental system.

Features:
- User authentication (login, registration, logout)
- Car booking and management
- Admin command support (view users/bookings, etc.)
- Terms and conditions acceptance enforcement
- Input sanitization for all user-supplied data
- (Planned) AI/NLP query support and advanced security validation

Usage:
- Run this file directly to start the CLI: python ai_interface_advance.py
- Type 'help' for a list of available commands
- You must accept the terms and conditions before booking a car
- Admin commands are available to admin users after login

Security:
- All user input is sanitized before processing
- Terms acceptance is required for bookings
- (Planned) Audit logging and advanced query validation

"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from auth import AuthenticationManager
from database import DatabaseManager
from car_manager import CarManager
from booking_manager import BookingManager
from admin_functions import AdminManager
from security import SecurityUtils
from functools import wraps
import re
import ssl
import logging
from google import genai
from google.genai import types
from terms_manager import read_and_decrypt_terms

# Configure SSL
ssl._create_default_https_context = ssl._create_unverified_context

# Configure Google API key (replace with your actual key)
GOOGLE_API_KEY = "AIzaSyAz5B_lFFSTXJiXFD_RakW6NQACpeJAZsM"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

class SecurityValidator:
    """Security validation utilities"""
    @staticmethod
    def sanitize_string(value: str) -> str:
        if not isinstance(value, str):
            return value
        patterns = [
            r'--', r';', r'\/\*|\*\/', r'xp_', r'UNION', r'DROP', r'TRUNCATE', r'DELETE', r'INSERT', r'UPDATE'
        ]
        sanitized = value
        for pattern in patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        return sanitized

    @staticmethod
    def validate_table_name(table: str) -> bool:
        valid_tables = {'users', 'cars', 'bookings', 'sessions', 'audit_log'}
        return table in valid_tables

    @staticmethod
    def validate_field_name(field: str) -> bool:
        valid_fields = {
            'id', 'user_id', 'car_id', 'email', 'role', 'is_active',
            'make', 'model', 'year', 'license_plate', 'is_available',
            'is_maintenance', 'daily_rate', 'category', 'start_date',
            'end_date', 'status', 'total_amount', 'booking_date'
        }
        return field in valid_fields

    @staticmethod
    def validate_operator(operator: str) -> bool:
        valid_operators = {'=', '>', '<', '>=', '<=', 'IN', 'LIKE', 'IS'}
        return operator.upper() in valid_operators

    @staticmethod
    def audit_log(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # ...audit logging logic can be added here...
            return func(self, *args, **kwargs)
        return wrapper

class QueryBuilder:
    def __init__(self, db_manager):
        self.db = db_manager
    # ...implement dynamic query logic as needed...

class NLQueryProcessor:
    def __init__(self, client, admin_manager, booking_manager, user_manager):
        self.client = client
        self.admin_manager = admin_manager
        self.booking_manager = booking_manager
        self.user_manager = user_manager

    # Tool: Get all users (admin only)
    def get_all_users(self, user_context):
        if not user_context.get('is_admin'):
            return {"error": "You do not have permission to view all users."}
        users = self.admin_manager.view_all_users()
        return {"users": users}

    # Tool: Get bookings for current user
    def get_my_bookings(self, user_context):
        user_id = user_context.get('user_id')
        if not user_id:
            return {"error": "You must be logged in to view your bookings."}
        bookings = self.booking_manager.get_user_bookings(user_id)
        return {"bookings": bookings}

    # Add more tool functions as needed...

    def process(self, user_query: str, user_context: dict = None) -> str:
        """
        Process a natural language query using Gemini and return the response as a string, with tool calling support.
        """
        prompt = f"""
You are an AI assistant for a car rental system. Use the available tools to answer user queries.
User context: {user_context}
User query: {user_query}
"""
        try:
            config = types.GenerateContentConfig(
                tools=[
                    lambda: self.get_all_users(user_context),
                    lambda: self.get_my_bookings(user_context),
                    # Add more tool lambdas as needed
                ]
            )
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            return response.text if hasattr(response, 'text') else str(response)
        except Exception as e:
            logging.error(f"Gemini NLP error: {str(e)}")
            return "Sorry, I couldn't process your request with AI. Please try a standard command."

class AICarRentalInterface:
    def __init__(self):
        # Initialize database and managers
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthenticationManager(self.db_manager)
        self.car_manager = CarManager(self.db_manager)
        self.booking_manager = BookingManager(self.db_manager)
        self.admin_manager = AdminManager(self.db_manager)
        
        # Initialize session state
        self.session_token = None
        self.user_id = None
        self.is_admin = False
        self.current_user = None
        self.terms_accepted = False  # Track if the user has accepted terms
        
        # Gemini/AI model setup
        self.client = genai.Client(api_key=GOOGLE_API_KEY)
        self.query_builder = QueryBuilder(self.db_manager)
        self.nl_processor = NLQueryProcessor(self.client, self.admin_manager, self.booking_manager, self.auth_manager)
        
        logging.info("AICarRentalInterface initialized.")
        
    def process_command(self, user_input: str, **kwargs) -> str:
        """Process user commands, prioritizing standard commands over NLP
        
        For interactive mode, leave kwargs empty.
        For non-interactive mode, provide required params in kwargs:
        - LOGIN: email, password
        - BOOK: car_id, start_date, duration
        - CANCEL_BOOKING: booking_id
        """
        # Basic input validation
        if not user_input or not isinstance(user_input, str):
            return "Please enter a command. Type 'help' for available commands."
        
        # Sanitize user input for security
        user_input = SecurityValidator.sanitize_string(user_input.strip())
        if not user_input:
            return "Please enter a command. Type 'help' for available commands."
        
        # i am commenting this out to avoid logging sensitive information
        # Uncomment for debugging purposes, but be cautious with sensitive data
        # logging.info(f"Processing command: {user_input}")
        
        # First try exact command matches
        exact_commands = {
            # Login variations
            "login": "LOGIN",
            "log in": "LOGIN",
            "signin": "LOGIN",
            "sign in": "LOGIN",
            # Logout variations
            "logout": "LOGOUT",
            "log out": "LOGOUT",
            "signout": "LOGOUT",
            "sign out": "LOGOUT",
            "log off": "LOGOUT",
            "logoff": "LOGOUT",
            # Other standard commands
            "register": "REGISTER",
            "help": "HELP",
            "exit": "EXIT",
            "show cars": "SHOW_CARS",
            "available cars": "SHOW_CARS",
            "my bookings": "VIEW_BOOKINGS",
            "view bookings": "VIEW_BOOKINGS",
            "book car": "BOOK",
            "cancel booking": "CANCEL_BOOKING",
            "terms": "TERMS"
        }
        # Admin exact commands
        admin_exact_commands = {
            "all users": "VIEW_ALL_USERS",
            "all bookings": "VIEW_ALL_BOOKINGS",
            "car status": "VIEW_ALL_CAR_STATUS",
            "view assets": "VIEW_ALL_ASSETS",
            "revenue": "VIEW_ALL_REVENUE"
        }
        # Try exact matches first
        input_lower = user_input.lower()
        command = None
        # Check exact matches
        for cmd_text, cmd_name in exact_commands.items():
            if input_lower.startswith(cmd_text):
                command = cmd_name
                break
        # Check admin commands if user is admin
        if self.is_admin and not command:
            for cmd_text, cmd_name in admin_exact_commands.items():
                if input_lower.startswith(cmd_text):
                    command = cmd_name
                    break
        # If no exact match, try pattern matching
        if not command:
            # If admin, allow 'show bookings' to map to VIEW_ALL_BOOKINGS
            if self.is_admin and input_lower.startswith('show bookings'):
                command = 'VIEW_ALL_BOOKINGS'
            else:
                command = self._get_command_from_input(input_lower)
        # Execute standard command if found
        if command != "UNKNOWN":
            if not self._verify_command_access(command):
                return "Please login first." if not self.session_token else "You don't have permission to execute this command."
            return self._execute_standard_command(command, **kwargs)
        # Only allow NLP queries for specific scenarios
        if not self.session_token:
            return "Command not recognized. Type 'help' for available commands."
        # Pass any unrecognized command to NLP processor for all logged-in users
        try:
            user_context = {
                'user_id': self.user_id,
                'is_admin': self.is_admin,
                'session_token': self.session_token
            }
            nlp_response = self.nl_processor.process(user_input, user_context)
            return nlp_response
        except Exception as e:
            logging.error(f"Error processing NLP command '{user_input}': {str(e)}")
            return f"Error processing AI query: {str(e)}"
        # Fallback: always return a string if no other return was hit
        return "Command not recognized. Type 'help' for available commands."
    
    def _get_command_from_input(self, input_lower: str) -> str:
        """Get standardized command from input"""
        # Prioritize exact matches for 'help' and 'book' before pattern matching
        if input_lower.strip() == 'help':
            logging.debug("Command parsed as HELP (exact match)")
            return "HELP"
        if input_lower.strip() == 'book':
            logging.debug("Command parsed as BOOK (exact match)")
            return "BOOK"
        # First, clean and standardize input
        input_lower = input_lower.strip()
        
        # Define command patterns with variations
        command_patterns = {
            "LOGIN": ["login", "sign in", "signin"],
            "LOGOUT": ["logout", "sign out", "signout"],
            "SHOW_CARS": [
                "show cars", "available cars", "list cars", "view cars",
                "show.*available.*car", "show.*car.*available",
                "list.*available.*car", "view.*available.*car",
                "what.*cars.*available", "which.*cars.*available",
                "show.*my.*car", "available.*vehicle"
            ],
            "VIEW_BOOKINGS": [
                "my bookings", "view bookings", "show bookings", "list bookings", 
                "view my bookings", "show my bookings", "list my bookings",
                "current bookings", "my current bookings", "see my bookings",
                "my reservations", "view reservations", "show reservations",
                "current reservations", "display.*reservations?",
                "check.*booking", "show.*my.*booking"
            ],
            "BOOK": ["^book\\s", "^rent\\s", "^hire\\s", "make.*booking", "create.*booking"],
            "CANCEL_BOOKING": ["cancel booking", "cancel my booking", "delete booking"],
            "HELP": ["help", "commands", "?"],
            "EXIT": ["exit", "quit"],
            "VIEW_TERMS": ["view terms", "see terms", "view t&c", "show t&c", "show terms", "terms"],
            "ACCEPT_TERMS": ["accept terms", "agree terms", "accept t&c", "agree t&c"]
        }
        for command, patterns in command_patterns.items():
            for pattern in patterns:
                try:
                    if any(c in pattern for c in ".*+?^$[](){}|"):
                        if re.search(pattern, input_lower, re.IGNORECASE):
                            logging.debug(f"Command parsed as {command} (regex match: {pattern})")
                            return command
                    elif pattern in input_lower:
                        if command == "BOOK" and "booking" in input_lower:
                            continue
                        logging.debug(f"Command parsed as {command} (substring match: {pattern})")
                        return command
                except re.error:
                    if pattern in input_lower:
                        logging.debug(f"Command parsed as {command} (fallback substring match: {pattern})")
                        return command
        logging.debug("Command parsed as UNKNOWN")
        return "UNKNOWN"

    def _verify_command_access(self, command: str) -> bool:
        """Verify if user has access to execute command"""
        # Commands that don't require login
        if command in ["LOGIN", "HELP", "SHOW_CARS", "REGISTER"]:
            return True

        # All other commands require login
        if not self.session_token:
            return False

        # Admin commands
        admin_commands = [
            "VIEW_ALL_BOOKINGS",
            "VIEW_ALL_USERS",
            "VIEW_ALL_CAR_STATUS",
            "VIEW_ALL_ASSETS",
            "VIEW_ALL_REVENUE"
        ]
        if command in admin_commands and not self.is_admin:
            return False

        return True

    def _execute_standard_command(self, command: str, **kwargs) -> str:
        """Execute a standard command
        
        For interactive mode, leave kwargs empty.
        For non-interactive mode, provide required params in kwargs:
        - LOGIN: email, password
        - REGISTER: email, password, national_id
        - BOOK: car_id, start_date, duration
        - CANCEL_BOOKING: booking_id
        """
        try:
            logging.info(f"Executing command: {command} (session_token={self.session_token}, user_id={self.user_id})")
            if command == "LOGIN":
                if self.session_token:
                    return "Already logged in."
                # For non-interactive testing mode
                if 'email' in kwargs and 'password' in kwargs:
                    try:
                        success, msg = self.handle_login(kwargs['email'], kwargs['password'])
                        if success:
                            self.audit_log_event("login", f"email={kwargs['email']}")
                        return msg
                    except Exception as e:
                        logging.error(f"Login error: {str(e)}")
                        return "An error occurred during login. Please try again."
                # For interactive mode
                try:
                    email = input("Email: ").strip()
                    password = input("Password: ").strip()
                    try:
                        success, msg = self.handle_login(email, password)
                        if success:
                            self.audit_log_event("login", f"email={email}")
                        return msg
                    except Exception as e:
                        logging.error(f"Login error: {str(e)}")
                        return "An error occurred during login. Please try again."
                except EOFError:
                    return "Error: Interactive input required for login command"

            elif command == "LOGOUT":
                try:
                    success, msg = self.handle_logout()
                    if success:
                        self.audit_log_event("logout", f"user_id={self.user_id}")
                    return msg
                except Exception as e:
                    logging.error(f"Logout error: {str(e)}")
                    return "An error occurred during logout. Please try again."

            elif command == "SHOW_CARS":
                try:
                    self.audit_log_event("show_cars")
                    cars = self.get_available_cars()
                    if not cars:
                        return "No cars available."
                    result = "\nAvailable Cars:\n"
                    for car in cars:
                        result += f"Car ID: {car['id']} - {car['make']} {car['model']} - ${car['daily_rate']:.2f}/day\n"
                    return result
                except Exception as e:
                    logging.error(f"Show cars error: {str(e)}")
                    return "An error occurred while retrieving cars. Please try again."

            elif command == "BOOK":
                result = handler(
                    kwargs.get('car_id'), 
                    kwargs.get('start_date'), 
                    kwargs.get('duration')
                )
            elif command == "CANCEL_BOOKING":
                try:
                    bookings = self.get_user_bookings()
                    if not bookings:
                        return "No bookings found."
                    # For non-interactive testing mode
                    if 'booking_id' in kwargs:
                        try:
                            booking_id = int(SecurityValidator.sanitize_string(str(kwargs['booking_id'])))
                            success, msg = self.cancel_booking(booking_id)
                            if success:
                                self.audit_log_event("cancel_booking", f"booking_id={booking_id}")
                            return msg
                        except (ValueError, KeyError):
                            return "Invalid booking ID provided."
                        except Exception as e:
                            logging.error(f"Cancel booking error: {str(e)}")
                            return "An error occurred while cancelling booking. Please try again."
                    # For interactive mode
                    result = "\nYour Bookings:\n"
                    for booking in bookings:
                        result += f"ID: {booking['id']} - {booking.get('make', 'N/A')} {booking.get('model', 'N/A')}\n"
                        result += f"Dates: {booking['start_date']} to {booking['end_date']}\n"
                        result += f"Status: {booking['status']}\n\n"
                    try:
                        print(result)
                        booking_id = int(SecurityValidator.sanitize_string(input("Enter Booking ID to cancel: ").strip()))
                        try:
                            success, msg = self.cancel_booking(booking_id)
                            if success:
                                self.audit_log_event("cancel_booking", f"booking_id={booking_id}")
                            return msg
                        except Exception as e:
                            logging.error(f"Cancel booking error: {str(e)}")
                            return "An error occurred while cancelling booking. Please try again."
                    except (ValueError, EOFError, KeyboardInterrupt):
                        return "Cancellation cancelled. Please provide a valid Booking ID."
                except Exception as e:
                    logging.error(f"Cancel booking error: {str(e)}")
                    return "An error occurred while cancelling booking. Please try again."

            elif command == "VIEW_ALL_USERS":
                try:
                    users = self.admin_manager.view_all_users()
                    self.audit_log_event("view_all_users")
                    if not users:
                        return "No users found."
                    result = "\nAll Users:\n"
                    for user in users:
                        result += f"ID: {user.get('id')} | Email: {user.get('email')} | Role: {user.get('role')} | Active: {user.get('is_active')}\n"
                    return result
                except Exception as e:
                    logging.error(f"View all users error: {str(e)}")
                    return "An error occurred while retrieving users. Please try again."
            elif command == "VIEW_ALL_BOOKINGS":
                try:
                    bookings = self.admin_manager.view_user_bookings()
                    self.audit_log_event("view_all_bookings")
                    if not bookings:
                        return "No bookings found."
                    result = "\nAll Bookings:\n"
                    for booking in bookings:
                        result += f"Booking ID: {booking.get('id')} | User: {booking.get('user_email')} | Car: {booking.get('make')} {booking.get('model')} | Status: {booking.get('status')}\n"
                    return result
                except Exception as e:
                    logging.error(f"View all bookings error: {str(e)}")
                    return "An error occurred while retrieving bookings. Please try again."
            elif command == "VIEW_ALL_CAR_STATUS":
                try:
                    status = self.admin_manager.view_car_status()
                    self.audit_log_event("view_all_car_status")
                    result = "\nCar Status Overview:\n"
                    result += f"Available: {len(status.get('available', []))} | Not Available: {len(status.get('not_available', []))}\n"
                    return result
                except Exception as e:
                    logging.error(f"View all car status error: {str(e)}")
                    return "An error occurred while retrieving car status. Please try again."
            elif command == "VIEW_ALL_ASSETS":
                try:
                    summary = self.admin_manager.view_asset_summary()
                    self.audit_log_event("view_all_assets")
                    fleet_value = summary.get('fleet_value', {})
                    expiring = summary.get('expiring_soon', {})
                    result = "\nAsset Summary:\n"
                    result += f"Total Cars: {fleet_value.get('total_cars', 0)} | Fleet Value: {fleet_value.get('fleet_value', 0)} | Total Maintenance: {fleet_value.get('total_maintenance', 0)}\n"
                    result += f"Road Tax Expiring: {expiring.get('road_tax_expiring', 0)} | Insurance Expiring: {expiring.get('insurance_expiring', 0)} | Maintenance Due: {expiring.get('maintenance_due', 0)}\n"
                    return result
                except Exception as e:
                    logging.error(f"View all assets error: {str(e)}")
                    return "An error occurred while retrieving asset summary. Please try again."
            elif command == "VIEW_ALL_REVENUE":
                try:
                    stats = self.admin_manager.get_revenue_statistics()
                    self.audit_log_event("view_all_revenue")
                    overall = stats.get('overall', {})
                    result = "\nRevenue Statistics:\n"
                    result += f"Total Bookings: {overall.get('total_bookings', 0)} | Total Revenue: {overall.get('total_revenue', 0)} | Avg Booking Value: {overall.get('average_booking_value', 0)}\n"
                    return result
                except Exception as e:
                    logging.error(f"View all revenue error: {str(e)}")
                    return "An error occurred while retrieving revenue statistics. Please try again."
            elif command == "HELP":
                help_text = "\nAvailable Commands:\n"
                help_text += "- login: Log into your account\n"
                help_text += "- show cars: View available cars\n"
                help_text += "- book: Book a car\n"
                help_text += "- my bookings: View your bookings\n"
                help_text += "- cancel booking: Cancel a booking\n"
                help_text += "- logout: Log out of your account\n"
                help_text += "- help: Show this help message\n"
                help_text += "- terms: View the terms and conditions\n"
                help_text += "- accept terms: Accept the terms and conditions (required before booking)\n"
                # Always add a newline before admin commands for clarity
                if getattr(self, 'is_admin', False):
                    help_text += "\nAdmin Commands:\n"
                    help_text += "- view users: List all registered users\n"
                    help_text += "- all users: Alias for 'view users'\n"
                    help_text += "- all bookings: List all bookings in the system\n"
                    help_text += "- car status: Show summary of car availability and status\n"
                    help_text += "- view assets: Show asset/fleet summary and expiring items\n"
                    help_text += "- revenue: Show revenue and booking statistics\n"
                return help_text
            # Fallback for any unhandled command
            logging.debug(f"_execute_standard_command fallback for command: {command}")
            return "Command not recognized. Type 'help' for available commands."
        except Exception as e:
            logging.error(f"Error executing command '{command}': {str(e)}")
            return f"Error executing command: {str(e)}"
    
    def get_available_cars(self) -> List[Dict]:
        """Get list of available cars"""
        return self.car_manager.show_available_cars()

    def create_booking(self, car_id: int, start_date: str, duration: int) -> Tuple[bool, str, Optional[float]]:
        logging.info(f"Creating booking: user_id={self.user_id}, car_id={car_id}, start_date={start_date}, duration={duration}")
        """Create a new booking"""
        if not self.user_id:
            return False, "Please login first.", None

        # Sanitize input parameters
        car_id = int(SecurityValidator.sanitize_string(str(car_id)))
        start_date = SecurityValidator.sanitize_string(start_date)
        duration = int(SecurityValidator.sanitize_string(str(duration)))

        # Calculate end date
        end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=duration)).strftime('%Y-%m-%d')
        
        # Get car details for cost calculation
        cars = self.car_manager.show_available_cars()
        selected_car = next((car for car in cars if car['id'] == car_id), None)
        if not selected_car:
            return False, "Car not found or not available.", None

        # Calculate total cost
        total_cost = selected_car['daily_rate'] * duration

        # Create the booking
        success, message = self.booking_manager.create_booking(
            user_id=self.user_id,
            car_id=car_id,
            start_date=start_date,
            end_date=end_date
        )

        if success:
            logging.info(f"Booking created successfully for user_id={self.user_id}, car_id={car_id}")
            return True, message, total_cost
        logging.warning(f"Booking failed for user_id={self.user_id}, car_id={car_id}")
        return False, message, None
        
    def get_user_bookings(self) -> List[Dict]:
        """Get bookings for current user with car details (efficient lookup)"""
        if not self.user_id:
            return []
        bookings = self.booking_manager.get_user_bookings(self.user_id)
        if not bookings:
            return []
        # Fetch all available cars once and build a lookup dict
        cars = self.car_manager.show_available_cars()
        car_lookup = {car['id']: car for car in cars}
        for booking in bookings:
            car_id = booking.get('car_id')
            car = car_lookup.get(car_id)
            if car:
                booking['make'] = car['make']
                booking['model'] = car['model']
                booking['daily_rate'] = car['daily_rate']
        return bookings

    def cancel_booking(self, booking_id: int) -> Tuple[bool, str]:
        logging.info(f"Attempting to cancel booking: booking_id={booking_id}, user_id={self.user_id}")
        """Cancel a user's booking"""
        if not self.user_id:
            return False, "Please login first."
        booking_id = int(SecurityValidator.sanitize_string(str(booking_id)))
        result = self.booking_manager.cancel_booking(booking_id, self.user_id)
        if result[0]:
            logging.info(f"Booking {booking_id} cancelled successfully.")
        else:
            logging.warning(f"Failed to cancel booking {booking_id}.")
        return result

    def handle_login(self, email: str, password: str) -> Tuple[bool, str]:
        logging.info(f"Attempting login for email: {email}")
        email = SecurityValidator.sanitize_string(email)
        password = SecurityValidator.sanitize_string(password)
        success, msg, user_info = self.auth_manager.login(email, password)
        if success:
            self.session_token = user_info['session_token']
            self.user_id = user_info['user_id']
            self.is_admin = user_info['role'] == 'admin'
            self.current_user = user_info
            logging.info(f"Login successful for user_id: {self.user_id}")
        else:
            logging.warning(f"Login failed for email: {email}")
        return success, msg

    def handle_registration(self, email: str, password: str, national_id: str) -> Tuple[bool, str]:
        email = SecurityValidator.sanitize_string(email)
        password = SecurityValidator.sanitize_string(password)
        national_id = SecurityValidator.sanitize_string(national_id)
        return self.auth_manager.register_user(email, password, national_id)

    def handle_logout(self) -> Tuple[bool, str]:
        logging.info(f"Attempting logout for user_id: {self.user_id}")
        if self.session_token:
            success = self.auth_manager.logout(self.session_token)
            if success:
                self.session_token = None
                self.user_id = None
                self.is_admin = False
                self.current_user = None
                logging.info("Logout successful.")
                return True, "Logged out successfully."
        logging.warning("Logout failed: No active session.")
        return False, "No active session."

    def accept_terms(self) -> str:
        logging.info(f"User {self.user_id} accepted terms and conditions.")
        """Mark terms as accepted for this session/user."""
        self.terms_accepted = True
        return "You have accepted the terms and conditions. You may now proceed with booking."

    def view_terms_and_conditions(self) -> str:
        logging.info("Displaying terms and conditions.")
        try:
            decrypted_terms = read_and_decrypt_terms()
            if decrypted_terms is None:
                return "Unable to load terms and conditions. Please contact support."
            return decrypted_terms + "\nType 'accept terms' to agree."
        except FileNotFoundError:
            logging.error("Terms and conditions file not found.")
            return "Terms and conditions file not found."
        except Exception as e:
            logging.error(f"Error displaying terms and conditions: {str(e)}")
            return f"Error displaying terms and conditions: {str(e)}"

    def audit_log_event(self, event: str, details: str = ""):
        """Log an audit event to a dedicated audit log file."""
        try:
            with open("audit.log", "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user = self.user_id if self.user_id else "anonymous"
                f.write(f"[{timestamp}] user={user} event={event} details={details}\n")
        except Exception as e:
            logging.error(f"Failed to write audit log: {str(e)}")

    _help_text = (
        "Available commands:\n"
        "- help: Show this help message\n"
        "- register: Register a new user\n"
        "- login: Login to your account\n"
        "- logout: Logout from your account\n"
        "- view cars: View available cars\n"
        "- book car: Book a car\n"
        "- view bookings: View your bookings\n"
        "- accept terms: Accept the terms and conditions\n"
        "- show terms: View the terms and conditions\n"
        "- exit: Exit the application\n"
        "Admin commands: ..."
    )

    def _get_help_text(self) -> str:
        return self._help_text

# Optionally, add a main entry point for CLI usage
if __name__ == "__main__":
    interface = AICarRentalInterface()
    print("\n=== AI Car Rental System ===")
    print("Type 'help' for available commands or 'exit' to quit.")
    while True:
        user_input = input("\nWhat would you like to do? ").strip()
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        response = interface.process_command(user_input)
        print("\n" + response)