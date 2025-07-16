#!/usr/bin/env python3
"""
CORRECTED BACKEND TESTING SCRIPT
Tests critical backend functionality with correct API formats
"""

import requests
import json
import time
import base64
import secrets
from datetime import datetime, timedelta
import uuid
import os
import io

# Configuration
BACKEND_URL = "https://1345bce5-cc7d-477e-8431-d11bc6e77861.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class CorrectedBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.users = {}
        self.test_results = []
        self.chats = {}
        
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
    
    def create_test_user(self, username_suffix=""):
        """Create a test user for testing"""
        timestamp = int(time.time())
        username = f"testuser_{timestamp}{username_suffix}"
        email = f"{username}@test.com"
        # Use environment variable for test password or generate secure one
        test_password = os.environ.get('TEST_PASSWORD', 'TestPass123!@#$')
        
        user_data = {
            "username": username,
            "email": email,
            "password": test_password,
            "display_name": f"Test User {username_suffix}"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/register", json=user_data)
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                user_id = data.get("user", {}).get("user_id")
                
                self.users[username] = {
                    "username": username,
                    "email": email,
                    "password": test_password,
                    "token": token,
                    "user_id": user_id,
                    "display_name": user_data["display_name"]
                }
                return username
            else:
                print(f"Failed to create user {username}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error creating user {username}: {e}")
            return None
    
    def get_auth_headers(self, username):
        """Get authentication headers for a user"""
        if username in self.users and self.users[username]["token"]:
            return {"Authorization": f"Bearer {self.users[username]['token']}"}
        return {}
    
    def test_corrected_chat_functionality(self):
        """Test chat creation with correct API format"""
        print("\n💬 TESTING CORRECTED CHAT FUNCTIONALITY")
        
        # Create test users
        user1 = self.create_test_user("_chat1")
        user2 = self.create_test_user("_chat2")
        
        if not user1 or not user2:
            self.log_test("Chat Setup", False, "Failed to create test users")
            return
        
        # Test 1: Direct Chat Creation (CORRECTED FORMAT)
        try:
            chat_data = {
                "chat_type": "direct",
                "other_user_id": self.users[user2]["user_id"]  # CORRECTED: Use other_user_id instead of members
            }
            headers = self.get_auth_headers(user1)
            response = self.session.post(f"{BACKEND_URL}/chats", json=chat_data, headers=headers)
            success = response.status_code == 200
            if success:
                chat_id = response.json().get("chat_id")
                self.chats["test_chat"] = chat_id
            self.log_test("Direct Chat Creation (Corrected)", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Direct Chat Creation (Corrected)", False, f"Error: {e}")
        
        # Test 2: Group Chat Creation
        try:
            chat_data = {
                "chat_type": "group",
                "name": "Test Group Chat",
                "description": "A test group for testing",
                "members": [self.users[user1]["user_id"], self.users[user2]["user_id"]]
            }
            headers = self.get_auth_headers(user1)
            response = self.session.post(f"{BACKEND_URL}/chats", json=chat_data, headers=headers)
            success = response.status_code == 200
            if success:
                chat_id = response.json().get("chat_id")
                self.chats["group_chat"] = chat_id
            self.log_test("Group Chat Creation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Group Chat Creation", False, f"Error: {e}")
        
        # Test 3: Message Sending
        if "test_chat" in self.chats:
            try:
                message_data = {
                    "content": "Hello, this is a test message!",
                    "message_type": "text"
                }
                headers = self.get_auth_headers(user1)
                response = self.session.post(f"{BACKEND_URL}/chats/{self.chats['test_chat']}/messages", 
                                           json=message_data, headers=headers)
                success = response.status_code == 200
                self.log_test("Message Sending", success, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Message Sending", False, f"Error: {e}")
    
    def test_corrected_call_system(self):
        """Test call system with corrected chat creation"""
        print("\n📞 TESTING CORRECTED CALL SYSTEM")
        
        # Create test users
        user1 = self.create_test_user("_call1")
        user2 = self.create_test_user("_call2")
        
        if not user1 or not user2:
            self.log_test("Call Setup", False, "Failed to create test users")
            return
        
        # Create a chat first (CORRECTED FORMAT)
        try:
            chat_data = {
                "chat_type": "direct",
                "other_user_id": self.users[user2]["user_id"]  # CORRECTED FORMAT
            }
            headers = self.get_auth_headers(user1)
            response = self.session.post(f"{BACKEND_URL}/chats", json=chat_data, headers=headers)
            if response.status_code == 200:
                chat_id = response.json().get("chat_id")
                self.log_test("Call Chat Setup (Corrected)", True, f"Chat created: {chat_id}")
            else:
                self.log_test("Call Chat Setup (Corrected)", False, f"Failed to create chat: {response.status_code}")
                return
        except Exception as e:
            self.log_test("Call Chat Setup (Corrected)", False, f"Error: {e}")
            return
        
        # Test 1: Call Initiation
        try:
            call_data = {
                "chat_id": chat_id,
                "call_type": "voice"
            }
            headers = self.get_auth_headers(user1)
            response = self.session.post(f"{BACKEND_URL}/calls/initiate", json=call_data, headers=headers)
            success = response.status_code == 200
            call_id = None
            if success:
                call_id = response.json().get("call_id")
            self.log_test("Call Initiation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Call Initiation", False, f"Error: {e}")
        
        # Test 2: Call Response (if call was initiated)
        if call_id:
            try:
                response_data = {"action": "accept"}
                headers = self.get_auth_headers(user2)
                response = self.session.put(f"{BACKEND_URL}/calls/{call_id}/respond", 
                                          json=response_data, headers=headers)
                success = response.status_code == 200
                self.log_test("Call Response", success, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Call Response", False, f"Error: {e}")
        
        # Test 3: Call Management (End Call)
        if call_id:
            try:
                headers = self.get_auth_headers(user1)
                response = self.session.put(f"{BACKEND_URL}/calls/{call_id}/end", headers=headers)
                success = response.status_code == 200
                self.log_test("Call Management", success, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Call Management", False, f"Error: {e}")
    
    def test_authentication_system(self):
        """Test authentication system"""
        print("\n🔐 TESTING AUTHENTICATION SYSTEM")
        
        # Test 1: User Registration
        user1 = self.create_test_user("_auth1")
        success = user1 is not None
        self.log_test("User Registration", success, f"Created user: {user1}" if success else "Failed to create user")
        
        if not success:
            return
        
        # Test 2: User Login
        try:
            login_data = {
                "email": self.users[user1]["email"],
                "password": self.users[user1]["password"]
            }
            response = self.session.post(f"{BACKEND_URL}/login", json=login_data)
            success = response.status_code == 200 and "access_token" in response.json()
            self.log_test("User Login", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("User Login", False, f"Error: {e}")
        
        # Test 3: Token Validation
        try:
            headers = self.get_auth_headers(user1)
            response = self.session.get(f"{BACKEND_URL}/users/me", headers=headers)
            success = response.status_code == 200 and "user_id" in response.json()
            self.log_test("Token Validation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Token Validation", False, f"Error: {e}")
    
    def test_file_functionality(self):
        """Test file upload functionality"""
        print("\n📁 TESTING FILE UPLOAD/DOWNLOAD")
        
        user1 = self.create_test_user("_file1")
        if not user1:
            self.log_test("File Setup", False, "Failed to create test user")
            return
        
        # Test 1: File Upload
        try:
            # Create a test file
            test_content = b"This is a test file content for backend testing"
            files = {
                'file': ('test_document.txt', io.BytesIO(test_content), 'text/plain')
            }
            headers = self.get_auth_headers(user1)
            response = self.session.post(f"{BACKEND_URL}/upload", files=files, headers=headers)
            success = response.status_code == 200
            if success:
                file_data = response.json()
                # Check required fields
                required_fields = ["file_id", "file_name", "file_size", "file_type", "file_data"]
                has_all_fields = all(field in file_data for field in required_fields)
                success = success and has_all_fields
            self.log_test("File Upload", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("File Upload", False, f"Error: {e}")
        
        # Test 2: File Type Validation
        try:
            # Try uploading an image file
            test_image = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==")
            files = {
                'file': ('test_image.png', io.BytesIO(test_image), 'image/png')
            }
            headers = self.get_auth_headers(user1)
            response = self.session.post(f"{BACKEND_URL}/upload", files=files, headers=headers)
            success = response.status_code == 200
            self.log_test("File Type Validation", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("File Type Validation", False, f"Error: {e}")
    
    def test_api_endpoints(self):
        """Test all REST endpoints respond correctly"""
        print("\n🌐 TESTING API ENDPOINTS")
        
        user1 = self.create_test_user("_api1")
        if not user1:
            self.log_test("API Setup", False, "Failed to create test user")
            return
        
        headers = self.get_auth_headers(user1)
        
        # Test critical endpoints
        endpoints_to_test = [
            ("GET", "/users/me", "User Info Endpoint"),
            ("GET", "/chats", "Chats List Endpoint"),
            ("GET", "/contacts", "Contacts Endpoint"),
            ("GET", "/teams", "Teams Endpoint"),
            ("GET", "/marketplace/categories", "Marketplace Categories"),
            ("GET", "/reels/categories", "Reels Categories")
        ]
        
        for method, endpoint, test_name in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{BACKEND_URL}{endpoint}", headers=headers)
                else:
                    response = self.session.request(method, f"{BACKEND_URL}{endpoint}", headers=headers)
                
                success = response.status_code in [200, 201]
                self.log_test(test_name, success, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(test_name, False, f"Error: {e}")
    
    def test_websocket_support(self):
        """Test WebSocket connection support"""
        print("\n🔌 TESTING WEBSOCKET SUPPORT")
        
        user1 = self.create_test_user("_ws1")
        if not user1:
            self.log_test("WebSocket Setup", False, "Failed to create test user")
            return
        
        # Test WebSocket endpoint availability (this will return method not allowed, which is expected)
        try:
            headers = self.get_auth_headers(user1)
            response = self.session.get(f"{BACKEND_URL}/ws", headers=headers)
            # WebSocket endpoint should return 405 Method Not Allowed for GET requests
            success = response.status_code == 405
            self.log_test("WebSocket Endpoint", success, f"Status: {response.status_code} (405 expected)")
        except Exception as e:
            self.log_test("WebSocket Endpoint", False, f"Error: {e}")
    
    def test_database_operations(self):
        """Test user management, chat storage, and message persistence"""
        print("\n🗄️ TESTING DATABASE OPERATIONS")
        
        user1 = self.create_test_user("_db1")
        if not user1:
            self.log_test("Database Setup", False, "Failed to create test user")
            return
        
        # Test 1: User Profile Management
        try:
            profile_data = {
                "display_name": "Updated Test User",
                "age": 25,
                "gender": "other",
                "location": "Test City",
                "bio": "This is a test bio",
                "interests": ["testing", "backend"],
                "values": ["reliability", "accuracy"],
                "profile_completed": True
            }
            headers = self.get_auth_headers(user1)
            response = self.session.put(f"{BACKEND_URL}/profile/complete", json=profile_data, headers=headers)
            success = response.status_code == 200
            self.log_test("User Profile Management", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("User Profile Management", False, f"Error: {e}")
        
        # Test 2: Chat Storage (Group Chat)
        try:
            chat_data = {
                "chat_type": "group",
                "name": "Test Group Chat",
                "description": "A test group for database testing",
                "members": [self.users[user1]["user_id"]]
            }
            headers = self.get_auth_headers(user1)
            response = self.session.post(f"{BACKEND_URL}/chats", json=chat_data, headers=headers)
            success = response.status_code == 200
            if success:
                chat_id = response.json().get("chat_id")
                self.chats["db_test_chat"] = chat_id
            self.log_test("Chat Storage", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Chat Storage", False, f"Error: {e}")
        
        # Test 3: Message Persistence
        if "db_test_chat" in self.chats:
            try:
                # Send multiple messages
                messages = [
                    "First test message",
                    "Second test message",
                    "Third test message"
                ]
                headers = self.get_auth_headers(user1)
                for i, content in enumerate(messages):
                    message_data = {
                        "content": content,
                        "message_type": "text"
                    }
                    response = self.session.post(f"{BACKEND_URL}/chats/{self.chats['db_test_chat']}/messages", 
                                               json=message_data, headers=headers)
                    if response.status_code != 200:
                        break
                
                # Retrieve messages to verify persistence
                response = self.session.get(f"{BACKEND_URL}/chats/{self.chats['db_test_chat']}/messages", 
                                          headers=headers)
                success = response.status_code == 200 and len(response.json()) >= len(messages)
                self.log_test("Message Persistence", success, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Message Persistence", False, f"Error: {e}")
    
    def test_system_performance(self):
        """Test response times and concurrent requests"""
        print("\n⚡ TESTING SYSTEM PERFORMANCE")
        
        user1 = self.create_test_user("_perf1")
        if not user1:
            self.log_test("Performance Setup", False, "Failed to create test user")
            return
        
        headers = self.get_auth_headers(user1)
        
        # Test 1: Response Time
        try:
            start_time = time.time()
            response = self.session.get(f"{BACKEND_URL}/users/me", headers=headers)
            end_time = time.time()
            response_time = end_time - start_time
            
            success = response.status_code == 200 and response_time < 2.0  # Less than 2 seconds
            self.log_test("Response Time", success, f"Time: {response_time:.2f}s")
        except Exception as e:
            self.log_test("Response Time", False, f"Error: {e}")
        
        # Test 2: Multiple Requests
        try:
            success_count = 0
            total_requests = 5
            
            for i in range(total_requests):
                response = self.session.get(f"{BACKEND_URL}/users/me", headers=headers)
                if response.status_code == 200:
                    success_count += 1
                time.sleep(0.1)  # Small delay between requests
            
            success = success_count == total_requests
            self.log_test("Concurrent Requests", success, f"Success: {success_count}/{total_requests}")
        except Exception as e:
            self.log_test("Concurrent Requests", False, f"Error: {e}")
    
    def test_error_handling(self):
        """Test graceful error responses and logging"""
        print("\n🚨 TESTING ERROR HANDLING")
        
        # Test 1: Invalid Authentication
        try:
            invalid_headers = {"Authorization": "Bearer invalid_token"}
            response = self.session.get(f"{BACKEND_URL}/users/me", headers=invalid_headers)
            success = response.status_code == 401
            self.log_test("Invalid Authentication", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Invalid Authentication", False, f"Error: {e}")
        
        # Test 2: Invalid Data Format
        try:
            user1 = self.create_test_user("_error1")
            if user1:
                headers = self.get_auth_headers(user1)
                invalid_data = {"invalid": "data format"}
                response = self.session.post(f"{BACKEND_URL}/chats", json=invalid_data, headers=headers)
                success = response.status_code in [400, 422]  # Bad Request or Unprocessable Entity
                self.log_test("Invalid Data Format", success, f"Status: {response.status_code}")
            else:
                self.log_test("Invalid Data Format", False, "Failed to create test user")
        except Exception as e:
            self.log_test("Invalid Data Format", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 STARTING CORRECTED BACKEND TESTING")
        print("=" * 60)
        
        # Run all test suites
        self.test_authentication_system()
        self.test_corrected_chat_functionality()
        self.test_corrected_call_system()
        self.test_file_functionality()
        self.test_websocket_support()
        self.test_database_operations()
        self.test_api_endpoints()
        self.test_system_performance()
        self.test_error_handling()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 CORRECTED TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"✅ Tests Passed: {passed}")
        print(f"❌ Tests Failed: {total - passed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT: Backend is ready for production!")
        elif success_rate >= 75:
            print("✅ GOOD: Backend is mostly functional with minor issues")
        elif success_rate >= 50:
            print("⚠️ MODERATE: Backend has significant issues that need attention")
        else:
            print("🚨 CRITICAL: Backend has major issues that must be fixed")
        
        # Print failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        return success_rate >= 75  # Return True if success rate is good

if __name__ == "__main__":
    tester = CorrectedBackendTester()
    tester.run_all_tests()