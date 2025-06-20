#!/usr/bin/env python3
"""
Check database contents
"""

from database import DatabaseManager

def check_database():
    """Check what's in the database"""
    db = DatabaseManager()
    
    # Connect to database
    import sqlite3
    conn = sqlite3.connect('car_rental.db')
    cursor = conn.cursor()
    
    # Check schema
    print("Database tables:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  Table: {table[0]}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"    Column: {col[1]} ({col[2]})")
        print()
      # Check users with roles
    print("Users in database:")
    cursor.execute("SELECT email, role FROM users")
    users = cursor.fetchall()
    for user in users:
        print(f"  Email: {user[0]}, Role: {user[1]}")
    
    # Check passwords (first few chars of hash)
    print("\nUser credentials (hash preview):")
    cursor.execute("SELECT email, password_hash FROM users WHERE email LIKE '%admin%' OR email LIKE '%abc%'")
    creds = cursor.fetchall()
    for cred in creds:
        print(f"  {cred[0]}: {cred[1][:20]}...")
    
    conn.close()

if __name__ == "__main__":
    check_database()
