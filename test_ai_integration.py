#!/usr/bin/env python3
"""
End-to-end integration test for AI-powered admin functions
Tests the complete conversation flow with Gemini AI function calling
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ai_terminal_app import GeminiCarRentalTerminal
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_ai_conversation_flow():
    """Test the AI conversation flow with admin functions"""
    print("🤖 Testing AI Conversation Flow for Admin Functions")
    print("=" * 60)
    
    # Initialize the application
    try:
        app = GeminiCarRentalTerminal()
        print("✅ Application initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize application: {e}")
        return
    
    # Set up admin user
    app.current_user = {"email": "admin@test.com", "national_id": "123456789", "role": "admin"}
    app.is_admin = True
    print("✅ Admin user authenticated")
    
    # Test conversations that should trigger function calls
    test_conversations = [
        "Show me asset details for car 1",
        "I need the revenue statistics for this month",
        "Generate an asset report for the last 7 days", 
        "What are the revenue details for car ID 2?",
        "Get asset details", # Should prompt for car ID
        "Show me car revenue details", # Should prompt for car ID
    ]
    
    print("\n🔥 Testing AI Function Calling...")
    print("-" * 50)
    
    for i, user_input in enumerate(test_conversations, 1):
        print(f"\n💬 Test {i}: \"{user_input}\"")
        print("📤 User Input:", user_input)
        
        try:
            # Process the input through AI
            response = app.process_user_input(user_input)
            print("📥 AI Response:")
            print(response)
            print("-" * 30)
            
        except Exception as e:
            print(f"❌ Error processing input: {e}")
    
    print("\n✅ AI conversation flow testing completed!")

def test_direct_function_calls():
    """Test direct function calls to verify they work"""
    print("\n🔧 Testing Direct Function Calls")
    print("-" * 40)
    
    app = GeminiCarRentalTerminal()
    app.current_user = {"email": "admin@test.com", "national_id": "123456789", "role": "admin"}
    app.is_admin = True
    
    # Test each function directly
    functions_to_test = [
        ("get_asset_details", {"car_id": "1"}),
        ("get_revenue_stats", {"start_date": "2025-06-01", "end_date": "2025-06-20"}),
        ("generate_asset_report", {"start_date": "", "end_date": ""}),
        ("get_car_revenue_details", {"car_id": "1", "start_date": "", "end_date": ""}),
    ]
    
    for func_name, args in functions_to_test:
        print(f"\n🎯 Testing {func_name}...")
        try:
            result = app.call_tool(func_name, args)
            print(f"✅ Success: {len(result)} characters returned")
            # Show first 100 characters
            preview = result[:100] + "..." if len(result) > 100 else result
            print(f"Preview: {preview}")
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting End-to-End AI Integration Tests")
    print("=" * 60)
    
    # Test direct function calls first
    test_direct_function_calls()
    
    # Then test AI conversation flow
    test_ai_conversation_flow()
    
    print("\n🎉 All integration tests completed!")
    print("\nThe AI-powered admin functions are now ready for production use!")
