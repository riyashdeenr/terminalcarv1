from database import DatabaseManager
from security import SecurityUtils



class BookingManager:
    """Manage car bookings and reservations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_booking(self, user_id: int, car_id: int, start_date: str, 
                      end_date: str, terms_accepted: bool = False) -> Tuple[bool, str, Optional[int]]:
        """Create a new booking"""
        try:
            with self.db.get_connection() as conn:
                # Check if car exists and is available
                car = conn.execute("""
                    SELECT * FROM cars WHERE id = ? AND is_available = 1 AND is_maintenance = 0
                """, (car_id,)).fetchone()
                
                if not car:
                    return False, "Car not available", None
                
                # Check for conflicting bookings
                conflict = conn.execute("""
                    SELECT id FROM bookings
                    WHERE car_id = ? AND status = 'active'
                    AND (
                        (start_date <= ? AND end_date >= ?) OR
                        (start_date <= ? AND end_date >= ?) OR
                        (start_date >= ? AND end_date <= ?)
                    )
                """, (car_id, start_date, start_date, end_date, end_date, start_date, end_date)).fetchone()
                
                if conflict:
                    return False, "Car is already booked for the selected dates", None
                
                # Calculate total amount
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                days = (end_dt - start_dt).days + 1
                total_amount = days * car['daily_rate']
                
                # Generate terms and conditions hash
                terms_hash = None
                if terms_accepted:
                    terms_content = self.get_terms_and_conditions()
                    terms_hash = hashlib.sha256(terms_content.encode()).hexdigest()
                
                # Create booking
                cursor = conn.execute("""
                    INSERT INTO bookings (user_id, car_id, start_date, end_date, 
                                        total_amount, terms_accepted_hash)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, car_id, start_date, end_date, total_amount, terms_hash))
                
                booking_id = cursor.lastrowid
                conn.commit()
                
                # Log action
                auth = AuthenticationManager(self.db)
                auth.log_action(user_id, "BOOKING_CREATED", 
                              f"Created booking ID {booking_id} for car ID {car_id}")
                
                return True, f"Booking created successfully. Total: ${total_amount:.2f}", booking_id
        
        except Exception as e:
            return False, f"Failed to create booking: {str(e)}", None
    
    def cancel_booking(self, booking_id: int, user_id: int, is_admin: bool = False) -> Tuple[bool, str]:
        """Cancel a booking"""
        with self.db.get_connection() as conn:
            # Get booking details
            if is_admin:
                booking = conn.execute("""
                    SELECT * FROM bookings WHERE id = ? AND status = 'active'
                """, (booking_id,)).fetchone()
            else:
                booking = conn.execute("""
                    SELECT * FROM bookings WHERE id = ? AND user_id = ? AND status = 'active'
                """, (booking_id, user_id)).fetchone()
            
            if not booking:
                return False, "Booking not found or already cancelled"
            
            # Check if booking can be cancelled (e.g., not within 24 hours)
            booking_start = datetime.strptime(booking['start_date'], '%Y-%m-%d')
            if datetime.now() + timedelta(hours=24) > booking_start:
                if not is_admin:
                    return False, "Cannot cancel booking within 24 hours of start time"
            
            # Cancel booking
            conn.execute("""
                UPDATE bookings SET status = 'cancelled' WHERE id = ?
            """, (booking_id,))
            conn.commit()
            
            # Log action
            auth = AuthenticationManager(self.db)
            auth.log_action(user_id, "BOOKING_CANCELLED", f"Cancelled booking ID {booking_id}")
            
            return True, "Booking cancelled successfully"
    
    def get_user_bookings(self, user_id: int) -> List[Dict]:
        """Get bookings for a specific user"""
        with self.db.get_connection() as conn:
            bookings = conn.execute("""
                SELECT b.*, c.make, c.model, c.year, c.license_plate
                FROM bookings b
                JOIN cars c ON b.car_id = c.id
                WHERE b.user_id = ?
                ORDER BY b.created_at DESC
            """, (user_id,)).fetchall()
            
            return [dict(booking) for booking in bookings]
    
    def get_all_bookings(self) -> List[Dict]:
        """Get all bookings (admin/superuser only)"""
        with self.db.get_connection() as conn:
            bookings = conn.execute("""
                SELECT b.*, c.make, c.model, c.year, c.license_plate, u.email
                FROM bookings b
                JOIN cars c ON b.car_id = c.id
                JOIN users u ON b.user_id = u.id
                ORDER BY b.created_at DESC
            """, ).fetchall()
            
            return [dict(booking) for booking in bookings]
    
    def get_terms_and_conditions(self) -> str:
        """Get terms and conditions content"""
        terms = """
        CAR RENTAL TERMS AND CONDITIONS
        
        1. The renter must be at least 21 years old with a valid driver's license.
        2. A security deposit is required and will be refunded upon safe return of the vehicle.
        3. The vehicle must be returned in the same condition as received.
        4. Any damage to the vehicle will be charged to the renter.
        5. Late returns will incur additional charges.
        6. The renter is responsible for all traffic violations and parking tickets.
        7. Smoking is prohibited in all rental vehicles.
        8. The rental company is not liable for personal belongings left in the vehicle.
        9. Cancellations must be made at least 24 hours before the rental start time.
        10. By accepting these terms, you agree to all conditions stated above.
        """
        return terms
