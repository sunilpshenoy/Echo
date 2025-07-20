#!/usr/bin/env python3
"""
FOCUSED CHATS ENDPOINT TESTING SCRIPT
Tests the specific GET /api/chats endpoint that is causing loading issues in the frontend
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://a205b7e3-f535-4569-8dd8-c1f8fc23e5dc.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class ChatsEndpointTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.test_results = []
        self.auth_token = None
        
    def log_test(self, test_name, success, details="", response_time=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.3f}s)" if response_time else ""
        print(f"{status}: {test_name}{time_info}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time
        })
    
    def register_test_user(self):
        """Register a test user for authentication"""
        try:
            user_data = {
                "username": f"chats_test_user_{int(time.time())}",
                "email": f"chats_test_{int(time.time())}@example.com",
                "password": "testpassword123",
                "display_name": "Chats Test User"
            }
            
            start_time = time.time()
            response = self.session.post(f"{BACKEND_URL}/register", json=user_data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_test("User Registration", True, f"User registered successfully", response_time)
                return True
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_chats_endpoint_basic(self):
        """Test basic GET /api/chats endpoint functionality"""
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/chats")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("GET /api/chats - Basic Request", True, 
                             f"Status: 200, Response type: {type(data)}, Length: {len(data) if isinstance(data, list) else 'N/A'}", 
                             response_time)
                return data
            else:
                self.log_test("GET /api/chats - Basic Request", False, 
                             f"Status: {response.status_code}, Response: {response.text}", 
                             response_time)
                return None
                
        except requests.exceptions.Timeout:
            self.log_test("GET /api/chats - Basic Request", False, "Request timed out after 30 seconds")
            return None
        except Exception as e:
            self.log_test("GET /api/chats - Basic Request", False, f"Exception: {str(e)}")
            return None
    
    def test_chats_endpoint_response_format(self, chats_data):
        """Test the response format of GET /api/chats endpoint"""
        try:
            if chats_data is None:
                self.log_test("GET /api/chats - Response Format", False, "No data to validate")
                return False
            
            # Check if response is a list
            if not isinstance(chats_data, list):
                self.log_test("GET /api/chats - Response Format", False, f"Expected list, got {type(chats_data)}")
                return False
            
            # If there are chats, validate the structure
            if len(chats_data) > 0:
                chat = chats_data[0]
                required_fields = ['chat_id', 'chat_type', 'members']
                missing_fields = [field for field in required_fields if field not in chat]
                
                if missing_fields:
                    self.log_test("GET /api/chats - Response Format", False, f"Missing required fields: {missing_fields}")
                    return False
                else:
                    self.log_test("GET /api/chats - Response Format", True, f"Valid chat structure with {len(chats_data)} chats")
                    return True
            else:
                self.log_test("GET /api/chats - Response Format", True, "Empty chats list (valid for new user)")
                return True
                
        except Exception as e:
            self.log_test("GET /api/chats - Response Format", False, f"Exception: {str(e)}")
            return False
    
    def test_chats_endpoint_performance(self):
        """Test performance and timeout issues of GET /api/chats endpoint"""
        try:
            # Test multiple requests to check for consistency
            response_times = []
            
            for i in range(3):
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/chats")
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code != 200:
                    self.log_test(f"GET /api/chats - Performance Test {i+1}", False, 
                                 f"Status: {response.status_code}")
                    return False
                
                time.sleep(0.5)  # Small delay between requests
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Check if any request took too long (potential timeout issue)
            if max_response_time > 10:
                self.log_test("GET /api/chats - Performance Test", False, 
                             f"Slow response detected. Max: {max_response_time:.3f}s, Avg: {avg_response_time:.3f}s")
                return False
            else:
                self.log_test("GET /api/chats - Performance Test", True, 
                             f"Consistent performance. Max: {max_response_time:.3f}s, Avg: {avg_response_time:.3f}s")
                return True
                
        except Exception as e:
            self.log_test("GET /api/chats - Performance Test", False, f"Exception: {str(e)}")
            return False
    
    def test_chats_endpoint_with_data(self):
        """Test GET /api/chats endpoint after creating some test data"""
        try:
            # First, create a test chat to ensure we have data
            chat_data = {
                "chat_type": "direct",
                "members": [f"test_user_{int(time.time())}@example.com"]
            }
            
            start_time = time.time()
            create_response = self.session.post(f"{BACKEND_URL}/chats", json=chat_data)
            create_time = time.time() - start_time
            
            if create_response.status_code in [200, 201]:
                self.log_test("Create Test Chat", True, f"Chat created successfully", create_time)
                
                # Now test GET /api/chats with actual data
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/chats")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        self.log_test("GET /api/chats - With Data", True, 
                                     f"Retrieved {len(data)} chats successfully", response_time)
                        return True
                    else:
                        self.log_test("GET /api/chats - With Data", False, 
                                     f"Expected chats but got empty response", response_time)
                        return False
                else:
                    self.log_test("GET /api/chats - With Data", False, 
                                 f"Status: {response.status_code}, Response: {response.text}", response_time)
                    return False
            else:
                self.log_test("Create Test Chat", False, 
                             f"Failed to create test chat. Status: {create_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("GET /api/chats - With Data", False, f"Exception: {str(e)}")
            return False
    
    def test_chats_endpoint_authentication(self):
        """Test GET /api/chats endpoint authentication requirements"""
        try:
            # Test without authentication
            temp_session = requests.Session()
            temp_session.timeout = TEST_TIMEOUT
            
            start_time = time.time()
            response = temp_session.get(f"{BACKEND_URL}/chats")
            response_time = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test("GET /api/chats - Authentication Required", True, 
                             "Correctly requires authentication (401)", response_time)
                return True
            else:
                self.log_test("GET /api/chats - Authentication Required", False, 
                             f"Expected 401, got {response.status_code}", response_time)
                return False
                
        except Exception as e:
            self.log_test("GET /api/chats - Authentication Required", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all chats endpoint tests"""
        print("🔍 STARTING FOCUSED CHATS ENDPOINT TESTING")
        print("=" * 60)
        
        # Test authentication requirement first
        self.test_chats_endpoint_authentication()
        
        # Register test user for authenticated tests
        if not self.register_test_user():
            print("❌ Cannot proceed with authenticated tests - registration failed")
            return
        
        # Test basic functionality
        chats_data = self.test_chats_endpoint_basic()
        
        # Test response format
        self.test_chats_endpoint_response_format(chats_data)
        
        # Test performance
        self.test_chats_endpoint_performance()
        
        # Test with actual data
        self.test_chats_endpoint_with_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        # Show performance metrics
        timed_tests = [result for result in self.test_results if result.get("response_time")]
        if timed_tests:
            avg_time = sum(test["response_time"] for test in timed_tests) / len(timed_tests)
            max_time = max(test["response_time"] for test in timed_tests)
            print(f"\n⏱️ PERFORMANCE METRICS:")
            print(f"  Average Response Time: {avg_time:.3f}s")
            print(f"  Maximum Response Time: {max_time:.3f}s")
            
            if max_time > 5:
                print("  ⚠️ WARNING: Slow response times detected - potential timeout issue")
            elif max_time > 2:
                print("  ⚠️ CAUTION: Some responses are slow")
            else:
                print("  ✅ Response times are acceptable")

if __name__ == "__main__":
    tester = ChatsEndpointTester()
    tester.run_all_tests()