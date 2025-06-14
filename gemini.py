
from car_manager import CarManager
from booking_manager import BookingManager



client = genai.Client(api_key="AIzaSyAz5B_lFFSTXJiXFD_RakW6NQACpeJAZsM")
#API_URL = "https://api.google.com/gemini"  # Replace with the actual Google Gemini API endpoint
#API_KEY = "AIzaSyAz5B_lFFSTXJiXFD_RakW6NQACpeJAZsM"  # Replace with your actual API key

def get_ai_response(user_query):
   # headers = {
    #    "Authorization": f"Bearer {API_KEY}",
    #    "Content-Type": "application/json" 
   # }
    
   # payload = {
   #     "query": user_query
    #}
    
    #response = requests.post(API_URL, json=payload, headers=headers)
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=user_query,)

    print(response.text)
    if response.ok:
        #return response.json()  # Assuming the response contains the AI's answer and possibly an image URL
        return response.text  # Assuming the response contains the AI's answer and possibly an image URL
    else:
        

class GeminiIntegration:
    """Integration with Gemini AI for sales assistance"""
    
    def __init__(self, car_manager: CarManager, booking_manager: BookingManager):
        self.car_manager = car_manager
        self.booking_manager = booking_manager
        self.conversation_history = {}
    
    def get_available_functions(self) -> Dict[str, Dict]:
        """Define available functions for Gemini"""
        return {
            "search_cars": {
                "description": "Search for available cars based on criteria",
                "parameters": {
                    "start_date": "Start date for rental (YYYY-MM-DD)",
                    "end_date": "End date for rental (YYYY-MM-DD)",
                    "car_type": "Type of car (optional)"
                }
            },
            "get_car_details": {
                "description": "Get detailed information about a specific car",
                "parameters": {
                    "car_id": "ID of the car to get details for"
                }
            },
            "calculate_rental_cost": {
                "description": "Calculate rental cost for a car and date range",
                "parameters": {
                    "car_id": "ID of the car",
                    "start_date": "Start date (YYYY-MM-DD)",
                    "end_date": "End date (YYYY-MM-DD)"
                }
            },
            "get_terms_conditions": {
                "description": "Get rental terms and conditions",
                "parameters": {}
            }
        }
    
    def execute_function(self, function_name: str, parameters: Dict) -> Dict:
        """Execute a function call from Gemini"""
        try:
            if function_name == "search_cars":
                cars = self.car_manager.get_available_cars(
                    parameters.get('start_date'),
                    parameters.get('end_date')
                )
                # Remove sensitive data like image_base64
                cleaned_cars = []
                for car in cars:
                    clean_car = {k: v for k, v in car.items() if k != 'image_base64'}
                    cleaned_cars.append(clean_car)
                return {"success": True, "data": cleaned_cars}
            
            elif function_name == "get_car_details":
                car = self.car_manager.get_car_by_id(parameters['car_id'])
                if car:
                    # Remove sensitive data
                    clean_car = {k: v for k, v in car.items() if k != 'image_base64'}
                    return {"success": True, "data": clean_car}
                return {"success": False, "error": "Car not found"}
            
            elif function_name == "calculate_rental_cost":
                car = self.car_manager.get_car_by_id(parameters['car_id'])
                if car:
                    start_dt = datetime.strptime(parameters['start_date'], '%Y-%m-%d')
                    end_dt = datetime.strptime(parameters['end_date'], '%Y-%m-%d')
                    days = (end_dt - start_dt).days + 1
                    total_cost = days * car['daily_rate']
                    return {
                        "success": True, 
                        "data": {
                            "daily_rate": car['daily_rate'],
                            "days": days,
                            "total_cost": total_cost
                        }
                    }
                return {"success": False, "error": "Car not found"}
            
            elif function_name == "get_terms_conditions":
                terms = self.booking_manager.get_terms_and_conditions()
                return {"success": True, "data": terms}
            
            return {"success": False, "error": "Unknown function"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def simulate_ai_response(self, user_message: str, session_id: str) -> str:
        """Simulate AI response (placeholder for actual Gemini integration)"""
        # In a real implementation, this would call Gemini API
        # This is a simplified simulation for demonstration
        
        user_message = user_message.lower()
        
        if "available cars" in user_message or "show cars" in user_message:
            cars = self.car_manager.get_available_cars()
            if cars:
                response = "Here are our available cars:\n\n"
                for car in cars[:3]:  # Show first 3 cars
                    response += f"• {car['year']} {car['make']} {car['model']} - ${car['daily_rate']}/day\n"
                response += "\nWould you like more details about any of these vehicles?"
            else:
                response = "I'm sorry, we don't have any cars available at the moment."
        
        elif "luxury" in user_message or "premium" in user_message:
            response = "For luxury options, I'd recommend our BMW X5 or similar premium vehicles. They feature advanced comfort and performance. Would you like to see availability for specific dates?"
        
        elif "cheap" in user_message or "budget" in user_message or "affordable" in user_message:
            response = "For budget-friendly options, check out our Honda Civic or Toyota Camry. They offer great value at $45-50 per day. Would you like to make a reservation?"
        
        elif "terms" in user_message or "conditions" in user_message:
            response = "Our rental terms include: 21+ age requirement, valid license, security deposit, and 24-hour cancellation policy. Would you like me to show you the complete terms and conditions?"
        
        elif "book" in user_message or "reserve" in user_message:
            response = "I'd be happy to help you book a car! Please log in to your account and let me know:\n1. Which car you're interested in\n2. Your preferred dates\n3. Any special requirements"
        
        else:
            response = "Welcome to our car rental service! I can help you:\n• Find available cars\n• Check pricing and details\n• Explain rental terms\n• Guide you through booking\n\nWhat would you like to know?"
        
        return response
