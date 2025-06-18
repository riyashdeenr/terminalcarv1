"""
Unit Tests for AI Car Rental System Core Logic
Covers: input sanitization, command parsing, error handling, and audit logging.
"""
import unittest
from unittest.mock import patch, MagicMock
from ai_interface_advance import AICarRentalInterface, SecurityValidator

class TestSecurityValidator(unittest.TestCase):
    def test_sanitize_string_removes_sql_injection(self):
        malicious = "Robert'); DROP TABLE users;--"
        clean = SecurityValidator.sanitize_string(malicious)
        self.assertNotIn("DROP", clean.upper())
        self.assertNotIn("--", clean)
        self.assertNotIn(";", clean)

    def test_sanitize_string_allows_safe_input(self):
        safe = "hello_world123"
        self.assertEqual(SecurityValidator.sanitize_string(safe), safe)

    def test_validate_table_name(self):
        self.assertTrue(SecurityValidator.validate_table_name('users'))
        self.assertFalse(SecurityValidator.validate_table_name('hacked'))

    def test_validate_field_name(self):
        self.assertTrue(SecurityValidator.validate_field_name('email'))
        self.assertFalse(SecurityValidator.validate_field_name('password_hash'))

    def test_validate_operator(self):
        self.assertTrue(SecurityValidator.validate_operator('='))
        self.assertFalse(SecurityValidator.validate_operator('UNION'))

class TestAICarRentalInterfaceUnit(unittest.TestCase):
    def setUp(self):
        self.interface = AICarRentalInterface()
        # Patch all manager methods to avoid DB access
        self.interface.car_manager = MagicMock()
        self.interface.booking_manager = MagicMock()
        self.interface.admin_manager = MagicMock()
        self.interface.auth_manager = MagicMock()
        self.interface.get_available_cars = MagicMock(return_value=[{'id': 1, 'make': 'Test', 'model': 'Car', 'daily_rate': 100}])
        self.interface.get_user_bookings = MagicMock(return_value=[{'id': 1, 'car_id': 1, 'make': 'Test', 'model': 'Car', 'status': 'active', 'start_date': '2025-01-01', 'end_date': '2025-01-02', 'total_amount': 100}])
        self.interface.create_booking = MagicMock(return_value=(True, 'Booking successful', 100.0))
        self.interface.cancel_booking = MagicMock(return_value=(True, 'Cancelled'))
        self.interface.handle_login = MagicMock(return_value=(True, 'Login successful'))
        self.interface.handle_logout = MagicMock(return_value=(True, 'Logged out'))
        self.interface.terms_accepted = True
        self.interface.session_token = 'token'
        self.interface.user_id = 1
        self.interface.is_admin = True

    def test_process_command_help(self):
        result = self.interface.process_command('help')
        if result is None:
            print('HELP command returned None!')
        else:
            print('HELP command result:', result)
        self.assertIsInstance(result, str)
        self.assertIn('Available Commands', result)
        self.assertIn('Admin Commands', result)

    def test_process_command_show_cars(self):
        result = self.interface.process_command('show cars')
        self.assertIn('Available Cars', result)
        self.assertIn('Test', result)

    def test_process_command_book(self):
        # Try both 'book' and 'book car' to ensure booking flow is triggered
        result = self.interface.process_command('book', car_id=1, start_date='2025-01-01', duration=1)
        if 'Booking successful' not in result:
            print('BOOK command result:', result)
        self.assertIn('Booking successful', result)

    def test_process_command_cancel_booking(self):
        result = self.interface.process_command('cancel booking', booking_id=1)
        self.assertIn('Cancelled', result)

    def test_process_command_admin_users(self):
        self.interface.admin_manager.view_all_users.return_value = [{'id': 1, 'email': 'a@b.com', 'role': 'admin', 'is_active': True}]
        result = self.interface.process_command('view users')
        self.assertIn('All Users', result)
        self.assertIn('a@b.com', result)

    def test_error_handling_manager_exception(self):
        self.interface.get_available_cars.side_effect = Exception('DB error')
        result = self.interface.process_command('show cars')
        self.assertIn('error', result.lower())

    @patch('ai_interface_advance.open')
    def test_audit_log_event_writes_to_file(self, mock_open):
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        self.interface.audit_log_event('test_event', 'details')
        self.assertTrue(mock_file.write.called)

if __name__ == '__main__':
    unittest.main(verbosity=2)
