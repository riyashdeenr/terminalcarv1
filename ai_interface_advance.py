import google.generativeai as genai
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from auth import AuthenticationManager
from database import DatabaseManager
from car_manager import CarManager
from booking_manager import BookingManager
from admin_functions import AdminManager
from security import SecurityUtils
import ssl
import sqlite3
import re
from functools import wraps

# Configure SSL
ssl._create_default_https_context = ssl._create_unverified_context

# Configure Google API key
GOOGLE_API_KEY = "AIzaSyAz5B_lFFSTXJiXFD_RakW6NQACpeJAZsM"  # Replace with your actual API key

class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Remove potentially dangerous characters from strings"""
        if not isinstance(value, str):
            return value
        # Remove SQL injection patterns
        patterns = [
            r'--',           # SQL comments
            r';',            # Statement terminators
            r'\/\*|\*\/',    # Multi-line comments
            r'xp_',          # SQL Server stored procedures
            r'UNION',        # SQL UNION attacks
            r'DROP',         # DROP statements
            r'TRUNCATE',     # TRUNCATE statements
            r'DELETE',       # DELETE statements
            r'INSERT',       # INSERT statements
            r'UPDATE'        # UPDATE statements
        ]
        sanitized = value
        for pattern in patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        return sanitized

    @staticmethod
    def validate_table_name(table: str) -> bool:
        """Validate table names against whitelist"""
        valid_tables = {'users', 'cars', 'bookings', 'sessions', 'audit_log'}
        return table in valid_tables

    @staticmethod
    def validate_field_name(field: str) -> bool:
        """Validate field names against whitelist"""
        valid_fields = {
            'id', 'user_id', 'car_id', 'email', 'role', 'is_active',
            'make', 'model', 'year', 'license_plate', 'is_available',
            'is_maintenance', 'daily_rate', 'category', 'start_date',
            'end_date', 'status', 'total_amount', 'booking_date'
        }
        return field in valid_fields

    @staticmethod
    def validate_operator(operator: str) -> bool:
        """Validate SQL operators against whitelist"""
        valid_operators = {'=', '>', '<', '>=', '<=', 'IN', 'LIKE', 'IS'}
        return operator.upper() in valid_operators

    @staticmethod
    def audit_log(func):
        """Decorator to log sensitive operations"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                result = func(self, *args, **kwargs)
                # Log successful operation
                if hasattr(self, 'db_manager'):
                    with self.db_manager.get_connection() as conn:
                        conn.execute("""
                            INSERT INTO audit_log (user_id, action, details)
                            VALUES (?, ?, ?)
                        """, (
                            getattr(self, 'user_id', None),
                            func.__name__,
                            str(args) if args else None
                        ))
                return result
            except Exception as e:
                # Log failed operation
                if hasattr(self, 'db_manager'):
                    with self.db_manager.get_connection() as conn:
                        conn.execute("""
                            INSERT INTO audit_log (user_id, action, details)
                            VALUES (?, ?, ?)
                        """, (
                            getattr(self, 'user_id', None),
                            f"{func.__name__}_failed",
                            str(e)
                        ))
                raise
        return wrapper

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
        
        # Initialize advanced query processors
        self.query_builder = QueryBuilder(self.db_manager)
        self.nl_processor = NLQueryProcessor(self.model, self.db_manager)

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
    
    def verify_command_access(self, command: str) -> bool:
        """Verify if the current user has access to execute the command"""
        # Commands that don't require login
        public_commands = ["LOGIN", "REGISTER", "SHOW_CARS", "HELP", "EXIT"]
        if command in public_commands:
            return True
            
        # All other commands require login
        if not self.session_token:
            return False
            
        # Admin has access to everything once logged in
        if self.is_admin:
            return True
            
        # Regular user commands
        user_commands = [
            "LOGOUT", "BOOK", "VIEW_BOOKINGS", 
            "CANCEL_BOOKING", "TERMS"
        ]
        return command in user_commands

    def process_command(self, user_input: str) -> str:
        """Process user commands, prioritizing standard commands over NLP"""
        try:
            # Basic input validation
            if not user_input or not isinstance(user_input, str):
                return "Please enter a command. Type 'help' for available commands."
            
            user_input = user_input.strip()
            if not user_input:
                return "Please enter a command. Type 'help' for available commands."            # First try exact command matches
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
                "view users": "ADMIN_USERS",
                "all users": "ADMIN_USERS",
                "all bookings": "VIEW_ALL_BOOKINGS",
                "car status": "ADMIN_CAR_STATUS",
                "view assets": "ADMIN_ASSETS",
                "revenue": "ADMIN_REVENUE"
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
                command = self._get_command_from_input(input_lower)

            # Execute standard command if found
            if command != "UNKNOWN":
                if not self._verify_command_access(command):
                    return "Please login first." if not self.session_token else \
                           "You don't have permission to execute this command."
                return self._execute_standard_command(command)

            # Only allow NLP queries for specific scenarios
            if not self.session_token:
                return "Command not recognized. Type 'help' for available commands."

            # Only process as NLP if it looks like a car or booking query
            allowed_nlp_terms = ['car', 'book', 'rent', 'vehicle', 'available']
            if not any(term in input_lower for term in allowed_nlp_terms):
                return "Command not recognized. Type 'help' for available commands."

            # Process as NLP query with specific scope
            try:
                if 'car' in input_lower or 'available' in input_lower:
                    results = self.get_available_cars()
                elif 'book' in input_lower:
                    results = self.get_user_bookings()
                else:
                    return "Command not recognized. Type 'help' for available commands."

                return self._format_results(results) if results else "No results found."
            except Exception as e:
                return f"Error processing query: {str(e)}"

        except Exception as e:
            return f"Error: {str(e)}"
    
    def _get_command_from_input(self, input_lower: str) -> str:
        """Get standardized command from input"""
        # First, clean and standardize input
        input_lower = input_lower.strip()
        
        # Define command patterns with variations
        command_patterns = {
            "LOGIN": ["login", "sign in", "signin"],
            "LOGOUT": ["logout", "sign out", "signout"],            "SHOW_CARS": [
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
                "check.*booking", "show.*my.*booking"
            ],
            "BOOK": ["^book\\s", "^rent\\s", "^hire\\s", "make.*booking", "create.*booking"],
            "CANCEL_BOOKING": ["cancel booking", "cancel my booking", "delete booking"],
            "HELP": ["help", "commands", "?"],
            "EXIT": ["exit", "quit"]
        }        # Check each command pattern
        for command, patterns in command_patterns.items():
            for pattern in patterns:
                try:
                    # If pattern contains special regex chars (except spaces), treat as regex
                    if any(c in pattern for c in ".*+?^$[](){}|"):
                        if re.search(pattern, input_lower, re.IGNORECASE):
                            print(f"Debug: Matched pattern '{pattern}' for command {command}")  # Debug line
                            return command
                    # Otherwise do exact phrase matching
                    elif pattern in input_lower:
                        # For BOOK command, make sure it's not part of "bookings"
                        if command == "BOOK" and "booking" in input_lower:
                            continue
                        print(f"Debug: Matched exact phrase '{pattern}' for command {command}")  # Debug line
                        return command
                except re.error:
                    # If regex is invalid, try exact match
                    if pattern in input_lower:
                        return command
                
        return "UNKNOWN"

    def _verify_command_access(self, command: str) -> bool:
        """Verify if user has access to execute command"""
        # Commands that don't require login
        if command in ["LOGIN", "HELP", "SHOW_CARS"]:
            return True

        # All other commands require login
        if not self.session_token:
            return False

        # Admin commands
        admin_commands = ["VIEW_ALL_BOOKINGS", "VIEW_ALL_USERS"]
        if command in admin_commands and not self.is_admin:
            return False

        return True

    def _execute_standard_command(self, command: str) -> str:
        """Execute a standard command"""
        try:
            if command == "LOGIN":
                if self.session_token:
                    return "Already logged in."
                email = input("Email: ").strip()
                password = input("Password: ").strip()
                success, msg = self.handle_login(email, password)
                return msg

            elif command == "LOGOUT":
                success, msg = self.handle_logout()
                return msg

            elif command == "SHOW_CARS":
                cars = self.get_available_cars()
                if not cars:
                    return "No cars available."
                
                result = "\nAvailable Cars:\n"
                for car in cars:
                    result += f"Car ID: {car['id']} - {car['make']} {car['model']} - ${car['daily_rate']}/day\n"
                return result

            elif command == "BOOK":
                cars = self.get_available_cars()
                if not cars:
                    return "No cars available for booking."
                
                print("\nAvailable Cars:")
                for car in cars:
                    print(f"Car ID: {car['id']} - {car['make']} {car['model']} - ${car['daily_rate']}/day")
                
                try:
                    car_id = int(input("\nEnter Car ID to book: ").strip())
                    start_date = input("Enter start date (YYYY-MM-DD): ").strip()
                    duration = int(input("Enter rental duration in days: ").strip())
                    
                    success, msg, cost = self.create_booking(car_id, start_date, duration)
                    if success:
                        return f"{msg}\nTotal cost: ${cost:.2f}"
                    return msg
                except ValueError:
                    return "Invalid input. Please enter valid numbers for Car ID and duration."

            elif command == "VIEW_BOOKINGS":
                bookings = self.get_user_bookings()
                if not bookings:
                    return "No bookings found."
                
                result = "\nYour Bookings:\n"
                for booking in bookings:
                    result += f"Booking ID: {booking['id']}\n"
                    result += f"Car: {booking.get('make', 'N/A')} {booking.get('model', 'N/A')}\n"
                    result += f"Status: {booking['status']}\n"
                    result += f"Dates: {booking['start_date']} to {booking['end_date']}\n"
                    result += f"Total Cost: ${booking.get('total_amount', 0):.2f}\n\n"
                return result

            elif command == "CANCEL_BOOKING":
                bookings = self.get_user_bookings()
                if not bookings:
                    return "No bookings found."
                
                print("\nYour Bookings:")
                for booking in bookings:
                    print(f"ID: {booking['id']} - {booking.get('make', 'N/A')} {booking.get('model', 'N/A')}")
                    print(f"Dates: {booking['start_date']} to {booking['end_date']}")
                    print(f"Status: {booking['status']}\n")
                
                try:
                    booking_id = int(input("Enter Booking ID to cancel: ").strip())
                    success, msg = self.cancel_booking(booking_id)
                    return msg
                except ValueError:
                    return "Invalid booking ID."

            elif command == "HELP":
                help_text = "\nAvailable Commands:\n"
                help_text += "- login: Log into your account\n"
                help_text += "- show cars: View available cars\n"
                help_text += "- book: Book a car\n"
                help_text += "- my bookings: View your bookings\n"
                help_text += "- cancel booking: Cancel a booking\n"
                help_text += "- logout: Log out of your account\n"
                help_text += "- help: Show this help message\n"
                
                if self.is_admin:
                    help_text += "\nAdmin Commands:\n"
                    help_text += "- view all bookings: View all bookings\n"
                    help_text += "- view all users: View all users\n"
                return help_text

            return "Command not recognized. Type 'help' for available commands."

        except Exception as e:
            return f"Error executing command: {str(e)}"

    def _process_nlp_query(self, query: str) -> List[Dict]:
        """Process natural language query"""
        # For now, just handle basic queries about cars and bookings
        query_lower = query.lower()
        
        if "car" in query_lower:
            return self.get_available_cars()
        elif "book" in query_lower:
            return self.get_user_bookings()
        
        return []

    def _format_results(self, results: List[Dict]) -> str:
        """Format results into readable string"""
        if not results:
            return "No results found."
            
        # Get all possible keys from results
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
            
        # Create header
        headers = list(all_keys)
        widths = {header: len(header) for header in headers}
        
        # Calculate column widths
        for result in results:
            for header in headers:
                value = str(result.get(header, ''))
                widths[header] = max(widths[header], len(value))
                
        # Create separator line
        separator = '+' + '+'.join('-' * (widths[header] + 2) for header in headers) + '+'
        
        # Create result string
        lines = [separator]
        
        # Add header
        header_line = '|'
        for header in headers:
            header_line += f" {header.ljust(widths[header])} |"
        lines.append(header_line)
        lines.append(separator)
        
        # Add data rows
        for result in results:
            data_line = '|'
            for header in headers:
                value = str(result.get(header, ''))
                data_line += f" {value.ljust(widths[header])} |"
            lines.append(data_line)
            
        lines.append(separator)
        return '\n'.join(lines)

