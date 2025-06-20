#!/usr/bin/env python3
"""
Test script to verify Gemini AI login functionality
"""

from ai_terminal_app import GeminiCarRentalTerminal

def test_ai_login():
    """Test AI-powered login functionality"""
    print("Testing AI-powered login functionality...")
    
    # Initialize the app
    app = GeminiCarRentalTerminal()
    
    # Test various login phrases that should trigger the login function
    test_queries = [
        "login with email admin@carental.com and password Admin@2025",
        "I want to login with admin@carental.com password Admin@2025",
        "sign in using admin@carental.com and Admin@2025",
        "log me in: admin@carental.com / Admin@2025"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {query}")
        print('='*60)
        
        # Reset session before each test
        app.current_user = None
        app.is_admin = False
        app.session_token = None
        
        # Process the query with AI
        result = app.process_user_input(query)
        print(f"AI Response: {result}")
        
        # Check if login was successful
        if app.current_user:
            print(f"✅ Login successful! User: {app.current_user.get('email')}, Admin: {app.is_admin}")
        else:
            print("❌ Login failed - session not set")
        
        print(f"Session state: current_user={bool(app.current_user)}, is_admin={app.is_admin}")

if __name__ == "__main__":
    test_ai_login()
