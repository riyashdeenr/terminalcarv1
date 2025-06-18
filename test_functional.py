#!/usr/bin/env python3
"""
Functional Tests for Car Rental Management System
Tests all major functionality and integrations between components
"""
import unittest
import os
import sqlite3
from datetime import datetime, timedelta
from auth import AuthenticationManager
from database import DatabaseManager
from car_manager import CarManager
from booking_manager import BookingManager
from admin_functions import AdminManager
from ai_interface_advance import AICarRentalInterface
from security import SecurityUtils
from unittest.mock import patch

class TestCarRentalSystem(unittest.TestCase):
    """Test suite for the Car Rental Management System"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test database and managers"""
        # Use a test database
        cls.test_db = "test_car_rental.db"
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)
            
        # Initialize managers with test database
        cls.db_manager = DatabaseManager(db_path=cls.test_db)
        
        # Wait for database initialization to complete
        with cls.db_manager.get_connection() as conn:
            conn.execute("SELECT 1")  # Simple query to ensure DB is ready
            
        cls.auth_manager = AuthenticationManager(cls.db_manager)
        cls.car_manager = CarManager(cls.db_manager)
        cls.booking_manager = BookingManager(cls.db_manager)
        cls.admin_manager = AdminManager(cls.db_manager)
        
        # Initialize interface with test database
        cls.interface = AICarRentalInterface()
        cls.interface.db_manager = cls.db_manager  # Use test database
        cls.interface.auth_manager = cls.auth_manager
        cls.interface.car_manager = cls.car_manager
        cls.interface.booking_manager = cls.booking_manager
        cls.interface.admin_manager = cls.admin_manager
        
        # Create test data
        cls._create_test_data()
    
    @classmethod
    def _create_test_data(cls):
        """Create sample data for testing"""
        # Create test users
        cls.test_user = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'national_id': 'TEST123'
        }
        cls.test_admin = {
            'email': 'admin@example.com',
            'password': 'AdminPass123!',
            'national_id': 'ADMIN123'
        }
        
        # Add test cars
        cls.test_cars = [
            {
                'make': 'Toyota',
                'model': 'Camry',
                'year': 2023,
                'license_plate': 'TEST001',
                'daily_rate': 80.00,
                'category': 'standard'
            },
            {
                'make': 'BMW',
                'model': '7 Series',
                'year': 2024,
                'license_plate': 'TEST002',
                'daily_rate': 200.00,
                'category': 'luxury'
            }
        ]
        
        # Register users and add cars
        cls.auth_manager.register_user(
            cls.test_user['email'], 
            cls.test_user['password'],
            cls.test_user['national_id']
        )
        cls.auth_manager.register_user(
            cls.test_admin['email'], 
            cls.test_admin['password'],
            cls.test_admin['national_id'],
            role='admin'
        )
        
        for car in cls.test_cars:
            with cls.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO cars (make, model, year, license_plate, 
                                    daily_rate, category, is_available)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (car['make'], car['model'], car['year'], 
                     car['license_plate'], car['daily_rate'], 
                     car['category'], True))
    
    def setUp(self):
        """Reset interface state before each test"""
        # Create fresh interface instance with test database
        self.interface = AICarRentalInterface()
        self.interface.db_manager = self.db_manager
        self.interface.auth_manager = self.auth_manager
        self.interface.car_manager = self.car_manager
        self.interface.booking_manager = self.booking_manager
        self.interface.admin_manager = self.admin_manager
        
        # Reset session state
        self.interface.session_token = None
        self.interface.user_id = None
        self.interface.is_admin = False
        self.interface.current_user = None
        
        # Make test data available to instance methods
        self.test_user = type(self).test_user
        self.test_admin = type(self).test_admin
        self.test_cars = type(self).test_cars
        
    def test_01_user_registration(self):
        """Test user registration"""
        email = "newuser@example.com"
        password = "NewPass123!"
        national_id = "NEW123"
        
        # Test registration
        success, msg = self.auth_manager.register_user(email, password, national_id)
        self.assertTrue(success)
        self.assertIn("registered", msg.lower())
        
        # Test duplicate registration
        success, msg = self.auth_manager.register_user(email, password, national_id)
        self.assertFalse(success)
        self.assertIn("exists", msg.lower())
        
    @patch('builtins.input', side_effect=Exception('input() called during test'))
    def test_02_user_login(self, mock_input):
        """Test user login and session management"""
        # Test login using process_command with credentials (non-interactive)
        response = self.interface.process_command("login", 
            email=self.test_user['email'],
            password=self.test_user['password']
        )
        self.assertNotIn("failed", response.lower(), "Login failed")
        self.assertNotIn("invalid", response.lower(), "Login failed")
        
        # Test logged-in functionality
        response = self.interface.process_command("my bookings")
        self.assertNotIn("login first", response.lower())
        
        # Test logout
        response = self.interface.process_command("logout")
        self.assertIn("logged out", response.lower(), "Logout failed")
        self.assertIsNone(self.interface.session_token)
        
        # Verify logged out state
        response = self.interface.process_command("my bookings")
        self.assertIn("login", response.lower())
        # Test re-login after logout (non-interactive)
        response = self.interface.process_command("login", 
            email=self.test_user['email'],
            password=self.test_user['password']
        )
        self.assertNotIn("failed", response.lower(), "Re-login failed")
        self.assertNotIn("invalid", response.lower(), "Re-login failed")
        
    def test_03_car_listing(self):
        """Test car listing functionality"""
        # Test without login
        response = self.interface.process_command("show cars")
        self.assertTrue(any(car['make'] in response for car in self.test_cars))
        
        # Test with specific make/model
        response = self.interface.process_command("show available Toyota cars")
        self.assertIn("Toyota", response)
        self.assertIn("Camry", response)
    
    def test_04_booking_flow(self):
        """Test complete booking flow"""
        # Login first
        success, msg, user_info = self.auth_manager.login(
            self.test_user['email'], 
            self.test_user['password']
        )
        self.assertTrue(success)
        
        # Get available cars
        cars = self.car_manager.show_available_cars()
        self.assertTrue(len(cars) > 0)
        car_id = cars[0]['id']
        
        # Create booking
        start_date = datetime.now().strftime('%Y-%m-%d')
        success, msg = self.booking_manager.create_booking(
            user_info['user_id'],
            car_id,
            start_date,
            (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        )
        self.assertTrue(success)
        
        # View bookings
        bookings = self.booking_manager.get_user_bookings(user_info['user_id'])
        self.assertTrue(len(bookings) > 0)
        self.assertEqual(bookings[0]['car_id'], car_id)
    
    def test_05_admin_functions(self):
        """Test admin-specific functions"""
        # Login as admin
        success, msg, admin_info = self.auth_manager.login(
            self.test_admin['email'], 
            self.test_admin['password']
        )
        self.assertTrue(success)
        
        # Test viewing all users
        users = self.admin_manager.view_all_users()
        self.assertTrue(len(users) >= 2)  # At least test user and admin
        
        # Test viewing all bookings
        bookings = self.admin_manager.view_user_bookings()
        self.assertIsInstance(bookings, list)        # Test car maintenance status
        success, msg = self.car_manager.set_maintenance_status(1, False, admin_info['user_id'])
        self.assertTrue(success)
        
        # Test revenue statistics
        stats = self.admin_manager.get_revenue_statistics()
        self.assertIsInstance(stats, dict)
    
    def test_06_nlp_queries(self):
        """Test natural language query processing"""
        # Login first
        success, msg, user_info = self.auth_manager.login(
            self.test_user['email'], 
            self.test_user['password']
        )
        self.assertTrue(success, "Login failed")
        
        # Set up interface with login info
        self.interface.session_token = user_info['session_token']
        self.interface.user_id = user_info['user_id']
        self.interface.is_admin = user_info['role'] == 'admin'
        self.interface.current_user = user_info
        
        # Test standard command variations
        standard_queries = [
            "show cars",
            "my bookings",
            "available cars"
        ]
        
        for query in standard_queries:
            response = self.interface.process_command(query)
            self.assertIsInstance(response, str)
            self.assertNotIn("not recognized", response.lower())
            self.assertNotIn("error", response.lower())
            
        # Test natural language variations for car listing
        car_queries = [
            "what cars can I rent today",
            "list all available vehicles"
        ]
        
        for query in car_queries:
            response = self.interface.process_command(query)
            self.assertIsInstance(response, str)
            self.assertTrue(
                any(car['make'].lower() in response.lower() for car in self.test_cars),
                f"Car query '{query}' failed to return car list"
            )
            
        # Test booking queries
        booking_queries = [
            "show me my current bookings",
            "display my reservations"
        ]
        
        # Create a test booking first
        cars = self.car_manager.show_available_cars()
        if cars:
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
            self.booking_manager.create_booking(
                user_info['user_id'],
                cars[0]['id'],
                start_date,
                end_date
            )
        
        for query in booking_queries:
            response = self.interface.process_command(query)
            self.assertIsInstance(response, str)
            self.assertTrue(
                any(text in response.lower() for text in ['booking id', 'status', 'dates']),
                f"Booking query '{query}' failed to return booking info"
            )
    
    def test_07_security_features(self):
        """Test security-related features"""
        # Test SQL injection prevention
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users; --",
            "' OR '1'='1"
        ]
        
        for bad_input in malicious_inputs:
            # Test in login
            success, msg, _ = self.auth_manager.login(bad_input, "password")
            self.assertFalse(success)
              # Test in car listing for SQL injection
            cars = self.interface.process_command(f"show cars {bad_input}")
            self.assertIn("toyota", cars.lower(), "Failed to list cars safely")
            
    def test_08_command_variations(self):
        """Test different command variations"""
        # Test without login first
        variations_no_login = {
            "login": ["login", "log in", "signin", "sign in"],
            "show_cars": ["show cars", "available cars", "list cars", "view cars"]
        }
        for command_type, variants in variations_no_login.items():
            for variant in variants:
                if command_type == "login":
                    response = self.interface.process_command(
                        variant,
                        email=self.test_user['email'],
                        password=self.test_user['password']
                    )
                    self.assertTrue(
                        any(text in response.lower() for text in ["email", "enter", "login", "logged in", "success"]),
                        f"Login command '{variant}' not recognized"
                    )
                else:  # show_cars
                    response = self.interface.process_command(variant)
                    self.assertTrue(
                        any(car['make'] in response for car in self.test_cars),
                        f"Car list not shown for command '{variant}'"
                    )
        # Now test logout variations with login
        success, msg, user_info = self.auth_manager.login(
            self.test_user['email'], 
            self.test_user['password']
        )
        self.assertTrue(success)
        # Set the interface session
        self.interface.session_token = user_info['session_token']
        self.interface.user_id = user_info['user_id']
        self.interface.current_user = user_info
        self.interface.is_admin = user_info['role'] == 'admin'
        # Test logout variations
        logout_variations = ["logout", "log out", "signout", "sign out", "log off"]
        for variant in logout_variations:
            response = self.interface.process_command(variant)
            if variant == logout_variations[0]:  # Only test first logout
                self.assertIn("logged out", response.lower())
                self.assertIsNone(self.interface.session_token)
                break
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test resources"""
        try:
            # Close any open connections
            with cls.db_manager.get_connection() as conn:
                conn.execute("SELECT 1")  # Ensure connection is working
                
            # Remove the test database file
            if os.path.exists(cls.test_db):
                os.remove(cls.test_db)
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
            # Still try to remove the file
            try:
                if os.path.exists(cls.test_db):
                    os.remove(cls.test_db)
            except:
                pass

if __name__ == '__main__':
    unittest.main(verbosity=2)
