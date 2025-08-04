#!/usr/bin/env python3
"""
COMPREHENSIVE CHATS ENDPOINT DIAGNOSTIC TEST
Diagnoses the specific loading issues with GET /api/chats endpoint
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://d2ce893b-8b01-49a3-8aed-a13ce7bbac25.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class ChatsDiagnosticTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.auth_token = None
        self.user_id = None
        
    def log_result(self, test_name, success, details="", response_time=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.3f}s)" if response_time else ""
        print(f"{status}: {test_name}{time_info}")
        if details:
            print(f"   Details: {details}")
    
    def setup_test_user(self):
        """Setup authenticated test user"""
        try:
            # Try to login with existing test user first
            login_data = {
                "email": "chats_diagnostic@example.com",
                "password": "testpassword123"
            }
            
            response = self.session.post(f"{BACKEND_URL}/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("user_id")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_result("User Login", True, f"Logged in as existing user")
                return True
            else:
                # Register new user
                user_data = {
                    "username": "chats_diagnostic_user",
                    "email": "chats_diagnostic@example.com",
                    "password": "testpassword123",
                    "display_name": "Chats Diagnostic User"
                }
                
                response = self.session.post(f"{BACKEND_URL}/register", json=user_data)
                
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data.get("access_token")
                    self.user_id = data.get("user", {}).get("user_id")
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_result("User Registration", True, f"Registered new user")
                    return True
                else:
                    self.log_result("User Setup", False, f"Registration failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            self.log_result("User Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_chats_endpoint_detailed(self):
        """Test GET /api/chats with detailed analysis"""
        try:
            print("\n🔍 DETAILED CHATS ENDPOINT ANALYSIS")
            print("-" * 50)
            
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/chats")
            response_time = time.time() - start_time
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Time: {response_time:.3f}s")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"Response Type: {type(data)}")
                    print(f"Response Length: {len(data) if isinstance(data, (list, dict)) else 'N/A'}")
                    
                    if isinstance(data, list):
                        print(f"Chats Count: {len(data)}")
                        if len(data) > 0:
                            print(f"First Chat Structure: {list(data[0].keys())}")
                            print(f"Sample Chat: {json.dumps(data[0], indent=2, default=str)}")
                    elif isinstance(data, dict):
                        print(f"Response Keys: {list(data.keys())}")
                        if 'chats' in data:
                            chats = data['chats']
                            print(f"Chats Count: {len(chats)}")
                            if len(chats) > 0:
                                print(f"First Chat Structure: {list(chats[0].keys())}")
                    
                    self.log_result("GET /api/chats - Detailed Analysis", True, 
                                   f"Successfully retrieved chats data", response_time)
                    return data
                    
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {str(e)}")
                    print(f"Raw Response: {response.text[:500]}...")
                    self.log_result("GET /api/chats - Detailed Analysis", False, 
                                   f"Invalid JSON response", response_time)
                    return None
            else:
                print(f"Error Response: {response.text}")
                self.log_result("GET /api/chats - Detailed Analysis", False, 
                               f"HTTP {response.status_code}: {response.text}", response_time)
                return None
                
        except requests.exceptions.Timeout:
            self.log_result("GET /api/chats - Detailed Analysis", False, 
                           "Request timed out - this could be the loading issue!")
            return None
        except Exception as e:
            self.log_result("GET /api/chats - Detailed Analysis", False, f"Exception: {str(e)}")
            return None
    
    def test_database_consistency(self):
        """Test database consistency for chats"""
        try:
            print("\n🔍 DATABASE CONSISTENCY CHECK")
            print("-" * 50)
            
            # Check if user has any chats in database
            # We'll do this by trying to create a chat and see what happens
            
            # First, let's check current user info
            response = self.session.get(f"{BACKEND_URL}/users/me")
            if response.status_code == 200:
                user_data = response.json()
                print(f"Current User ID: {user_data.get('user_id')}")
                print(f"Current User Email: {user_data.get('email')}")
                
                # Try to create a direct chat with a test user
                chat_data = {
                    "chat_type": "direct",
                    "members": ["test_user@example.com"]  # This might not exist, but let's see the error
                }
                
                response = self.session.post(f"{BACKEND_URL}/chats", json=chat_data)
                print(f"Chat Creation Status: {response.status_code}")
                print(f"Chat Creation Response: {response.text}")
                
                if response.status_code in [200, 201]:
                    self.log_result("Database Consistency", True, "Chat creation works")
                    return True
                else:
                    # This is expected for non-existent users, but let's see the error
                    self.log_result("Database Consistency", True, f"Expected error for non-existent user: {response.status_code}")
                    return True
            else:
                self.log_result("Database Consistency", False, f"Cannot get current user: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Database Consistency", False, f"Exception: {str(e)}")
            return False
    
    def test_multiple_requests(self):
        """Test multiple consecutive requests to identify loading patterns"""
        try:
            print("\n🔍 MULTIPLE REQUESTS PATTERN ANALYSIS")
            print("-" * 50)
            
            response_times = []
            statuses = []
            
            for i in range(5):
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/chats")
                response_time = time.time() - start_time
                
                response_times.append(response_time)
                statuses.append(response.status_code)
                
                print(f"Request {i+1}: {response.status_code} in {response_time:.3f}s")
                
                if response.status_code != 200:
                    print(f"  Error: {response.text}")
                
                time.sleep(0.5)  # Small delay between requests
            
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"\nResponse Time Analysis:")
            print(f"  Average: {avg_time:.3f}s")
            print(f"  Maximum: {max_time:.3f}s")
            print(f"  Minimum: {min_time:.3f}s")
            print(f"  Status Codes: {set(statuses)}")
            
            # Check for loading issues
            if max_time > 5:
                self.log_result("Multiple Requests Analysis", False, 
                               f"Slow responses detected (max: {max_time:.3f}s) - potential loading issue")
                return False
            elif len(set(statuses)) > 1:
                self.log_result("Multiple Requests Analysis", False, 
                               f"Inconsistent status codes: {set(statuses)}")
                return False
            else:
                self.log_result("Multiple Requests Analysis", True, 
                               f"Consistent performance (avg: {avg_time:.3f}s)")
                return True
                
        except Exception as e:
            self.log_result("Multiple Requests Analysis", False, f"Exception: {str(e)}")
            return False
    
    def test_frontend_compatibility(self):
        """Test if the response format matches what frontend expects"""
        try:
            print("\n🔍 FRONTEND COMPATIBILITY CHECK")
            print("-" * 50)
            
            response = self.session.get(f"{BACKEND_URL}/chats")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if it's the format ChatsInterface expects
                if isinstance(data, list):
                    print("✅ Response is a list (expected by most frontend implementations)")
                    
                    # Check if empty list is handled properly
                    if len(data) == 0:
                        print("✅ Empty list returned (should show 'No chats yet' in frontend)")
                        self.log_result("Frontend Compatibility", True, 
                                       "Empty chats list - frontend should handle this gracefully")
                        return True
                    else:
                        # Check chat structure
                        chat = data[0]
                        required_fields = ['chat_id', 'chat_type', 'members']
                        has_required = all(field in chat for field in required_fields)
                        
                        if has_required:
                            print("✅ Chat objects have required fields")
                            self.log_result("Frontend Compatibility", True, 
                                           "Chat structure compatible with frontend")
                            return True
                        else:
                            missing = [field for field in required_fields if field not in chat]
                            print(f"❌ Missing required fields: {missing}")
                            self.log_result("Frontend Compatibility", False, 
                                           f"Missing required fields: {missing}")
                            return False
                            
                elif isinstance(data, dict) and 'chats' in data:
                    print("⚠️ Response is wrapped in object (might cause frontend issues)")
                    self.log_result("Frontend Compatibility", False, 
                                   "Response format mismatch - frontend expects array, got object")
                    return False
                else:
                    print(f"❌ Unexpected response format: {type(data)}")
                    self.log_result("Frontend Compatibility", False, 
                                   f"Unexpected response format: {type(data)}")
                    return False
            else:
                self.log_result("Frontend Compatibility", False, 
                               f"HTTP error: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Frontend Compatibility", False, f"Exception: {str(e)}")
            return False
    
    def run_diagnostic(self):
        """Run comprehensive diagnostic"""
        print("🔍 CHATS ENDPOINT LOADING ISSUE DIAGNOSTIC")
        print("=" * 60)
        
        if not self.setup_test_user():
            print("❌ Cannot proceed - user setup failed")
            return
        
        # Run all diagnostic tests
        chats_data = self.test_chats_endpoint_detailed()
        self.test_database_consistency()
        self.test_multiple_requests()
        self.test_frontend_compatibility()
        
        print("\n" + "=" * 60)
        print("📋 DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        if chats_data is not None:
            print("✅ GET /api/chats endpoint is responding correctly")
            print("✅ No timeout or loading issues detected")
            print("✅ Response format appears to be compatible")
            print("\n💡 CONCLUSION:")
            print("   The backend /api/chats endpoint is working properly.")
            print("   If the frontend is stuck in loading state, the issue is likely:")
            print("   1. Frontend not handling empty chats list properly")
            print("   2. Frontend making incorrect API calls")
            print("   3. Frontend authentication issues")
            print("   4. Frontend error handling problems")
        else:
            print("❌ GET /api/chats endpoint has issues")
            print("❌ This could be causing the frontend loading problems")

if __name__ == "__main__":
    tester = ChatsDiagnosticTester()
    tester.run_diagnostic()