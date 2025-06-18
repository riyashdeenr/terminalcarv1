from typing import List, Dict, Optional
from database import DatabaseManager
from datetime import datetime

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
    
    def view_user_bookings(self, user_identifier: str = None) -> List[Dict]:
        """View bookings for specific user or all bookings
        Args:
            user_identifier: Can be either a user ID (int) or email address (str)
        """
        with self.db.get_connection() as conn:
            query = """
                SELECT b.*, u.email as user_email, 
                       c.make, c.model, c.license_plate, c.daily_rate,
                       b.status
                FROM bookings b
                JOIN users u ON b.user_id = u.id
                JOIN cars c ON b.car_id = c.id
            """
            params = []
            
            if user_identifier:
                try:
                    # Try to convert to integer (user ID)
                    user_id = int(user_identifier)
                    query += " WHERE b.user_id = ?"
                    params = [user_id]
                except ValueError:
                    # If conversion fails, treat as email
                    query += " WHERE u.email LIKE ?"
                    params = [f"%{user_identifier}%"]
            
            if params:
                bookings = conn.execute(query, params).fetchall()
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
                       c.make, c.model, c.license_plate, c.daily_rate
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

    def view_asset_summary(self) -> Dict:
        """View summary of all car assets"""
        with self.db.get_connection() as conn:
            # Get total fleet value
            total_value = conn.execute("""
                SELECT SUM(purchase_price) as fleet_value,
                       COUNT(*) as total_cars,
                       SUM(total_maintenance_cost) as total_maintenance
                FROM cars
            """).fetchone()
            
            # Get upcoming expirations
            current_date = datetime.now().strftime('%Y-%m-%d')
            expiring_soon = conn.execute("""
                SELECT 
                    COUNT(CASE WHEN road_tax_expiry <= date('now', '+30 days') 
                              AND road_tax_expiry >= ? THEN 1 END) as road_tax_expiring,
                    COUNT(CASE WHEN insurance_expiry <= date('now', '+30 days')
                              AND insurance_expiry >= ? THEN 1 END) as insurance_expiring,
                    COUNT(CASE WHEN next_maintenance_date <= date('now', '+30 days')
                              AND next_maintenance_date >= ? THEN 1 END) as maintenance_due
                FROM cars
            """, (current_date, current_date, current_date)).fetchone()
            
            return {
                'fleet_value': dict(total_value),
                'expiring_soon': dict(expiring_soon)
            }
    
    def get_asset_details(self, car_id: int) -> Optional[Dict]:
        """Get detailed asset information for a specific car"""
        with self.db.get_connection() as conn:
            car = conn.execute("""
                SELECT 
                    make, model, year, license_plate, daily_rate, category,
                    COALESCE(purchase_date, '') as purchase_date,
                    COALESCE(purchase_price, 0) as purchase_price,
                    COALESCE(road_tax_expiry, '') as road_tax_expiry,
                    COALESCE(road_tax_amount, 0) as road_tax_amount,
                    COALESCE(insurance_expiry, '') as insurance_expiry,
                    COALESCE(insurance_provider, '') as insurance_provider,
                    COALESCE(insurance_policy_number, '') as insurance_policy_number,
                    COALESCE(insurance_amount, 0) as insurance_amount,
                    COALESCE(last_maintenance_date, '') as last_maintenance_date,
                    COALESCE(next_maintenance_date, '') as next_maintenance_date,
                    COALESCE(total_maintenance_cost, 0) as total_maintenance_cost,
                    COALESCE(mileage, 0) as mileage,
                    COALESCE((SELECT COUNT(*) FROM bookings b WHERE b.car_id = c.id), 0) as total_bookings,
                    COALESCE((
                        SELECT CAST(SUM(JULIANDAY(end_date) - JULIANDAY(start_date)) AS INTEGER)
                        FROM bookings b 
                        WHERE b.car_id = c.id
                    ), 0) as total_rental_days
                FROM cars c
                WHERE c.id = ?
            """, (car_id,)).fetchone()
            
            if not car:
                return None
            
            return dict(car)
    
    def generate_asset_report(self, start_date: str = None, end_date: str = None) -> Dict:
        """Generate asset report for specified date range"""
        with self.db.get_connection() as conn:
            if not start_date:
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Get financial metrics
            financials = conn.execute("""
                SELECT 
                    SUM(c.purchase_price) as total_investment,
                    SUM(c.total_maintenance_cost) as total_maintenance,
                    SUM(c.road_tax_amount) as total_road_tax,
                    SUM(c.insurance_amount) as total_insurance,
                    COUNT(*) as total_vehicles
                FROM cars c
            """).fetchone()
            
            # Get rental metrics
            rentals = conn.execute("""
                SELECT 
                    COUNT(*) as total_bookings,
                    SUM(JULIANDAY(end_date) - JULIANDAY(start_date)) as total_rental_days,
                    COUNT(DISTINCT car_id) as cars_rented
                FROM bookings
                WHERE start_date BETWEEN ? AND ?
            """, (start_date, end_date)).fetchone()
            
            # Get maintenance due
            maintenance = conn.execute("""
                SELECT COUNT(*) as due_maintenance
                FROM cars
                WHERE next_maintenance_date <= date('now', '+30 days')
            """).fetchone()
            
            return {
                'period': {'start': start_date, 'end': end_date},
                'financials': dict(financials),
                'rentals': dict(rentals),
                'maintenance': dict(maintenance)
            }
    
    def get_revenue_statistics(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get revenue statistics for all cars"""
        with self.db.get_connection() as conn:
            if not start_date:
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')

            # Overall revenue
            overall = conn.execute("""
                SELECT 
                    COUNT(*) as total_bookings,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as average_booking_value,
                    COUNT(DISTINCT car_id) as cars_rented
                FROM bookings
                WHERE status = 'completed'
                AND end_date BETWEEN ? AND ?
            """, (start_date, end_date)).fetchone()

            # Revenue by car category
            by_category = conn.execute("""
                SELECT 
                    c.category,
                    COUNT(*) as bookings,
                    SUM(b.total_amount) as revenue,
                    AVG(b.total_amount) as avg_revenue
                FROM bookings b
                JOIN cars c ON b.car_id = c.id
                WHERE b.status = 'completed'
                AND b.end_date BETWEEN ? AND ?
                GROUP BY c.category
            """, (start_date, end_date)).fetchall()

            # Top performing cars
            top_cars = conn.execute("""
                SELECT 
                    c.id,
                    c.make,
                    c.model,
                    c.license_plate,
                    c.category,
                    COUNT(*) as total_bookings,
                    SUM(b.total_amount) as total_revenue,
                    AVG(b.total_amount) as avg_revenue_per_booking
                FROM bookings b
                JOIN cars c ON b.car_id = c.id
                WHERE b.status = 'completed'
                AND b.end_date BETWEEN ? AND ?
                GROUP BY c.id
                ORDER BY total_revenue DESC
                LIMIT 5
            """, (start_date, end_date)).fetchall()

            return {
                'period': {'start': start_date, 'end': end_date},
                'overall': dict(overall),
                'by_category': [dict(row) for row in by_category],
                'top_cars': [dict(row) for row in top_cars]
            }

    def get_car_revenue_details(self, car_id: int, start_date: str = None, end_date: str = None) -> Dict:
        """Get detailed revenue information for a specific car"""
        with self.db.get_connection() as conn:
            # First check if the car exists
            car_exists = conn.execute("SELECT id, make, model FROM cars WHERE id = ?", (car_id,)).fetchone()
            if not car_exists:
                return None
                
            if not start_date:
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')

            # Get car details and summary
            car_summary = conn.execute("""
                SELECT 
                    c.*,
                    COALESCE(COUNT(b.id), 0) as total_bookings,
                    COALESCE(SUM(b.total_amount), 0) as total_revenue,
                    COALESCE(AVG(b.total_amount), 0) as avg_revenue_per_booking,
                    COALESCE(SUM(JULIANDAY(b.end_date) - JULIANDAY(b.start_date)), 0) as total_days_rented
                FROM cars c
                LEFT JOIN bookings b ON c.id = b.car_id 
                    AND b.status = 'completed'
                    AND b.end_date BETWEEN ? AND ?
                WHERE c.id = ?
                GROUP BY c.id
            """, (start_date, end_date, car_id)).fetchone()

            car_dict = dict(car_summary) if car_summary else dict(car_exists)
            
            # Ensure all required fields have default values
            car_dict.setdefault('total_bookings', 0)
            car_dict.setdefault('total_revenue', 0)
            car_dict.setdefault('avg_revenue_per_booking', 0)
            car_dict.setdefault('total_days_rented', 0)

            # Get monthly revenue breakdown
            monthly_revenue = conn.execute("""
                SELECT 
                    strftime('%Y-%m', end_date) as month,
                    COUNT(*) as bookings,
                    SUM(total_amount) as revenue,
                    AVG(total_amount) as avg_booking_value
                FROM bookings
                WHERE car_id = ?
                AND status = 'completed'
                AND end_date BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', end_date)
                ORDER BY month DESC
            """, (car_id, start_date, end_date)).fetchall()

            # Calculate ROI and other metrics only if we have the necessary data
            if car_dict.get('purchase_price'):
                total_costs = (float(car_dict.get('purchase_price', 0)) + 
                             float(car_dict.get('total_maintenance_cost', 0)) +
                             float(car_dict.get('insurance_amount', 0)) +
                             float(car_dict.get('road_tax_amount', 0)))
                if total_costs > 0:
                    car_dict['roi'] = ((float(car_dict['total_revenue']) - total_costs) / total_costs) * 100
                else:
                    car_dict['roi'] = 0
                
                if car_dict['total_days_rented'] > 0:
                    car_dict['revenue_per_day'] = car_dict['total_revenue'] / car_dict['total_days_rented']
                else:
                    car_dict['revenue_per_day'] = 0

            return {
                'car_details': car_dict,
                'monthly_revenue': [dict(row) for row in monthly_revenue]
            }

    def get_revenue_alerts(self) -> List[Dict]:
        """Get alerts for cars with below-average revenue performance"""
        with self.db.get_connection() as conn:
            # Calculate average revenue per category
            underperforming = conn.execute("""
                WITH CategoryAverages AS (
                    SELECT 
                        c.category,
                        AVG(b.total_amount) as category_avg_revenue
                    FROM cars c
                    LEFT JOIN bookings b ON c.id = b.car_id
                    WHERE b.status = 'completed'
                    GROUP BY c.category
                )
                SELECT 
                    c.id,
                    c.make,
                    c.model,
                    c.license_plate,
                    c.category,
                    COALESCE(AVG(b.total_amount), 0) as car_avg_revenue,
                    ca.category_avg_revenue,
                    COUNT(b.id) as total_bookings
                FROM cars c
                LEFT JOIN bookings b ON c.id = b.car_id AND b.status = 'completed'
                JOIN CategoryAverages ca ON c.category = ca.category
                GROUP BY c.id
                HAVING car_avg_revenue < ca.category_avg_revenue * 0.8
                OR (total_bookings = 0 AND c.purchase_date <= date('now', '-30 days'))
                ORDER BY (car_avg_revenue / ca.category_avg_revenue) ASC
            """).fetchall()

            return [dict(car) for car in underperforming]