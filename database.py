import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from security import SecurityUtils

class DatabaseManager:
    """Database operations and management"""
    
    def __init__(self, db_path: str = "car_rental.db"):
        self.db_path = db_path
        self.init_database()
        self.insert_sample_data()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            # Create users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    national_id TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            """)

            # Create cars table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    make TEXT NOT NULL,
                    model TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    license_plate TEXT UNIQUE NOT NULL,
                    is_available BOOLEAN DEFAULT 1,
                    daily_rate REAL NOT NULL,
                    category TEXT NOT NULL,
                    purchase_date DATE,
                    purchase_price REAL,
                    road_tax_expiry DATE,
                    road_tax_amount REAL,
                    insurance_expiry DATE,
                    insurance_provider TEXT,
                    insurance_policy_number TEXT,
                    insurance_amount REAL,
                    last_maintenance_date DATE,
                    next_maintenance_date DATE,
                    total_maintenance_cost REAL DEFAULT 0,
                    mileage INTEGER DEFAULT 0
                )
            """)

            # Create bookings table
            conn.execute("""                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    car_id INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    terms_accepted BOOLEAN DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    total_amount REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (car_id) REFERENCES cars (id)
                )
            """)

            # Create sessions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            # Create audit_log table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            conn.commit()

    def insert_sample_data(self):
        """Insert sample data including luxury to economy cars and bookings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if data already exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cursor.fetchone()[0] > 0:
                print("Sample data already exists.")
                return

            print("\nInitializing database with sample data...")

            # Create admin user first with known credentials
            admin_email = "admin@carental.com"
            admin_password = "Admin@2025"  # Strong password pattern
            admin_national_id = "ADMIN001"
            password_hash, salt = SecurityUtils.hash_password(admin_password)
            encrypted_national_id = SecurityUtils.encrypt_data(admin_national_id, admin_password)
            
            cursor.execute("""
                INSERT INTO users (email, password_hash, password_salt, national_id, role)
                VALUES (?, ?, ?, ?, ?)
            """, (admin_email, password_hash, salt, encrypted_national_id, 'admin'))

            print("\n=== Admin Credentials ===")
            print("Email:", admin_email)
            print("Password:", admin_password)
            print("======================\n")

            # Sample cars data with realistic models and pricing
            cars_data = [
                # Luxury cars
                ("Mercedes-Benz", "S-Class", 2025, "MB001", 200.00, "luxury"),
                ("Mercedes-Benz", "E-Class", 2024, "MB002", 150.00, "luxury"),
                ("BMW", "7 Series", 2025, "BMW001", 190.00, "luxury"),
                ("BMW", "5 Series", 2024, "BMW002", 140.00, "luxury"),
                ("Audi", "A8", 2025, "AUD001", 180.00, "luxury"),
                
                # Mid-range cars
                ("Volkswagen", "Passat", 2024, "VW001", 90.00, "mid-range"),
                ("Honda", "Accord", 2024, "HON001", 85.00, "mid-range"),
                ("Toyota", "Camry", 2024, "TOY001", 80.00, "mid-range"),
                ("Hyundai", "Sonata", 2024, "HYU001", 75.00, "mid-range"),
                ("Mazda", "6", 2024, "MAZ001", 78.00, "mid-range"),
                
                # Economy cars
                ("Toyota", "Corolla", 2024, "TOY002", 65.00, "economy"),
                ("Honda", "Civic", 2024, "HON002", 65.00, "economy"),
                ("Volkswagen", "Golf", 2024, "VW002", 68.00, "economy"),
                ("Hyundai", "Elantra", 2024, "HYU002", 60.00, "economy"),
                ("Kia", "Forte", 2024, "KIA001", 58.00, "economy"),
                
                # SUVs
                ("Toyota", "RAV4", 2024, "TOY003", 95.00, "suv"),
                ("Honda", "CR-V", 2024, "HON003", 95.00, "suv"),
                ("Mazda", "CX-5", 2024, "MAZ002", 92.00, "suv"),
                ("Hyundai", "Tucson", 2024, "HYU003", 88.00, "suv"),
                ("Kia", "Sportage", 2024, "KIA002", 85.00, "suv")
            ]

            # Insert cars
            cursor.executemany("""
                INSERT INTO cars (make, model, year, license_plate, daily_rate, category)
                VALUES (?, ?, ?, ?, ?, ?)
            """, cars_data)

            # Sample users with hashed passwords
            users_data = []
            for i in range(1, 11):
                email = f"user{i}@example.com"
                password = f"Password{i}@2025"  # Strong password pattern
                national_id = f"ID{i:08d}"
                password_hash, salt = SecurityUtils.hash_password(password)
                encrypted_national_id = SecurityUtils.encrypt_data(national_id, password)
                users_data.append((
                    email,
                    password_hash,
                    salt,
                    encrypted_national_id,
                    'user'
                ))

            # Insert users
            cursor.executemany("""
                INSERT INTO users (email, password_hash, password_salt, national_id, role)
                VALUES (?, ?, ?, ?, ?)
            """, users_data)

            # Create bookings for each user
            current_date = datetime.now()
            for user_id in range(1, 11):
                # Random start date within next 7 days
                start_date = (current_date + timedelta(days=user_id)).strftime('%Y-%m-%d')
                # Booking duration of 1-2 weeks
                end_date = (current_date + timedelta(days=user_id + 7 + (user_id % 7))).strftime('%Y-%m-%d')
                
                # Assign different cars to different users
                car_id = user_id  # This will distribute bookings across different cars
                
                cursor.execute("""
                    INSERT INTO bookings (user_id, car_id, start_date, end_date)
                    VALUES (?, ?, ?, ?)
                """, (user_id, car_id, start_date, end_date))
                
                # Update car availability
                cursor.execute("""
                    UPDATE cars SET is_available = 0
                    WHERE id = ?
                """, (car_id,))

            conn.commit()
            print("Inserted sample data: 20 cars, 10 users, and 10 bookings")