class QueryBuilder:
    def __init__(self, db_manager):
        self.db = db_manager
        
    def execute_dynamic_query(self, table: str, filters: Dict, fields: List[str] = None, joins: List[Dict] = None) -> List[Dict]:
        """Dynamically builds and executes SQL queries based on filters and joins"""
        # Validate table name
        if not SecurityValidator.validate_table_name(table):
            raise ValueError(f"Invalid table name: {table}")
        
        # Validate and sanitize fields
        if fields:
            for field in fields:
                if not SecurityValidator.validate_field_name(field):
                    raise ValueError(f"Invalid field name: {field}")
        fields_str = ", ".join(fields) if fields else "*"
        
        query = f"SELECT {fields_str} FROM {table}"
        params = []
        
        # Validate and process joins
        if joins:
            for join in joins:
                if not SecurityValidator.validate_table_name(join['table']):
                    raise ValueError(f"Invalid join table: {join['table']}")
                if not join['type'].upper() in {'LEFT', 'RIGHT', 'INNER', 'OUTER'}:
                    raise ValueError(f"Invalid join type: {join['type']}")
                # Validate join condition
                if not all(SecurityValidator.validate_field_name(f.strip()) 
                          for f in re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)', join['condition'])):
                    raise ValueError(f"Invalid join condition: {join['condition']}")
                query += f" {join['type']} JOIN {join['table']} ON {join['condition']}"
        
        # Process filters with validation
        if filters:
            conditions = []
            for k, v in filters.items():
                # Validate field name
                if not SecurityValidator.validate_field_name(k):
                    raise ValueError(f"Invalid filter field: {k}")
                
                if isinstance(v, (list, tuple)):
                    # Validate each value in the list
                    sanitized_values = [SecurityValidator.sanitize_string(val) if isinstance(val, str) else val for val in v]
                    conditions.append(f"{k} IN ({','.join(['?' for _ in sanitized_values])})")
                    params.extend(sanitized_values)
                else:
                    # Sanitize single value
                    sanitized_value = SecurityValidator.sanitize_string(v) if isinstance(v, str) else v
                    conditions.append(f"{k} = ?")
                    params.append(sanitized_value)
            
            query += " WHERE " + " AND ".join(conditions)
        
        # Execute query with parameters
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                results = cursor.execute(query, params).fetchall()
                return [dict(row) for row in results]
            except sqlite3.Error as e:
                raise Exception(f"Database error: {str(e)}")
            except Exception as e:
                raise Exception(f"Error executing query: {str(e)}")

