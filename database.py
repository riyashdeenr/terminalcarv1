import sqlite3
from contextlib import contextmanager
import hashlib
import secrets
import base64
import re
import sqlite3
import hashlib
import secrets
import base64
import json
import re
import time
import os

class DatabaseManager:
    """Database operations and management"""
    
    def __init__(self, db_path: str = "car_rental.db"):
        self.db_path = db_path
        self.init_database()
    
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
            # Users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            """)
            
            # User identity table (separated for security)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_identity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    national_id_encrypted TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Cars table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    make TEXT NOT NULL,
                    model TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    license_plate TEXT UNIQUE NOT NULL,
                    daily_rate REAL NOT NULL,
                    capacity INTEGER NOT NULL,
                    fuel_type TEXT NOT NULL,
                    transmission TEXT NOT NULL,
                    is_available BOOLEAN DEFAULT 1,
                    is_maintenance BOOLEAN DEFAULT 0,
                    image_base64 TEXT,
                    image_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Bookings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    car_id INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    total_amount REAL NOT NULL,
                    status TEXT DEFAULT 'active',
                    terms_accepted_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (car_id) REFERENCES cars (id)
                )
            """)
            
            # Sessions table
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
            
            # Audit log table
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
        """Insert sample data for testing"""
        with self.get_connection() as conn:
            # Sample cars with base64 placeholder images
            sample_image = base64.b64encode(b"sample_car_image_data").decode()
            image_hash = hashlib.sha256(b"sample_car_image_data").hexdigest()
            
            cars_data = [
                ('Toyota', 'Camry', 2022, 'ABC123', 50.0, 5, 'Gasoline', 'Automatic', sample_image, image_hash),
                ('Honda', 'Civic', 2021, 'DEF456', 45.0, 5, 'Gasoline', 'Manual', sample_image, image_hash),
                ('BMW', 'X5', 2023, 'GHI789', 120.0, 7, 'Gasoline', 'Automatic', sample_image, image_hash),
                ('Tesla', 'Model 3', 2022, 'JKL012', 80.0, 5, 'Electric', 'Automatic', sample_image, image_hash),
            ]
            
            for car in cars_data:
                try:
                    conn.execute("""
                        INSERT INTO cars (make, model, year, license_plate, daily_rate, 
                                        capacity, fuel_type, transmission, image_base64, image_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, car)
                except sqlite3.IntegrityError:
                    pass  # Car already exists
            
            conn.commit()
