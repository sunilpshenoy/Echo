#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script for Enhanced Marketplace Features (Indian Market)
Tests all new marketplace endpoints with Indian-specific validation
"""

import requests
import json
import time
import base64
import secrets
from datetime import datetime, timedelta
import uuid
import re

# Configuration
BACKEND_URL = "https://9b83238d-a27b-406f-8157-e448fada6ab0.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class IndianMarketplaceTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.users = {}  # Store user data and tokens
        self.test_results = []
        self.listings = {}  # Store created listings
        self.check_ins = {}  # Store safety check-ins
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    def register_test_user(self, username, email, password, phone=None):
        """Register a test user or login if already exists"""
        try:
            # Try to register first
            user_data = {
                "username": username,
                "email": email,
                "password": password,
                "display_name": username
            }
            if phone:
                user_data["phone"] = phone
                
            response = self.session.post(f"{BACKEND_URL}/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                user_info = {
                    "user_id": data["user"]["user_id"],
                    "username": username,
                    "email": email,
                    "phone": phone,
                    "token": data["access_token"]
                }
                self.users[username] = user_info
                return True, user_info
            elif response.status_code == 400 and "already registered" in response.text:
                # User already exists, try to login
                login_response = self.session.post(f"{BACKEND_URL}/login", json={
                    "email": email,
                    "password": password
                })
                
                if login_response.status_code == 200:
                    data = login_response.json()
                    user_info = {
                        "user_id": data["user"]["user_id"],
                        "username": username,
                        "email": email,
                        "phone": phone,
                        "token": data["access_token"]
                    }
                    self.users[username] = user_info
                    return True, user_info
                else:
                    return False, f"Login failed: {login_response.status_code} - {login_response.text}"
            else:
                return False, f"Registration failed: {response.status_code} - {response.text}"
        except Exception as e:
            return False, f"Registration error: {str(e)}"
    
    def get_auth_headers(self, username):
        """Get authorization headers for a user"""
        if username not in self.users:
            return {}
        return {"Authorization": f"Bearer {self.users[username]['token']}"}
    
    def validate_indian_phone(self, phone):
        """Validate Indian phone number format"""
        pattern = r"^\+91[6-9]\d{9}$"
        return re.match(pattern, phone) is not None
    
    def validate_indian_pincode(self, pincode):
        """Validate Indian pincode format"""
        pattern = r"^\d{6}$"
        return re.match(pattern, pincode) is not None
    
    def validate_aadhaar(self, aadhaar):
        """Validate Aadhaar number format"""
        pattern = r"^\d{12}$"
        return re.match(pattern, aadhaar) is not None
    
    def validate_pan(self, pan):
        """Validate PAN number format"""
        pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
        return re.match(pattern, pan) is not None
    
    def test_user_registration(self):
        """Test user registration with Indian phone numbers"""
        print("\n=== Testing User Registration with Indian Phone Numbers ===")
        
        # Register users with Indian phone numbers
        test_users = [
            ("rajesh_mumbai", "rajesh.mumbai@test.com", "password123", "+919876543210"),
            ("priya_delhi", "priya.delhi@test.com", "password123", "+918765432109"),
            ("amit_bangalore", "amit.bangalore@test.com", "password123", "+917654321098"),
            ("seller_verified", "seller.verified@test.com", "password123", "+916543210987")
        ]
        
        for username, email, password, phone in test_users:
            success, result = self.register_test_user(username, email, password, phone)
            phone_valid = self.validate_indian_phone(phone)
            self.log_test(f"Register {username} with Indian phone", success and phone_valid, 
                         f"Phone: {phone}, Valid: {phone_valid}")
        
        return len(self.users) >= 4
    
    def test_phone_verification_system(self):
        """Test Indian phone number verification system"""
        print("\n=== Testing Phone Verification System ===")
        
        if "rajesh_mumbai" not in self.users:
            self.log_test("Phone Verification System", False, "Test user not available")
            return
        
        try:
            headers = self.get_auth_headers("rajesh_mumbai")
            phone = self.users["rajesh_mumbai"]["phone"]
            
            # Test 1: Send OTP to Indian mobile number
            otp_data = {"phone_number": phone}
            response = self.session.post(
                f"{BACKEND_URL}/verification/phone/send-otp",
                json=otp_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "success"
                self.log_test("Send OTP to Indian mobile", success, 
                             f"Phone: {phone}, Response: {data.get('message', '')}")
                
                # Test 2: Verify OTP (using mock OTP for testing)
                verify_data = {
                    "phone_number": phone,
                    "otp": "123456"  # Mock OTP for testing
                }
                verify_response = self.session.post(
                    f"{BACKEND_URL}/verification/phone/verify-otp",
                    json=verify_data,
                    headers=headers
                )
                
                if verify_response.status_code == 200:
                    verify_result = verify_response.json()
                    verify_success = verify_result.get("status") == "success"
                    self.log_test("Verify OTP for Indian mobile", verify_success, 
                                 f"Response: {verify_result.get('message', '')}")
                else:
                    self.log_test("Verify OTP for Indian mobile", False, 
                                 f"HTTP {verify_response.status_code}: {verify_response.text}")
            else:
                self.log_test("Send OTP to Indian mobile", False, 
                             f"HTTP {response.status_code}: {response.text}")
            
            # Test 3: Invalid phone number format
            invalid_phone_data = {"phone_number": "+1234567890"}  # Non-Indian format
            invalid_response = self.session.post(
                f"{BACKEND_URL}/verification/phone/send-otp",
                json=invalid_phone_data,
                headers=headers
            )
            
            invalid_rejected = invalid_response.status_code == 400
            self.log_test("Invalid phone format rejected", invalid_rejected, 
                         f"Non-Indian phone rejected: {invalid_rejected}")
                         
        except Exception as e:
            self.log_test("Phone Verification System", False, f"Error: {str(e)}")
    
    def test_government_id_verification(self):
        """Test Indian government ID verification system"""
        print("\n=== Testing Government ID Verification System ===")
        
        if "priya_delhi" not in self.users:
            self.log_test("Government ID Verification", False, "Test user not available")
            return
        
        try:
            headers = self.get_auth_headers("priya_delhi")
            
            # Test different Indian ID types
            id_tests = [
                {
                    "id_type": "aadhaar",
                    "id_number": "123456789012",
                    "full_name": "Priya Sharma",
                    "date_of_birth": "1990-05-15",
                    "address": "123 MG Road, New Delhi, 110001"
                },
                {
                    "id_type": "pan",
                    "id_number": "ABCDE1234F",
                    "full_name": "Priya Sharma",
                    "date_of_birth": "1990-05-15"
                },
                {
                    "id_type": "voter_id",
                    "id_number": "ABC1234567",
                    "full_name": "Priya Sharma",
                    "date_of_birth": "1990-05-15",
                    "address": "123 MG Road, New Delhi, 110001"
                },
                {
                    "id_type": "passport",
                    "id_number": "A1234567",
                    "full_name": "Priya Sharma",
                    "date_of_birth": "1990-05-15"
                },
                {
                    "id_type": "driving_license",
                    "id_number": "DL1420110012345",
                    "full_name": "Priya Sharma",
                    "date_of_birth": "1990-05-15",
                    "address": "123 MG Road, New Delhi, 110001"
                }
            ]
            
            for id_test in id_tests:
                response = self.session.post(
                    f"{BACKEND_URL}/verification/government-id",
                    json=id_test,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("status") == "success"
                    self.log_test(f"Government ID verification ({id_test['id_type']})", success, 
                                 f"ID: {id_test['id_number']}, Response: {data.get('message', '')}")
                else:
                    self.log_test(f"Government ID verification ({id_test['id_type']})", False, 
                                 f"HTTP {response.status_code}: {response.text}")
            
            # Test invalid ID formats
            invalid_tests = [
                {"id_type": "aadhaar", "id_number": "12345", "full_name": "Test User"},  # Too short
                {"id_type": "pan", "id_number": "INVALID", "full_name": "Test User"},  # Wrong format
            ]
            
            for invalid_test in invalid_tests:
                response = self.session.post(
                    f"{BACKEND_URL}/verification/government-id",
                    json=invalid_test,
                    headers=headers
                )
                
                invalid_rejected = response.status_code == 400
                self.log_test(f"Invalid {invalid_test['id_type']} format rejected", invalid_rejected, 
                             f"ID: {invalid_test['id_number']}")
                             
        except Exception as e:
            self.log_test("Government ID Verification", False, f"Error: {str(e)}")
    
    def test_verification_status(self):
        """Test user verification status endpoint"""
        print("\n=== Testing Verification Status ===")
        
        if "rajesh_mumbai" not in self.users:
            self.log_test("Verification Status", False, "Test user not available")
            return
        
        try:
            headers = self.get_auth_headers("rajesh_mumbai")
            
            response = self.session.get(
                f"{BACKEND_URL}/verification/status",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["phone_verified", "email_verified", "government_id_verified", "verification_level"]
                has_all_fields = all(field in data for field in required_fields)
                
                self.log_test("Verification status retrieval", has_all_fields, 
                             f"Status fields: {list(data.keys())}")
                
                # Check verification levels
                valid_levels = ["basic", "verified", "premium"]
                level_valid = data.get("verification_level") in valid_levels
                self.log_test("Verification level validation", level_valid, 
                             f"Level: {data.get('verification_level')}")
            else:
                self.log_test("Verification status retrieval", False, 
                             f"HTTP {response.status_code}: {response.text}")
                             
        except Exception as e:
            self.log_test("Verification Status", False, f"Error: {str(e)}")
    
    def test_enhanced_marketplace_search(self):
        """Test enhanced marketplace search with Indian location filtering"""
        print("\n=== Testing Enhanced Marketplace Search ===")
        
        if "amit_bangalore" not in self.users:
            self.log_test("Enhanced Marketplace Search", False, "Test user not available")
            return
        
        try:
            headers = self.get_auth_headers("amit_bangalore")
            
            # Create some test listings first
            test_listings = [
                {
                    "title": "iPhone 13 for Sale",
                    "description": "Excellent condition iPhone 13, 128GB, with original box and accessories",
                    "category": "items",
                    "price": 45000,
                    "price_type": "fixed",
                    "location": {
                        "state": "Karnataka",
                        "city": "Bangalore",
                        "pincode": "560001",
                        "latitude": 12.9716,
                        "longitude": 77.5946
                    },
                    "tags": ["smartphone", "apple", "electronics"]
                },
                {
                    "title": "Web Development Services",
                    "description": "Professional web development services for businesses and startups",
                    "category": "services",
                    "price": 2000,
                    "price_type": "hourly",
                    "location": {
                        "state": "Maharashtra",
                        "city": "Mumbai",
                        "pincode": "400001",
                        "latitude": 19.0760,
                        "longitude": 72.8777
                    },
                    "tags": ["web", "development", "programming"]
                }
            ]
            
            # Create listings
            for i, listing_data in enumerate(test_listings):
                response = self.session.post(
                    f"{BACKEND_URL}/marketplace/listings",
                    json=listing_data,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    listing_id = data.get("listing_id")
                    self.listings[f"listing_{i}"] = listing_id
                    self.log_test(f"Create test listing {i+1}", True, f"ID: {listing_id}")
                else:
                    self.log_test(f"Create test listing {i+1}", False, 
                                 f"HTTP {response.status_code}: {response.text}")
            
            # Test enhanced search parameters
            search_tests = [
                {
                    "name": "Search by state",
                    "params": {"state": "Karnataka"}
                },
                {
                    "name": "Search by city",
                    "params": {"city": "Mumbai"}
                },
                {
                    "name": "Search by pincode",
                    "params": {"pincode": "560001"}
                },
                {
                    "name": "Search with verification level",
                    "params": {"verification_level": "verified"}
                },
                {
                    "name": "Search only verified sellers",
                    "params": {"only_verified_sellers": True}
                },
                {
                    "name": "Sort by price low to high",
                    "params": {"sort_by": "price_low"}
                },
                {
                    "name": "Sort by price high to low",
                    "params": {"sort_by": "price_high"}
                },
                {
                    "name": "Sort by date new",
                    "params": {"sort_by": "date_new"}
                },
                {
                    "name": "Sort by relevance",
                    "params": {"sort_by": "relevance", "query": "iPhone"}
                }
            ]
            
            for search_test in search_tests:
                response = self.session.get(
                    f"{BACKEND_URL}/marketplace/listings",
                    params=search_test["params"],
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    listings = data.get("listings", [])
                    self.log_test(search_test["name"], True, 
                                 f"Found {len(listings)} listings")
                else:
                    self.log_test(search_test["name"], False, 
                                 f"HTTP {response.status_code}: {response.text}")
            
            # Test pincode validation
            invalid_pincode_response = self.session.get(
                f"{BACKEND_URL}/marketplace/listings",
                params={"pincode": "12345"},  # Invalid 5-digit pincode
                headers=headers
            )
            
            pincode_validation = invalid_pincode_response.status_code == 400
            self.log_test("Invalid pincode format rejected", pincode_validation, 
                         "5-digit pincode rejected")
                         
        except Exception as e:
            self.log_test("Enhanced Marketplace Search", False, f"Error: {str(e)}")
    
    def test_safety_checkin_system(self):
        """Test safety check-in system for marketplace meetings"""
        print("\n=== Testing Safety Check-in System ===")
        
        if "seller_verified" not in self.users or not self.listings:
            self.log_test("Safety Check-in System", False, "Required data not available")
            return
        
        try:
            headers = self.get_auth_headers("seller_verified")
            listing_id = list(self.listings.values())[0] if self.listings else "test_listing"
            
            # Test 1: Create safety check-in
            checkin_data = {
                "listing_id": listing_id,
                "meeting_location": "Phoenix MarketCity, Bangalore",
                "meeting_time": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
                "contact_phone": "+919876543210",
                "emergency_contact_name": "Rahul Sharma",
                "emergency_contact_phone": "+918765432109"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/safety/check-in",
                json=checkin_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                checkin_id = data.get("checkin_id")
                self.check_ins["test_checkin"] = checkin_id
                self.log_test("Create safety check-in", True, f"Check-in ID: {checkin_id}")
                
                # Test 2: Update check-in status
                status_update = {"status": "met"}
                update_response = self.session.put(
                    f"{BACKEND_URL}/safety/check-in/{checkin_id}/status",
                    json=status_update,
                    headers=headers
                )
                
                if update_response.status_code == 200:
                    update_data = update_response.json()
                    self.log_test("Update check-in status", True, 
                                 f"Status updated to: {status_update['status']}")
                else:
                    self.log_test("Update check-in status", False, 
                                 f"HTTP {update_response.status_code}: {update_response.text}")
                
                # Test 3: Emergency status
                emergency_update = {"status": "emergency"}
                emergency_response = self.session.put(
                    f"{BACKEND_URL}/safety/check-in/{checkin_id}/status",
                    json=emergency_update,
                    headers=headers
                )
                
                emergency_handled = emergency_response.status_code == 200
                self.log_test("Emergency status handling", emergency_handled, 
                             "Emergency status update processed")
                
            else:
                self.log_test("Create safety check-in", False, 
                             f"HTTP {response.status_code}: {response.text}")
            
            # Test 4: Get user's check-ins
            checkins_response = self.session.get(
                f"{BACKEND_URL}/safety/check-ins",
                headers=headers
            )
            
            if checkins_response.status_code == 200:
                checkins_data = checkins_response.json()
                checkins = checkins_data.get("check_ins", [])
                self.log_test("Retrieve user check-ins", True, 
                             f"Found {len(checkins)} check-ins")
            else:
                self.log_test("Retrieve user check-ins", False, 
                             f"HTTP {checkins_response.status_code}: {checkins_response.text}")
            
            # Test 5: Invalid phone number format
            invalid_checkin = {
                "listing_id": listing_id,
                "meeting_location": "Test Location",
                "meeting_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "contact_phone": "+1234567890"  # Non-Indian format
            }
            
            invalid_response = self.session.post(
                f"{BACKEND_URL}/safety/check-in",
                json=invalid_checkin,
                headers=headers
            )
            
            phone_validation = invalid_response.status_code == 400
            self.log_test("Invalid phone format in check-in rejected", phone_validation, 
                         "Non-Indian phone format rejected")
                         
        except Exception as e:
            self.log_test("Safety Check-in System", False, f"Error: {str(e)}")
    
    def test_analytics_dashboard(self):
        """Test analytics dashboard endpoints"""
        print("\n=== Testing Analytics Dashboard ===")
        
        if "amit_bangalore" not in self.users:
            self.log_test("Analytics Dashboard", False, "Test user not available")
            return
        
        try:
            headers = self.get_auth_headers("amit_bangalore")
            
            # Test 1: User's marketplace analytics
            response = self.session.get(
                f"{BACKEND_URL}/analytics/dashboard",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_listings", "active_listings", "total_views", "total_inquiries"]
                has_required_fields = all(field in data for field in required_fields)
                
                self.log_test("User marketplace analytics", has_required_fields, 
                             f"Analytics fields: {list(data.keys())}")
            else:
                self.log_test("User marketplace analytics", False, 
                             f"HTTP {response.status_code}: {response.text}")
            
            # Test 2: Overall marketplace statistics
            stats_response = self.session.get(
                f"{BACKEND_URL}/analytics/marketplace-stats",
                headers=headers
            )
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                stats_fields = ["total_listings", "total_users", "categories_breakdown", "location_breakdown"]
                has_stats_fields = all(field in stats_data for field in stats_fields)
                
                self.log_test("Overall marketplace statistics", has_stats_fields, 
                             f"Stats fields: {list(stats_data.keys())}")
            else:
                self.log_test("Overall marketplace statistics", False, 
                             f"HTTP {stats_response.status_code}: {stats_response.text}")
            
            # Test 3: Specific listing analytics
            if self.listings:
                listing_id = list(self.listings.values())[0]
                listing_response = self.session.get(
                    f"{BACKEND_URL}/analytics/listing/{listing_id}",
                    headers=headers
                )
                
                if listing_response.status_code == 200:
                    listing_data = listing_response.json()
                    listing_fields = ["listing_id", "views", "inquiries", "performance_metrics"]
                    has_listing_fields = all(field in listing_data for field in listing_fields)
                    
                    self.log_test("Specific listing analytics", has_listing_fields, 
                                 f"Listing analytics fields: {list(listing_data.keys())}")
                else:
                    self.log_test("Specific listing analytics", False, 
                                 f"HTTP {listing_response.status_code}: {listing_response.text}")
            else:
                self.log_test("Specific listing analytics", False, "No listings available for testing")
                
        except Exception as e:
            self.log_test("Analytics Dashboard", False, f"Error: {str(e)}")
    
    def test_data_validation(self):
        """Test Indian-specific data validation"""
        print("\n=== Testing Indian Data Validation ===")
        
        # Test phone number validation
        phone_tests = [
            ("+919876543210", True),   # Valid
            ("+918765432109", True),   # Valid
            ("+917654321098", True),   # Valid
            ("+916543210987", True),   # Valid
            ("+915432109876", False),  # Invalid (starts with 5)
            ("+91987654321", False),   # Invalid (too short)
            ("+9198765432100", False), # Invalid (too long)
            ("+1234567890", False),    # Invalid (non-Indian)
        ]
        
        for phone, expected in phone_tests:
            result = self.validate_indian_phone(phone)
            self.log_test(f"Phone validation: {phone}", result == expected, 
                         f"Expected: {expected}, Got: {result}")
        
        # Test pincode validation
        pincode_tests = [
            ("560001", True),   # Valid
            ("400001", True),   # Valid
            ("110001", True),   # Valid
            ("12345", False),   # Invalid (5 digits)
            ("1234567", False), # Invalid (7 digits)
            ("ABCDEF", False),  # Invalid (letters)
        ]
        
        for pincode, expected in pincode_tests:
            result = self.validate_indian_pincode(pincode)
            self.log_test(f"Pincode validation: {pincode}", result == expected, 
                         f"Expected: {expected}, Got: {result}")
        
        # Test Aadhaar validation
        aadhaar_tests = [
            ("123456789012", True),   # Valid
            ("987654321098", True),   # Valid
            ("12345678901", False),   # Invalid (11 digits)
            ("1234567890123", False), # Invalid (13 digits)
            ("ABCDEFGHIJKL", False),  # Invalid (letters)
        ]
        
        for aadhaar, expected in aadhaar_tests:
            result = self.validate_aadhaar(aadhaar)
            self.log_test(f"Aadhaar validation: {aadhaar}", result == expected, 
                         f"Expected: {expected}, Got: {result}")
        
        # Test PAN validation
        pan_tests = [
            ("ABCDE1234F", True),   # Valid
            ("XYZAB5678C", True),   # Valid
            ("ABCDE123F", False),   # Invalid (missing digit)
            ("ABCD1234F", False),   # Invalid (missing letter)
            ("abcde1234f", False),  # Invalid (lowercase)
        ]
        
        for pan, expected in pan_tests:
            result = self.validate_pan(pan)
            self.log_test(f"PAN validation: {pan}", result == expected, 
                         f"Expected: {expected}, Got: {result}")
    
    def test_rate_limiting(self):
        """Test rate limiting on verification endpoints"""
        print("\n=== Testing Rate Limiting ===")
        
        if "rajesh_mumbai" not in self.users:
            self.log_test("Rate Limiting", False, "Test user not available")
            return
        
        try:
            headers = self.get_auth_headers("rajesh_mumbai")
            phone = self.users["rajesh_mumbai"]["phone"]
            
            # Send multiple OTP requests rapidly
            rate_limit_hit = False
            for i in range(10):  # Try 10 requests
                response = self.session.post(
                    f"{BACKEND_URL}/verification/phone/send-otp",
                    json={"phone_number": phone},
                    headers=headers
                )
                
                if response.status_code == 429:  # Too Many Requests
                    rate_limit_hit = True
                    break
                
                time.sleep(0.1)  # Small delay between requests
            
            self.log_test("Rate limiting on OTP endpoint", rate_limit_hit, 
                         "Rate limiting activated after multiple requests")
                         
        except Exception as e:
            self.log_test("Rate Limiting", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all Indian marketplace tests"""
        print("🇮🇳 Starting Enhanced Marketplace Features Testing (Indian Market)")
        print("=" * 70)
        
        # Test sequence
        if not self.test_user_registration():
            print("❌ User registration failed - cannot continue with marketplace tests")
            return
        
        # Core marketplace tests
        self.test_phone_verification_system()
        self.test_government_id_verification()
        self.test_verification_status()
        self.test_enhanced_marketplace_search()
        self.test_safety_checkin_system()
        self.test_analytics_dashboard()
        
        # Validation and security tests
        self.test_data_validation()
        self.test_rate_limiting()
        
        # Summary
        print("\n" + "=" * 70)
        print("🇮🇳 INDIAN MARKETPLACE TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🇮🇳 Indian Marketplace Testing Complete!")
        return passed == total

if __name__ == "__main__":
    tester = IndianMarketplaceTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)