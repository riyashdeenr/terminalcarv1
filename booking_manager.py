from database import DatabaseManager
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, List


class BookingManager:
    """Manage car bookings and reservations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_booking(self, user_id: int, car_id: int, start_date: str, end_date: str) -> Tuple[bool, str]:
        """Create a new booking"""
        try:
            # Validate car availability for the date range
            with self.db.get_connection() as conn:
                # Check if car exists and is available
                car = conn.execute("""
                    SELECT is_available FROM cars 
                    WHERE id = ?
                """, (car_id,)).fetchone()

                if not car:
                    return False, "Car not found."

                if not car['is_available']:
                    return False, "Car is not available for booking."

                # Check for overlapping bookings
                existing_booking = conn.execute("""
                    SELECT id FROM bookings 
                    WHERE car_id = ? AND 
                          ((start_date <= ? AND end_date >= ?) OR
                           (start_date <= ? AND end_date >= ?) OR
                           (start_date >= ? AND end_date <= ?))
                """, (car_id, start_date, start_date, end_date, end_date, start_date, end_date)).fetchone()

                if existing_booking:
                    return False, "Car is already booked for these dates."

                # Create the booking
                conn.execute("""
                    INSERT INTO bookings (user_id, car_id, start_date, end_date, terms_accepted)
                    VALUES (?, ?, ?, ?, 1)
                """, (user_id, car_id, start_date, end_date))

                # Update car availability
                conn.execute("""
                    UPDATE cars SET is_available = 0
                    WHERE id = ?
                """, (car_id,))

                conn.commit()
                return True, "Booking created successfully."

        except Exception as e:
            return False, f"Error creating booking: {str(e)}"

    def get_user_bookings(self, user_id: int) -> List[Dict]:
        """Get bookings for a specific user"""
        with self.db.get_connection() as conn:
            bookings = conn.execute("""
                SELECT b.*, c.make, c.model, c.daily_rate, c.category
                FROM bookings b
                JOIN cars c ON b.car_id = c.id
                WHERE b.user_id = ?
                ORDER BY b.start_date DESC
            """, (user_id,)).fetchall()
            return [dict(booking) for booking in bookings]

    def cancel_booking(self, booking_id: int, user_id: int) -> Tuple[bool, str]:
        """Cancel a booking"""
        try:
            with self.db.get_connection() as conn:
                # Verify booking exists and belongs to user
                booking = conn.execute("""
                    SELECT car_id, start_date FROM bookings
                    WHERE id = ? AND user_id = ?
                """, (booking_id, user_id)).fetchone()

                if not booking:
                    return False, "Booking not found or unauthorized."

                # Check if cancellation is allowed (e.g., not within 24 hours of start)
                start_date = datetime.strptime(booking['start_date'], '%Y-%m-%d')
                if datetime.now() + timedelta(days=1) >= start_date:
                    return False, "Cancellation is not allowed within 24 hours of start date."

                # Cancel booking
                conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
                
                # Update car availability
                conn.execute("""
                    UPDATE cars SET is_available = 1
                    WHERE id = ?
                """, (booking['car_id'],))

                conn.commit()
                return True, "Booking cancelled successfully."

        except Exception as e:
            return False, f"Error cancelling booking: {str(e)}"
