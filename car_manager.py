from database import DatabaseManager
from security import SecurityUtils
from typing import Optional, Dict, Tuple, List
import base64
import hashlib
import sqlite3
from datetime import datetime, timedelta
from auth import AuthenticationManager

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
    
    def show_available_cars(self) -> List[Dict]:
        """Show all available cars"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM cars WHERE is_available = 1")
            cars = [dict(row) for row in cursor.fetchall()]
            return cars
        
    def update_car_assets(self, car_id: int, asset_data: Dict, user_id: int) -> Tuple[bool, str]:
        """Update car asset information (admin only)"""
        try:
            with self.db.get_connection() as conn:
                # Check if car exists
                car = conn.execute("SELECT id FROM cars WHERE id = ?", (car_id,)).fetchone()
                if not car:
                    return False, "Car not found"
                
                # Update asset information
                conn.execute("""
                    UPDATE cars SET 
                        purchase_date = ?,
                        purchase_price = ?,
                        road_tax_expiry = ?,
                        road_tax_amount = ?,
                        insurance_expiry = ?,
                        insurance_provider = ?,
                        insurance_policy_number = ?,
                        insurance_amount = ?,
                        last_maintenance_date = ?,
                        next_maintenance_date = ?,
                        total_maintenance_cost = ?,
                        mileage = ?
                    WHERE id = ?
                """, (
                    asset_data.get('purchase_date'),
                    asset_data.get('purchase_price'),
                    asset_data.get('road_tax_expiry'),
                    asset_data.get('road_tax_amount'),
                    asset_data.get('insurance_expiry'),
                    asset_data.get('insurance_provider'),
                    asset_data.get('insurance_policy_number'),
                    asset_data.get('insurance_amount'),
                    asset_data.get('last_maintenance_date'),
                    asset_data.get('next_maintenance_date'),
                    asset_data.get('total_maintenance_cost'),
                    asset_data.get('mileage'),
                    car_id
                ))
                conn.commit()
            
            # Log action
            auth = AuthenticationManager(self.db)
            auth.log_action(user_id, "CAR_ASSETS_UPDATED", f"Updated asset information for car ID {car_id}")
            
            return True, "Car asset information updated successfully"
        
        except Exception as e:
            return False, f"Failed to update car asset information: {str(e)}"

    def get_car_assets(self, car_id: int) -> Optional[Dict]:
        """Get car asset information"""
        with self.db.get_connection() as conn:
            car = conn.execute("""
                SELECT id, make, model, year, license_plate, 
                       purchase_date, purchase_price, 
                       road_tax_expiry, road_tax_amount,
                       insurance_expiry, insurance_provider, 
                       insurance_policy_number, insurance_amount,
                       last_maintenance_date, next_maintenance_date, 
                       total_maintenance_cost, mileage
                FROM cars WHERE id = ?
            """, (car_id,)).fetchone()
            return dict(car) if car else None

    def get_expiring_assets(self, days: int = 30) -> Dict[str, List[Dict]]:
        """Get cars with expiring road tax or insurance within specified days"""
        with self.db.get_connection() as conn:
            expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            
            road_tax_expiring = conn.execute("""
                SELECT id, make, model, license_plate, road_tax_expiry
                FROM cars 
                WHERE road_tax_expiry <= ? AND road_tax_expiry >= date('now')
                ORDER BY road_tax_expiry
            """, (expiry_date,)).fetchall()
            
            insurance_expiring = conn.execute("""
                SELECT id, make, model, license_plate, 
                       insurance_expiry, insurance_provider
                FROM cars 
                WHERE insurance_expiry <= ? AND insurance_expiry >= date('now')
                ORDER BY insurance_expiry
            """, (expiry_date,)).fetchall()
            
            return {
                'road_tax_expiring': [dict(car) for car in road_tax_expiring],
                'insurance_expiring': [dict(car) for car in insurance_expiring]
            }

    def update_maintenance_record(self, car_id: int, maintenance_data: Dict, user_id: int) -> Tuple[bool, str]:
        """Update car maintenance record"""
        try:
            with self.db.get_connection() as conn:
                current_car = conn.execute("""
                    SELECT total_maintenance_cost FROM cars WHERE id = ?
                """, (car_id,)).fetchone()
                
                if not current_car:
                    return False, "Car not found"
                
                # Calculate new total maintenance cost
                new_total = current_car['total_maintenance_cost'] + maintenance_data.get('cost', 0)
                
                conn.execute("""
                    UPDATE cars SET 
                        last_maintenance_date = ?,
                        next_maintenance_date = ?,
                        total_maintenance_cost = ?,
                        mileage = ?
                    WHERE id = ?
                """, (
                    maintenance_data.get('maintenance_date'),
                    maintenance_data.get('next_maintenance_date'),
                    new_total,
                    maintenance_data.get('mileage'),
                    car_id
                ))
                conn.commit()
            
            # Log action
            auth = AuthenticationManager(self.db)
            auth.log_action(user_id, "MAINTENANCE_UPDATED", 
                          f"Updated maintenance record for car ID {car_id}")
            
            return True, "Maintenance record updated successfully"
        
        except Exception as e:
            return False, f"Failed to update maintenance record: {str(e)}"
