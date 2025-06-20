#!/usr/bin/env python3

from ai_terminal_app import GeminiCarRentalTerminal
import traceback

def test_ai_function_calling():
    """Test AI function calling with debug output."""
    app = GeminiCarRentalTerminal()
    app.current_user = 'testuser'
    
    print("=== Testing AI Function Calling Debug ===")
    
    # Test inputs
    test_inputs = [
        "book 19",
        "book car 1 for 3 days starting 2024-02-01",
        "show stats"
    ]
    
    for user_input in test_inputs:
        print(f"\n--- Testing: '{user_input}' ---")
        
        try:
            # Manually test the AI function calling part
            if not app.client:
                print("❌ No AI client available")
                continue
                
            # Create the system prompt for the AI
            system_prompt = """
You are an AI assistant for a car rental system. You have access to various functions to help users.

Key guidelines:
- ALWAYS call the appropriate function for user requests, even if information is missing
- For booking requests, ALWAYS call 'create_booking' even with partial info - the system will guide the user
- For cancellation requests, ALWAYS call 'cancel_booking' even if booking ID is missing
- For admin requests (revenue, assets, etc.), check if user is admin and call appropriate functions
- Be helpful and conversational while ensuring accurate function calls

Available functions will be automatically provided to you.
"""
            
            # Create function calling messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Create function definitions for Gemini
            functions = app._define_functions()
            print(f"Functions available: {len(functions)}")
            
            # Format tools for the newer API
            tools = []
            function_declarations = []
            for func_name, func_def in functions.items():
                function_declaration = {
                    "name": func_name,
                    "description": func_def["description"],
                    "parameters": {
                        "type": "object",
                        "properties": func_def.get("parameters", {}),
                        "required": []  # Make all parameters optional
                    }
                }
                function_declarations.append(function_declaration)
            
            if function_declarations:
                from ai_interface_advance import types
                tools = [types.Tool(function_declarations=function_declarations)]
                print(f"Tools created: {len(tools)}")
            
            # Generate response with function calling
            print("Calling Gemini API...")
            response = app.client.models.generate_content(
                model=app.model_name,
                contents=messages,
                tools=tools if tools else None
            )
            
            print(f"Response received: {bool(response)}")
            print(f"Response candidates: {len(response.candidates) if response.candidates else 0}")
            
            # Handle function calls
            if hasattr(response.candidates[0].content, 'parts'):
                print(f"Response parts: {len(response.candidates[0].content.parts)}")
                for i, part in enumerate(response.candidates[0].content.parts):
                    print(f"Part {i}: has function_call = {hasattr(part, 'function_call')}")
                    if hasattr(part, 'function_call'):
                        function_call = part.function_call
                        function_name = function_call.name
                        function_args = dict(function_call.args) if function_call.args else {}
                        print(f"Function call: {function_name}({function_args})")
                        
                        # Execute the function
                        result = app.call_tool(function_name, function_args)
                        print(f"Function result: {result}")
                        break
                else:
                    print("No function calls found in response")
                    if response.text:
                        print(f"Text response: {response.text}")
            else:
                print("No parts in response content")
            
        except Exception as e:
            print(f"Error in AI function calling: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    test_ai_function_calling()
