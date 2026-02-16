#!/usr/bin/env python3
"""
Synthetic Credential Generator for Honeypot Agent

This script generates realistic but fake Indian financial credentials
for use during honeypot operations. All generated data is synthetic
and does not correspond to real accounts.

SECURITY NOTE: This script generates FAKE data only. Never use real credentials.
"""

import random
import string
from datetime import datetime, timedelta


class SyntheticCredentialGenerator:
    """Generate believable fake credentials for honeypot operations"""
    
    # Real Indian bank names for authenticity
    BANKS = [
        'sbi', 'hdfc', 'icici', 'axis', 'kotak', 'pnb', 
        'bob', 'canara', 'union', 'indusind', 'yes', 'idbi'
    ]
    
    # UPI providers
    UPI_PROVIDERS = ['paytm', 'phonepe', 'googlepay', 'amazonpay', 'mobikwik']
    
    # Common Indian first names
    FIRST_NAMES = [
        'Ramesh', 'Suresh', 'Rajesh', 'Amit', 'Vijay', 'Anil',
        'Savita', 'Priya', 'Sunita', 'Anjali', 'Kavita', 'Rekha',
        'Arjun', 'Rohan', 'Karan', 'Varun', 'Lakshmi', 'Deepak'
    ]
    
    # Common Indian last names
    LAST_NAMES = [
        'Kumar', 'Sharma', 'Verma', 'Singh', 'Patel', 'Gupta',
        'Reddy', 'Rao', 'Nair', 'Iyer', 'Desai', 'Mehta',
        'Shah', 'Joshi', 'Agarwal', 'Pillai'
    ]
    
    # Indian cities for addresses
    CITIES = [
        'Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai',
        'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow',
        'Indore', 'Nashik', 'Vadodara', 'Coimbatore', 'Nagpur'
    ]
    
    def __init__(self, seed=None):
        """Initialize generator with optional seed for reproducibility"""
        if seed:
            random.seed(seed)
    
    def generate_bank_account(self):
        """
        Generate synthetic bank account number
        Format: 4-digit bank code + 10 random digits
        Returns: dict with account number and bank name
        """
        bank = random.choice(self.BANKS)
        # Bank codes typically 3000-9999 range
        bank_code = random.randint(3000, 9999)
        # Account number: 10 digits
        account_digits = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        
        return {
            'account_number': f"{bank_code}{account_digits}",
            'bank_name': bank.upper(),
            'bank_code': str(bank_code)
        }
    
    def generate_ifsc_code(self, bank=None):
        """
        Generate synthetic IFSC code
        Format: BANK0001234
        Returns: IFSC code string
        """
        if not bank:
            bank = random.choice(self.BANKS)
        
        # IFSC codes are 11 characters: 4 bank + 0 + 6 branch
        bank_code = bank[:4].upper().ljust(4, 'X')
        branch_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        return f"{bank_code}0{branch_code}"
    
    def generate_upi_id(self):
        """
        Generate synthetic UPI ID
        Format: firstname.lastname@provider
        Returns: dict with UPI ID and name
        """
        first_name = random.choice(self.FIRST_NAMES).lower()
        last_name = random.choice(self.LAST_NAMES).lower()
        provider = random.choice(self.UPI_PROVIDERS)
        
        # Sometimes use just first name
        if random.random() > 0.3:
            upi_id = f"{first_name}.{last_name}@{provider}"
            full_name = f"{first_name.title()} {last_name.title()}"
        else:
            upi_id = f"{first_name}@{provider}"
            full_name = first_name.title()
        
        return {
            'upi_id': upi_id,
            'name': full_name,
            'provider': provider
        }
    
    def generate_mobile_number(self):
        """
        Generate synthetic Indian mobile number
        Format: +91-XXXXXXXXXX (starts with 6-9)
        Returns: mobile number string
        """
        # Indian mobile numbers start with 6, 7, 8, or 9
        first_digit = random.choice(['6', '7', '8', '9'])
        remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        
        return f"+91-{first_digit}{remaining_digits}"
    
    def generate_aadhaar_number(self):
        """
        Generate synthetic Aadhaar number
        Format: XXXX XXXX XXXX (12 digits)
        Note: Starts with 2-3 to avoid real number ranges
        Returns: Aadhaar number string
        """
        # Start with 2 or 3 to avoid real Aadhaar ranges
        first_digit = random.choice(['2', '3'])
        remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(11)])
        
        full_number = first_digit + remaining_digits
        # Format as XXXX XXXX XXXX
        formatted = f"{full_number[0:4]} {full_number[4:8]} {full_number[8:12]}"
        
        return formatted
    
    def generate_pan_number(self):
        """
        Generate synthetic PAN number
        Format: ABCDE1234F
        Returns: PAN number string
        """
        # PAN format: 3 letters (random) + 1 letter (P for person) + 1 letter (first name) + 4 digits + 1 letter
        random_letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        entity_type = 'P'  # Person
        first_name_initial = random.choice(string.ascii_uppercase)
        digits = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        check_letter = random.choice(string.ascii_uppercase)
        
        return f"{random_letters}{entity_type}{first_name_initial}{digits}{check_letter}"
    
    def generate_otp(self, length=6):
        """
        Generate synthetic OTP
        Args:
            length: OTP length (default 6)
        Returns: OTP string
        """
        return ''.join([str(random.randint(0, 9)) for _ in range(length)])
    
    def generate_balance_amount(self, persona_type='shop_owner'):
        """
        Generate realistic account balance based on persona
        Args:
            persona_type: Type of persona (shop_owner, student, elderly, homemaker)
        Returns: Balance amount in rupees
        """
        ranges = {
            'shop_owner': (12000, 250000),
            'student': (500, 15000),
            'elderly': (25000, 180000),  # Pension accounts
            'homemaker': (8000, 85000)
        }
        
        min_amt, max_amt = ranges.get(persona_type, (5000, 100000))
        # Generate amount with realistic variation (not perfectly round)
        base_amount = random.randint(min_amt, max_amt)
        variation = random.randint(-999, 999)
        
        return max(0, base_amount + variation)
    
    def generate_transaction_id(self):
        """
        Generate synthetic transaction/reference ID
        Format: Various formats used by Indian banks
        Returns: Transaction ID string
        """
        formats = [
            # Format 1: YYYYMMDDXXXXXX (date + random)
            lambda: datetime.now().strftime('%Y%m%d') + ''.join([str(random.randint(0, 9)) for _ in range(6)]),
            # Format 2: TXNXXXXXXXXXX (12 digits)
            lambda: 'TXN' + ''.join([str(random.randint(0, 9)) for _ in range(12)]),
            # Format 3: UPIXXXXXXXXXXXXXX (16 chars)
            lambda: 'UPI' + ''.join(random.choices(string.digits + string.ascii_uppercase, k=13)),
        ]
        
        return random.choice(formats)()
    
    def generate_address(self):
        """
        Generate synthetic Indian address
        Returns: dict with address components
        """
        house_no = random.randint(1, 999)
        street_types = ['Street', 'Road', 'Nagar', 'Colony', 'Layout']
        street_name = random.choice(['MG', 'Gandhi', 'Station', 'Main', 'Park', 'Market'])
        street_type = random.choice(street_types)
        city = random.choice(self.CITIES)
        pincode = random.randint(400001, 799999)  # Indian pincode range
        
        return {
            'line1': f"{house_no}, {street_name} {street_type}",
            'city': city,
            'state': self._get_state_for_city(city),
            'pincode': str(pincode)
        }
    
    def _get_state_for_city(self, city):
        """Map city to state (simplified)"""
        city_state_map = {
            'Mumbai': 'Maharashtra', 'Pune': 'Maharashtra', 'Nashik': 'Maharashtra', 'Nagpur': 'Maharashtra',
            'Delhi': 'Delhi', 'Bangalore': 'Karnataka', 'Hyderabad': 'Telangana',
            'Chennai': 'Tamil Nadu', 'Coimbatore': 'Tamil Nadu', 'Kolkata': 'West Bengal',
            'Ahmedabad': 'Gujarat', 'Vadodara': 'Gujarat', 'Jaipur': 'Rajasthan',
            'Lucknow': 'Uttar Pradesh', 'Indore': 'Madhya Pradesh'
        }
        return city_state_map.get(city, 'India')
    
    def generate_full_profile(self, persona_type='shop_owner'):
        """
        Generate complete synthetic profile for honeypot persona
        Args:
            persona_type: Type of persona
        Returns: Complete profile dict
        """
        first_name = random.choice(self.FIRST_NAMES)
        last_name = random.choice(self.LAST_NAMES)
        
        account = self.generate_bank_account()
        upi = self.generate_upi_id()
        address = self.generate_address()
        
        profile = {
            'personal': {
                'first_name': first_name,
                'last_name': last_name,
                'full_name': f"{first_name} {last_name}",
                'mobile': self.generate_mobile_number(),
                'aadhaar': self.generate_aadhaar_number(),
                'pan': self.generate_pan_number(),
            },
            'banking': {
                'account_number': account['account_number'],
                'bank_name': account['bank_name'],
                'ifsc_code': self.generate_ifsc_code(account['bank_name'].lower()),
                'balance': self.generate_balance_amount(persona_type),
            },
            'upi': {
                'primary_id': upi['upi_id'],
                'provider': upi['provider'],
            },
            'address': address,
            'generated_at': datetime.now().isoformat(),
            'persona_type': persona_type
        }
        
        return profile


