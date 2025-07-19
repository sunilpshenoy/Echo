#!/usr/bin/env python3
"""
Comprehensive test script for Contextual Profile Backend Endpoints
Tests the new contextual profile management functionality:
1. GET /api/users/profile/completeness - profile completeness for all contexts
2. POST /api/users/profile/{context} - update contextual profiles
3. GET /api/users/profile/requirements/{context} - requirements for each context
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://1345bce5-cc7d-477e-8431-d11bc6e77861.preview.emergentagent.com/api"
TEST_USER_EMAIL = "contextual_test@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_USERNAME = "contextual_tester"

class ContextualProfileTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", response_time=0):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "response_time": f"{response_time:.3f}s"
        })
        print(f"{status} {test_name}: {details} ({response_time:.3f}s)")
    
    def setup_test_user(self):
        """Register and login test user"""
        print("\n🔧 Setting up test user...")
        
        # Register user
        register_data = {
            "username": TEST_USER_USERNAME,
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "display_name": "Contextual Test User"
        }
        
        start_time = time.time()
        try:
            response = self.session.post(f"{BASE_URL}/register", json=register_data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.user_id = data["user"]["user_id"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_test("User Registration", True, f"User registered successfully", response_time)
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                # User exists, try login
                return self.login_existing_user()
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("User Registration", False, f"Exception: {str(e)}", response_time)
            return False
    
    def login_existing_user(self):
        """Login existing user"""
        login_data = {
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        }
        
        start_time = time.time()
        try:
            response = self.session.post(f"{BASE_URL}/login", json=login_data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                self.user_id = data["user"]["user_id"]
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_test("User Login", True, f"User logged in successfully", response_time)
                return True
            else:
                self.log_test("User Login", False, f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("User Login", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_profile_completeness_endpoint(self):
        """Test GET /api/users/profile/completeness"""
        print("\n📊 Testing Profile Completeness Endpoint...")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BASE_URL}/users/profile/completeness")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if "status" in data and "profiles" in data:
                    profiles = data["profiles"]
                    expected_contexts = ["chats", "groups", "marketplace", "premium"]
                    
                    # Check if all contexts are present
                    contexts_present = all(context in profiles for context in expected_contexts)
                    
                    if contexts_present:
                        self.log_test("Profile Completeness - Structure", True, 
                                    f"All contexts present: {list(profiles.keys())}", response_time)
                        
                        # Test individual context data
                        for context in expected_contexts:
                            context_data = profiles.get(context, {})
                            self.log_test(f"Profile Completeness - {context.title()}", True,
                                        f"Context data: {len(context_data)} fields", 0)
                    else:
                        missing = [c for c in expected_contexts if c not in profiles]
                        self.log_test("Profile Completeness - Structure", False,
                                    f"Missing contexts: {missing}", response_time)
                else:
                    self.log_test("Profile Completeness - Structure", False,
                                f"Invalid response structure: {list(data.keys())}", response_time)
            else:
                self.log_test("Profile Completeness", False,
                            f"Status: {response.status_code}, Response: {response.text}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Profile Completeness", False, f"Exception: {str(e)}", response_time)
    
    def test_context_requirements_endpoints(self):
        """Test GET /api/users/profile/requirements/{context}"""
        print("\n📋 Testing Context Requirements Endpoints...")
        
        contexts = ["chats", "groups", "marketplace", "premium"]
        
        for context in contexts:
            start_time = time.time()
            try:
                response = self.session.get(f"{BASE_URL}/users/profile/requirements/{context}")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "status" in data and "requirements" in data:
                        requirements = data["requirements"]
                        expected_fields = ["required", "optional", "description", "impact", "can_skip"]
                        
                        if all(field in requirements for field in expected_fields):
                            required_count = len(requirements.get("required", []))
                            optional_count = len(requirements.get("optional", []))
                            
                            self.log_test(f"Requirements - {context.title()}", True,
                                        f"Required: {required_count}, Optional: {optional_count}", response_time)
                        else:
                            missing = [f for f in expected_fields if f not in requirements]
                            self.log_test(f"Requirements - {context.title()}", False,
                                        f"Missing fields: {missing}", response_time)
                    else:
                        self.log_test(f"Requirements - {context.title()}", False,
                                    f"Invalid response structure", response_time)
                else:
                    self.log_test(f"Requirements - {context.title()}", False,
                                f"Status: {response.status_code}", response_time)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(f"Requirements - {context.title()}", False, f"Exception: {str(e)}", response_time)
        
        # Test invalid context
        start_time = time.time()
        try:
            response = self.session.get(f"{BASE_URL}/users/profile/requirements/invalid_context")
            response_time = time.time() - start_time
            
            if response.status_code == 404:
                self.log_test("Requirements - Invalid Context", True,
                            "Properly returns 404 for invalid context", response_time)
            else:
                self.log_test("Requirements - Invalid Context", False,
                            f"Expected 404, got {response.status_code}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Requirements - Invalid Context", False, f"Exception: {str(e)}", response_time)
    
    def test_contextual_profile_updates(self):
        """Test POST /api/users/profile/{context}"""
        print("\n✏️ Testing Contextual Profile Updates...")
        
        # Test data for each context
        test_profiles = {
            "chats": {
                "display_name": "Chat Display Name",
                "status_message": "Available for chat",
                "avatar_url": "https://example.com/avatar.jpg"
            },
            "groups": {
                "interests": ["technology", "music", "sports"],
                "location": "Mumbai, India",
                "age_range": "25-30",
                "skills": ["programming", "design"],
                "availability": "weekends",
                "group_preferences": ["tech meetups", "music events"]
            },
            "marketplace": {
                "full_name": "John Doe Marketplace",
                "phone_verification": True,
                "location": "Delhi, India",
                "id_verification": False,
                "business_info": "Freelance developer",
                "service_categories": ["web development", "mobile apps"]
            },
            "premium": {
                "premium_display_name": "Premium User",
                "current_mood": "excited",
                "personality_insights": ["creative", "analytical"],
                "relationship_goals": "meaningful connections",
                "premium_interests": ["art", "philosophy", "travel"]
            }
        }
        
        for context, profile_data in test_profiles.items():
            start_time = time.time()
            try:
                response = self.session.post(f"{BASE_URL}/users/profile/{context}", json=profile_data)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "status" in data and data["status"] == "success":
                        profile = data.get("profile", {})
                        updated_fields = len([k for k in profile_data.keys() if k in profile])
                        
                        self.log_test(f"Profile Update - {context.title()}", True,
                                    f"Updated {updated_fields}/{len(profile_data)} fields", response_time)
                    else:
                        self.log_test(f"Profile Update - {context.title()}", False,
                                    f"Unexpected response: {data}", response_time)
                else:
                    self.log_test(f"Profile Update - {context.title()}", False,
                                f"Status: {response.status_code}, Response: {response.text}", response_time)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(f"Profile Update - {context.title()}", False, f"Exception: {str(e)}", response_time)
        
        # Test invalid context
        start_time = time.time()
        try:
            response = self.session.post(f"{BASE_URL}/users/profile/invalid_context", 
                                       json={"test": "data"})
            response_time = time.time() - start_time
            
            if response.status_code == 400:
                self.log_test("Profile Update - Invalid Context", True,
                            "Properly returns 400 for invalid context", response_time)
            else:
                self.log_test("Profile Update - Invalid Context", False,
                            f"Expected 400, got {response.status_code}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Profile Update - Invalid Context", False, f"Exception: {str(e)}", response_time)
    
    def test_profile_completeness_after_updates(self):
        """Test profile completeness after updates"""
        print("\n🔄 Testing Profile Completeness After Updates...")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BASE_URL}/users/profile/completeness")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                profiles = data.get("profiles", {})
                
                # Check if profiles have been updated
                updated_contexts = []
                for context in ["chats", "groups", "marketplace", "premium"]:
                    context_data = profiles.get(context, {})
                    if context_data and len(context_data) > 1:  # More than just user_id
                        updated_contexts.append(context)
                
                if len(updated_contexts) >= 3:  # At least 3 contexts should be updated
                    self.log_test("Profile Completeness After Updates", True,
                                f"Updated contexts: {updated_contexts}", response_time)
                else:
                    self.log_test("Profile Completeness After Updates", False,
                                f"Only {len(updated_contexts)} contexts updated", response_time)
            else:
                self.log_test("Profile Completeness After Updates", False,
                            f"Status: {response.status_code}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Profile Completeness After Updates", False, f"Exception: {str(e)}", response_time)
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🚨 Testing Error Handling...")
        
        # Test unauthorized access (without token)
        temp_headers = self.session.headers.copy()
        self.session.headers.pop("Authorization", None)
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BASE_URL}/users/profile/completeness")
            response_time = time.time() - start_time
            
            if response.status_code in [401, 403]:
                self.log_test("Error Handling - Unauthorized", True,
                            f"Properly returns {response.status_code} for unauthorized access", response_time)
            else:
                self.log_test("Error Handling - Unauthorized", False,
                            f"Expected 401/403, got {response.status_code}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Error Handling - Unauthorized", False, f"Exception: {str(e)}", response_time)
        
        # Restore headers
        self.session.headers.update(temp_headers)
        
        # Test invalid JSON data
        start_time = time.time()
        try:
            response = self.session.post(f"{BASE_URL}/users/profile/chats", 
                                       data="invalid json", 
                                       headers={"Content-Type": "application/json"})
            response_time = time.time() - start_time
            
            if response.status_code == 422:  # Unprocessable Entity
                self.log_test("Error Handling - Invalid JSON", True,
                            "Properly handles invalid JSON", response_time)
            else:
                self.log_test("Error Handling - Invalid JSON", False,
                            f"Expected 422, got {response.status_code}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Error Handling - Invalid JSON", False, f"Exception: {str(e)}", response_time)
    
    def test_data_persistence(self):
        """Test data persistence across requests"""
        print("\n💾 Testing Data Persistence...")
        
        # Update a profile
        test_data = {
            "display_name": "Persistent Test Name",
            "status_message": "Testing persistence"
        }
        
        start_time = time.time()
        try:
            # Update profile
            response = self.session.post(f"{BASE_URL}/users/profile/chats", json=test_data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Wait a moment
                time.sleep(1)
                
                # Retrieve profile completeness
                start_time2 = time.time()
                response2 = self.session.get(f"{BASE_URL}/users/profile/completeness")
                response_time2 = time.time() - start_time2
                
                if response2.status_code == 200:
                    data = response2.json()
                    chats_profile = data.get("profiles", {}).get("chats", {})
                    
                    if chats_profile.get("display_name") == test_data["display_name"]:
                        self.log_test("Data Persistence", True,
                                    "Profile data persisted correctly", response_time + response_time2)
                    else:
                        self.log_test("Data Persistence", False,
                                    f"Data not persisted: {chats_profile}", response_time + response_time2)
                else:
                    self.log_test("Data Persistence", False,
                                f"Failed to retrieve: {response2.status_code}", response_time + response_time2)
            else:
                self.log_test("Data Persistence", False,
                            f"Failed to update: {response.status_code}", response_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Data Persistence", False, f"Exception: {str(e)}", response_time)
    
    def run_all_tests(self):
        """Run all contextual profile tests"""
        print("🚀 Starting Contextual Profile Backend Testing...")
        print(f"Base URL: {BASE_URL}")
        print(f"Test User: {TEST_USER_EMAIL}")
        print("=" * 80)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return
        
        # Run tests
        self.test_profile_completeness_endpoint()
        self.test_context_requirements_endpoints()
        self.test_contextual_profile_updates()
        self.test_profile_completeness_after_updates()
        self.test_error_handling()
        self.test_data_persistence()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 CONTEXTUAL PROFILE TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅" in r["status"]])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Print detailed results
        for result in self.test_results:
            print(f"{result['status']} {result['test']}: {result['details']} ({result['response_time']})")
        
        print("\n" + "=" * 80)
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! Contextual profile system is working perfectly!")
        elif success_rate >= 75:
            print("✅ GOOD! Most contextual profile features are working correctly.")
        elif success_rate >= 50:
            print("⚠️ PARTIAL! Some contextual profile features need attention.")
        else:
            print("❌ CRITICAL! Major issues with contextual profile system.")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = ContextualProfileTester()
    tester.run_all_tests()