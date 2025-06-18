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
            conn.execute("""                CREATE TABLE IF NOT EXISTS cars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    make TEXT NOT NULL,
                    model TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    license_plate TEXT UNIQUE NOT NULL,
                    is_available BOOLEAN DEFAULT 1,
                    is_maintenance BOOLEAN DEFAULT 0,
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
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] > 0:
                print("\nDatabase already contains data. Skipping initialization.")
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
            current_date = datetime.now()
            cars_data = [
                # Existing luxury cars
                ("Mercedes-Benz", "S-Class", 2025, "MB001", 200.00, "luxury", 
                 current_date.strftime('%Y-%m-%d'), 120000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 2000.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "LuxInsure", "LUX001", 5000.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 1500.00, 5000),
                ("Mercedes-Benz", "E-Class", 2024, "MB002", 150.00, "luxury", 
                 current_date.strftime('%Y-%m-%d'), 90000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 1800.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "LuxInsure", "LUX002", 4000.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 1200.00, 8000),
                ("BMW", "7 Series", 2025, "BMW001", 190.00, "luxury", 
                 current_date.strftime('%Y-%m-%d'), 110000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 1900.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "LuxInsure", "LUX003", 4800.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 1400.00, 3000),
                # Additional luxury cars
                ("BMW", "X7", 2025, "BMW002", 180.00, "luxury", 
                 current_date.strftime('%Y-%m-%d'), 95000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 1800.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "LuxInsure", "LUX004", 4500.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 1300.00, 7000),
                ("Audi", "A8", 2025, "AUD001", 185.00, "luxury", 
                 current_date.strftime('%Y-%m-%d'), 98000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 1850.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "LuxInsure", "LUX005", 4600.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 1350.00, 6000),
                ("Lexus", "LS", 2025, "LEX001", 175.00, "luxury", 
                 current_date.strftime('%Y-%m-%d'), 92000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 1750.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "LuxInsure", "LUX006", 4400.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 1250.00, 4000),
                # Existing mid-range cars
                ("Volkswagen", "Passat", 2024, "VW001", 90.00, "mid-range", 
                 current_date.strftime('%Y-%m-%d'), 45000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 1200.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "MidInsure", "MID001", 2500.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 800.00, 12000),
                ("Toyota", "Camry", 2024, "TOY001", 80.00, "mid-range", 
                 current_date.strftime('%Y-%m-%d'), 40000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 1100.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "MidInsure", "MID002", 2200.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 700.00, 15000),
                # Additional mid-range cars
                ("Honda", "Accord", 2024, "HON001", 85.00, "mid-range", 
                 current_date.strftime('%Y-%m-%d'), 42000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 1150.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "MidInsure", "MID003", 2300.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 750.00, 13000),
                ("Mazda", "6", 2024, "MAZ001", 82.00, "mid-range", 
                 current_date.strftime('%Y-%m-%d'), 41000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 1120.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "MidInsure", "MID004", 2250.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 725.00, 14000),
                ("Hyundai", "Sonata", 2024, "HYU001", 78.00, "mid-range", 
                 current_date.strftime('%Y-%m-%d'), 38000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 1050.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "MidInsure", "MID005", 2150.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 675.00, 16000),
                ("Kia", "K5", 2024, "KIA001", 77.00, "mid-range", 
                 current_date.strftime('%Y-%m-%d'), 37000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 1030.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "MidInsure", "MID006", 2100.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 650.00, 17000),
                # Existing economy cars
                ("Toyota", "Corolla", 2024, "TOY002", 65.00, "economy", 
                 current_date.strftime('%Y-%m-%d'), 30000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 900.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "EcoInsure", "ECO001", 1800.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 500.00, 20000),
                ("Honda", "Civic", 2024, "HON002", 65.00, "economy", 
                 current_date.strftime('%Y-%m-%d'), 28000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 850.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "EcoInsure", "ECO002", 1700.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 450.00, 18000),
                # Additional economy cars
                ("Hyundai", "Elantra", 2024, "HYU002", 62.00, "economy", 
                 current_date.strftime('%Y-%m-%d'), 27000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 830.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "EcoInsure", "ECO003", 1650.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 425.00, 19000),
                ("Nissan", "Sentra", 2024, "NIS001", 61.00, "economy", 
                 current_date.strftime('%Y-%m-%d'), 26500.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 820.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "EcoInsure", "ECO004", 1600.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 400.00, 21000),
                ("Mazda", "3", 2024, "MAZ002", 63.00, "economy", 
                 current_date.strftime('%Y-%m-%d'), 27500.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 840.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "EcoInsure", "ECO005", 1675.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 435.00, 17500),
                ("Kia", "Forte", 2024, "KIA002", 60.00, "economy", 
                 current_date.strftime('%Y-%m-%d'), 26000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 810.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "EcoInsure", "ECO006", 1550.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 390.00, 22000),
                ("Volkswagen", "Jetta", 2024, "VW002", 64.00, "economy", 
                 current_date.strftime('%Y-%m-%d'), 28000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 860.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "EcoInsure", "ECO007", 1700.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 445.00, 16500),
                ("Toyota", "Yaris", 2024, "TOY003", 58.00, "economy", 
                 current_date.strftime('%Y-%m-%d'), 25000.00,
                 (current_date + timedelta(days=365)).strftime('%Y-%m-%d'), 800.00,
                 (current_date + timedelta(days=180)).strftime('%Y-%m-%d'), "EcoInsure", "ECO008", 1500.00,
                 current_date.strftime('%Y-%m-%d'), (current_date + timedelta(days=90)).strftime('%Y-%m-%d'),
                 380.00, 23000)
            ]

            # Insert cars with extended data
            cursor.executemany("""
                INSERT INTO cars (
                    make, model, year, license_plate, daily_rate, category,
                    purchase_date, purchase_price, road_tax_expiry, road_tax_amount,
                    insurance_expiry, insurance_provider, insurance_policy_number, insurance_amount,
                    last_maintenance_date, next_maintenance_date, total_maintenance_cost, mileage
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, cars_data)

            # Create sample users
            users_data = []
            for i in range(1, 11):
                email = f"user{i}@example.com"
                password = f"User{i}@2024"  # Strong password pattern
                national_id = f"ID{i:05d}"
                password_hash, salt = SecurityUtils.hash_password(password)
                encrypted_national_id = SecurityUtils.encrypt_data(national_id, password)
                users_data.append((email, password_hash, salt, encrypted_national_id, 'user'))
                print(f"Created user {i}: {email} with password: {password}")

            # Insert users
            cursor.executemany("""
                INSERT INTO users (email, password_hash, password_salt, national_id, role)
                VALUES (?, ?, ?, ?, ?)
            """, users_data)

            # Create sample bookings
            today = datetime.now()
            booking_data = []
            
            # Create 10 bookings with different statuses and dates
            for i in range(1, 11):
                user_id = i + 1  # Skip admin user (id 1)
                car_id = i  # Each user books a different car
                
                # Past completed booking
                start_date = (today - timedelta(days=30+i)).strftime('%Y-%m-%d')
                end_date = (today - timedelta(days=25+i)).strftime('%Y-%m-%d')
                amount = cars_data[i-1][4] * 5  # 5 days rental
                booking_data.append((user_id, car_id, start_date, end_date, 'completed', amount))
                
                # Current active booking
                if i <= 5:  # Only some cars have active bookings
                    start_date = (today - timedelta(days=2)).strftime('%Y-%m-%d')
                    end_date = (today + timedelta(days=3)).strftime('%Y-%m-%d')
                    amount = cars_data[i-1][4] * 5
                    booking_data.append((user_id, car_id+10, start_date, end_date, 'active', amount))
                
                # Future pending booking
                if i <= 3:  # Only some cars have pending bookings
                    start_date = (today + timedelta(days=10)).strftime('%Y-%m-%d')
                    end_date = (today + timedelta(days=15)).strftime('%Y-%m-%d')
                    amount = cars_data[i-1][4] * 5
                    booking_data.append((user_id, car_id+15, start_date, end_date, 'pending', amount))

            # Insert bookings
            cursor.executemany("""
                INSERT INTO bookings (user_id, car_id, start_date, end_date, status, total_amount)
                VALUES (?, ?, ?, ?, ?, ?)
            """, booking_data)

            conn.commit()
            print("\nSample data initialization completed successfully!")
