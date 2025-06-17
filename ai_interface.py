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

# Configure Gemini
GOOGLE_API_KEY = "AIzaSyAz5B_lFFSTXJiXFD_RakW6NQACpeJAZsM"  # Replace with your actual API key
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

class AICarRentalInterface:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.auth_manager = AuthenticationManager(self.db_manager)
        self.car_manager = CarManager(self.db_manager)
        self.booking_manager = BookingManager(self.db_manager)
        self.admin_manager = AdminManager(self.db_manager)
        self.session_token = None
        self.user_id = None
        self.is_admin = False
        self.current_user = None

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
            start_date=start_date,
            end_date=end_date
        )

        if success:
            return True, message, total_cost
        return False, message, None

    def get_user_bookings(self) -> List[Dict]:
        """Get bookings for current user"""
        if not self.user_id:
            return []
        return self.booking_manager.get_user_bookings(self.user_id)

    def process_command(self, user_input: str) -> str:
        """Process natural language commands using Gemini"""
        # Context for the AI
        system_context = f"""
        You are a car rental system assistant. Current status:
        User: {self.current_user['email'] if self.current_user else 'Not logged in'}
        Role: {'Admin' if self.is_admin else 'User' if self.user_id else 'Guest'}
        
        Available commands:
        - Login/Register
        - View available cars
        - Book a car
        - View my bookings
        - View terms and conditions
        - Logout
        - Admin functions (if admin)

        Based on the user's input, determine which action they want to take.
        Respond with a single command: LOGIN, REGISTER, SHOW_CARS, BOOK, VIEW_BOOKINGS, TERMS, LOGOUT, or UNKNOWN.
        """

        try:
            # Combine context and user input
            prompt = f"{system_context}\n\nUser input: {user_input}\nCommand:"
            
            # Generate response using Gemini
            response = model.generate_content(prompt)
            
            # Get the command from response
            if response.text:
                command = response.text.strip().upper()
            else:
                return "Sorry, I couldn't understand that command."

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
                    result += f"\nBooking ID: {booking['id']}\n"
                    result += f"Start Date: {booking['start_date']}\n"
                    result += f"End Date: {booking['end_date']}\n"
                    result += "-" * 30
                return result

            elif command == "LOGOUT":
                success, msg = self.handle_logout()
                return msg

            else:
                return "I'm not sure what you want to do. Please try again with a clearer command."

        except Exception as e:
            return f"Error processing command: {str(e)}"

def main():
    interface = AICarRentalInterface()
    print("\n=== AI Car Rental System ===")
    print("Type 'help' for available commands or 'exit' to quit.")
    
    while True:
        user_input = input("\nWhat would you like to do? ").strip()
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        if user_input.lower() == 'help':
            print("\nAvailable commands:")
            print("- Login")
            print("- Register")
            print("- Show available cars")
            print("- Book a car")
            print("- View my bookings")
            print("- View terms and conditions")
            print("- Logout")
            print("- Exit")
            continue
        
        response = interface.process_command(user_input)
        print("\n" + response)

if __name__ == "__main__":
    interface = AICarRentalInterface()
    print("\n=== AI Car Rental System ===")
    print("Type 'help' for available commands or 'exit' to quit.")
    
    while True:
        user_input = input("\nWhat would you like to do? ").strip()
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        if user_input.lower() == 'help':
            print("\nAvailable commands:")
            print("- Login")
            print("- Register")
            print("- Show available cars")
            print("- Book a car")
            print("- View my bookings")
            print("- View terms and conditions")
            print("- Logout")
            print("- Exit")
            continue
        
        response = interface.process_command(user_input)
        print("\n" + response)