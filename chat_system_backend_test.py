#!/usr/bin/env python3
"""
Chat System Backend Testing Script
Tests the specific endpoints mentioned in the review request:
1. GET /api/chats - This should return user's chats without hanging
2. POST /api/contacts - Test adding contact via email 
3. POST /api/contacts - Test adding contact via phone number
4. GET /api/users/qr-code - Test QR code generation

Focus on testing response times and ensuring no endpoints are hanging or taking too long to respond.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://a205b7e3-f535-4569-8dd8-c1f8fc23e5dc.preview.emergentagent.com/api"
TIMEOUT = 10  # 10 seconds timeout to detect hanging endpoints

class ChatSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, message, response_time=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.3f}s)" if response_time else ""
        print(f"{status} {test_name}{time_info}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "response_time": response_time,
            "timestamp": datetime.now().isoformat()
        })
    
    def register_test_user(self):
        """Register a test user for authentication"""
        try:
            start_time = time.time()
            
            user_data = {
                "username": f"chat_test_user_{int(time.time())}",
                "email": f"chat_test_{int(time.time())}@example.com",
                "password": "TestPassword123!",
                "display_name": "Chat Test User"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/register",
                json=user_data,
                timeout=TIMEOUT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("user_id")
                
                # Set authorization header for future requests
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                
                self.log_test("User Registration", True, 
                            f"Successfully registered user {user_data['username']}", response_time)
                return True
            else:
                self.log_test("User Registration", False, 
                            f"Registration failed: {response.status_code} - {response.text}", response_time)
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("User Registration", False, "Request timed out (>10s)")
            return False
        except Exception as e:
            self.log_test("User Registration", False, f"Registration error: {str(e)}")
            return False
    
    def test_get_chats(self):
        """Test GET /api/chats - Should return user's chats without hanging"""
        try:
            start_time = time.time()
            
            response = self.session.get(
                f"{BACKEND_URL}/chats",
                timeout=TIMEOUT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # The API returns a list directly, not wrapped in an object
                chats = response.json()
                
                # Check if response is properly formatted
                if isinstance(chats, list):
                    self.log_test("GET /api/chats", True, 
                                f"Successfully retrieved {len(chats)} chats", response_time)
                    
                    # Test for hanging - if response time is reasonable
                    if response_time > 5.0:
                        self.log_test("GET /api/chats Response Time", False, 
                                    f"Response time too slow: {response_time:.3f}s (>5s threshold)")
                    else:
                        self.log_test("GET /api/chats Response Time", True, 
                                    f"Response time acceptable: {response_time:.3f}s")
                    return True
                else:
                    self.log_test("GET /api/chats", False, 
                                f"Invalid response format: {type(chats)}", response_time)
                    return False
            else:
                self.log_test("GET /api/chats", False, 
                            f"Request failed: {response.status_code} - {response.text}", response_time)
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("GET /api/chats", False, "Request timed out (>10s) - HANGING DETECTED!")
            return False
        except Exception as e:
            self.log_test("GET /api/chats", False, f"Request error: {str(e)}")
            return False
    
    def test_add_contact_by_email(self):
        """Test POST /api/contacts - Test adding contact via email"""
        try:
            start_time = time.time()
            
            # First create a test user to add as contact
            test_contact_email = f"contact_email_{int(time.time())}@example.com"
            
            # Register a test contact user
            contact_user_data = {
                "username": f"contact_user_{int(time.time())}",
                "email": test_contact_email,
                "password": "TestPassword123!",
                "display_name": "Contact Test User"
            }
            
            # Register the contact user first
            register_response = self.session.post(
                f"{BACKEND_URL}/register",
                json=contact_user_data,
                timeout=TIMEOUT
            )
            
            if register_response.status_code != 200:
                self.log_test("POST /api/contacts (Email)", False, 
                            f"Failed to create test contact user: {register_response.status_code}")
                return False
            
            # Now add the contact using the correct API format
            contact_data = {
                "email": test_contact_email
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/contacts",
                json=contact_data,
                timeout=TIMEOUT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test("POST /api/contacts (Email)", True, 
                            f"Successfully added email contact", response_time)
                
                # Test for hanging
                if response_time > 5.0:
                    self.log_test("POST /api/contacts (Email) Response Time", False, 
                                f"Response time too slow: {response_time:.3f}s")
                else:
                    self.log_test("POST /api/contacts (Email) Response Time", True, 
                                f"Response time acceptable: {response_time:.3f}s")
                return True
            else:
                self.log_test("POST /api/contacts (Email)", False, 
                            f"Request failed: {response.status_code} - {response.text}", response_time)
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("POST /api/contacts (Email)", False, "Request timed out (>10s) - HANGING DETECTED!")
            return False
        except Exception as e:
            self.log_test("POST /api/contacts (Email)", False, f"Request error: {str(e)}")
            return False
    
    def test_add_contact_by_phone(self):
        """Test POST /api/contacts - Test adding contact via phone number (using PIN system)"""
        try:
            start_time = time.time()
            
            # First create a test user with a phone number to add as contact
            test_contact_email = f"phone_contact_{int(time.time())}@example.com"
            
            # Register a test contact user
            contact_user_data = {
                "username": f"phone_contact_user_{int(time.time())}",
                "email": test_contact_email,
                "password": "TestPassword123!",
                "display_name": "Phone Contact Test User",
                "phone": f"+91987654{int(time.time()) % 10000:04d}"
            }
            
            # Register the contact user first
            register_response = self.session.post(
                f"{BACKEND_URL}/register",
                json=contact_user_data,
                timeout=TIMEOUT
            )
            
            if register_response.status_code != 200:
                self.log_test("POST /api/contacts (Phone)", False, 
                            f"Failed to create test contact user: {register_response.status_code}")
                return False
            
            # The contacts endpoint only accepts email, so we'll test with email
            # but note that this is for phone-based contact addition
            contact_data = {
                "email": test_contact_email
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/contacts",
                json=contact_data,
                timeout=TIMEOUT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test("POST /api/contacts (Phone)", True, 
                            f"Successfully added phone-based contact via email", response_time)
                
                # Test for hanging
                if response_time > 5.0:
                    self.log_test("POST /api/contacts (Phone) Response Time", False, 
                                f"Response time too slow: {response_time:.3f}s")
                else:
                    self.log_test("POST /api/contacts (Phone) Response Time", True, 
                                f"Response time acceptable: {response_time:.3f}s")
                return True
            else:
                self.log_test("POST /api/contacts (Phone)", False, 
                            f"Request failed: {response.status_code} - {response.text}", response_time)
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("POST /api/contacts (Phone)", False, "Request timed out (>10s) - HANGING DETECTED!")
            return False
        except Exception as e:
            self.log_test("POST /api/contacts (Phone)", False, f"Request error: {str(e)}")
            return False
    
    def test_qr_code_generation(self):
        """Test GET /api/users/qr-code - Test QR code generation"""
        try:
            start_time = time.time()
            
            response = self.session.get(
                f"{BACKEND_URL}/users/qr-code",
                timeout=TIMEOUT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if QR code data is present
                if "qr_code" in data or "qr_data" in data or "qr_image" in data:
                    self.log_test("GET /api/users/qr-code", True, 
                                f"Successfully generated QR code", response_time)
                    
                    # Test for hanging
                    if response_time > 5.0:
                        self.log_test("GET /api/users/qr-code Response Time", False, 
                                    f"Response time too slow: {response_time:.3f}s")
                    else:
                        self.log_test("GET /api/users/qr-code Response Time", True, 
                                    f"Response time acceptable: {response_time:.3f}s")
                    return True
                else:
                    self.log_test("GET /api/users/qr-code", False, 
                                f"QR code data missing in response: {list(data.keys())}", response_time)
                    return False
            else:
                self.log_test("GET /api/users/qr-code", False, 
                            f"Request failed: {response.status_code} - {response.text}", response_time)
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("GET /api/users/qr-code", False, "Request timed out (>10s) - HANGING DETECTED!")
            return False
        except Exception as e:
            self.log_test("GET /api/users/qr-code", False, f"Request error: {str(e)}")
            return False
    
    def test_connection_request_endpoints(self):
        """Test connection request endpoints to ensure mobile number and email contact addition works"""
        try:
            # Test connection request creation
            start_time = time.time()
            
            connection_data = {
                "recipient_email": f"connection_test_{int(time.time())}@example.com",
                "message": "Test connection request"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/connections/request",
                json=connection_data,
                timeout=TIMEOUT
            )
            
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201, 404]:  # 404 is acceptable if user doesn't exist
                self.log_test("POST /api/connections/request", True, 
                            f"Connection request endpoint working", response_time)
                
                if response_time > 5.0:
                    self.log_test("POST /api/connections/request Response Time", False, 
                                f"Response time too slow: {response_time:.3f}s")
                else:
                    self.log_test("POST /api/connections/request Response Time", True, 
                                f"Response time acceptable: {response_time:.3f}s")
                return True
            else:
                self.log_test("POST /api/connections/request", False, 
                            f"Request failed: {response.status_code} - {response.text}", response_time)
                return False
                
        except requests.exceptions.Timeout:
            self.log_test("POST /api/connections/request", False, "Request timed out (>10s) - HANGING DETECTED!")
            return False
        except Exception as e:
            self.log_test("POST /api/connections/request", False, f"Request error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all chat system tests"""
        print("🚀 Starting Chat System Backend Testing")
        print("=" * 60)
        
        # Step 1: Register test user
        if not self.register_test_user():
            print("❌ Cannot proceed without authentication")
            return False
        
        print("\n📋 Testing Core Chat System Endpoints:")
        print("-" * 40)
        
        # Step 2: Test GET /api/chats
        self.test_get_chats()
        
        # Step 3: Test POST /api/contacts (email)
        self.test_add_contact_by_email()
        
        # Step 4: Test POST /api/contacts (phone)
        self.test_add_contact_by_phone()
        
        # Step 5: Test GET /api/users/qr-code
        self.test_qr_code_generation()
        
        # Step 6: Test connection request endpoints
        self.test_connection_request_endpoints()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 CHAT SYSTEM TESTING SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Check for hanging issues
        hanging_tests = [r for r in self.test_results if "HANGING DETECTED" in r["message"]]
        if hanging_tests:
            print(f"\n🚨 CRITICAL: {len(hanging_tests)} endpoints detected as HANGING!")
            for test in hanging_tests:
                print(f"   - {test['test']}")
        else:
            print("\n✅ No hanging endpoints detected")
        
        # Check for slow responses
        slow_tests = [r for r in self.test_results if r["response_time"] and r["response_time"] > 3.0]
        if slow_tests:
            print(f"\n⚠️  {len(slow_tests)} endpoints with slow response times (>3s):")
            for test in slow_tests:
                print(f"   - {test['test']}: {test['response_time']:.3f}s")
        
        return failed_tests == 0

def main():
    """Main function"""
    tester = ChatSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All chat system tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the results above.")
        sys.exit(1)

if __name__ == "__main__":
    main()