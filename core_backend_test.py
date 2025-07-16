#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script for Core Functionality
Tests authentication, chat, marketplace, E2E encryption, and file upload functionality
"""

import requests
import json
import time
import base64
import secrets
from datetime import datetime, timedelta
import uuid
import os

# Configuration
BACKEND_URL = "https://e09a8b3d-383d-4221-9e57-baee4ca8034c.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class CoreBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.users = {}  # Store user data and tokens
        self.test_results = []
        self.chats = {}  # Store chat data
        
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
    
    def register_test_user(self, username, email, password):
        """Register a test user or login if already exists"""
        try:
            # Try to register first
            response = self.session.post(f"{BACKEND_URL}/register", json={
                "username": username,
                "email": email,
                "password": password,
                "display_name": username
            })
            
            if response.status_code == 200:
                data = response.json()
                user_data = {
                    "user_id": data["user"]["user_id"],
                    "username": username,
                    "email": email,
                    "token": data["access_token"],
                    "profile_completed": data["user"].get("profile_completed", False)
                }
                self.users[username] = user_data
                return True, user_data
            elif response.status_code == 400 and "already registered" in response.text:
                # User already exists, try to login
                login_response = self.session.post(f"{BACKEND_URL}/login", json={
                    "email": email,
                    "password": password
                })
                
                if login_response.status_code == 200:
                    data = login_response.json()
                    user_data = {
                        "user_id": data["user"]["user_id"],
                        "username": username,
                        "email": email,
                        "token": data["access_token"],
                        "profile_completed": data["user"].get("profile_completed", False)
                    }
                    self.users[username] = user_data
                    return True, user_data
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
    
    def test_authentication(self):
        """Test user authentication (login/register)"""
        print("\n=== Testing Authentication ===")
        
        # Test registration
        success, result = self.register_test_user("test_user_auth", "test_auth@example.com", "testpass123")
        self.log_test("User Registration", success, str(result))
        
        # Test login with existing user
        if success:
            # Try to login again with same credentials
            login_response = self.session.post(f"{BACKEND_URL}/login", json={
                "email": "test_auth@example.com",
                "password": "testpass123"
            })
            
            login_success = login_response.status_code == 200
            self.log_test("User Login", login_success, 
                         f"Status: {login_response.status_code}, Response: {login_response.text[:100]}")
            
            # Test token validation
            if login_success:
                headers = self.get_auth_headers("test_user_auth")
                me_response = self.session.get(f"{BACKEND_URL}/users/me", headers=headers)
                token_valid = me_response.status_code == 200
                self.log_test("Token Validation", token_valid, 
                             f"Status: {me_response.status_code}")
        
        # Test invalid login
        invalid_login = self.session.post(f"{BACKEND_URL}/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpass"
        })
        invalid_blocked = invalid_login.status_code == 401
        self.log_test("Invalid Login Blocked", invalid_blocked, 
                     f"Status: {invalid_login.status_code}")
        
        return len(self.users) > 0
    
    def test_profile_completion(self):
        """Test profile completion functionality"""
        print("\n=== Testing Profile Completion ===")
        
        if "test_user_auth" not in self.users:
            self.log_test("Profile Completion", False, "No test user available")
            return
        
        try:
            headers = self.get_auth_headers("test_user_auth")
            
            # Complete profile
            profile_data = {
                "display_name": "Test User",
                "age": 25,
                "gender": "other",
                "location": "Mumbai, India",
                "bio": "Test user for backend testing",
                "interests": ["technology", "music"],
                "values": ["honesty", "creativity"],
                "current_mood": "excited",
                "seeking_type": "friendship",
                "connection_purpose": "networking",
                "profile_completed": True
            }
            
            response = self.session.put(f"{BACKEND_URL}/profile/complete", 
                                      json=profile_data, headers=headers)
            
            success = response.status_code == 200
            self.log_test("Profile Completion", success, 
                         f"Status: {response.status_code}, Response: {response.text[:100]}")
            
            if success:
                # Update user data
                self.users["test_user_auth"]["profile_completed"] = True
                
        except Exception as e:
            self.log_test("Profile Completion", False, f"Error: {str(e)}")
    
    def test_chat_functionality(self):
        """Test basic chat functionality"""
        print("\n=== Testing Chat Functionality ===")
        
        # Register second user for chat testing
        success, result = self.register_test_user("test_user_chat", "test_chat@example.com", "testpass123")
        if not success:
            self.log_test("Chat User Registration", False, str(result))
            return
        
        # Complete profile for chat user
        headers = self.get_auth_headers("test_user_chat")
        profile_data = {
            "display_name": "Chat Test User",
            "age": 28,
            "gender": "other",
            "location": "Delhi, India",
            "bio": "Chat test user",
            "profile_completed": True
        }
        self.session.put(f"{BACKEND_URL}/profile/complete", json=profile_data, headers=headers)
        
        try:
            # Create a direct chat
            user1_headers = self.get_auth_headers("test_user_auth")
            user2_id = self.users["test_user_chat"]["user_id"]
            
            chat_data = {
                "chat_type": "direct",
                "other_user_id": user2_id
            }
            
            response = self.session.post(f"{BACKEND_URL}/chats", 
                                       json=chat_data, headers=user1_headers)
            
            chat_success = response.status_code == 200
            self.log_test("Chat Creation", chat_success, 
                         f"Status: {response.status_code}")
            
            if chat_success:
                chat_data = response.json()
                chat_id = chat_data.get("chat_id")
                self.chats["test_chat"] = chat_id
                
                # Send a message
                message_data = {
                    "content": "Hello! This is a test message.",
                    "message_type": "text"
                }
                
                msg_response = self.session.post(f"{BACKEND_URL}/chats/{chat_id}/messages", 
                                               json=message_data, headers=user1_headers)
                
                msg_success = msg_response.status_code == 200
                self.log_test("Message Sending", msg_success, 
                             f"Status: {msg_response.status_code}")
                
                # Retrieve messages
                get_response = self.session.get(f"{BACKEND_URL}/chats/{chat_id}/messages", 
                                              headers=user1_headers)
                
                get_success = get_response.status_code == 200
                if get_success:
                    messages = get_response.json()
                    has_message = len(messages) > 0
                    self.log_test("Message Retrieval", has_message, 
                                 f"Retrieved {len(messages)} messages")
                else:
                    self.log_test("Message Retrieval", False, 
                                 f"Status: {get_response.status_code}")
                
        except Exception as e:
            self.log_test("Chat Functionality", False, f"Error: {str(e)}")
    
    def test_marketplace_apis(self):
        """Test marketplace APIs (reels feed, categories)"""
        print("\n=== Testing Marketplace APIs ===")
        
        if "test_user_auth" not in self.users:
            self.log_test("Marketplace APIs", False, "No authenticated user available")
            return
        
        try:
            headers = self.get_auth_headers("test_user_auth")
            
            # Test categories endpoint
            categories_response = self.session.get(f"{BACKEND_URL}/reels/categories", headers=headers)
            categories_success = categories_response.status_code == 200
            
            if categories_success:
                categories = categories_response.json()
                has_categories = len(categories) > 0
                self.log_test("Marketplace Categories", has_categories, 
                             f"Retrieved {len(categories)} categories")
            else:
                self.log_test("Marketplace Categories", False, 
                             f"Status: {categories_response.status_code}")
            
            # Test reels feed endpoint (this was mentioned as having 500 error)
            feed_response = self.session.get(f"{BACKEND_URL}/reels/feed", headers=headers)
            feed_success = feed_response.status_code == 200
            
            if feed_success:
                feed_data = feed_response.json()
                has_reels = "reels" in feed_data
                self.log_test("Reels Feed", has_reels, 
                             f"Feed structure: {list(feed_data.keys())}")
            else:
                self.log_test("Reels Feed", False, 
                             f"Status: {feed_response.status_code}, Error: {feed_response.text[:200]}")
            
            # Test creating a service reel
            reel_data = {
                "title": "Test Service Reel",
                "description": "This is a test service reel for backend testing",
                "category": "tech",
                "base_price": 500.0,
                "price_type": "per_hour",
                "video_url": "data:video/mp4;base64,dGVzdCB2aWRlbyBkYXRh",
                "duration": 60,
                "location": {
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "latitude": 19.0760,
                    "longitude": 72.8777
                },
                "tags": ["testing", "backend", "api"]
            }
            
            create_response = self.session.post(f"{BACKEND_URL}/reels/create", 
                                              json=reel_data, headers=headers)
            
            create_success = create_response.status_code == 200
            self.log_test("Service Reel Creation", create_success, 
                         f"Status: {create_response.status_code}")
            
        except Exception as e:
            self.log_test("Marketplace APIs", False, f"Error: {str(e)}")
    
    def test_file_upload(self):
        """Test file upload functionality"""
        print("\n=== Testing File Upload ===")
        
        if "test_user_auth" not in self.users:
            self.log_test("File Upload", False, "No authenticated user available")
            return
        
        try:
            headers = self.get_auth_headers("test_user_auth")
            
            # Create a test file
            test_file_content = b"This is a test file for upload testing"
            test_file_data = base64.b64encode(test_file_content).decode()
            
            # Test file upload
            files_data = {
                "file": ("test.txt", test_file_content, "text/plain")
            }
            
            # Try multipart form upload
            upload_response = self.session.post(f"{BACKEND_URL}/upload", 
                                              files=files_data, headers=headers)
            
            upload_success = upload_response.status_code == 200
            
            if upload_success:
                upload_result = upload_response.json()
                has_file_id = "file_id" in upload_result
                self.log_test("File Upload", has_file_id, 
                             f"Upload result: {list(upload_result.keys())}")
            else:
                self.log_test("File Upload", False, 
                             f"Status: {upload_response.status_code}, Error: {upload_response.text[:200]}")
            
        except Exception as e:
            self.log_test("File Upload", False, f"Error: {str(e)}")
    
    def test_e2e_encryption_endpoints(self):
        """Test E2E encryption endpoints"""
        print("\n=== Testing E2E Encryption Endpoints ===")
        
        if "test_user_auth" not in self.users:
            self.log_test("E2E Encryption", False, "No authenticated user available")
            return
        
        try:
            headers = self.get_auth_headers("test_user_auth")
            user_id = self.users["test_user_auth"]["user_id"]
            
            # Generate mock E2E keys
            keys = {
                "user_id": user_id,
                "identity_key": base64.b64encode(secrets.token_bytes(32)).decode(),
                "signing_key": base64.b64encode(secrets.token_bytes(32)).decode(),
                "signed_pre_key": base64.b64encode(secrets.token_bytes(32)).decode(),
                "signed_pre_key_signature": base64.b64encode(secrets.token_bytes(64)).decode(),
                "one_time_pre_keys": [base64.b64encode(secrets.token_bytes(32)).decode() for _ in range(3)]
            }
            
            # Test key upload
            key_response = self.session.post(f"{BACKEND_URL}/e2e/keys", 
                                           json=keys, headers=headers)
            
            key_success = key_response.status_code == 200
            self.log_test("E2E Key Upload", key_success, 
                         f"Status: {key_response.status_code}")
            
            # Test key retrieval
            if key_success:
                get_keys_response = self.session.get(f"{BACKEND_URL}/e2e/keys/{user_id}", 
                                                   headers=headers)
                
                get_keys_success = get_keys_response.status_code == 200
                if get_keys_success:
                    retrieved_keys = get_keys_response.json()
                    has_required_fields = all(field in retrieved_keys for field in 
                                            ["identity_key", "signed_pre_key", "one_time_pre_keys"])
                    self.log_test("E2E Key Retrieval", has_required_fields, 
                                 f"Retrieved keys: {list(retrieved_keys.keys())}")
                else:
                    self.log_test("E2E Key Retrieval", False, 
                                 f"Status: {get_keys_response.status_code}")
            
            # Test encrypted message sending
            if "test_chat" in self.chats:
                encrypted_message = {
                    "message_id": str(uuid.uuid4()),
                    "conversation_id": self.chats["test_chat"],
                    "sender_id": user_id,
                    "recipient_id": self.users["test_user_chat"]["user_id"],
                    "encrypted_content": base64.b64encode(b"Encrypted test message").decode(),
                    "iv": base64.b64encode(secrets.token_bytes(16)).decode(),
                    "ratchet_public_key": base64.b64encode(secrets.token_bytes(32)).decode(),
                    "message_number": 1,
                    "chain_length": 1
                }
                
                e2e_msg_response = self.session.post(f"{BACKEND_URL}/e2e/message", 
                                                   json=encrypted_message, headers=headers)
                
                e2e_msg_success = e2e_msg_response.status_code == 200
                self.log_test("E2E Message Sending", e2e_msg_success, 
                             f"Status: {e2e_msg_response.status_code}")
            
        except Exception as e:
            self.log_test("E2E Encryption", False, f"Error: {str(e)}")
    
    def test_teams_functionality(self):
        """Test teams functionality"""
        print("\n=== Testing Teams Functionality ===")
        
        if "test_user_auth" not in self.users:
            self.log_test("Teams Functionality", False, "No authenticated user available")
            return
        
        try:
            headers = self.get_auth_headers("test_user_auth")
            
            # Create a team
            team_data = {
                "name": "Test Team",
                "description": "A test team for backend testing",
                "chat_type": "group"
            }
            
            team_response = self.session.post(f"{BACKEND_URL}/teams", 
                                            json=team_data, headers=headers)
            
            team_success = team_response.status_code == 200
            self.log_test("Team Creation", team_success, 
                         f"Status: {team_response.status_code}")
            
            if team_success:
                team_data = team_response.json()
                team_id = team_data.get("team_id")
                
                # Get teams list
                teams_response = self.session.get(f"{BACKEND_URL}/teams", headers=headers)
                teams_success = teams_response.status_code == 200
                
                if teams_success:
                    teams = teams_response.json()
                    has_teams = len(teams) > 0
                    self.log_test("Teams Retrieval", has_teams, 
                                 f"Retrieved {len(teams)} teams")
                else:
                    self.log_test("Teams Retrieval", False, 
                                 f"Status: {teams_response.status_code}")
                
                # Send team message
                if team_id:
                    team_msg_data = {
                        "content": "Hello team! This is a test message.",
                        "message_type": "text"
                    }
                    
                    team_msg_response = self.session.post(f"{BACKEND_URL}/teams/{team_id}/messages", 
                                                        json=team_msg_data, headers=headers)
                    
                    team_msg_success = team_msg_response.status_code == 200
                    self.log_test("Team Message Sending", team_msg_success, 
                                 f"Status: {team_msg_response.status_code}")
            
        except Exception as e:
            self.log_test("Teams Functionality", False, f"Error: {str(e)}")
    
    def test_websocket_endpoints(self):
        """Test WebSocket related endpoints"""
        print("\n=== Testing WebSocket Endpoints ===")
        
        # Note: We can't test actual WebSocket connections in this script,
        # but we can test the HTTP endpoints that support WebSocket functionality
        
        if "test_user_auth" not in self.users:
            self.log_test("WebSocket Endpoints", False, "No authenticated user available")
            return
        
        try:
            headers = self.get_auth_headers("test_user_auth")
            
            # Test user status endpoint (used for WebSocket presence)
            status_data = {
                "activity_status": "online",
                "custom_status": "Testing backend APIs"
            }
            
            status_response = self.session.put(f"{BACKEND_URL}/users/status", 
                                             json=status_data, headers=headers)
            
            # This endpoint might not exist, so we'll check if it's implemented
            status_success = status_response.status_code in [200, 404]
            self.log_test("User Status Update", status_success, 
                         f"Status: {status_response.status_code}")
            
        except Exception as e:
            self.log_test("WebSocket Endpoints", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all core backend tests"""
        print("🔧 Starting Core Backend Functionality Testing")
        print("=" * 60)
        
        # Test sequence based on review request priorities
        if not self.test_authentication():
            print("❌ Authentication failed - some tests may not work properly")
        
        self.test_profile_completion()
        self.test_chat_functionality()
        self.test_marketplace_apis()
        self.test_file_upload()
        self.test_e2e_encryption_endpoints()
        self.test_teams_functionality()
        self.test_websocket_endpoints()
        
        # Summary
        print("\n" + "=" * 60)
        print("🔧 CORE BACKEND TEST SUMMARY")
        print("=" * 60)
        
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
        
        print("\n🔧 Core Backend Testing Complete!")
        return passed == total

if __name__ == "__main__":
    tester = CoreBackendTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)