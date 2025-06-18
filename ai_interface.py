import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from auth import AuthenticationManager
from database import DatabaseManager
from car_manager import CarManager
from booking_manager import BookingManager
from admin_functions import AdminManager
from security import SecurityUtils
import os
import ssl

# Configure SSL
ssl._create_default_https_context = ssl._create_unverified_context

# Configure Google API key
GOOGLE_API_KEY = "AIzaSyAz5B_lFFSTXJiXFD_RakW6NQACpeJAZsM"  # Replace with your actual API key

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
        
        # Initialize Gemini AI model
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def handle_login(self, email: str, password: str) -> Tuple[bool, str]:
        """Handle user login"""
        success, msg, user_info = self.auth_manager.login(email, password)
        if success:
            self.session_token = user_info['session_token']
            self.user_id = user_info['user_id']
            self.is_admin = user_info['role'] == 'admin'
            self.current_user = user_info
        return success, msg

    def handle_registration(self, email: str, password: str, national_id: str) -> Tuple[bool, str]:
        """Handle user registration"""
        return self.auth_manager.register_user(email, password, national_id)

    def handle_logout(self) -> Tuple[bool, str]:
        """Handle user logout"""
        if self.session_token:
            success = self.auth_manager.logout(self.session_token)
            if success:
                self.session_token = None
                self.user_id = None
                self.is_admin = False
                self.current_user = None
                return True, "Logged out successfully."
        return False, "No active session."

    def get_available_cars(self) -> List[Dict]:
        """Get list of available cars"""
        return self.car_manager.show_available_cars()

    def create_booking(self, car_id: int, start_date: str, duration: int) -> Tuple[bool, str, Optional[float]]:
        """Create a new booking"""
        if not self.user_id:
            return False, "Please login first.", None

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
            start_date=start_date,            end_date=end_date
        )

        if success:
            return True, message, total_cost
        return False, message, None
        
    def get_user_bookings(self) -> List[Dict]:
        """Get bookings for current user with car details"""
        if not self.user_id:
            return []
        bookings = self.booking_manager.get_user_bookings(self.user_id)
        
        # If no bookings found, return empty list
        if not bookings:
            return []
            
        # Get car details for each booking to include make, model and daily rate
        for booking in bookings:
            car_id = booking.get('car_id')
            if car_id:
                cars = self.car_manager.show_available_cars()
                car = next((c for c in cars if c['id'] == car_id), None)
                if car:
                    booking['make'] = car['make']
                    booking['model'] = car['model']
                    booking['daily_rate'] = car['daily_rate']
                    
        return bookings

    def cancel_booking(self, booking_id: int) -> Tuple[bool, str]:
        """Cancel a user's booking"""
        if not self.user_id:
            return False, "Please login first."
        return self.booking_manager.cancel_booking(booking_id, self.user_id)

    def view_terms_and_conditions(self) -> str:
        """Display the terms and conditions"""
        try:
            with open("terms_conditions.enc", "r") as f:
                encrypted_terms = f.read()
            key = "SecureCarRental2024"
            decrypted_terms = SecurityUtils.decrypt_data(encrypted_terms, key)
            return decrypted_terms
        except FileNotFoundError:
            return "Terms and conditions file not found."
        except Exception as e:
            return f"Error displaying terms and conditions: {str(e)}"

    def process_command(self, user_input: str) -> str:
        """Process natural language commands using Gemini"""
        try:
            # Build the system prompt with all available commands and context
            prompt_parts = [
                "You are a car rental system assistant by the name Yash. Current status:",
                f"User: {self.current_user['email'] if self.current_user else 'Not logged in'}",
                f"Role: {'Admin' if self.is_admin else 'User' if self.user_id else 'Guest'}",
                "",
                "Available commands:",
                "For all users:",
                "- Login/Register",
                "- View available cars",
                "- Book a car",
                "- View my bookings",
                "- Cancel booking",
                "- View terms and conditions",
                "- Logout",
                "",
                "Additional admin commands:",                
                "- View all users",
                "- View all bookings",
                "- Search bookings by username",
                "- View car status",
                "- Search car by plate",
                "- Search cars by make/model",
                "- Set car maintenance",
                "- View asset summary",
                "- Update car assets",
                "- View revenue statistics",
                "- Generate asset report",
                "",
                "Based on the user's input, determine which action they want to take.",
                "Respond with a single command: LOGIN, REGISTER, SHOW_CARS, BOOK, VIEW_BOOKINGS,",
                "CANCEL_BOOKING, TERMS, LOGOUT, ADMIN_USERS, VIEW_ALL_BOOKINGS, ADMIN_SEARCH_BOOKINGS,",
                "ADMIN_CAR_STATUS, ADMIN_SEARCH_CAR, ADMIN_SEARCH_CARS, ADMIN_MAINTENANCE,",
                "ADMIN_ASSETS, ADMIN_UPDATE_ASSETS, ADMIN_REVENUE, ADMIN_REPORT, or UNKNOWN."
            ]
            
            # Join all parts with newlines to create the system prompt
            system_prompt = "\n".join(prompt_parts)
            
            # Combine context and user input
            prompt = f"{system_prompt}\n\nUser input: {user_input}\nCommand:"
              # Generate response using Gemini
            response = self.model.generate_content(prompt)
            
            # Get the command from response
            if not response.text:
                return "Sorry, I couldn't understand that command."
            
            command = response.text.strip().upper()

            # Handle commands
            if command == "LOGIN":
                if not self.session_token:
                    email = input("Email: ").strip()
                    password = input("Password: ").strip()
                    success, msg = self.handle_login(email, password)
                    return msg
                return "Already logged in."
            
            elif command == "REGISTER":
                if not self.session_token:
                    email = input("Email: ").strip()
                    password = input("Password: ").strip()
                    national_id = input("National ID: ").strip()
                    success, msg = self.handle_registration(email, password, national_id)
                    return msg
                return "Please logout first."

            elif command == "SHOW_CARS":
                cars = self.get_available_cars()
                if not cars:
                    return "No cars available."
                
                result = "\nAvailable Cars:\n"
                for car in cars:
                    result += f"\nCar ID: {car['id']}\n"
                    result += f"Make/Model: {car['make']} {car['model']}\n"
                    result += f"Category: {car['category']}\n"
                    result += f"Daily Rate: ${car['daily_rate']}/day\n"
                    result += "-" * 30
                return result

            elif command == "BOOK":
                if not self.session_token:
                    return "Please login first."
                
                cars = self.get_available_cars()
                if not cars:
                    return "No cars available for booking."

                print("\nAvailable Cars:")
                for car in cars:
                    print(f"Car ID: {car['id']} - {car['make']} {car['model']} - ${car['daily_rate']}/day")

                try:
                    car_id = int(input("Enter Car ID to book: ").strip())
                    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
                    duration = int(input("Enter number of days: ").strip())
                    
                    success, msg, total_cost = self.create_booking(car_id, start_date, duration)
                    if success and total_cost:
                        return f"{msg}\nTotal cost: ${total_cost:.2f}"                    
                    return msg
                except ValueError:
                    return "Invalid input. Please try again."
                    
            elif command == "VIEW_BOOKINGS":
                if not self.session_token:
                    return "Please login first."
                
                bookings = self.get_user_bookings()
                if not bookings:
                    return "No bookings found."
                
                result = "\nYour Bookings:\n"
                for booking in bookings:
                    # Calculate number of days
                    start_date = datetime.strptime(booking['start_date'], '%Y-%m-%d')
                    end_date = datetime.strptime(booking['end_date'], '%Y-%m-%d')
                    days = (end_date - start_date).days
                    
                    # Calculate total cost
                    daily_rate = booking.get('daily_rate', 0)
                    total_cost = daily_rate * days
                    
                    result += f"\nBooking ID: {booking['id']}\n"
                    result += f"Car: {booking.get('make', 'N/A')} {booking.get('model', 'N/A')}\n"
                    result += f"Start Date: {booking['start_date']}\n"
                    result += f"End Date: {booking['end_date']}\n"
                    result += f"Duration: {days} days\n"
                    result += f"Daily Rate: ${daily_rate:.2f}\n"
                    result += f"Total Cost: ${total_cost:.2f}\n"
                    result += "-" * 30
                return result

            elif command == "CANCEL_BOOKING":
                if not self.session_token:
                    return "Please login first."
                
                bookings = self.get_user_bookings()
                if not bookings:
                    return "No bookings found to cancel."
                
                result = "\nYour Bookings:\n"
                for booking in bookings:
                    result += f"Booking ID: {booking['id']} ({booking['start_date']} to {booking['end_date']})\n"
                
                booking_id = input("\nEnter Booking ID to cancel: ").strip()
                if not booking_id:
                    return "Cancellation aborted."
                
                try:
                    success, msg = self.cancel_booking(int(booking_id))
                    return msg
                except ValueError:
                    return "Invalid booking ID. Please try again."            
            elif command == "TERMS":
                return self.view_terms_and_conditions()

            # Admin commands
            elif command == "VIEW_ALL_BOOKINGS" or command == "ADMIN_VIEW_BOOKINGS":
                if not self.is_admin:
                    return "Admin access required."
                bookings = self.admin_manager.view_user_bookings()
                if not bookings:
                    return "No bookings found."
                result = "\nAll Bookings:\n"
                for booking in bookings:
                    # Calculate number of days and total cost
                    start_date = datetime.strptime(booking['start_date'], '%Y-%m-%d')
                    end_date = datetime.strptime(booking['end_date'], '%Y-%m-%d')
                    days = (end_date - start_date).days
                    daily_rate = booking.get('daily_rate', 0)
                    total_cost = daily_rate * days

                    result += f"Booking ID: {booking['id']}\n"
                    result += f"User: {booking.get('user_email', 'Unknown')}\n"
                    result += f"Car: {booking['make']} {booking['model']}\n"
                    result += f"Period: {booking['start_date']} to {booking['end_date']}\n"
                    result += f"Duration: {days} days\n"
                    result += f"Daily Rate: ${daily_rate:.2f}\n"
                    result += f"Total Cost: ${total_cost:.2f}\n"
                    result += f"Status: {booking['status'].upper()}\n"
                    result += "-" * 30 + "\n"
                return result

            elif command == "ADMIN_USERS":
                if not self.is_admin:
                    return "Admin access required."
                users = self.view_all_users()
                result = "\nAll Users:\n"
                for user in users:
                    result += f"ID: {user['id']}, Email: {user['email']}, Role: {user['role']}\n"
                return result

            elif command == "ADMIN_SEARCH_BOOKINGS":
                if not self.is_admin:
                    return "Admin access required."
                username = input("Enter username (email): ")
                bookings = self.search_bookings_by_username(username)
                result = "\nUser Bookings:\n"
                for booking in bookings:
                    # Calculate number of days and total cost
                    start_date = datetime.strptime(booking['start_date'], '%Y-%m-%d')
                    end_date = datetime.strptime(booking['end_date'], '%Y-%m-%d')
                    days = (end_date - start_date).days
                    daily_rate = booking.get('daily_rate', 0)
                    total_cost = daily_rate * days

                    result += f"Booking ID: {booking['id']}\n"
                    result += f"Car: {booking['make']} {booking['model']}\n"
                    result += f"Period: {booking['start_date']} to {booking['end_date']}\n"
                    result += f"Duration: {days} days\n"
                    result += f"Daily Rate: ${daily_rate:.2f}\n"
                    result += f"Total Cost: ${total_cost:.2f}\n"
                    result += "-" * 30 + "\n"
                return result

            elif command == "ADMIN_CAR_STATUS":
                if not self.is_admin:
                    return "Admin access required."
                cars = self.view_car_status()
                result = "\nCar Status:\n"
                for car in cars:
                    result += f"ID: {car['id']}, {car['make']} {car['model']}\n"
                    result += f"Status: {'Available' if car['is_available'] else 'Not Available'}\n"
                    if car.get('booked_by'):
                        result += f"Booked by: {car['booked_by']}\n"
                    result += "-" * 30 + "\n"
                return result

            elif command == "ADMIN_SEARCH_CAR":
                if not self.is_admin:
                    return "Admin access required."
                plate = input("Enter license plate: ").strip().upper()
                car = self.search_car_by_plate(plate)
                if car:
                    return f"\nCar Details:\nMake/Model: {car['make']} {car['model']}\nYear: {car['year']}\nStatus: {'Available' if car['is_available'] else 'Not Available'}"
                return "Car not found."

            elif command == "ADMIN_SEARCH_CARS":
                if not self.is_admin:
                    return "Admin access required."
                make = input("Enter make: ")
                model = input("Enter model: ")
                cars = self.search_cars_by_make_model(make, model)
                result = "\nSearch Results:\n"
                for car in cars:
                    result += f"{car['make']} {car['model']} ({car['license_plate']})\n"
                return result

            elif command == "ADMIN_MAINTENANCE":
                if not self.is_admin:
                    return "Admin access required."
                car_id = input("Enter Car ID: ").strip()
                try:
                    is_available = input("Set as available? (y/n): ").lower() == 'y'
                    success, msg = self.set_car_maintenance_status(int(car_id), is_available)
                    return msg
                except ValueError:
                    return "Invalid car ID."

            elif command == "ADMIN_ASSETS":
                if not self.is_admin:
                    return "Admin access required."
                summary = self.view_asset_summary()
                if not summary:
                    return "No asset data available."
                
                result = "\nFleet Summary:\n"
                result += f"Total Cars: {summary.get('fleet_value', {}).get('total_cars', 0)}\n"
                result += f"Fleet Value: ${summary.get('fleet_value', {}).get('fleet_value', 0):,.2f}\n"
                result += f"Total Maintenance Cost: ${summary.get('fleet_value', {}).get('total_maintenance', 0):,.2f}\n"
                return result

            elif command == "ADMIN_REVENUE":
                if not self.is_admin:
                    return "Admin access required."
                start_date = input("Start Date (YYYY-MM-DD) or press Enter for this month: ")
                end_date = input("End Date (YYYY-MM-DD) or press Enter for today: ")
                stats = self.get_revenue_statistics(start_date or None, end_date or None)
                
                result = "\nRevenue Statistics:\n"
                result += f"Period: {stats.get('period', {}).get('start', 'N/A')} to {stats.get('period', {}).get('end', 'N/A')}\n"
                result += f"Total Revenue: ${stats.get('overall', {}).get('total_revenue', 0):,.2f}\n"
                result += f"Total Bookings: {stats.get('overall', {}).get('total_bookings', 0)}\n"
                return result

            elif command == "ADMIN_REPORT":
                if not self.is_admin:
                    return "Admin access required."
                start_date = input("Start Date (YYYY-MM-DD) or press Enter for this month: ")
                end_date = input("End Date (YYYY-MM-DD) or press Enter for today: ")
                report = self.generate_asset_report(start_date or None, end_date or None)
                
                result = "\nAsset Report:\n"
                result += f"Period: {report.get('period', {}).get('start', 'N/A')} to {report.get('period', {}).get('end', 'N/A')}\n"
                result += f"Total Investment: ${report.get('financials', {}).get('total_investment', 0):,.2f}\n"
                result += f"Total Maintenance: ${report.get('financials', {}).get('total_maintenance', 0):,.2f}\n"
                result += f"Total Revenue: ${report.get('financials', {}).get('total_revenue', 0):,.2f}\n"
                return result

            elif command == "LOGOUT":
                success, msg = self.handle_logout()
                return msg

            else:
                return "I'm not sure what you want to do. Please try again with a clearer command."

        except Exception as e:
            return f"Error processing command: {str(e)}"

    def view_all_users(self) -> List[Dict]:
        """Admin: View all users in the system"""
        if not self.is_admin:
            return []
        return self.admin_manager.view_all_users()

    def search_bookings_by_username(self, username: str) -> List[Dict]:
        """Admin: Search bookings by username"""
        if not self.is_admin:
            return []
        return self.admin_manager.search_bookings_by_username(username)

    def search_car_by_plate(self, license_plate: str) -> Optional[Dict]:
        """Admin: Search car by license plate"""
        if not self.is_admin:
            return None
        return self.admin_manager.search_car_by_plate(license_plate)

    def search_cars_by_make_model(self, make: str, model: str) -> List[Dict]:
        """Admin: Search cars by make and model"""
        if not self.is_admin:
            return []
        return self.admin_manager.search_cars_by_make_model(make, model)

    def set_car_maintenance_status(self, car_id: int, is_available: bool) -> Tuple[bool, str]:
        """Admin: Set car maintenance status"""
        if not self.is_admin:
            return False, "Admin access required"
        return self.car_manager.set_car_maintenance_status(car_id, is_available)

    def view_car_status(self) -> List[Dict]:
        """Admin: View status of all cars"""
        if not self.is_admin:
            return []
        return self.car_manager.show_car_status()

    def get_revenue_statistics(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Admin: Get revenue statistics"""
        if not self.is_admin:
            return {}
        return self.admin_manager.get_revenue_statistics(start_date, end_date)

    def get_revenue_alerts(self) -> List[Dict]:
        """Admin: Get revenue alerts"""
        if not self.is_admin:
            return []
        return self.admin_manager.get_revenue_alerts()

    def view_asset_summary(self) -> Dict:
        """Admin: View asset summary"""
        if not self.is_admin:
            return {}
        return self.admin_manager.view_asset_summary()

    def generate_asset_report(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """Admin: Generate asset report"""
        if not self.is_admin:
            return {}
        return self.admin_manager.generate_asset_report(start_date, end_date)

    def update_car_assets(self, car_id: int, asset_data: Dict) -> Tuple[bool, str]:
        """Admin: Update car asset information"""
        if not self.is_admin:
            return False, "Admin access required"
        return self.car_manager.update_car_assets(car_id, asset_data, self.user_id)

    def update_maintenance_record(self, car_id: int, maintenance_data: Dict) -> Tuple[bool, str]:
        """Admin: Update car maintenance record"""
        if not self.is_admin:
            return False, "Admin access required"
        return self.car_manager.update_maintenance_record(car_id, maintenance_data, self.user_id)

def main():
    interface = AICarRentalInterface()
    print("\n=== AI Car Rental System Developed by Riyashdeen Abdul Rahman ===")
    print("Type 'help' for available commands or 'exit' to quit.")
    
    while True:
        user_input = input("\nWhat would you like to do? ").strip()
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        if user_input.lower() == 'help':
            print("\nAvailable commands:")
            # Show base commands for all users
            print("\nGeneral Commands:")
            print("- Login")
            print("- Register")
            print("- Show available cars")
            print("- Book a car")
            print("- View my bookings")
            print("- Cancel booking")
            print("- View terms and conditions")
            print("- Logout")
            print("- Exit")
            
            # Show additional admin commands if user is admin
            if interface.is_admin:
                print("\nAdmin Commands:")                
                print("User Management:")
                print("- View all users")
                print("- View all bookings")
                print("- Search bookings by username")
                
                print("\nCar Management:")
                print("- View car status")
                print("- Search car by plate")
                print("- Search cars by make/model")
                print("- Set car maintenance status")
                
                print("\nAsset Management:")
                print("- View asset summary")
                print("- Update car assets")
                print("- Update maintenance record")
                
                print("\nFinancial Management:")
                print("- View revenue statistics")
                print("- Generate asset report")
            continue
        
        response = interface.process_command(user_input)
        print("\n" + response)

if __name__ == "__main__":
    main()