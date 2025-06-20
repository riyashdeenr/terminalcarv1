#!/usr/bin/env python3
"""
Check admin credentials in database
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager

def check_admin_users():
    """Check what admin users exist"""
    print("🔍 Checking admin users in database...")
    
    db = DatabaseManager()
    
    try:
        with db.get_connection() as conn:
            result = conn.execute("SELECT email, role FROM users WHERE role = 'admin'").fetchall()
            print("Admin users found:")
            for row in result:
                print(f"  - Email: {row[0]}, Role: {row[1]}")
            
            # Also check all users
            all_users = conn.execute("SELECT email, role FROM users").fetchall()
            print(f"\nAll users ({len(all_users)} total):")
            for row in all_users:
                print(f"  - Email: {row[0]}, Role: {row[1]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_admin_users()