# CLI Usage
if __name__ == "__main__":
    import json
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate synthetic credentials for honeypot')
    parser.add_argument('--type', choices=['account', 'upi', 'otp', 'profile', 'all'], 
                       default='profile', help='Type of credential to generate')
    parser.add_argument('--persona', choices=['shop_owner', 'student', 'elderly', 'homemaker'],
                       default='shop_owner', help='Persona type for profile generation')
    parser.add_argument('--count', type=int, default=1, help='Number of credentials to generate')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    generator = SyntheticCredentialGenerator(seed=args.seed)
    
    results = []
    for _ in range(args.count):
        if args.type == 'account':
            results.append(generator.generate_bank_account())
        elif args.type == 'upi':
            results.append(generator.generate_upi_id())
        elif args.type == 'otp':
            results.append({'otp': generator.generate_otp()})
        elif args.type == 'profile':
            results.append(generator.generate_full_profile(args.persona))
        elif args.type == 'all':
            results.append({
                'bank_account': generator.generate_bank_account(),
                'upi': generator.generate_upi_id(),
                'mobile': generator.generate_mobile_number(),
                'aadhaar': generator.generate_aadhaar_number(),
                'pan': generator.generate_pan_number(),
                'otp': generator.generate_otp(),
                'balance': generator.generate_balance_amount(args.persona)
            })
    
    # Pretty print JSON
    print(json.dumps(results if args.count > 1 else results[0], indent=2))
