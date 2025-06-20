 def process_command(self, user_input: str, **kwargs) -> str:
        """Process user commands, prioritizing standard commands over NLP
        
        For interactive mode, leave kwargs empty.
        For non-interactive mode, provide required params in kwargs:
        - LOGIN: email, password
        - BOOK: car_id, start_date, duration
        - CANCEL_BOOKING: booking_id
        """
        # Basic input validation
        if not user_input or not isinstance(user_input, str):
            return "Please enter a command. Type 'help' for available commands."
        
        # Sanitize user input for security
        user_input = SecurityValidator.sanitize_string(user_input.strip())
        if not user_input:
            return "Please enter a command. Type 'help' for available commands."
        
        # i am commenting this out to avoid logging sensitive information
        # Uncomment for debugging purposes, but be cautious with sensitive data
        # logging.info(f"Processing command: {user_input}")
        
        # First try exact command matches
        exact_commands = {
            # Login variations
            "login": "LOGIN",
            "log in": "LOGIN",
            "signin": "LOGIN",
            "sign in": "LOGIN",
            # Logout variations
            "logout": "LOGOUT",
            "log out": "LOGOUT",
            "signout": "LOGOUT",
            "sign out": "LOGOUT",
            "log off": "LOGOUT",
            "logoff": "LOGOUT",
            # Other standard commands
            "register": "REGISTER",
            "help": "HELP",
            "exit": "EXIT",
            "show cars": "SHOW_CARS",
            "available cars": "SHOW_CARS",
            "my bookings": "VIEW_BOOKINGS",
            "view bookings": "VIEW_BOOKINGS",
            "book car": "BOOK",
            "cancel booking": "CANCEL_BOOKING",
            "terms": "TERMS"
        }
        # Admin exact commands
        admin_exact_commands = {
            "all users": "VIEW_ALL_USERS",
            "all bookings": "VIEW_ALL_BOOKINGS",
            "car status": "VIEW_ALL_CAR_STATUS",
            "view assets": "VIEW_ALL_ASSETS",
            "revenue": "VIEW_ALL_REVENUE"
        }
        # Try exact matches first
        input_lower = user_input.lower()
        command = None
        # Check exact matches
        for cmd_text, cmd_name in exact_commands.items():
            if input_lower.startswith(cmd_text):
                command = cmd_name
                break
        # Check admin commands if user is admin
        if self.is_admin and not command:
            for cmd_text, cmd_name in admin_exact_commands.items():
                if input_lower.startswith(cmd_text):
                    command = cmd_name
                    break
        # If no exact match, try pattern matching
        if not command:
            # If admin, allow 'show bookings' to map to VIEW_ALL_BOOKINGS
            if self.is_admin and input_lower.startswith('show bookings'):
                command = 'VIEW_ALL_BOOKINGS'
            else:
                command = self._get_command_from_input(input_lower)
        # Execute standard command if found
        if command != "UNKNOWN":
            if not self._verify_command_access(command):
                return "Please login first." if not self.session_token else "You don't have permission to execute this command."
            return self._execute_standard_command(command, **kwargs)
        # Only allow NLP queries for specific scenarios
        if not self.session_token:
            return "Command not recognized. Type 'help' for available commands."
        # Pass any unrecognized command to NLP processor for all logged-in users
        try:
            user_context = {
                'user_id': self.user_id,
                'is_admin': self.is_admin,
                'session_token': self.session_token
            }
            nlp_response = self.nl_processor.process(user_input, user_context)
            return nlp_response
        except Exception as e:
            logging.error(f"Error processing NLP command '{user_input}': {str(e)}")
            return f"Error processing AI query: {str(e)}"
        # Fallback: always return a string if no other return was hit
        return "Command not recognized. Type 'help' for available commands."
    