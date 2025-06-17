from security import SecurityUtils
from database import DatabaseManager
from typing import Optional, Dict, Tuple
import sqlite3
from datetime import datetime, timedelta
from google import genai

# Importing components
from database import DatabaseManager   
from auth import AuthenticationManager


class CarRentalApp:
    
    def __init__(self):
        # Initialize components
        self.db = DatabaseManager()
        self.auth = AuthenticationManager(self.db)
        
        # Insert sample data
        self.db.insert_sample_data()
        
        # Create default superuser
        self.create_default_users()
    
    def create_default_users(self):

        # Create superuser
        self.auth.register_user("admin@carental.com", "Admin123!", "000000000", "superuser")
        
        # Create admin
        self.auth.register_user("staff@carental.com", "Staff123!", "111111111", "admin")
        
        # Create regular user
        self.auth.register_user("user@carental.com", "User123!", "222222222", "user")

    def user_auth_menu(self):
        while True:
            print("\n1. Register\n2. Login\n3. Exit")
            choice = input("Choose an option: ")
            if choice == "1":
                username = input("Enter new username: ")
                password = input("Enter new password: ")
                if AuthenticationManager().register_user(username, password):
                    print("Registration successful!")
                else:
                    print("Registration failed. Username may already exist.")
            elif choice == "2":
                username = input("Enter username: ")
                password = input("Enter password: ")
                if AuthenticationManager().login(username, password):
                    print("Login successful!")
                else:
                    print("Login failed. Check your credentials.")
            elif choice == "3":
                print("Goodbye!")
                break
            else:
                print("Invalid option. Try again.")


if __name__ == "__main__":
    while True:
        print("\nWelcome to the Car Rental App!")
        app = CarRentalApp()
        app.user_auth_menu()

