from database import DatabaseManager
from security import SecurityUtils


class CarManager:
    """Manage car inventory and operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_available_cars(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """Get list of available cars"""
        with self.db.get_connection() as conn:
            if start_date and end_date:
                # Check for cars not booked in the date range
                cars = conn.execute("""
                    SELECT c.* FROM cars c
                    WHERE c.is_available = 1 AND c.is_maintenance = 0
                    AND c.id NOT IN (
                        SELECT car_id FROM bookings
                        WHERE status = 'active'
                        AND (
                            (start_date <= ? AND end_date >= ?) OR
                            (start_date <= ? AND end_date >= ?) OR
                            (start_date >= ? AND end_date <= ?)
                        )
                    )
                """, (start_date, start_date, end_date, end_date, start_date, end_date)).fetchall()
            else:
                cars = conn.execute("""
                    SELECT * FROM cars WHERE is_available = 1 AND is_maintenance = 0
                """).fetchall()
            
            return [dict(car) for car in cars]
    
    def get_car_by_id(self, car_id: int) -> Optional[Dict]:
        """Get specific car by ID"""
        with self.db.get_connection() as conn:
            car = conn.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
            return dict(car) if car else None
    
    def add_car(self, car_data: Dict, user_id: int) -> Tuple[bool, str]:
        """Add new car (superuser only)"""
        try:
            # Validate and process image
            image_hash = None
            if car_data.get('image_base64'):
                # Calculate hash for integrity
                image_data = base64.b64decode(car_data['image_base64'])
                image_hash = hashlib.sha256(image_data).hexdigest()
            
            with self.db.get_connection() as conn:
                conn.execute("""
                    INSERT INTO cars (make, model, year, license_plate, daily_rate,
                                    capacity, fuel_type, transmission, image_base64, image_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    car_data['make'], car_data['model'], car_data['year'],
                    car_data['license_plate'], car_data['daily_rate'],
                    car_data['capacity'], car_data['fuel_type'],
                    car_data['transmission'], car_data.get('image_base64'),
                    image_hash
                ))
                conn.commit()
            
            # Log action
            auth = AuthenticationManager(self.db)
            auth.log_action(user_id, "CAR_ADDED", f"Added car {car_data['make']} {car_data['model']}")
            
            return True, "Car added successfully"
        
        except sqlite3.IntegrityError:
            return False, "License plate already exists"
        except Exception as e:
            return False, f"Failed to add car: {str(e)}"
    
    def update_car(self, car_id: int, car_data: Dict, user_id: int) -> Tuple[bool, str]:
        """Update car information (superuser only)"""
        try:
            with self.db.get_connection() as conn:
                # Check if car exists
                car = conn.execute("SELECT id FROM cars WHERE id = ?", (car_id,)).fetchone()
                if not car:
                    return False, "Car not found"
                
                # Update car
                conn.execute("""
                    UPDATE cars SET make = ?, model = ?, year = ?, daily_rate = ?,
                                  capacity = ?, fuel_type = ?, transmission = ?
                    WHERE id = ?
                """, (
                    car_data['make'], car_data['model'], car_data['year'],
                    car_data['daily_rate'], car_data['capacity'],
                    car_data['fuel_type'], car_data['transmission'], car_id
                ))
                conn.commit()
            
            # Log action
            auth = AuthenticationManager(self.db)
            auth.log_action(user_id, "CAR_UPDATED", f"Updated car ID {car_id}")
            
            return True, "Car updated successfully"
        
        except Exception as e:
            return False, f"Failed to update car: {str(e)}"
    
    def set_maintenance_status(self, car_id: int, is_maintenance: bool, user_id: int) -> Tuple[bool, str]:
        """Set car maintenance status (admin/superuser)"""
        with self.db.get_connection() as conn:
            car = conn.execute("SELECT id FROM cars WHERE id = ?", (car_id,)).fetchone()
            if not car:
                return False, "Car not found"
            
            conn.execute("""
                UPDATE cars SET is_maintenance = ? WHERE id = ?
            """, (is_maintenance, car_id))
            conn.commit()
        
        # Log action
        auth = AuthenticationManager(self.db)
        status = "maintenance" if is_maintenance else "active"
        auth.log_action(user_id, "CAR_MAINTENANCE", f"Set car ID {car_id} to {status}")
        
        return True, f"Car set to {'maintenance' if is_maintenance else 'active'} status"
    
    def delete_car(self, car_id: int, user_id: int) -> Tuple[bool, str]:
        """Delete car (superuser only)"""
        with self.db.get_connection() as conn:
            # Check for active bookings
            booking = conn.execute("""
                SELECT id FROM bookings WHERE car_id = ? AND status = 'active'
            """, (car_id,)).fetchone()
            
            if booking:
                return False, "Cannot delete car with active bookings"
            
            result = conn.execute("DELETE FROM cars WHERE id = ?", (car_id,))
            if result.rowcount == 0:
                return False, "Car not found"
            
            conn.commit()
        
        # Log action
        auth = AuthenticationManager(self.db)
        auth.log_action(user_id, "CAR_DELETED", f"Deleted car ID {car_id}")
        
        return True, "Car deleted successfully"
