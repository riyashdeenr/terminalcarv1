from typing import List, Dict, Optional
from database import DatabaseManager

class AdminManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def view_all_users(self) -> List[Dict]:
        """View all users and their details"""
        with self.db.get_connection() as conn:
            users = conn.execute("""
                SELECT id, email, role, created_at, last_login, is_active 
                FROM users
            """).fetchall()
            return [dict(user) for user in users]
    
    def view_user_bookings(self, user_id: int = None) -> List[Dict]:
        """View bookings for specific user or all bookings"""
        with self.db.get_connection() as conn:
            query = """
                SELECT b.*, u.email as user_email, 
                       c.make, c.model, c.license_plate
                FROM bookings b
                JOIN users u ON b.user_id = u.id
                JOIN cars c ON b.car_id = c.id
            """
            if user_id:
                query += " WHERE b.user_id = ?"
                bookings = conn.execute(query, (user_id,)).fetchall()
            else:
                bookings = conn.execute(query).fetchall()
            return [dict(booking) for booking in bookings]
    
    def view_car_status(self) -> Dict[str, List[Dict]]:
        """View all cars grouped by availability"""
        with self.db.get_connection() as conn:
            available = conn.execute("""
                SELECT * FROM cars WHERE is_available = 1
            """).fetchall()
            
            not_available = conn.execute("""
                SELECT c.*, b.start_date, b.end_date, u.email as booked_by
                FROM cars c
                JOIN bookings b ON c.id = b.car_id
                JOIN users u ON b.user_id = u.id
                WHERE c.is_available = 0
            """).fetchall()
            
            return {
                'available': [dict(car) for car in available],
                'not_available': [dict(car) for car in not_available]
            }
    
    def search_booking_by_id(self, booking_id: str) -> Optional[Dict]:
        """Search for a booking by ID"""
        with self.db.get_connection() as conn:
            booking = conn.execute("""
                SELECT b.*, u.email as user_email, 
                       c.make, c.model, c.license_plate
                FROM bookings b
                JOIN users u ON b.user_id = u.id
                JOIN cars c ON b.car_id = c.id
                WHERE b.id = ?
            """, (booking_id,)).fetchone()
            return dict(booking) if booking else None

    def search_bookings_by_username(self, username: str) -> List[Dict]:
        """Search for bookings by username (email)"""
        with self.db.get_connection() as conn:
            bookings = conn.execute("""
                SELECT b.*, u.email as user_email, 
                       c.make, c.model, c.license_plate
                FROM bookings b
                JOIN users u ON b.user_id = u.id
                JOIN cars c ON b.car_id = c.id
                WHERE u.email LIKE ?
            """, (f"%{username}%",)).fetchall()
            return [dict(booking) for booking in bookings]

    def search_car_by_plate(self, license_plate: str) -> Optional[Dict]:
        """Search for a car by license plate"""
        with self.db.get_connection() as conn:
            car = conn.execute("""
                SELECT c.*, 
                       CASE WHEN b.id IS NOT NULL 
                            THEN (SELECT email FROM users WHERE id = b.user_id)
                            ELSE NULL 
                       END as booked_by,
                       b.start_date, b.end_date
                FROM cars c
                LEFT JOIN bookings b ON c.id = b.car_id AND b.end_date >= date('now')
                WHERE c.license_plate LIKE ?
            """, (f"%{license_plate}%",)).fetchone()
            return dict(car) if car else None

    def search_cars_by_make_model(self, make: str, model: str) -> List[Dict]:
        """Search for cars by make and model"""
        with self.db.get_connection() as conn:
            cars = conn.execute("""
                SELECT c.*, 
                       CASE WHEN b.id IS NOT NULL 
                            THEN (SELECT email FROM users WHERE id = b.user_id)
                            ELSE NULL 
                       END as booked_by,
                       b.start_date, b.end_date
                FROM cars c
                LEFT JOIN bookings b ON c.id = b.car_id AND b.end_date >= date('now')
                WHERE c.make LIKE ? AND c.model LIKE ?
            """, (f"%{make}%", f"%{model}%")).fetchall()
            return [dict(car) for car in cars]