import http.server
from main import CarRentalApp


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler"""
    
    def __init__(self, *args, app=None, **kwargs):
        self.app = app
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        self.app.web_interface.handle_request(self)
    
    def do_POST(self):
        self.app.web_interface.handle_request(self)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()



class WebInterface:
    """Simple web interface for the application"""
    
    def __init__(self, app):
        self.app = app
        self.sessions = {}
    
    def handle_request(self, handler):
        """Handle HTTP request"""
        try:
            path = handler.path
            method = handler.command
            
            if path.startswith('/api/'):
                self.handle_api_request(handler, path, method)
            else:
                self.serve_static_content(handler, path)
        
        except Exception as e:
            handler.send_error(500, f"Internal Server Error: {str(e)}")
    
    def handle_api_request(self, handler, path, method):
        """Handle API requests"""
        content_length = int(handler.headers.get('Content-Length', 0))
        post_data = {}
        
        if content_length > 0:
            raw_data = handler.rfile.read(content_length)
            try:
                post_data = json.loads(raw_data.decode('utf-8'))
            except:
                post_data = {}
        
        # Parse query parameters
        parsed_url = urlparse(path)
        query_params = parse_qs(parsed_url.query)
        
        # Route API requests
        response_data = {"success": False, "message": "Not implemented"}
        
        if path == "/api/register":
            response_data = self.handle_register(post_data)
        elif path == "/api/login":
            response_data = self.handle_login(post_data)
        elif path == "/api/logout":
            response_data = self.handle_logout(handler.headers)
        elif path == "/api/cars":
            response_data = self.handle_get_cars(query_params, handler.headers)
        elif path == "/api/booking":
            response_data = self.handle_booking(post_data, handler.headers)
        elif path == "/api/ai-chat":
            response_data = self.handle_ai_chat(post_data, handler.headers)
        
        # Send JSON response
        handler.send_response(200)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        handler.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        handler.end_headers()
        handler.wfile.write(json.dumps(response_data).encode('utf-8'))
    
    def serve_static_content(self, handler, path):
        """Serve static HTML content"""
        if path == "/" or path == "/index.html":
            content = self.get_main_page()
        else:
            handler.send_error(404, "File not found")
            return
        
        handler.send_response(200)
        handler.send_header('Content-type', 'text/html')
        handler.end_headers()
        handler.wfile.write(content.encode('utf-8'))
    
    def get_main_page(self):
        """Generate main HTML page"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Secure Car Rental System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; color: #333; margin-bottom: 30px; }
                .auth-section, .main-section, .chat-section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                .hidden { display: none; }
                button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
                button:hover { background-color: #0056b3; }
                input, select, textarea { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                .car-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
                .car-item { border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #f9f9f9; }
                .chat-messages { height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; background: #f9f9f9; }
                .user-message { text-align: right; margin: 10px 0; }
                .ai-message { text-align: left; margin: 10px 0; color: #007bff; }
                .error { color: #dc3545; }
                .success { color: #28a745; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚗 Secure Car Rental System</h1>
                    <p>AI-Powered Car Rental with Advanced Security</p>
                </div>
                
                <!-- Authentication Section -->
                <div id="auth-section" class="auth-section">
                    <h2>Login / Register</h2>
                    <div id="login-form">
                        <h3>Login</h3>
                        <input type="email" id="login-email" placeholder="Email" required>
                        <input type="password" id="login-password" placeholder="Password" required>
                        <button onclick="login()">Login</button>
                        <button onclick="showRegister()">Register New User</button>
                        <button onclick="showForgotPassword()">Forgot Password</button>
                    </div>
                    
                    <div id="register-form" class="hidden">
                        <h3>Register</h3>
                        <input type="email" id="reg-email" placeholder="Email" required>
                        <input type="password" id="reg-password" placeholder="Password" required>
                        <input type="text" id="reg-national-id" placeholder="National ID Number" required>
                        <select id="reg-role">
                            <option value="user">User</option>
                            <option value="admin">Admin</option>
                            <option value="superuser">Superuser</option>
                        </select>
                        <button onclick="register()">Register</button>
                        <button onclick="showLogin()">Back to Login</button>
                    </div>
                    
                    <div id="forgot-password-form" class="hidden">
                        <h3>Reset Password</h3>
                        <input type="email" id="reset-email" placeholder="Email" required>
                        <input type="password" id="new-password" placeholder="New Password" required>
                        <button onclick="resetPassword()">Reset Password</button>
                        <button onclick="showLogin()">Back to Login</button>
                    </div>
                    
                    <div id="message"></div>
                </div>
                
                <!-- Main Application Section -->
                <div id="main-section" class="main-section hidden">
                    <div id="user-info"></div>
                    
                    <div id="user-functions" class="hidden">
                        <h3>Available Functions</h3>
                        <button onclick="loadAvailableCars()">View Available Cars</button>
                        <button onclick="showMyBookings()">My Bookings</button>
                        <button onclick="showBookingForm()">Make a Booking</button>
                        <button onclick="logout()">Logout</button>
                    </div>
                    
                    <div id="admin-functions" class="hidden">
                        <h3>Admin Functions</h3>
                        <button onclick="loadAllBookings()">View All Bookings</button>
                        <button onclick="showMaintenanceForm()">Set Car Maintenance</button>
                        <button onclick="showPasswordResetForm()">Reset User Password</button>
                        <button onclick="logout()">Logout</button>
                    </div>
                    
                    <div id="superuser-functions" class="hidden">
                        <h3>Superuser Functions</h3>
                        <button onclick="loadAllBookings()">Manage Bookings</button>
                        <button onclick="showCarManagement()">Manage Cars</button>
                        <button onclick="showUserManagement()">Manage Users</button>
                        <button onclick="insertSampleData()">Insert Sample Data</button>
                        <button onclick="logout()">Logout</button>
                    </div>
                    
                    <!-- Car Booking Form -->
                    <div id="booking-form" class="hidden">
                        <h3>Make a Booking</h3>
                        <select id="booking-car-id">
                            <option value="">Select a car...</option>
                        </select>
                        <input type="date" id="booking-start-date" required>
                        <input type="date" id="booking-end-date" required>
                        <label>
                            <input type="checkbox" id="terms-accepted" required>
                            I accept the terms and conditions
                        </label>
                        <button onclick="createBooking()">Book Car</button>
                        <button onclick="hideBookingForm()">Cancel</button>
                    </div>
                    
                    <!-- Results Display -->
                    <div id="results"></div>
                </div>
                
                <!-- AI Chat Section -->
                <div id="chat-section" class="chat-section hidden">
                    <h3>🤖 AI Sales Assistant</h3>
                    <div id="chat-messages" class="chat-messages"></div>
                    <div>
                        <input type="text" id="chat-input" placeholder="Ask me about our cars..." onkeypress="if(event.key==='Enter') sendMessage()">
                        <button onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
            
            <script>
                let currentSession = null;
                let currentUser = null;
                
                function showLogin() {
                    document.getElementById('login-form').classList.remove('hidden');
                    document.getElementById('register-form').classList.add('hidden');
                    document.getElementById('forgot-password-form').classList.add('hidden');
                }
                
                function showRegister() {
                    document.getElementById('login-form').classList.add('hidden');
                    document.getElementById('register-form').classList.remove('hidden');
                    document.getElementById('forgot-password-form').classList.add('hidden');
                }
                
                function showForgotPassword() {
                    document.getElementById('login-form').classList.add('hidden');
                    document.getElementById('register-form').classList.add('hidden');
                    document.getElementById('forgot-password-form').classList.remove('hidden');
                }
                
                async function login() {
                    const email = document.getElementById('login-email').value;
                    const password = document.getElementById('login-password').value;
                    
                    if (!email || !password) {
                        showMessage('Please fill in all fields', 'error');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/login', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email, password })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            currentSession = data.session_token;
                            currentUser = data.user_info;
                            showMainSection();
                            showMessage('Login successful!', 'success');
                        } else {
                            showMessage(data.message, 'error');
                        }
                    } catch (error) {
                        showMessage('Login failed: ' + error.message, 'error');
                    }
                }
                
                async function register() {
                    const email = document.getElementById('reg-email').value;
                    const password = document.getElementById('reg-password').value;
                    const nationalId = document.getElementById('reg-national-id').value;
                    const role = document.getElementById('reg-role').value;
                    
                    if (!email || !password || !nationalId) {
                        showMessage('Please fill in all fields', 'error');
                        return;
                    }
                    
                    try {
                        const response = await fetch('/api/register', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ email, password, national_id: nationalId, role })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            showMessage('Registration successful! Please login.', 'success');
                            showLogin();
                        } else {
                            showMessage(data.message, 'error');
                        }
                    } catch (error) {
                        showMessage('Registration failed: ' + error.message, 'error');
                    }
                }
                
                function showMainSection() {
                    document.getElementById('auth-section').classList.add('hidden');
                    document.getElementById('main-section').classList.remove('hidden');
                    document.getElementById('chat-section').classList.remove('hidden');
                    
                    document.getElementById('user-info').innerHTML = 
                        `<h3>Welcome, ${currentUser.email} (${currentUser.role})</h3>`;
                    
                    // Show appropriate functions based on role
                    document.getElementById('user-functions').classList.add('hidden');
                    document.getElementById('admin-functions').classList.add('hidden');
                    document.getElementById('superuser-functions').classList.add('hidden');
                    
                    if (currentUser.role === 'user') {
                        document.getElementById('user-functions').classList.remove('hidden');
                    } else if (currentUser.role === 'admin') {
                        document.getElementById('admin-functions').classList.remove('hidden');
                    } else if (currentUser.role === 'superuser') {
                        document.getElementById('superuser-functions').classList.remove('hidden');
                    }
                }
                
                async function logout() {
                    try {
                        await fetch('/api/logout', {
                            method: 'POST',
                            headers: { 'Authorization': 'Bearer ' + currentSession }
                        });
                    } catch (error) {
                        console.error('Logout error:', error);
                    }
                    
                    currentSession = null;
                    currentUser = null;
                    
                    document.getElementById('auth-section').classList.remove('hidden');
                    document.getElementById('main-section').classList.add('hidden');
                    document.getElementById('chat-section').classList.add('hidden');
                    
                    showMessage('Logged out successfully', 'success');
                    showLogin();
                }
                
                async function loadAvailableCars() {
                    try {
                        const response = await fetch('/api/cars', {
                            headers: { 'Authorization': 'Bearer ' + currentSession }
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            displayCars(data.cars);
                        } else {
                            showMessage(data.message, 'error');
                        }
                    } catch (error) {
                        showMessage('Failed to load cars: ' + error.message, 'error');
                    }
                }
                
                function displayCars(cars) {
                    let html = '<h3>Available Cars</h3><div class="car-list">';
                    
                    cars.forEach(car => {
                        html += `
                            <div class="car-item">
                                <h4>${car.year} ${car.make} ${car.model}</h4>
                                <p><strong>License:</strong> ${car.license_plate}</p>
                                <p><strong>Rate:</strong> $${car.daily_rate}/day</p>
                                <p><strong>Capacity:</strong> ${car.capacity} people</p>
                                <p><strong>Fuel:</strong> ${car.fuel_type}</p>
                                <p><strong>Transmission:</strong> ${car.transmission}</p>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                    document.getElementById('results').innerHTML = html;
                }
                
                function showBookingForm() {
                    // Load cars for booking
                    loadAvailableCars();
                    document.getElementById('booking-form').classList.remove('hidden');
                }
                
                function hideBookingForm() {
                    document.getElementById('booking-form').classList.add('hidden');
                }
                
                async function sendMessage() {
                    const input = document.getElementById('chat-input');
                    const message = input.value.trim();
                    
                    if (!message) return;
                    
                    // Add user message to chat
                    addChatMessage(message, 'user');
                    input.value = '';
                    
                    try {
                        const response = await fetch('/api/ai-chat', {
                            method: 'POST',
                            headers: { 
                                'Content-Type': 'application/json',
                                'Authorization': 'Bearer ' + currentSession 
                            },
                            body: JSON.stringify({ message })
                        });
                        
                        const data = await response.json();
                        
                        if (data.success) {
                            addChatMessage(data.response, 'ai');
                        } else {
                            addChatMessage('Sorry, I could not process your request.', 'ai');
                        }
                    } catch (error) {
                        addChatMessage('Sorry, there was an error processing your request.', 'ai');
                    }
                }
                
                function addChatMessage(message, sender) {
                    const chatMessages = document.getElementById('chat-messages');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = sender === 'user' ? 'user-message' : 'ai-message';
                    messageDiv.innerHTML = `<strong>${sender === 'user' ? 'You' : 'AI Assistant'}:</strong> ${message}`;
                    chatMessages.appendChild(messageDiv);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
                
                function showMessage(message, type) {
                    const messageDiv = document.getElementById('message');
                    messageDiv.innerHTML = `<div class="${type}">${message}</div>`;
                    setTimeout(() => {
                        messageDiv.innerHTML = '';
                    }, 5000);
                }
                
                // Initialize chat with welcome message
                document.addEventListener('DOMContentLoaded', function() {
                    addChatMessage('Hello! I\'m your AI assistant. I can help you find the perfect car for your rental needs. How can I assist you today?', 'ai');
                });
            </script>
        </body>
        </html>
        """
    
    def handle_register(self, data):
        """Handle user registration"""
        try:
            success, message = self.app.auth.register_user(
                data['email'], data['password'], data['national_id'], data.get('role', 'user')
            )
            return {"success": success, "message": message}
        except Exception as e:
            return {"success": False, "message": f"Registration error: {str(e)}"}
    
    def handle_login(self, data):
        """Handle user login"""
        try:
            success, message, user_info = self.app.auth.login(data['email'], data['password'])
            if success:
                return {
                    "success": True, 
                    "message": message,
                    "session_token": user_info['session_token'],
                    "user_info": {
                        "email": user_info['email'],
                        "role": user_info['role'],
                        "user_id": user_info['user_id']
                    }
                }
            return {"success": False, "message": message}
        except Exception as e:
            return {"success": False, "message": f"Login error: {str(e)}"}
    
    def handle_logout(self, headers):
        """Handle user logout"""
        try:
            auth_header = headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                self.app.auth.logout(token)
            return {"success": True, "message": "Logged out successfully"}
        except Exception as e:
            return {"success": False, "message": f"Logout error: {str(e)}"}
    
    def handle_get_cars(self, query_params, headers):
        """Handle get available cars"""
        try:
            # Validate session
            auth_header = headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return {"success": False, "message": "Authentication required"}
            
            token = auth_header[7:]
            user_info = self.app.auth.validate_session(token)
            if not user_info:
                return {"success": False, "message": "Invalid session"}
            
            cars = self.app.car_manager.get_available_cars()
            return {"success": True, "cars": cars}
        
        except Exception as e:
            return {"success": False, "message": f"Error loading cars: {str(e)}"}
    
    def handle_booking(self, data, headers):
        """Handle car booking"""
        try:
            # Validate session
            auth_header = headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return {"success": False, "message": "Authentication required"}
            
            token = auth_header[7:]
            user_info = self.app.auth.validate_session(token)
            if not user_info:
                return {"success": False, "message": "Invalid session"}
            
            success, message, booking_id = self.app.booking_manager.create_booking(
                user_info['user_id'], data['car_id'], data['start_date'], 
                data['end_date'], data.get('terms_accepted', False)
            )
            
            return {"success": success, "message": message, "booking_id": booking_id}
        
        except Exception as e:
            return {"success": False, "message": f"Booking error: {str(e)}"}
    
    def handle_ai_chat(self, data, headers):
        """Handle AI chat interaction"""
        try:
            # Validate session
            auth_header = headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return {"success": False, "message": "Authentication required"}
            
            token = auth_header[7:]
            user_info = self.app.auth.validate_session(token)
            if not user_info:
                return {"success": False, "message": "Invalid session"}
            
            response = self.app.gemini.simulate_ai_response(data['message'], token)
            return {"success": True, "response": response}
        
        except Exception as e:
            return {"success": False, "message": f"AI chat error: {str(e)}"}
