#!/usr/bin/env python3
"""
Secure Car Rental Management System
Educational Implementation with AI Integration
"""

import sqlite3
import hashlib
import secrets
import base64
import json
import re
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import quote, unquote
import threading
from contextlib import contextmanager

# Minimal web server implementation
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs

# Importing components
from database import DatabaseManager   
from auth import AuthenticationManager
from car_manager import CarManager
from booking_manager import BookingManager
from gemini import GeminiIntegration   
from web import WebInterface
from security import SecurityUtils



class CarRentalApp:
    """Main application class"""
    
    def __init__(self):
        # Initialize components
        self.db = DatabaseManager()
        self.auth = AuthenticationManager(self.db)
        self.car_manager = CarManager(self.db)
        self.booking_manager = BookingManager(self.db)
        self.gemini = GeminiIntegration(self.car_manager, self.booking_manager)
        self.web_interface = WebInterface(self)
        
        # Insert sample data
        self.db.insert_sample_data()
        
        # Create default superuser
        self.create_default_users()
    
    def create_default_users(self):
        """Create default users for testing"""
        # Create superuser
        self.auth.register_user("admin@carental.com", "Admin123!", "000000000", "superuser")
        
        # Create admin
        self.auth.register_user("staff@carental.com", "Staff123!", "111111111", "admin")
        
        # Create regular user
        self.auth.register_user("user@carental.com", "User123!", "222222222", "user")
    
    def run_web_server(self, port=8080):
        """Run the web server"""
        def handler(*args, **kwargs):
            RequestHandler(*args, app=self, **kwargs)
        
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🚗 Car Rental System running on http://localhost:{port}")
            print(f"📋 Default accounts:")
            print(f"   Superuser: admin@carental.com / Admin123!")
            print(f"   Admin: staff@carental.com / Staff123!")
            print(f"   User: user@carental.com / User123!")
            print(f"🤖 AI Assistant ready for customer service")
            httpd.serve_forever()

def save_encrypted_terms():
    """Save encrypted terms and conditions file"""
    terms_content = """
    SECURE CAR RENTAL TERMS AND CONDITIONS
    
    1. RENTAL AGREEMENT
    This agreement constitutes the entire rental contract between the customer and Secure Car Rental.
    
    2. DRIVER REQUIREMENTS
    - Must be at least 21 years of age
    - Valid driver's license required
    - Clean driving record preferred
    
    3. VEHICLE CONDITION
    - Vehicle must be returned in same condition as received
    - Interior and exterior cleaning required
    - Fuel level must match pickup level
    
    4. SECURITY DEPOSIT
    - Required for all rentals
    - Refunded upon satisfactory vehicle return
    - May be used for damages or violations
    
    5. INSURANCE COVERAGE
    - Basic coverage included
    - Additional coverage available
    - Customer responsible for deductibles
    
    6. PROHIBITED USES
    - No smoking in vehicles
    - No pets without prior approval
    - No off-road driving
    - No racing or competitive events
    
    7. CANCELLATION POLICY
    - 24-hour advance notice required
    - Fees may apply for late cancellations
    - Emergency cancellations considered case-by-case
    
    8. LIABILITY
    - Customer liable for traffic violations
    - Customer liable for parking tickets
    - Customer liable for vehicle damage
    
    9. LATE RETURNS
    - Grace period: 30 minutes
    - Late fees apply after grace period
    - Daily rate charged for overnight delays
    
    10. AGREEMENT ACCEPTANCE
    By booking a vehicle, customer agrees to all terms and conditions herein.
    """
    
    # Encrypt and save
    key = "SecureCarRental2024"
    encrypted_terms = SecurityUtils.encrypt_data(terms_content, key)
    
    with open("terms_conditions.enc", "w") as f:
        f.write(encrypted_terms)
    
    print("✅ Encrypted terms and conditions saved to terms_conditions.enc")

if __name__ == "__main__":
    # Save encrypted terms and conditions
    save_encrypted_terms()
    
    # Start the application
    app = CarRentalApp()
    
    try:
        app.run_web_server(8080)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
