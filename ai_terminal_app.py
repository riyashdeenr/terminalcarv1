#!/usr/bin/env python3
"""
Gemini AI-Powered Terminal Car Rental Application
Uses Google Gemini's function calling to process natural language queries
"""

import os
from datetime import datetime, timedelta
import getpass
from google import genai
from google.genai import types

# Import existing managers
from auth import AuthenticationManager
from database import DatabaseManager
from car_manager import CarManager
from booking_manager import BookingManager
from admin_functions import AdminManager
from security import SecurityUtils
from terms_manager import read_and_decrypt_terms

class GeminiCarRentalTerminal:
    """AI-powered terminal interface for car rental system"""
    
    def __init__(self, api_key: str = None):
        """Initialize the terminal application"""
        # Initialize database and managers
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthenticationManager(self.db_manager)
        self.car_manager = CarManager(self.db_manager)
        self.booking_manager = BookingManager(self.db_manager)
        self.admin_manager = AdminManager(self.db_manager)
        
        # Session state
        self.current_user = None
        self.session_token = None
        self.is_admin = False
        
        # Configure Gemini AI
        api_key = "AIzaSyAz5B_lFFSTXJiXFD_RakW6NQACpeJAZsM"
        if not api_key:
            api_key = os.getenv('GEMINI_API_KEY')
        
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
                self.model_name = "gemini-2.0-flash-exp"
                print("✅ Gemini AI initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini AI: {str(e)}")
                self.client = None
        else:
            print("⚠️ No Gemini API key provided. AI features will be limited.")
            self.client = None
          # Define available functions for Gemini
        self.functions = self._define_functions()
    
    def _define_functions(self):
        """Define available functions for Gemini AI tool calling."""
        return {
            "get_available_cars": {
                "description": "Get list of all available cars for rental. Call this when user asks to see cars, view inventory, or browse available vehicles.",
                "parameters": {}
            },
            "user_login": {
                "description": "Login user with email and password. MUST be called when user provides login credentials, says 'login', 'log in', 'sign in', or provides email/password combination.",
                "parameters": {
                    "email": {"type": "string", "description": "User email address"},
                    "password": {"type": "string", "description": "User password"}
                }
            },            "user_register": {
                "description": "Register a new user account. ALWAYS call when user wants to register, sign up, or create account, even if missing details.",
                "parameters": {
                    "email": {"type": "string", "description": "User email address (optional - can be empty)"},
                    "password": {"type": "string", "description": "User password (optional - can be empty)"},
                    "national_id": {"type": "string", "description": "User national ID (optional - can be empty)"}
                }
            },
            "get_user_bookings": {
                "description": "Get current user's bookings. Call when user asks to see their bookings, reservations, or rental history.",
                "parameters": {}            },
            "create_booking": {
                "description": "Create a new car booking/reservation. ALWAYS call when user wants to book, rent, or reserve a car, even with partial information.",
                "parameters": {
                    "car_id": {"type": "string", "description": "ID of the car to book (can be empty string if not provided)"},
                    "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD format (can be empty string if not provided)"},
                    "duration": {"type": "string", "description": "Booking duration in days (can be empty string if not provided)"}
                }
            },
            "cancel_booking": {
                "description": "Cancel an existing booking. Call when user wants to cancel or remove a booking, even if they don't specify a booking ID.",
                "parameters": {
                    "booking_id": {"type": "string", "description": "ID of the booking to cancel (can be empty string if not provided)"}
                }
            },
            "user_logout": {
                "description": "Logout the current user. Call when user says 'logout', 'log out', 'sign out', or wants to logout.",
                "parameters": {}
            },"view_terms": {
                "description": "View terms and conditions document. ONLY call when user specifically asks for 'terms', 'terms and conditions', 'policies', or 'view terms'. Do NOT call for help, commands, or general assistance.",
                "parameters": {}
            },
            "get_all_users": {
                "description": "Get all users in the system (admin only). Call when admin wants to see all users.",
                "parameters": {}
            },
            "get_all_bookings": {
                "description": "Get all bookings in the system (admin only). Call when admin wants to see all bookings.",
                "parameters": {}
            },
            "get_car_status": {
                "description": "Get car status and availability summary (admin only). Call when admin asks for car status or fleet information.",
                "parameters": {}
            },            "get_revenue_stats": {
                "description": "Get revenue and booking statistics (admin only). Call when admin asks for revenue, stats, or financial information.",
                "parameters": {
                    "start_date": {"type": "string", "description": "Start date for revenue period in YYYY-MM-DD format (optional - can be empty)"},
                    "end_date": {"type": "string", "description": "End date for revenue period in YYYY-MM-DD format (optional - can be empty)"}
                }
            },
            "get_asset_details": {
                "description": "Get detailed asset information for a specific car (admin only). Call when admin asks for asset details, car information, or vehicle specifics.",
                "parameters": {
                    "car_id": {"type": "string", "description": "ID of the car to get asset details for (can be empty string if not provided)"}
                }
            },
            "generate_asset_report": {
                "description": "Generate comprehensive asset report for the fleet (admin only). Call when admin asks for asset report, fleet report, or asset summary.",
                "parameters": {
                    "start_date": {"type": "string", "description": "Start date for report period in YYYY-MM-DD format (optional - can be empty)"},
                    "end_date": {"type": "string", "description": "End date for report period in YYYY-MM-DD format (optional - can be empty)"}
                }
            },
            "get_car_revenue_details": {
                "description": "Get detailed revenue information for a specific car (admin only). Call when admin asks for car revenue, car performance, or vehicle financial details.",
                "parameters": {
                    "car_id": {"type": "string", "description": "ID of the car to get revenue details for (can be empty string if not provided)"},
                    "start_date": {"type": "string", "description": "Start date for revenue period in YYYY-MM-DD format (optional - can be empty)"},
                    "end_date": {"type": "string", "description": "End date for revenue period in YYYY-MM-DD format (optional - can be empty)"}
                }
            },
            "execute_sql": {
                "description": "Execute a SQL query (admin only). Call when admin wants to run SQL commands or database queries.",
                "parameters": {
                    "query": {"type": "string", "description": "SQL query to execute"}
                }
            }
        }
    
    # Function implementations for Gemini to call
    
    def register_user(self, email: str, password: str, national_id: str) -> str:
        """Register a new user"""
        try:
            # If any required fields are missing, prompt for interactive registration
            if not email or not password or not national_id:
                return "📝 I need your registration details. Please use the 'register' command to provide your email, password, and national ID interactively."
            
            success, message = self.auth_manager.register_user(email, password, national_id)
            if success:
                return f"✅ Registration successful! You can now login with your credentials."
            else:
                return f"❌ Registration failed: {message}"
        except Exception as e:
            return f"❌ Error during registration: {str(e)}"
    
    def login_user(self, email: str, password: str) -> str:
        """Login a user"""
        try:
            success, message, user_info = self.auth_manager.login(email, password)
            if success:
                self.current_user = user_info
                self.session_token = user_info['session_token']
                self.is_admin = (user_info.get('role', '').lower() == 'admin')
                role = "Administrator" if self.is_admin else "User"
                return f"✅ Login successful! Welcome back, {email}. You are logged in as {role}."
            else:
                return f"❌ Login failed: {message}"
        except Exception as e:
            return f"❌ Error during login: {str(e)}"
    
    def logout_user(self) -> str:
        """Logout the current user"""
        if self.current_user and self.session_token:
            user_email = self.current_user.get('email', 'User')
            
            # Properly logout using auth manager to invalidate session
            success = self.auth_manager.logout(self.session_token)
              # Clear local session data
            self.current_user = None
            self.session_token = None
            self.is_admin = False
            
            if success:
                return f"✅ Goodbye {user_email}! You have been logged out successfully."
            else:
                return f"✅ Goodbye {user_email}! You have been logged out (session cleanup completed)."
        else:
            return "ℹ️ You are not currently logged in."
    
    def show_available_cars(self, category: str = None) -> str:
        """Show available cars"""
        try:
            cars = self.car_manager.get_available_cars()
            if not cars:
                return "ℹ️ No cars are currently available for rental."
            
            if category:
                cars = [car for car in cars if car.get('category', '').lower() == category.lower()]
                if not cars:
                    return f"ℹ️ No cars available in the '{category}' category."
            
            result = "🚗 **Available Cars for Rental:**\n"
            result += "=" * 50 + "\n"
            
            for car in cars:
                result += f"**Car ID:** {car['id']}\n"
                result += f"**Make & Model:** {car['make']} {car['model']} ({car.get('year', 'N/A')})\n"
                result += f"**Daily Rate:** ${car['daily_rate']:.2f}/day\n"
                result += f"**Category:** {car.get('category', 'Standard')}\n"
                result += "-" * 30 + "\n"
            
            return result
        except Exception as e:
            return f"❌ Error retrieving cars: {str(e)}"
    
    def book_car(self, car_id, start_date: str, duration) -> str:
        """Book a car"""
        if not self.current_user:
            return "❌ You must be logged in to book a car. Please login first."
        
        # Convert and validate parameters
        try:
            # Handle car_id conversion
            if not car_id or car_id == "" or car_id == "0":
                car_id = None
            else:
                car_id = int(car_id)
        except (ValueError, TypeError):
            car_id = None
            
        try:
            # Handle duration conversion
            if not duration or duration == "" or duration == "0":
                duration = None
            else:
                duration = int(duration)
        except (ValueError, TypeError):
            duration = None
            
        # Handle start_date
        if not start_date or start_date == "":
            start_date = None
        
        # Handle missing or incomplete information
        if not car_id and not start_date and not duration:
            cars_result = self.show_available_cars()
            return f"{cars_result}\n\n� I can help you book a car! Please tell me:\n• Which car ID you'd like to book\n• The start date (YYYY-MM-DD format)\n• How many days you need it\n\nFor example: 'book car ID 1 for 3 days starting 2025-08-01'"
        
        if not car_id:
            # Show available cars and ask for car ID
            cars_result = self.show_available_cars()
            if start_date and duration:
                return f"{cars_result}\n\n📋 I see you want to book for {duration} days starting {start_date}. Please choose a car ID from the list above.\nFor example: 'book car ID 1 for {duration} days starting {start_date}'"
            elif duration:
                return f"{cars_result}\n\n📋 I see you want to rent for {duration} days. Please choose a car ID and start date.\nFor example: 'book car ID 1 for {duration} days starting 2025-08-01'"
            elif start_date:
                return f"{cars_result}\n\n📋 I see you want to start on {start_date}. Please choose a car ID and tell me how many days.\nFor example: 'book car ID 1 for 3 days starting {start_date}'"
            else:
                return f"{cars_result}\n\n📋 Please choose which car ID you'd like to book from the list above."
        
        if not start_date:
            return f"📅 Great! You want to book car ID {car_id}{f' for {duration} days' if duration else ''}. Please provide the start date in YYYY-MM-DD format.\nFor example: 'book car ID {car_id} for {duration if duration else '[days]'} days starting 2025-08-01'"
        
        if not duration:
            return f"⏰ Perfect! You want to book car ID {car_id} starting {start_date}. Please specify how many days you'd like to rent it.\nFor example: 'book car ID {car_id} for 3 days starting {start_date}'"

        try:
            # Validate date format
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            if start_dt.date() < datetime.now().date():
                return "❌ Start date cannot be in the past. Please choose a future date."
            
            # Validate duration
            if duration <= 0:
                return "❌ Duration must be at least 1 day."
            if duration > 30:
                return "❌ Maximum rental duration is 30 days. Please choose a shorter duration."
            
            end_dt = start_dt + timedelta(days=duration)
            end_date = end_dt.strftime('%Y-%m-%d')
            
            # Get car details for validation and cost calculation
            cars = self.car_manager.show_available_cars()
            selected_car = next((car for car in cars if car['id'] == car_id), None)
            if not selected_car:
                cars_result = self.show_available_cars()
                return f"{cars_result}\n\n❌ Car ID {car_id} is not available. Please choose from the available cars above."
            
            total_cost = selected_car['daily_rate'] * duration
            
            # Create booking
            success, message = self.booking_manager.create_booking(
                user_id=self.current_user['user_id'],
                car_id=car_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if success:
                result = f"✅ **Booking Confirmed!**\n"
                result += f"📋 **Booking Details:**\n"
                result += f"🚗 Car: {selected_car['make']} {selected_car['model']} ({selected_car['category']})\n"
                result += f"📅 Period: {start_date} to {end_date} ({duration} days)\n"
                result += f"💰 Daily Rate: ${selected_car['daily_rate']:.2f}/day\n"
                result += f"💰 **Total Cost: ${total_cost:.2f}**\n"
                result += f"✨ {message}\n"
                result += f"🎉 Thank you for booking with us! Your reservation is confirmed."
                return result
            else:
                return f"❌ Booking failed: {message}"
                
        except ValueError:
            return "❌ Invalid date format. Please use YYYY-MM-DD format (e.g., 2025-08-01)."
        except Exception as e:
            return f"❌ Error during booking: {str(e)}"
    
    def view_user_bookings(self) -> str:
        """View current user's bookings"""
        if not self.current_user:
            return "❌ You must be logged in to view your bookings. Please login first."
        
        try:
            bookings = self.booking_manager.get_user_bookings(self.current_user['user_id'])
            if not bookings:
                return "ℹ️ You have no bookings yet."
            
            result = f"📋 **Your Bookings:**\n"
            result += "=" * 50 + "\n"
            
            for booking in bookings:
                result += f"**Booking ID:** {booking['id']}\n"
                result += f"**Car:** {booking.get('make', 'N/A')} {booking.get('model', 'N/A')}\n"
                result += f"**Category:** {booking.get('category', 'N/A')}\n"
                result += f"**Status:** {booking['status']}\n"
                result += f"**Dates:** {booking['start_date']} to {booking['end_date']}\n"
                result += f"**Total Cost:** ${booking.get('total_amount', 0):.2f}\n"
                result += "-" * 30 + "\n"
            
            return result
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error retrieving bookings: {str(e)}"
    
    def cancel_booking(self, booking_id) -> str:
        """Cancel a booking"""
        if not self.current_user:
            return "❌ You must be logged in to cancel bookings. Please login first."
        
        try:
            # Handle missing booking ID
            if booking_id is None or booking_id == "":
                # Get user's current bookings to help them choose
                bookings = self.booking_manager.get_user_bookings(self.current_user['user_id'])
                if not bookings:
                    return "ℹ️ You have no bookings to cancel."
                
                result = "📋 **Your Current Bookings:**\n"
                result += "=" * 50 + "\n"
                
                for booking in bookings:
                    result += f"**Booking ID:** {booking['id']}\n"
                    result += f"**Car:** {booking.get('make', 'N/A')} {booking.get('model', 'N/A')}\n"
                    result += f"**Dates:** {booking['start_date']} to {booking['end_date']}\n"
                    result += f"**Status:** {booking['status']}\n"
                    result += "-" * 30 + "\n"
                
                result += "\n📝 Please specify which booking you'd like to cancel by saying:"
                result += "\n• 'Cancel booking ID [number]'"
                result += f"\n• For example: 'Cancel booking ID {bookings[0]['id']}'"
                return result
            
            # Convert booking_id to integer if it's a string
            try:
                booking_id = int(booking_id)
            except (ValueError, TypeError):
                return "❌ Invalid booking ID. Please provide a valid booking number."
            
            success, message = self.booking_manager.cancel_booking(booking_id, self.current_user['user_id'])
            if success:
                return f"✅ Booking #{booking_id} has been cancelled successfully."
            else:
                return f"❌ Failed to cancel booking: {message}"
        except Exception as e:
            return f"❌ Error cancelling booking: {str(e)}"
    
    def view_terms_conditions(self) -> str:
        """Display terms and conditions"""
        try:
            terms = read_and_decrypt_terms()
            return f"📋 **Terms and Conditions:**\n{'='*50}\n{terms}"
        except Exception as e:
            return f"❌ Error loading terms and conditions: {str(e)}"
    
    def admin_view_all_users(self) -> str:
        """Admin: View all users"""
        if not self.is_admin:
            return "❌ Admin privileges required for this operation."
        
        try:
            users = self.admin_manager.view_all_users()
            if not users:
                return "ℹ️ No users found in the system."
            
            result = f"👥 **All Users ({len(users)} total):**\n"
            result += "=" * 50 + "\n"
            
            for user in users:
                result += f"**ID:** {user['id']} | **Email:** {user['email']} | "
                result += f"**Role:** {'Admin' if user.get('is_admin') else 'User'}\n"
            
            return result
        except Exception as e:
            return f"❌ Error retrieving users: {str(e)}"
    
    def admin_view_all_bookings(self) -> str:
        """Admin: View all bookings"""
        if not self.is_admin:
            return "❌ Admin privileges required for this operation."
        
        try:
            bookings = self.admin_manager.view_user_bookings()
            if not bookings:
                return "ℹ️ No bookings found in the system."
            
            result = f"📋 **All Bookings ({len(bookings)} total):**\n"
            result += "=" * 50 + "\n"
            
            for booking in bookings:
                result += f"**Booking ID:** {booking['id']} | **User ID:** {booking['user_id']} | "
                result += f"**Car ID:** {booking['car_id']} | **Status:** {booking['status']}\n"
                result += f"**Dates:** {booking['start_date']} to {booking['end_date']}\n"
                result += "-" * 30 + "\n"
            
            return result
        except Exception as e:
            return f"❌ Error retrieving bookings: {str(e)}"
    
    def admin_search_user_bookings(self, username: str) -> str:
        """Admin: Search bookings by username"""
        if not self.is_admin:
            return "❌ Admin privileges required for this operation."
        
        try:
            bookings = self.admin_manager.search_bookings_by_username(username)
            if not bookings:
                return f"ℹ️ No bookings found for user: {username}"
            
            result = f"📋 **Bookings for {username}:**\n"
            result += "=" * 50 + "\n"
            
            for booking in bookings:
                result += f"**Booking ID:** {booking['id']}\n"
                result += f"**Car:** {booking.get('make', 'N/A')} {booking.get('model', 'N/A')}\n"
                result += f"**Status:** {booking['status']}\n"
                result += f"**Dates:** {booking['start_date']} to {booking['end_date']}\n"
                result += "-" * 30 + "\n"
            
            return result
        except Exception as e:
            return f"❌ Error searching bookings: {str(e)}"
    
    def admin_car_management(self, action: str, **kwargs) -> str:
        """Admin: Car management operations"""
        if not self.is_admin:
            return "❌ Admin privileges required for this operation."
        
        try:
            if action == "view_status":
                cars = self.car_manager.show_car_status()
                if not cars:
                    return "ℹ️ No cars found in the system."
                
                result = f"🚗 **Car Status Overview:**\n"
                result += "=" * 50 + "\n"
                
                for car in cars:
                    result += f"**ID:** {car['id']} | **Make/Model:** {car['make']} {car['model']}\n"
                    result += f"**Status:** {car['status']} | **License:** {car.get('license_plate', 'N/A')}\n"
                    result += "-" * 30 + "\n"
                
                return result
                
            elif action == "search_by_plate":
                license_plate = kwargs.get('license_plate')
                if not license_plate:
                    return "❌ License plate is required for this search."
                
                car = self.admin_manager.search_car_by_plate(license_plate)
                if not car:
                    return f"ℹ️ No car found with license plate: {license_plate}"
                
                result = f"🚗 **Car Found:**\n"
                result += f"**ID:** {car['id']} | **Make/Model:** {car['make']} {car['model']}\n"
                result += f"**Status:** {car['status']} | **License:** {car.get('license_plate', 'N/A')}\n"
                
                return result
                
            elif action == "search_by_make_model":
                make = kwargs.get('make', '')
                model = kwargs.get('model', '')
                
                cars = self.admin_manager.search_cars_by_make_model(make, model)
                if not cars:
                    return f"ℹ️ No cars found matching make: {make}, model: {model}"
                
                result = f"🚗 **Cars Found ({len(cars)} results):**\n"
                result += "=" * 50 + "\n"
                
                for car in cars:
                    result += f"**ID:** {car['id']} | **Make/Model:** {car['make']} {car['model']}\n"
                    result += f"**Status:** {car['status']} | **License:** {car.get('license_plate', 'N/A')}\n"
                    result += "-" * 30 + "\n"
                
                return result
                
            elif action == "set_maintenance":
                car_id = kwargs.get('car_id')
                status = kwargs.get('status')
                
                if not car_id or not status:
                    return "❌ Car ID and status are required for maintenance update."
                
                success, message = self.admin_manager.set_car_maintenance_status(car_id, status)
                if success:
                    return f"✅ Car #{car_id} maintenance status updated to: {status}"
                else:
                    return f"❌ Failed to update maintenance status: {message}"
            
            else:
                return f"❌ Unknown car management action: {action}"
                
        except Exception as e:
            return f"❌ Error in car management: {str(e)}"
    
    def admin_revenue_analytics(self, start_date: str = None, end_date: str = None) -> str:
        """Admin: View revenue analytics"""
        if not self.is_admin:
            return "❌ Admin privileges required for this operation."
        
        try:
            stats = self.admin_manager.get_revenue_statistics(start_date, end_date)
            
            result = f"💰 **Revenue Analytics:**\n"
            result += "=" * 50 + "\n"
            
            period = stats.get('period', {})
            overall = stats.get('overall', {})
            
            result += f"**Period:** {period.get('start', 'All time')} to {period.get('end', 'Present')}\n"
            result += f"**Total Bookings:** {overall.get('total_bookings', 0)}\n"
            result += f"**Total Revenue:** ${overall.get('total_revenue', 0):.2f}\n"
            result += f"**Average Booking Value:** ${overall.get('average_booking_value', 0):.2f}\n"
            
            return result
        except Exception as e:
            return f"❌ Error retrieving revenue analytics: {str(e)}"
    
    def execute_sql_query(self, query: str) -> str:
        """Execute a safe SQL query and format results"""
        if not self.is_admin:
            return "❌ Admin privileges required for SQL queries."
        
        # Security check: only allow SELECT queries
        query_upper = query.strip().upper()
        if not query_upper.startswith('SELECT'):
            return "❌ Only SELECT queries are allowed for security reasons."
          # Additional security checks
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in query_upper for keyword in dangerous_keywords):
            return "❌ Query contains potentially dangerous keywords."
        
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute(query)
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                if not rows:
                    return "ℹ️ Query executed successfully but returned no results."
                
                result = f"📊 **Query Results ({len(rows)} rows):**\n"
                result += "=" * 50 + "\n"                # Format results in a readable table format
                for i, row in enumerate(rows):
                    result += f"**Row {i+1}:**\n"
                    for col, value in zip(columns, row):
                        result += f"  {col}: {value}\n"
                    result += "-" * 30 + "\n"                
                return result
                
        except Exception as e:
            return f"❌ SQL Error: {str(e)}"
    
    def get_asset_details(self, car_id: str = "") -> str:
        """Get detailed asset information for a specific car (admin only)."""
        if not self.is_admin:
            return "❌ Admin privileges required for this operation."
        
        try:
            # Handle missing car ID
            if not car_id or car_id.strip() == "":
                # Get all cars from database for admin purposes
                try:
                    with self.db_manager.get_connection() as conn:
                        cars_data = conn.execute("SELECT id, make, model, license_plate FROM cars").fetchall()
                        cars = [dict(car) for car in cars_data]
                except Exception:
                    cars = []
                
                if not cars:
                    return "📋 No cars found in the system."
                
                result = "📋 **Available Cars:**\n"
                result += "=" * 40 + "\n"
                for car in cars[:10]:  # Show first 10 cars
                    result += f"**ID {car['id']}:** {car.get('make', 'Unknown')} {car.get('model', '')} - {car.get('license_plate', 'N/A')}\n"
                
                result += "\n📝 Please specify which car you'd like asset details for:"
                result += "\n• 'Get asset details for car ID [number]'"
                result += f"\n• For example: 'Get asset details for car ID {cars[0]['id']}'"
                return result
            
            # Convert car_id to integer
            try:
                car_id_int = int(car_id)
            except (ValueError, TypeError):
                return "❌ Invalid car ID. Please provide a valid car number."
            
            # Get asset details from admin manager
            asset_details = self.admin_manager.get_asset_details(car_id_int)
            if not asset_details:
                return f"❌ Car with ID {car_id_int} not found."
            
            result = f"🚗 **Asset Details - Car ID {car_id_int}:**\n"
            result += "=" * 50 + "\n"
            
            # Basic Information
            result += f"**Basic Information:**\n"
            result += f"• Make/Model: {asset_details.get('make', 'N/A')} {asset_details.get('model', 'N/A')}\n"
            result += f"• Year: {asset_details.get('year', 'N/A')}\n"
            result += f"• License Plate: {asset_details.get('license_plate', 'N/A')}\n"
            result += f"• Category: {asset_details.get('category', 'N/A')}\n"
            result += f"• Daily Rate: ${float(asset_details.get('daily_rate', 0)):,.2f}\n\n"
            
            # Financial Information
            result += f"**Financial Information:**\n"
            result += f"• Purchase Date: {asset_details.get('purchase_date') or 'Not set'}\n"
            result += f"• Purchase Price: ${float(asset_details.get('purchase_price', 0)):,.2f}\n"
            result += f"• Total Maintenance Cost: ${float(asset_details.get('total_maintenance_cost', 0)):,.2f}\n"
            result += f"• Current Mileage: {asset_details.get('mileage', 0):,} miles\n\n"
            
            # Insurance & Legal
            result += f"**Insurance & Legal:**\n"
            result += f"• Insurance Provider: {asset_details.get('insurance_provider') or 'Not set'}\n"
            result += f"• Policy Number: {asset_details.get('insurance_policy_number') or 'Not set'}\n"
            result += f"• Insurance Amount: ${float(asset_details.get('insurance_amount', 0)):,.2f}\n"
            result += f"• Insurance Expiry: {asset_details.get('insurance_expiry') or 'Not set'}\n"
            result += f"• Road Tax Amount: ${float(asset_details.get('road_tax_amount', 0)):,.2f}\n"
            result += f"• Road Tax Expiry: {asset_details.get('road_tax_expiry') or 'Not set'}\n\n"
            
            # Maintenance
            result += f"**Maintenance:**\n"
            result += f"• Last Maintenance: {asset_details.get('last_maintenance_date') or 'Not set'}\n"
            result += f"• Next Maintenance: {asset_details.get('next_maintenance_date') or 'Not set'}\n\n"
            
            # Usage Statistics
            result += f"**Usage Statistics:**\n"
            result += f"• Total Bookings: {asset_details.get('total_bookings', 0)}\n"
            result += f"• Total Rental Days: {asset_details.get('total_rental_days', 0)}\n"
            
            return result.strip()
            
        except Exception as e:
            return f"❌ Error retrieving asset details: {str(e)}"

    def get_revenue_stats(self, start_date: str = "", end_date: str = "") -> str:
        """Get revenue statistics for the specified period (admin only)."""
        if not self.is_admin:
            return "❌ Admin privileges required for this operation."
        
        try:
            # Handle date parameters - use None if empty strings
            start_param = start_date if start_date and start_date.strip() else None
            end_param = end_date if end_date and end_date.strip() else None
            
            # Get revenue statistics from admin manager
            stats = self.admin_manager.get_revenue_statistics(start_param, end_param)
            
            if not stats:
                return "📊 No revenue data available for the specified period."
            
            result = "💰 **Revenue Statistics:**\n"
            result += "=" * 40 + "\n"
            
            # Format period
            period_start = stats.get('period_start', 'N/A')
            period_end = stats.get('period_end', 'N/A')
            result += f"📅 **Period:** {period_start} to {period_end}\n\n"
            
            # Main revenue metrics
            result += f"**Financial Summary:**\n"
            result += f"• Total Revenue: ${float(stats.get('total_revenue', 0)):,.2f}\n"
            result += f"• Total Bookings: {stats.get('total_bookings', 0)}\n"
            result += f"• Average Revenue per Booking: ${float(stats.get('avg_revenue_per_booking', 0)):,.2f}\n"
            result += f"• Total Rental Days: {stats.get('total_rental_days', 0)}\n"
            result += f"• Average Daily Revenue: ${float(stats.get('avg_daily_revenue', 0)):,.2f}\n\n"
            
            # Monthly breakdown if available
            if 'monthly_revenue' in stats and stats['monthly_revenue']:
                result += f"**Monthly Breakdown:**\n"
                for month_data in stats['monthly_revenue']:
                    month = month_data.get('month', 'Unknown')
                    revenue = float(month_data.get('revenue', 0))
                    bookings = month_data.get('bookings', 0)
                    result += f"• {month}: ${revenue:,.2f} ({bookings} bookings)\n"
                result += "\n"
            
            # Top performing cars if available
            if 'top_cars' in stats and stats['top_cars']:
                result += f"**Top Performing Cars:**\n"
                for i, car in enumerate(stats['top_cars'][:5], 1):
                    car_info = f"{car.get('make', 'Unknown')} {car.get('model', '')}"
                    revenue = float(car.get('revenue', 0))
                    result += f"{i}. {car_info} - ${revenue:,.2f}\n"
            
            return result.strip()
            
        except Exception as e:
            return f"❌ Error retrieving revenue statistics: {str(e)}"

    def generate_asset_report(self, start_date: str = "", end_date: str = "") -> str:
        """Generate comprehensive asset report for the fleet (admin only)."""
        if not self.is_admin:
            return "❌ Admin privileges required for this operation."
        
        try:
            # Handle date parameters - use None if empty strings
            start_param = start_date if start_date and start_date.strip() else None
            end_param = end_date if end_date and end_date.strip() else None
            
            # Get asset report from admin manager
            report = self.admin_manager.generate_asset_report(start_param, end_param)
            if not report:
                return "📋 No asset report data available."
            
            result = "📊 **Fleet Asset Report:**\n"
            result += "=" * 50 + "\n"
            
            # Display period
            period = report.get('period', {})
            result += f"📅 **Report Period:** {period.get('start', 'Beginning')} to {period.get('end', 'Present')}\n\n"
            
            # Financial Summary
            financials = report.get('financials', {})
            result += f"💰 **Financial Summary:**\n"
            result += f"• Total Fleet Investment: ${float(financials.get('total_investment', 0)):,.2f}\n"
            result += f"• Total Maintenance Costs: ${float(financials.get('total_maintenance', 0)):,.2f}\n"
            result += f"• Total Insurance Costs: ${float(financials.get('total_insurance', 0)):,.2f}\n"
            result += f"• Total Road Tax: ${float(financials.get('total_road_tax', 0)):,.2f}\n"
            result += f"• Total Vehicles: {financials.get('total_vehicles', 0)}\n\n"
            
            # Rental Performance
            rentals = report.get('rentals', {})
            result += f"🚗 **Rental Performance (Period):**\n"
            result += f"• Total Bookings: {rentals.get('total_bookings', 0)}\n"
            result += f"• Total Rental Days: {int(rentals.get('total_rental_days', 0))}\n"
            result += f"• Cars Rented: {rentals.get('cars_rented', 0)}\n\n"
            
            # Maintenance Alerts
            maintenance = report.get('maintenance', {})
            result += f"🔧 **Maintenance Alerts:**\n"
            result += f"• Vehicles Due for Maintenance: {maintenance.get('due_maintenance', 0)}\n\n"
            
            # Calculate derived metrics
            total_investment = float(financials.get('total_investment', 0))
            total_vehicles = financials.get('total_vehicles', 0)
            if total_vehicles > 0:
                avg_vehicle_value = total_investment / total_vehicles
                result += f"📈 **Key Metrics:**\n"
                result += f"• Average Vehicle Value: ${avg_vehicle_value:,.2f}\n"
                
                total_days = int(rentals.get('total_rental_days', 0))
                if total_days > 0:
                    utilization = (total_days / (total_vehicles * 30)) * 100 if total_vehicles > 0 else 0
                    result += f"• Fleet Utilization Rate: {utilization:.1f}% (based on 30-day period)\n"
            
            return result.strip()
            
        except Exception as e:
            return f"❌ Error generating asset report: {str(e)}"

    def get_car_revenue_details(self, car_id: str = "", start_date: str = "", end_date: str = "") -> str:
        """Get detailed revenue information for a specific car (admin only)."""
        if not self.is_admin:
            return "❌ Admin privileges required for this operation."
        
        try:            # Handle missing car ID
            if not car_id or car_id.strip() == "":
                # Get all cars from database for admin purposes
                try:
                    with self.db_manager.get_connection() as conn:
                        cars_data = conn.execute("SELECT id, make, model, license_plate FROM cars").fetchall()
                        cars = [dict(car) for car in cars_data]
                except Exception:
                    cars = []
                
                if not cars:
                    return "📋 No cars found in the system."
                
                result = "📋 **Available Cars:**\n"
                result += "=" * 40 + "\n"
                for car in cars[:10]:  # Show first 10 cars
                    result += f"**ID {car['id']}:** {car.get('make', 'Unknown')} {car.get('model', '')} - {car.get('license_plate', 'N/A')}\n"
                
                result += "\n📝 Please specify which car you'd like revenue details for:"
                result += "\n• 'Get car revenue details for car ID [number]'"
                result += f"\n• For example: 'Get car revenue details for car ID {cars[0]['id']}'"
                return result
            
            # Convert car_id to integer
            try:
                car_id_int = int(car_id)
            except (ValueError, TypeError):
                return "❌ Invalid car ID. Please provide a valid car number."
            
            # Handle date parameters - use None if empty strings
            start_param = start_date if start_date and start_date.strip() else None
            end_param = end_date if end_date and end_date.strip() else None
            
            # Get revenue details from admin manager
            revenue_data = self.admin_manager.get_car_revenue_details(car_id_int, start_param, end_param)
            if not revenue_data:
                return f"❌ Car with ID {car_id_int} not found."
            
            car_details = revenue_data.get('car_details', {})
            monthly_revenue = revenue_data.get('monthly_revenue', [])
            
            result = f"💰 **Revenue Details - Car ID {car_id_int}:**\n"
            result += "=" * 50 + "\n"
            
            # Car Information
            result += f"🚗 **Car Information:**\n"
            result += f"• Vehicle: {car_details.get('make', 'N/A')} {car_details.get('model', 'N/A')}\n"
            result += f"• License Plate: {car_details.get('license_plate', 'N/A')}\n"
            result += f"• Category: {car_details.get('category', 'N/A')}\n"
            result += f"• Daily Rate: ${float(car_details.get('daily_rate', 0)):,.2f}\n\n"
            
            # Revenue Summary
            result += f"📊 **Revenue Summary:**\n"
            total_revenue = float(car_details.get('total_revenue', 0))
            total_bookings = car_details.get('total_bookings', 0)
            avg_revenue = float(car_details.get('avg_revenue_per_booking', 0))
            total_days = car_details.get('total_days_rented', 0)
            
            result += f"• Total Revenue: ${total_revenue:,.2f}\n"
            result += f"• Total Bookings: {total_bookings}\n"
            result += f"• Average Revenue per Booking: ${avg_revenue:,.2f}\n"
            result += f"• Total Days Rented: {total_days}\n"
            
            # Performance Metrics
            if 'roi' in car_details:
                result += f"• Return on Investment (ROI): {car_details['roi']:.2f}%\n"
            if 'revenue_per_day' in car_details:
                result += f"• Revenue per Day: ${car_details['revenue_per_day']:,.2f}\n"
            
            result += "\n"
            
            # Monthly Breakdown
            if monthly_revenue:
                result += f"📅 **Monthly Revenue Breakdown:**\n"
                for month_data in monthly_revenue:
                    month = month_data.get('month', 'Unknown')
                    month_bookings = month_data.get('bookings', 0)
                    month_rev = float(month_data.get('revenue', 0))
                    avg_booking = float(month_data.get('avg_booking_value', 0))
                    result += f"• {month}: ${month_rev:,.2f} ({month_bookings} bookings, avg: ${avg_booking:,.2f})\n"
            else:
                result += f"📅 **Monthly Revenue:** No revenue data for the specified period.\n"
            
            return result.strip()
            
        except Exception as e:
            return f"❌ Error retrieving car revenue details: {str(e)}"

    def process_user_input(self, user_input: str) -> str:
        """Process user input using Gemini AI with function calling."""
        if not self.client:
            return "❌ AI features are not available. Please check your API configuration."
        
        try:
            # Create the system prompt for the AI
            system_prompt = """
You are an AI assistant for a car rental system. You have access to various functions to help users.

Key guidelines:
- ALWAYS call the appropriate function for user requests, even if information is missing
- For booking requests, ALWAYS call 'create_booking' even with partial info - the system will guide the user
- For cancellation requests, ALWAYS call 'cancel_booking' even if booking ID is missing
- For admin requests (revenue, assets, etc.), check if user is admin and call appropriate functions
- Be helpful and conversational while ensuring accurate function calls

Available functions will be automatically provided to you.
"""
            
            # Create function calling messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Try to use function calling first, fall back to simple generation
            try:
                # Create function definitions for Gemini
                functions = self._define_functions()
                
                # Format tools for the newer API
                tools = []
                function_declarations = []
                for func_name, func_def in functions.items():
                    function_declaration = {
                        "name": func_name,
                        "description": func_def["description"],
                        "parameters": {
                            "type": "object",
                            "properties": func_def.get("parameters", {}),
                            "required": []  # Make all parameters optional
                        }
                    }
                    function_declarations.append(function_declaration)
                
                if function_declarations:
                    tools = [types.Tool(function_declarations=function_declarations)]
                
                # Generate response with function calling
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=messages,
                    tools=tools if tools else None
                )
                
                # Handle function calls
                if hasattr(response.candidates[0].content, 'parts'):
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call'):
                            function_call = part.function_call
                            function_name = function_call.name
                            function_args = dict(function_call.args) if function_call.args else {}
                              # Execute the function
                            result = self.call_tool(function_name, function_args)
                            return result
                
                # If no function call, return the text response
                return response.text if response.text else "I'm here to help! You can ask me about cars, bookings, or use commands like 'show cars', 'login', etc."
                
            except Exception as api_error:
                # Pattern matching fallback for common commands when AI fails
                user_input_lower = user_input.lower()
                
                # Show cars commands
                if any(phrase in user_input_lower for phrase in ['show cars', 'available cars', 'view cars', 'see cars', 'list cars', 'get cars']):
                    return self.show_available_cars()
                
                # Login commands
                if any(phrase in user_input_lower for phrase in ['login', 'log in', 'sign in']):
                    return "🔐 Please provide your login credentials:\n• Email: \n• Password: \n\nOr say 'login [email] [password]'"
                
                # Register commands
                if any(phrase in user_input_lower for phrase in ['register', 'sign up', 'create account']):
                    return "📝 To register, please provide:\n• Email: \n• Password: \n• National ID: \n\nOr say 'register [email] [password] [national_id]'"
                
                # Booking commands
                if any(phrase in user_input_lower for phrase in ['book', 'rent', 'reserve']):
                    if not self.current_user:
                        return "❌ You must be logged in to book a car. Please login first."
                    return "🚗 To book a car, I need:\n• Car ID (use 'show cars' to see available cars)\n• Start date (YYYY-MM-DD)\n• Duration in days\n\nOr say 'book car [ID] for [days] days starting [date]'"
                
                # View bookings
                if any(phrase in user_input_lower for phrase in ['my booking', 'view booking', 'see booking', 'check booking']):
                    return self.view_user_bookings()
                
                # Admin functions (if user is admin)
                if self.is_admin:
                    if 'asset detail' in user_input_lower:
                        return self.get_asset_details("")
                    if 'revenue stat' in user_input_lower:
                        return self.get_revenue_stats("", "")
                    if 'asset report' in user_input_lower:
                        return self.generate_asset_report("", "")
                
                # Fallback to simple generation without function calling
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=user_input
                    )
                    
                    ai_response = response.text if response.text else "I'm here to help with your car rental needs!"
                    
                    # Add contextual suggestions
                    if self.current_user is None:
                        ai_response += "\n\n💡 Try: 'login', 'register', or 'show cars'"
                    elif self.is_admin:
                        ai_response += "\n\n💡 Admin commands: 'asset details', 'revenue stats', 'asset report'"
                    else:
                        ai_response += "\n\n💡 Try: 'book a car', 'my bookings', or 'show cars'"
                    
                    return ai_response
                    
                except Exception as fallback_error:
                    return f"I can help you with car rental tasks. What would you like to do? (API Error: {str(fallback_error)})"
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error processing your request: {str(e)}"
    
    def call_tool(self, function_name: str, args: dict) -> str:
        """Execute a tool function based on the function name."""
        try:
            # Map function names to method calls
            function_mapping = {
                # User functions
                "get_available_cars": lambda: self.show_available_cars(),
                "user_login": lambda: self.login_user(
                    args.get("email", ""), 
                    args.get("password", "")
                ),
                "user_register": lambda: self.register_user(
                    args.get("email", ""), 
                    args.get("password", ""), 
                    args.get("national_id", "")
                ),
                "get_user_bookings": lambda: self.view_user_bookings(),
                "create_booking": lambda: self.book_car(
                    args.get("car_id", ""), 
                    args.get("start_date", ""), 
                    args.get("duration", "")
                ),
                "cancel_booking": lambda: self.cancel_booking(
                    args.get("booking_id", "")
                ),
                "user_logout": lambda: self.logout_user(),
                "view_terms": lambda: self.view_terms_conditions(),
                
                # Admin functions
                "get_all_users": lambda: self.admin_view_all_users(),
                "get_all_bookings": lambda: self.admin_view_all_bookings(),
                "get_car_status": lambda: self.get_car_status(),
                "get_revenue_stats": lambda: self.get_revenue_stats(
                    args.get("start_date", ""), 
                    args.get("end_date", "")
                ),
                "get_asset_details": lambda: self.get_asset_details(
                    args.get("car_id", "")
                ),
                "generate_asset_report": lambda: self.generate_asset_report(
                    args.get("start_date", ""), 
                    args.get("end_date", "")
                ),
                "get_car_revenue_details": lambda: self.get_car_revenue_details(
                    args.get("car_id", ""), 
                    args.get("start_date", ""), 
                    args.get("end_date", "")
                ),
                "execute_sql": lambda: self.execute_sql_query(
                    args.get("query", "")
                )
            }
            
            # Execute the function if it exists
            if function_name in function_mapping:
                return function_mapping[function_name]()
            else:
                return f"❌ Unknown function: {function_name}"
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Error executing function '{function_name}': {str(e)}"

    def interactive_login(self) -> str:
        """Interactive login with separate email and password prompts"""
        try:
            print("\n🔐 **Login Required**")
            print("=" * 30)
            
            # Get email
            email = input("📧 Please enter your email: ").strip()
            if not email:
                return "❌ Email cannot be empty."
            
            # Get password (hidden)
            password = getpass.getpass("🔒 Please enter your password: ")
            if not password:
                return "❌ Password cannot be empty."
            
            # Attempt login
            return self.login_user(email, password)
            
        except KeyboardInterrupt:
            return "\n❌ Login cancelled."
        except Exception as e:
            return f"❌ Error during login: {str(e)}"
    
    def interactive_register(self) -> str:
        """Interactive registration with separate prompts"""
        try:
            print("\n📝 **Create New Account**")
            print("=" * 30)
            
            # Get email
            email = input("📧 Please enter your email: ").strip()
            if not email:
                return "❌ Email cannot be empty."
            
            # Get password (hidden)
            password = getpass.getpass("🔒 Please enter your password: ")
            if not password:
                return "❌ Password cannot be empty."
            
            # Confirm password
            password_confirm = getpass.getpass("🔒 Please confirm your password: ")
            if password != password_confirm:
                return "❌ Passwords do not match."
            
            # Get national ID
            national_id = input("🆔 Please enter your national ID: ").strip()
            if not national_id:
                return "❌ National ID cannot be empty."
              # Attempt registration
            return self.register_user(email, password, national_id)
            
        except KeyboardInterrupt:
            return "\n❌ Registration cancelled."
        except Exception as e:
            return f"❌ Error during registration: {str(e)}"
    
    def show_help(self) -> str:
        """Display help information with available commands"""
        current_status = "NOT logged in" if not self.current_user else f"logged in as {self.current_user.get('email', 'user')} ({'admin' if self.is_admin else 'regular user'})"
        
        help_text = f"""
🆘 **HELP - Car Rental System Commands**
{'='*50}
**Current Status:** {current_status}

**Quick Commands:**
• login          - Sign in to your account
• register       - Create a new account  
• logout         - Sign out of your account
• help           - Show this help message
• exit/quit      - Leave the application

**Available Actions (use natural language):**

**🚗 Car Management:**
• "Show me available cars"
• "Show cars in [category]" (luxury, mid-range, economy)
• "Book car ID [number] for [days] days starting [YYYY-MM-DD]"

**📋 Booking Management:**
• "What are my current bookings?"
• "Show my booking history"
• "Cancel booking ID [number]"

**📄 Information:**
• "Show terms and conditions"
• "View terms"

**👨‍💼 Admin Commands (admin only):**
• "Show all users"
• "Show all bookings" 
• "Get car status summary"
• "Get revenue statistics"
• "Execute SQL: [SELECT query]"

**💡 Examples:**
• "I want to book car ID 1 for 3 days starting 2025-07-01"
• "Show me luxury cars only"
• "What bookings do I have this month?"
• "Cancel my booking number 5"

**🔒 Security Notes:**
• Passwords are hidden when typing
• Only admin users can access administrative functions
• SQL queries are restricted to SELECT statements only

Type any command or use natural language to describe what you want to do!
{'='*50}
"""
        return help_text.strip()

    def run(self):
        """Main application loop"""
        print("🚗 Welcome to the AI-Powered Car Rental System!")
        print("=" * 50)
        print("I'm your AI assistant. I can help you with:")
        print("• Creating an account or logging in")
        print("• Viewing and booking available cars")
        print("• Managing your bookings")
        print("• Administrative tasks (if you're an admin)")
        print("• Answering questions about our services")
        print("\nQuick Commands:")
        print("- Type 'login' to sign in")
        print("- Type 'register' to create a new account")
        print("- Type 'logout' to sign out")
        print("- Type 'help' to see all available commands")
        print("\nOr use natural language for other actions:")
        print("- 'Show me available cars'")
        print("- 'Book car ID 1 for 3 days starting 2025-07-01'")
        print("- 'What are my current bookings?'")
        print("\nType 'exit' or 'quit' to leave the application.")
        print("=" * 50)
        
        while True:
            try:
                # Generate context-aware prompt
                if not self.current_user:
                    prompt = "🤖 Welcome! How can I help you today? (Try 'login', 'register', or 'show cars')"
                else:
                    user_name = self.current_user.get('email', 'User').split('@')[0] 
                    if self.is_admin:
                        prompt = f"🤖 Hello Admin {user_name}! What would you like to do? (Bookings, users, cars, revenue, or help)"
                    else:
                        prompt = f"🤖 Hello {user_name}! Ready to book a car, view bookings, or need help?"
                
                user_input = input(f"\n{prompt} ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                    if self.current_user:
                        print(f"👋 Goodbye, {self.current_user.get('email', 'User')}!")
                    else:
                        print("👋 Goodbye! Thanks for using our car rental system.")
                    break
                
                if not user_input:
                    print("ℹ️ Please enter a command or question.")
                    continue
                
                # Check for simple login/register commands first
                user_input_lower = user_input.lower().strip()
                
                # Handle simple login command
                if user_input_lower in ['login', 'log in', 'signin', 'sign in']:
                    response = self.interactive_login()
                    print(f"\n{response}")
                    continue
                  # Handle simple register command  
                if user_input_lower in ['register', 'signup', 'sign up', 'create account', 'register account', 'new account', 'register new account', 'create new account']:
                    response = self.interactive_register()
                    print(f"\n{response}")
                    continue
                  # Handle logout command
                if user_input_lower in ['logout', 'log out', 'signout', 'sign out']:
                    response = self.logout_user()
                    print(f"\n{response}")
                    continue
                
                # Handle help command
                if user_input_lower in ['help', '?', 'commands', 'menu']:
                    response = self.show_help()
                    print(f"\n{response}")
                    continue
                
                # Process other inputs with Gemini AI
                response = self.process_user_input(user_input)
                print(f"\n{response}")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using our car rental system.")
                break
            except Exception as e:
                print(f"\n❌ An error occurred: {str(e)}")

def main():
    """Main entry point"""
    # You can set your Gemini API key here or as an environment variable
    api_key = "YOUR_GEMINI_API_KEY"  # Replace with your actual API key
    
    try:
        app = GeminiCarRentalTerminal(api_key=api_key)
        app.run()
    except Exception as e:
        print(f"❌ Failed to start application: {str(e)}")
        print("Please check your Gemini API key and try again.")

if __name__ == "__main__":
    main()
