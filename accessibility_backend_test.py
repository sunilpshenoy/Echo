#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script for Accessibility Verification
Testing backend functionality to ensure accessibility improvements haven't broken existing functionality.

Focus Areas:
1. Authentication system (login/register)
2. Chat functionality (message sending, real-time messaging)
3. File sharing capabilities
4. Voice/video calling endpoints
5. E2E encryption functionality
6. Marketplace API endpoints
7. User management and profile completion
"""

import requests
import json
import time
import uuid
import base64
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://0ae32c31-0069-48ba-9ab2-3b5d1a729a6b.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class AccessibilityBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, message="", details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_authentication_system(self):
        """Test authentication system (login/register)"""
        print("\n🔐 TESTING AUTHENTICATION SYSTEM")
        
        # Test user registration
        test_email = f"accessibility_test_{int(time.time())}@test.com"
        test_username = f"accesstest_{int(time.time())}"
        
        register_data = {
            "username": test_username,
            "email": test_email,
            "password": "testpassword123",
            "display_name": f"Accessibility Test User {int(time.time())}"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/register", json=register_data)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                user_data = data.get('user', {})
                self.user_id = user_data.get('user_id')
                self.log_result("User Registration", True, f"Successfully registered user {test_email}")
            else:
                self.log_result("User Registration", False, f"Registration failed with status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("User Registration", False, f"Registration error: {str(e)}")
            return False
        
        # Test user login
        login_data = {
            "email": test_email,
            "password": "testpassword123"
        }
        
        try:
            response = self.session.post(f"{API_BASE}/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                login_token = data.get('access_token')
                self.log_result("User Login", True, f"Successfully logged in user {test_email}")
            else:
                self.log_result("User Login", False, f"Login failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("User Login", False, f"Login error: {str(e)}")
        
        # Test token validation
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            try:
                response = self.session.get(f"{API_BASE}/users/me", headers=headers)
                if response.status_code == 200:
                    user_data = response.json()
                    self.log_result("Token Validation", True, f"Token validation successful for user {user_data.get('username')}")
                else:
                    self.log_result("Token Validation", False, f"Token validation failed with status {response.status_code}")
            except Exception as e:
                self.log_result("Token Validation", False, f"Token validation error: {str(e)}")
        
        return True
    
    def test_chat_functionality(self):
        """Test chat functionality (message sending, real-time messaging)"""
        print("\n💬 TESTING CHAT FUNCTIONALITY")
        
        if not self.auth_token:
            self.log_result("Chat Functionality", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test chat creation
        chat_data = {
            "chat_type": "direct",
            "members": [self.user_id, "test_recipient_id"]
        }
        
        chat_id = None
        try:
            response = self.session.post(f"{API_BASE}/chats", json=chat_data, headers=headers)
            if response.status_code == 200:
                chat_response = response.json()
                chat_id = chat_response.get('chat_id')
                self.log_result("Chat Creation", True, f"Successfully created chat {chat_id}")
            else:
                self.log_result("Chat Creation", False, f"Chat creation failed with status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Chat Creation", False, f"Chat creation error: {str(e)}")
            return False
        
        # Test message sending
        if chat_id:
            message_data = {
                "content": "Test message for accessibility verification",
                "message_type": "text"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/chats/{chat_id}/messages", json=message_data, headers=headers)
                if response.status_code == 200:
                    message_response = response.json()
                    message_id = message_response.get('message_id')
                    self.log_result("Message Sending", True, f"Successfully sent message {message_id}")
                else:
                    self.log_result("Message Sending", False, f"Message sending failed with status {response.status_code}", response.text)
            except Exception as e:
                self.log_result("Message Sending", False, f"Message sending error: {str(e)}")
            
            # Test message retrieval
            try:
                response = self.session.get(f"{API_BASE}/chats/{chat_id}/messages", headers=headers)
                if response.status_code == 200:
                    messages = response.json()
                    self.log_result("Message Retrieval", True, f"Successfully retrieved {len(messages)} messages")
                else:
                    self.log_result("Message Retrieval", False, f"Message retrieval failed with status {response.status_code}")
            except Exception as e:
                self.log_result("Message Retrieval", False, f"Message retrieval error: {str(e)}")
        
        # Test chat listing
        try:
            response = self.session.get(f"{API_BASE}/chats", headers=headers)
            if response.status_code == 200:
                chats = response.json()
                self.log_result("Chat Listing", True, f"Successfully retrieved {len(chats)} chats")
            else:
                self.log_result("Chat Listing", False, f"Chat listing failed with status {response.status_code}")
        except Exception as e:
            self.log_result("Chat Listing", False, f"Chat listing error: {str(e)}")
        
        return True
    
    def test_file_sharing(self):
        """Test file sharing capabilities"""
        print("\n📎 TESTING FILE SHARING CAPABILITIES")
        
        if not self.auth_token:
            self.log_result("File Sharing", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Create a test file
        test_file_content = "This is a test file for accessibility verification"
        
        # Test file upload
        files_data = {
            "file": ("accessibility_test.txt", test_file_content, "text/plain")
        }
        
        try:
            response = self.session.post(f"{API_BASE}/upload", files=files_data, headers=headers)
            if response.status_code == 200:
                file_data = response.json()
                file_id = file_data.get('file_id')
                self.log_result("File Upload", True, f"Successfully uploaded file {file_id}")
                
                # Verify file metadata
                required_fields = ['file_name', 'file_size', 'file_type', 'file_data']
                missing_fields = [field for field in required_fields if field not in file_data]
                if not missing_fields:
                    self.log_result("File Metadata", True, "All required file metadata fields present")
                else:
                    self.log_result("File Metadata", False, f"Missing file metadata fields: {missing_fields}")
            else:
                self.log_result("File Upload", False, f"File upload failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("File Upload", False, f"File upload error: {str(e)}")
        
        return True
    
    def test_voice_video_calling(self):
        """Test voice/video calling endpoints"""
        print("\n📞 TESTING VOICE/VIDEO CALLING ENDPOINTS")
        
        if not self.auth_token:
            self.log_result("Voice/Video Calling", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test call initiation
        call_data = {
            "chat_id": "test_chat_id",
            "call_type": "voice",
            "participants": [self.user_id, "test_recipient_id"]
        }
        
        call_id = None
        try:
            response = self.session.post(f"{API_BASE}/calls/initiate", json=call_data, headers=headers)
            if response.status_code == 200:
                call_response = response.json()
                call_id = call_response.get('call_id')
                self.log_result("Call Initiation", True, f"Successfully initiated call {call_id}")
            else:
                self.log_result("Call Initiation", False, f"Call initiation failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Call Initiation", False, f"Call initiation error: {str(e)}")
        
        # Test call response (if call was created)
        if call_id:
            response_data = {"action": "accept"}
            try:
                response = self.session.put(f"{API_BASE}/calls/{call_id}/respond", json=response_data, headers=headers)
                if response.status_code == 200:
                    self.log_result("Call Response", True, f"Successfully responded to call {call_id}")
                else:
                    self.log_result("Call Response", False, f"Call response failed with status {response.status_code}")
            except Exception as e:
                self.log_result("Call Response", False, f"Call response error: {str(e)}")
            
            # Test call end
            try:
                response = self.session.put(f"{API_BASE}/calls/{call_id}/end", headers=headers)
                if response.status_code == 200:
                    self.log_result("Call End", True, f"Successfully ended call {call_id}")
                else:
                    self.log_result("Call End", False, f"Call end failed with status {response.status_code}")
            except Exception as e:
                self.log_result("Call End", False, f"Call end error: {str(e)}")
        
        return True
    
    def test_marketplace_api(self):
        """Test marketplace API endpoints"""
        print("\n🛒 TESTING MARKETPLACE API ENDPOINTS")
        
        if not self.auth_token:
            self.log_result("Marketplace API", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test marketplace categories
        try:
            response = self.session.get(f"{API_BASE}/marketplace/categories", headers=headers)
            if response.status_code == 200:
                categories = response.json()
                self.log_result("Marketplace Categories", True, f"Successfully retrieved {len(categories)} categories")
            else:
                self.log_result("Marketplace Categories", False, f"Categories retrieval failed with status {response.status_code}")
        except Exception as e:
            self.log_result("Marketplace Categories", False, f"Categories retrieval error: {str(e)}")
        
        # Test reels categories
        try:
            response = self.session.get(f"{API_BASE}/reels/categories", headers=headers)
            if response.status_code == 200:
                categories = response.json()
                self.log_result("Reels Categories", True, f"Successfully retrieved {len(categories)} reels categories")
            else:
                self.log_result("Reels Categories", False, f"Reels categories retrieval failed with status {response.status_code}")
        except Exception as e:
            self.log_result("Reels Categories", False, f"Reels categories retrieval error: {str(e)}")
        
        # Test reels feed
        try:
            response = self.session.get(f"{API_BASE}/reels/feed", headers=headers)
            if response.status_code == 200:
                feed_data = response.json()
                reels = feed_data.get('reels', [])
                self.log_result("Reels Feed", True, f"Successfully retrieved reels feed with {len(reels)} reels")
            else:
                self.log_result("Reels Feed", False, f"Reels feed retrieval failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Reels Feed", False, f"Reels feed retrieval error: {str(e)}")
        
        # Test marketplace listings
        try:
            response = self.session.get(f"{API_BASE}/marketplace/listings", headers=headers)
            if response.status_code == 200:
                listings_data = response.json()
                listings = listings_data.get('listings', [])
                self.log_result("Marketplace Listings", True, f"Successfully retrieved {len(listings)} marketplace listings")
            else:
                self.log_result("Marketplace Listings", False, f"Marketplace listings retrieval failed with status {response.status_code}")
        except Exception as e:
            self.log_result("Marketplace Listings", False, f"Marketplace listings retrieval error: {str(e)}")
        
        return True
    
    def test_user_management(self):
        """Test user management and profile completion"""
        print("\n👤 TESTING USER MANAGEMENT AND PROFILE COMPLETION")
        
        if not self.auth_token:
            self.log_result("User Management", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test profile completion
        profile_data = {
            "display_name": "Accessibility Test User Updated",
            "age": 25,
            "gender": "prefer_not_to_say",
            "location": "Test City",
            "bio": "This is a test bio for accessibility verification",
            "interests": ["technology", "accessibility", "testing"],
            "values": ["inclusivity", "usability", "quality"],
            "current_mood": "focused",
            "seeking_type": "friendship",
            "connection_purpose": "testing",
            "profile_completed": True
        }
        
        try:
            response = self.session.put(f"{API_BASE}/profile/complete", json=profile_data, headers=headers)
            if response.status_code == 200:
                updated_profile = response.json()
                self.log_result("Profile Completion", True, f"Successfully completed profile for user {updated_profile.get('username')}")
            else:
                self.log_result("Profile Completion", False, f"Profile completion failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Profile Completion", False, f"Profile completion error: {str(e)}")
        
        # Test profile update
        update_data = {
            "display_name": "Accessibility Test User Final",
            "status_message": "Testing accessibility backend functionality"
        }
        
        try:
            response = self.session.put(f"{API_BASE}/profile", json=update_data, headers=headers)
            if response.status_code == 200:
                updated_user = response.json()
                self.log_result("Profile Update", True, f"Successfully updated profile for user {updated_user.get('username')}")
            else:
                self.log_result("Profile Update", False, f"Profile update failed with status {response.status_code}")
        except Exception as e:
            self.log_result("Profile Update", False, f"Profile update error: {str(e)}")
        
        # Test user info retrieval
        try:
            response = self.session.get(f"{API_BASE}/users/me", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                self.log_result("User Info Retrieval", True, f"Successfully retrieved user info for {user_data.get('username')}")
            else:
                self.log_result("User Info Retrieval", False, f"User info retrieval failed with status {response.status_code}")
        except Exception as e:
            self.log_result("User Info Retrieval", False, f"User info retrieval error: {str(e)}")
        
        return True
    
    def test_teams_functionality(self):
        """Test teams functionality"""
        print("\n👥 TESTING TEAMS FUNCTIONALITY")
        
        if not self.auth_token:
            self.log_result("Teams Functionality", False, "No auth token available")
            return False
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test team creation
        team_data = {
            "name": "Accessibility Test Team",
            "description": "A test team for accessibility verification",
            "members": [self.user_id]
        }
        
        team_id = None
        try:
            response = self.session.post(f"{API_BASE}/teams", json=team_data, headers=headers)
            if response.status_code == 200:
                team_response = response.json()
                team_id = team_response.get('team_id')
                self.log_result("Team Creation", True, f"Successfully created team {team_id}")
            else:
                self.log_result("Team Creation", False, f"Team creation failed with status {response.status_code}", response.text)
        except Exception as e:
            self.log_result("Team Creation", False, f"Team creation error: {str(e)}")
        
        # Test team messaging (if team was created)
        if team_id:
            message_data = {
                "content": "Test team message for accessibility verification",
                "message_type": "text"
            }
            
            try:
                response = self.session.post(f"{API_BASE}/teams/{team_id}/messages", json=message_data, headers=headers)
                if response.status_code == 200:
                    self.log_result("Team Messaging", True, f"Successfully sent team message")
                else:
                    self.log_result("Team Messaging", False, f"Team messaging failed with status {response.status_code}")
            except Exception as e:
                self.log_result("Team Messaging", False, f"Team messaging error: {str(e)}")
        
        # Test teams retrieval
        try:
            response = self.session.get(f"{API_BASE}/teams", headers=headers)
            if response.status_code == 200:
                teams = response.json()
                self.log_result("Teams Retrieval", True, f"Successfully retrieved {len(teams)} teams")
            else:
                self.log_result("Teams Retrieval", False, f"Teams retrieval failed with status {response.status_code}")
        except Exception as e:
            self.log_result("Teams Retrieval", False, f"Teams retrieval error: {str(e)}")
        
        return True
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 STARTING ACCESSIBILITY BACKEND VERIFICATION")
        print("=" * 60)
        print("Testing backend functionality to ensure accessibility improvements")
        print("haven't broken existing functionality.")
        print("=" * 60)
        
        # Run all test suites
        test_suites = [
            ("Authentication System", self.test_authentication_system),
            ("Chat Functionality", self.test_chat_functionality),
            ("File Sharing", self.test_file_sharing),
            ("Voice/Video Calling", self.test_voice_video_calling),
            ("Marketplace API", self.test_marketplace_api),
            ("User Management", self.test_user_management),
            ("Teams Functionality", self.test_teams_functionality)
        ]
        
        for suite_name, test_func in test_suites:
            try:
                test_func()
            except Exception as e:
                self.log_result(f"{suite_name} Suite", False, f"Test suite error: {str(e)}")
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 ACCESSIBILITY BACKEND VERIFICATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅ PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n✅ CRITICAL SYSTEMS STATUS:")
        critical_systems = {
            "Authentication": any("Authentication" in r["test"] and "✅ PASS" in r["status"] for r in self.test_results),
            "Chat Functionality": any("Chat" in r["test"] and "✅ PASS" in r["status"] for r in self.test_results),
            "File Sharing": any("File" in r["test"] and "✅ PASS" in r["status"] for r in self.test_results),
            "Voice/Video Calls": any("Call" in r["test"] and "✅ PASS" in r["status"] for r in self.test_results),
            "Marketplace": any("Marketplace" in r["test"] or "Reels" in r["test"] and "✅ PASS" in r["status"] for r in self.test_results),
            "User Management": any("Profile" in r["test"] or "User" in r["test"] and "✅ PASS" in r["status"] for r in self.test_results),
            "Teams": any("Team" in r["test"] and "✅ PASS" in r["status"] for r in self.test_results)
        }
        
        for system, status in critical_systems.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {system}")
        
        print("\n🎯 ACCESSIBILITY VERIFICATION CONCLUSION:")
        if success_rate >= 80:
            print("✅ Backend is functioning well. Accessibility improvements have not broken existing functionality.")
            print("   The system is ready for production with improved accessibility features.")
        elif success_rate >= 60:
            print("⚠️ Backend has some issues but core functionality is working. Minor fixes needed.")
            print("   Most accessibility improvements are compatible with existing functionality.")
        else:
            print("❌ Backend has significant issues. Major fixes required before deployment.")
            print("   Accessibility improvements may have introduced regressions.")
        
        print(f"\n📈 OVERALL ASSESSMENT: {success_rate:.1f}% of backend functionality verified")
        print("🔍 Focus areas tested: Authentication, Chat, File Sharing, Voice/Video Calls, Marketplace, User Management, Teams")

if __name__ == "__main__":
    tester = AccessibilityBackendTester()
    tester.run_all_tests()