class NLQueryProcessor:
    def __init__(self, model, db_manager):
        self.model = model
        self.db = db_manager
        
    def validate_generated_sql(self, sql: str) -> bool:
        """Validate AI-generated SQL for security"""
        sql_lower = sql.lower()
        
        # Check for dangerous operations
        dangerous_operations = [
            'drop', 'truncate', 'delete', 'update', 'insert',
            'alter', 'create', 'grant', 'revoke', 'exec',
            'execute', 'xp_', 'sp_'
        ]
        if any(op in sql_lower for op in dangerous_operations):
            return False
            
        # Ensure it's a SELECT statement
        if not sql_lower.strip().startswith('select'):
            return False
            
        # Validate table names in FROM and JOIN clauses
        tables = re.findall(r'from\s+(\w+)|join\s+(\w+)', sql_lower)
        for table_match in tables:
            table = next(t for t in table_match if t)  # Get non-empty group
            if not SecurityValidator.validate_table_name(table):
                return False
                
        # Validate field names
        fields = re.findall(r'select\s+(.+?)\s+from', sql_lower)[0].split(',')
        for field in fields:
            field = field.strip()
            if field != '*':
                if not SecurityValidator.validate_field_name(field):
                    return False
                    
        return True
        
    @SecurityValidator.audit_log
    def process_query(self, user_query: str) -> List[Dict]:
        """Convert natural language to SQL using AI with security measures"""
        system_prompt = """
        You are a SQL query generator for a car rental system. Generate only SELECT queries.
        The database schema is:
        
        bookings (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            car_id INTEGER,
            start_date TEXT,
            end_date TEXT,
            booking_date TIMESTAMP,
            terms_accepted BOOLEAN,
            status TEXT,
            total_amount REAL
        )
        
        cars (
            id INTEGER PRIMARY KEY,
            make TEXT,
            model TEXT,
            year INTEGER,
            license_plate TEXT,
            is_available BOOLEAN,
            is_maintenance BOOLEAN,
            daily_rate REAL,
            category TEXT
        )
        
        users (
            id INTEGER PRIMARY KEY,
            email TEXT,
            role TEXT,
            is_active BOOLEAN
        )
        
        Rules:
        1. Only generate SELECT queries
        2. No data modification queries (INSERT, UPDATE, DELETE, etc.)
        3. Use parameterized queries when possible
        4. Only use allowed table and field names
        5. Always include meaningful JOINs when needed
        """
        
        # Sanitize user input
        sanitized_query = SecurityValidator.sanitize_string(user_query)
        
        # Generate SQL using AI
        response = self.model.generate_content(f"{system_prompt}\nQuery: {sanitized_query}")
        sql_query = response.text.strip()
        
        # Validate generated SQL
        if not self.validate_generated_sql(sql_query):
            raise Exception("Generated SQL query failed security validation")
        
        # Execute query with safety measures
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                results = cursor.execute(sql_query).fetchall()
                return [dict(row) for row in results]
            except sqlite3.Error as e:
                raise Exception(f"Database error: {str(e)}")
            except Exception as e:
                raise Exception(f"Error executing query: {str(e)}")


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