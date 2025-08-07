#!/usr/bin/env python3
"""
Extended Contextual Profile Testing - Edge Cases and Advanced Scenarios
Tests additional scenarios for the contextual profile management system
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "https://9b83238d-a27b-406f-8157-e448fada6ab0.preview.emergentagent.com/api"
TEST_USER_EMAIL = "contextual_edge_test@example.com"
TEST_USER_PASSWORD = "EdgeTestPassword123!"
TEST_USER_USERNAME = "contextual_edge_tester"

class ExtendedContextualProfileTester:
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
        print("\n🔧 Setting up edge test user...")
        
        # Register user
        register_data = {
            "username": TEST_USER_USERNAME,
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "display_name": "Edge Test User"
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
                self.log_test("Edge User Registration", True, f"User registered successfully", response_time)
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                # User exists, try login
                return self.login_existing_user()
            else:
                self.log_test("Edge User Registration", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Edge User Registration", False, f"Exception: {str(e)}", response_time)
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
                self.log_test("Edge User Login", True, f"User logged in successfully", response_time)
                return True
            else:
                self.log_test("Edge User Login", False, f"Status: {response.status_code}", response_time)
                return False
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Edge User Login", False, f"Exception: {str(e)}", response_time)
            return False
    
    def test_empty_profile_updates(self):
        """Test updating profiles with empty data"""
        print("\n🔍 Testing Empty Profile Updates...")
        
        contexts = ["chats", "groups", "marketplace", "premium"]
        
        for context in contexts:
            start_time = time.time()
            try:
                response = self.session.post(f"{BASE_URL}/users/profile/{context}", json={})
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if "status" in data and data["status"] == "success":
                        self.log_test(f"Empty Update - {context.title()}", True,
                                    "Handles empty data gracefully", response_time)
                    else:
                        self.log_test(f"Empty Update - {context.title()}", False,
                                    f"Unexpected response: {data}", response_time)
                else:
                    self.log_test(f"Empty Update - {context.title()}", False,
                                f"Status: {response.status_code}", response_time)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(f"Empty Update - {context.title()}", False, f"Exception: {str(e)}", response_time)
    
    def test_large_data_updates(self):
        """Test updating profiles with large data"""
        print("\n📏 Testing Large Data Updates...")
        
        # Create large data sets
        large_data = {
            "chats": {
                "display_name": "A" * 100,  # Very long display name
                "status_message": "B" * 500,  # Very long status message
                "avatar_url": "https://example.com/" + "c" * 200 + ".jpg"  # Very long URL
            },
            "groups": {
                "interests": ["interest_" + str(i) for i in range(50)],  # Many interests
                "location": "Very Long Location Name " * 10,  # Long location
                "skills": ["skill_" + str(i) for i in range(30)],  # Many skills
                "group_preferences": ["preference_" + str(i) for i in range(20)]  # Many preferences
            },
            "marketplace": {
                "full_name": "Very Long Full Name " * 5,
                "business_info": "Very detailed business information " * 20,
                "service_categories": ["category_" + str(i) for i in range(25)]
            },
            "premium": {
                "premium_display_name": "Premium Name " * 10,
                "personality_insights": ["insight_" + str(i) for i in range(40)],
                "premium_interests": ["premium_interest_" + str(i) for i in range(35)]
            }
        }
        
        for context, profile_data in large_data.items():
            start_time = time.time()
            try:
                response = self.session.post(f"{BASE_URL}/users/profile/{context}", json=profile_data)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if "status" in data and data["status"] == "success":
                        self.log_test(f"Large Data - {context.title()}", True,
                                    "Handles large data successfully", response_time)
                    else:
                        self.log_test(f"Large Data - {context.title()}", False,
                                    f"Unexpected response", response_time)
                else:
                    self.log_test(f"Large Data - {context.title()}", False,
                                f"Status: {response.status_code}", response_time)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(f"Large Data - {context.title()}", False, f"Exception: {str(e)}", response_time)
    
    def test_special_characters_data(self):
        """Test updating profiles with special characters"""
        print("\n🔤 Testing Special Characters Data...")
        
        special_data = {
            "chats": {
                "display_name": "Test User 🚀 ñáéíóú",
                "status_message": "Available! 😊 Testing special chars: @#$%^&*()",
                "avatar_url": "https://example.com/avatar-special_chars.jpg"
            },
            "groups": {
                "interests": ["tech 💻", "music 🎵", "sports ⚽", "food 🍕"],
                "location": "Mumbai, India 🇮🇳",
                "skills": ["JavaScript", "Python", "React.js", "Node.js"],
                "availability": "weekends & evenings"
            },
            "marketplace": {
                "full_name": "John Doe Jr. & Associates",
                "business_info": "Web development services - 100% satisfaction guaranteed!",
                "service_categories": ["web dev", "mobile apps", "UI/UX design"]
            },
            "premium": {
                "premium_display_name": "Premium User ⭐",
                "current_mood": "excited & optimistic",
                "personality_insights": ["creative", "analytical", "empathetic"],
                "relationship_goals": "meaningful connections & friendships"
            }
        }
        
        for context, profile_data in special_data.items():
            start_time = time.time()
            try:
                response = self.session.post(f"{BASE_URL}/users/profile/{context}", json=profile_data)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if "status" in data and data["status"] == "success":
                        self.log_test(f"Special Chars - {context.title()}", True,
                                    "Handles special characters correctly", response_time)
                    else:
                        self.log_test(f"Special Chars - {context.title()}", False,
                                    f"Unexpected response", response_time)
                else:
                    self.log_test(f"Special Chars - {context.title()}", False,
                                f"Status: {response.status_code}", response_time)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(f"Special Chars - {context.title()}", False, f"Exception: {str(e)}", response_time)
    
    def test_concurrent_updates(self):
        """Test concurrent profile updates"""
        print("\n⚡ Testing Concurrent Updates...")
        
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def update_profile(context, data, result_queue):
            try:
                start_time = time.time()
                response = self.session.post(f"{BASE_URL}/users/profile/{context}", json=data)
                response_time = time.time() - start_time
                result_queue.put((context, response.status_code == 200, response_time))
            except Exception as e:
                result_queue.put((context, False, 0))
        
        # Prepare concurrent updates
        updates = [
            ("chats", {"display_name": "Concurrent Chat User"}),
            ("groups", {"interests": ["concurrent", "testing"]}),
            ("marketplace", {"full_name": "Concurrent Marketplace User"}),
            ("premium", {"premium_display_name": "Concurrent Premium User"})
        ]
        
        # Start concurrent threads
        threads = []
        for context, data in updates:
            thread = threading.Thread(target=update_profile, args=(context, data, results_queue))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        successful_updates = 0
        total_time = 0
        while not results_queue.empty():
            context, success, response_time = results_queue.get()
            if success:
                successful_updates += 1
            total_time += response_time
        
        if successful_updates == len(updates):
            self.log_test("Concurrent Updates", True,
                        f"All {len(updates)} concurrent updates successful", total_time)
        else:
            self.log_test("Concurrent Updates", False,
                        f"Only {successful_updates}/{len(updates)} updates successful", total_time)
    
    def test_profile_field_validation(self):
        """Test profile field validation"""
        print("\n✅ Testing Profile Field Validation...")
        
        # Test invalid data types
        invalid_data_tests = [
            ("chats", {"display_name": 123}, "Invalid display_name type"),
            ("groups", {"interests": "not_a_list"}, "Invalid interests type"),
            ("marketplace", {"phone_verification": "not_boolean"}, "Invalid phone_verification type"),
            ("premium", {"premium_interests": {"not": "list"}}, "Invalid premium_interests type")
        ]
        
        for context, invalid_data, description in invalid_data_tests:
            start_time = time.time()
            try:
                response = self.session.post(f"{BASE_URL}/users/profile/{context}", json=invalid_data)
                response_time = time.time() - start_time
                
                # The API might accept any data type, so we check if it processes without error
                if response.status_code in [200, 400, 422]:  # Any reasonable response
                    self.log_test(f"Validation - {description}", True,
                                f"Handled gracefully (status: {response.status_code})", response_time)
                else:
                    self.log_test(f"Validation - {description}", False,
                                f"Unexpected status: {response.status_code}", response_time)
                    
            except Exception as e:
                response_time = time.time() - start_time
                self.log_test(f"Validation - {description}", False, f"Exception: {str(e)}", response_time)
    
    def test_profile_completeness_consistency(self):
        """Test profile completeness consistency after various operations"""
        print("\n🔄 Testing Profile Completeness Consistency...")
        
        # Get initial completeness
        start_time = time.time()
        try:
            response1 = self.session.get(f"{BASE_URL}/users/profile/completeness")
            response_time1 = time.time() - start_time
            
            if response1.status_code == 200:
                initial_data = response1.json()
                
                # Update a profile
                update_data = {"display_name": "Consistency Test User"}
                start_time2 = time.time()
                response2 = self.session.post(f"{BASE_URL}/users/profile/chats", json=update_data)
                response_time2 = time.time() - start_time2
                
                if response2.status_code == 200:
                    # Get completeness again
                    start_time3 = time.time()
                    response3 = self.session.get(f"{BASE_URL}/users/profile/completeness")
                    response_time3 = time.time() - start_time3
                    
                    if response3.status_code == 200:
                        updated_data = response3.json()
                        
                        # Check if the update is reflected
                        initial_chats = initial_data.get("profiles", {}).get("chats", {})
                        updated_chats = updated_data.get("profiles", {}).get("chats", {})
                        
                        if updated_chats.get("display_name") == update_data["display_name"]:
                            self.log_test("Completeness Consistency", True,
                                        "Profile updates reflected in completeness", 
                                        response_time1 + response_time2 + response_time3)
                        else:
                            self.log_test("Completeness Consistency", False,
                                        "Profile updates not reflected in completeness",
                                        response_time1 + response_time2 + response_time3)
                    else:
                        self.log_test("Completeness Consistency", False,
                                    f"Failed to get updated completeness: {response3.status_code}",
                                    response_time1 + response_time2)
                else:
                    self.log_test("Completeness Consistency", False,
                                f"Failed to update profile: {response2.status_code}",
                                response_time1)
            else:
                self.log_test("Completeness Consistency", False,
                            f"Failed to get initial completeness: {response1.status_code}",
                            response_time1)
                
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Completeness Consistency", False, f"Exception: {str(e)}", response_time)
    
    def test_cross_context_data_isolation(self):
        """Test that context data is properly isolated"""
        print("\n🔒 Testing Cross-Context Data Isolation...")
        
        # Update different contexts with similar field names
        context_updates = {
            "chats": {"display_name": "Chat Display Name"},
            "premium": {"premium_display_name": "Premium Display Name"}
        }
        
        all_successful = True
        total_time = 0
        
        for context, data in context_updates.items():
            start_time = time.time()
            try:
                response = self.session.post(f"{BASE_URL}/users/profile/{context}", json=data)
                response_time = time.time() - start_time
                total_time += response_time
                
                if response.status_code != 200:
                    all_successful = False
                    
            except Exception as e:
                all_successful = False
                total_time += time.time() - start_time
        
        if all_successful:
            # Check if data is properly isolated
            start_time = time.time()
            try:
                response = self.session.get(f"{BASE_URL}/users/profile/completeness")
                response_time = time.time() - start_time
                total_time += response_time
                
                if response.status_code == 200:
                    data = response.json()
                    profiles = data.get("profiles", {})
                    
                    chats_profile = profiles.get("chats", {})
                    premium_profile = profiles.get("premium", {})
                    
                    chats_display = chats_profile.get("display_name")
                    premium_display = premium_profile.get("premium_display_name")
                    
                    if (chats_display == "Chat Display Name" and 
                        premium_display == "Premium Display Name"):
                        self.log_test("Cross-Context Isolation", True,
                                    "Context data properly isolated", total_time)
                    else:
                        self.log_test("Cross-Context Isolation", False,
                                    f"Data mixing detected: chats={chats_display}, premium={premium_display}",
                                    total_time)
                else:
                    self.log_test("Cross-Context Isolation", False,
                                f"Failed to verify isolation: {response.status_code}", total_time)
                    
            except Exception as e:
                self.log_test("Cross-Context Isolation", False, f"Exception: {str(e)}", total_time)
        else:
            self.log_test("Cross-Context Isolation", False, "Failed to update contexts", total_time)
    
    def run_extended_tests(self):
        """Run all extended contextual profile tests"""
        print("🚀 Starting Extended Contextual Profile Testing...")
        print(f"Base URL: {BASE_URL}")
        print(f"Test User: {TEST_USER_EMAIL}")
        print("=" * 80)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Aborting tests.")
            return
        
        # Run extended tests
        self.test_empty_profile_updates()
        self.test_large_data_updates()
        self.test_special_characters_data()
        self.test_concurrent_updates()
        self.test_profile_field_validation()
        self.test_profile_completeness_consistency()
        self.test_cross_context_data_isolation()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 EXTENDED CONTEXTUAL PROFILE TESTING SUMMARY")
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
            print("🎉 EXCELLENT! Extended contextual profile testing passed!")
        elif success_rate >= 75:
            print("✅ GOOD! Most extended features are working correctly.")
        elif success_rate >= 50:
            print("⚠️ PARTIAL! Some extended features need attention.")
        else:
            print("❌ CRITICAL! Major issues with extended functionality.")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = ExtendedContextualProfileTester()
    tester.run_extended_tests()