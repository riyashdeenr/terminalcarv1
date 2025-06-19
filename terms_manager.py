from security import SecurityUtils
import os

TERMS_FILE = "terms_and_conditions.enc"
TERMS_TEXT = """
SECURE CAR RENTAL TERMS AND CONDITIONS

1. RENTAL AGREEMENT
This agreement constitutes the entire rental contract between the customer and Secure Car Rental.

2. DRIVER REQUIREMENTS
- Must be at least 21 years of age
- Valid driver's license required
- Clean driving record preferred

3. VEHICLE CONDITION
- Vehicle must be returned in same condition as received
- Interior and exterior cleaning required
- Fuel level must match pickup level

4. SECURITY DEPOSIT
- Required for all rentals
- Refunded upon satisfactory vehicle return
- May be used for damages or violations

5. INSURANCE COVERAGE
- Basic coverage included
- Additional coverage available
- Customer responsible for deductibles

6. PROHIBITED USES
- No smoking in vehicles
- No pets without prior approval
- No off-road driving
- No racing or competitive events

7. CANCELLATION POLICY
- 24-hour advance notice required
- Fees may apply for late cancellations
- Emergency cancellations considered case-by-case

8. LIABILITY
- Customer liable for traffic violations
- Customer liable for parking tickets
- Customer liable for vehicle damage

9. LATE RETURNS
- Grace period: 30 minutes
- Late fees apply after grace period
- Daily rate charged for overnight delays

10. AGREEMENT ACCEPTANCE
By booking a vehicle, customer agrees to all terms and conditions herein.
"""
key = "SecureCarRental2026_RIYASHDEENABDULRAHAMN"

def initialize_terms_file():
    try:
        if not os.path.exists(TERMS_FILE):
            encrypted_terms = SecurityUtils.encrypt_data(TERMS_TEXT, key)
            with open(TERMS_FILE, "w") as f:
                f.write(encrypted_terms)
        print("Terms and conditions file initialized.")
    except Exception as e:
        print(f"Error initializing encrypted terms and conditions: {str(e)}")
        return None

def read_and_decrypt_terms():
    try:
        if not os.path.exists(TERMS_FILE):
            initialize_terms_file()
        with open(TERMS_FILE, "r") as f:
            encrypted_terms = f.read()
        # Decrypt terms using the same key used for encryption
        decrypted_terms = SecurityUtils.decrypt_data(encrypted_terms, key)
        return decrypted_terms
    except FileNotFoundError:
        print("Terms and conditions file not found.")
        return None
    except Exception as e:
        print(f"Error reading or decrypting terms and conditions: {str(e)}")
        return None
