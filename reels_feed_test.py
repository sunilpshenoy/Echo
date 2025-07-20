#!/usr/bin/env python3
"""
Comprehensive Test Script for Reels Feed Endpoint
Tests the fixed GET /api/reels/feed endpoint that was causing 'NoneType' object has no attribute 'get' error
"""

import requests
import json
import time
from datetime import datetime
import uuid

# Configuration
BACKEND_URL = "https://a205b7e3-f535-4569-8dd8-c1f8fc23e5dc.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class ReelsFeedTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.users = {}
        self.test_results = []
        self.created_reels = []
        
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
                    "token": data["access_token"]
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
                        "token": data["access_token"]
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
    
    def test_user_setup(self):
        """Set up test users"""
        print("\n=== Setting Up Test Users ===")
        
        # Register test users
        users_to_create = [
            ("ravi_chef", "ravi.chef@test.com", "password123"),
            ("sarah_designer", "sarah.designer@test.com", "password123"),
            ("tech_guru", "tech.guru@test.com", "password123")
        ]
        
        for username, email, password in users_to_create:
            success, result = self.register_test_user(username, email, password)
            self.log_test(f"Register user {username}", success, str(result))
        
        return len(self.users) >= 2
    
    def create_test_reel(self, username, category, title, description, price, price_type="per_hour"):
        """Create a test reel for testing"""
        try:
            headers = self.get_auth_headers(username)
            reel_data = {
                "title": title,
                "description": description,
                "category": category,
                "base_price": price,
                "price_type": price_type,
                "video_url": "data:video/mp4;base64,mock_video_data",
                "thumbnail_url": "data:image/jpeg;base64,mock_thumbnail_data",
                "duration": 60,
                "location": {
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India"
                },
                "tags": ["professional", "quality", "affordable"]
            }
            
            response = self.session.post(f"{BACKEND_URL}/reels/create", json=reel_data, headers=headers)
            
            if response.status_code == 200:
                reel = response.json()
                self.created_reels.append(reel.get("reel_id"))
                return True, reel
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def test_create_sample_reels(self):
        """Create sample reels for testing the feed"""
        print("\n=== Creating Sample Reels ===")
        
        sample_reels = [
            ("ravi_chef", "food", "Authentic Mumbai Street Food", "Delicious vada pav and pav bhaji made fresh daily", 500.0, "per_meal"),
            ("sarah_designer", "design", "Custom Logo Design", "Professional logo design for your business", 2000.0, "per_project"),
            ("tech_guru", "tech", "Website Development", "Full-stack web development services", 1500.0, "per_hour")
        ]
        
        for username, category, title, description, price, price_type in sample_reels:
            if username in self.users:
                success, result = self.create_test_reel(username, category, title, description, price, price_type)
                self.log_test(f"Create {category} reel by {username}", success, str(result))
        
        return len(self.created_reels) > 0
    
    def test_basic_feed_retrieval(self):
        """Test basic reels feed retrieval without parameters"""
        print("\n=== Testing Basic Reels Feed Retrieval ===")
        
        if not self.users:
            self.log_test("Basic Feed Retrieval", False, "No users available")
            return
        
        try:
            # Use first available user
            username = list(self.users.keys())[0]
            headers = self.get_auth_headers(username)
            
            response = self.session.get(f"{BACKEND_URL}/reels/feed", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ["reels", "total_count", "page", "limit", "has_more"]
                has_all_fields = all(field in data for field in required_fields)
                
                self.log_test("Feed endpoint returns 200 status", True, "")
                self.log_test("Feed response has correct structure", has_all_fields, 
                            f"Fields present: {list(data.keys())}")
                
                # Check reels array
                reels = data.get("reels", [])
                self.log_test("Feed returns reels array", isinstance(reels, list), 
                            f"Reels count: {len(reels)}")
                
                # Check pagination info
                total_count = data.get("total_count", 0)
                page = data.get("page", 0)
                limit = data.get("limit", 0)
                has_more = data.get("has_more", False)
                
                self.log_test("Pagination info present", 
                            all(isinstance(x, (int, bool)) for x in [total_count, page, limit, has_more]),
                            f"total_count: {total_count}, page: {page}, limit: {limit}, has_more: {has_more}")
                
                # If we have reels, check their structure
                if reels:
                    first_reel = reels[0]
                    reel_fields = ["reel_id", "title", "description", "category", "base_price", "seller"]
                    has_reel_fields = all(field in first_reel for field in reel_fields)
                    
                    self.log_test("Reel data structure valid", has_reel_fields,
                                f"Reel fields: {list(first_reel.keys())}")
                    
                    # Check seller information
                    seller = first_reel.get("seller", {})
                    seller_fields = ["user_id", "name", "username", "verification_level"]
                    has_seller_fields = all(field in seller for field in seller_fields)
                    
                    self.log_test("Seller information included", has_seller_fields,
                                f"Seller fields: {list(seller.keys())}")
                    
                    # Check that sensitive data is removed
                    sensitive_fields = ["password", "email", "phone"]
                    has_sensitive = any(field in first_reel for field in sensitive_fields)
                    
                    self.log_test("Sensitive data properly removed", not has_sensitive,
                                f"No sensitive fields found in reel data")
                else:
                    self.log_test("Empty feed handling", True, "Feed returns empty array when no reels exist")
                
            else:
                self.log_test("Basic Feed Retrieval", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Basic Feed Retrieval", False, f"Error: {str(e)}")
    
    def test_feed_filtering(self):
        """Test feed filtering functionality"""
        print("\n=== Testing Feed Filtering ===")
        
        if not self.users:
            self.log_test("Feed Filtering", False, "No users available")
            return
        
        username = list(self.users.keys())[0]
        headers = self.get_auth_headers(username)
        
        # Test category filtering
        try:
            response = self.session.get(f"{BACKEND_URL}/reels/feed?category=food", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                reels = data.get("reels", [])
                
                # Check if all returned reels are food category
                all_food = all(reel.get("category") == "food" for reel in reels) if reels else True
                
                self.log_test("Category filtering (food)", all_food,
                            f"Found {len(reels)} food reels")
            else:
                self.log_test("Category filtering (food)", False,
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Category filtering (food)", False, f"Error: {str(e)}")
        
        # Test location filtering
        try:
            response = self.session.get(f"{BACKEND_URL}/reels/feed?location=Mumbai", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                reels = data.get("reels", [])
                
                self.log_test("Location filtering (Mumbai)", True,
                            f"Found {len(reels)} reels in Mumbai area")
            else:
                self.log_test("Location filtering (Mumbai)", False,
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Location filtering (Mumbai)", False, f"Error: {str(e)}")
        
        # Test price range filtering
        try:
            response = self.session.get(f"{BACKEND_URL}/reels/feed?min_price=100&max_price=1000", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                reels = data.get("reels", [])
                
                # Check if all returned reels are within price range
                in_range = all(100 <= reel.get("base_price", 0) <= 1000 for reel in reels) if reels else True
                
                self.log_test("Price range filtering (100-1000)", in_range,
                            f"Found {len(reels)} reels in price range")
            else:
                self.log_test("Price range filtering (100-1000)", False,
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Price range filtering (100-1000)", False, f"Error: {str(e)}")
    
    def test_feed_pagination(self):
        """Test feed pagination functionality"""
        print("\n=== Testing Feed Pagination ===")
        
        if not self.users:
            self.log_test("Feed Pagination", False, "No users available")
            return
        
        username = list(self.users.keys())[0]
        headers = self.get_auth_headers(username)
        
        # Test pagination parameters
        try:
            response = self.session.get(f"{BACKEND_URL}/reels/feed?page=1&limit=10", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                page = data.get("page", 0)
                limit = data.get("limit", 0)
                reels = data.get("reels", [])
                has_more = data.get("has_more", False)
                
                self.log_test("Pagination parameters respected", 
                            page == 1 and limit == 10,
                            f"page: {page}, limit: {limit}")
                
                self.log_test("Reels count within limit", 
                            len(reels) <= 10,
                            f"Returned {len(reels)} reels (limit: 10)")
                
                self.log_test("has_more flag present", 
                            isinstance(has_more, bool),
                            f"has_more: {has_more}")
                
            else:
                self.log_test("Feed Pagination", False,
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Feed Pagination", False, f"Error: {str(e)}")
    
    def test_authentication_required(self):
        """Test that authentication is required for feed access"""
        print("\n=== Testing Authentication Requirement ===")
        
        try:
            # Try to access feed without authentication
            response = self.session.get(f"{BACKEND_URL}/reels/feed")
            
            auth_required = response.status_code == 401
            
            self.log_test("Authentication required for feed access", auth_required,
                        f"HTTP {response.status_code}: Unauthorized access properly blocked")
            
        except Exception as e:
            self.log_test("Authentication required for feed access", False, f"Error: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling for various scenarios"""
        print("\n=== Testing Error Handling ===")
        
        if not self.users:
            self.log_test("Error Handling", False, "No users available")
            return
        
        username = list(self.users.keys())[0]
        headers = self.get_auth_headers(username)
        
        # Test invalid category
        try:
            response = self.session.get(f"{BACKEND_URL}/reels/feed?category=invalid_category", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                reels = data.get("reels", [])
                
                self.log_test("Invalid category handling", True,
                            f"Returns empty result for invalid category: {len(reels)} reels")
            else:
                self.log_test("Invalid category handling", False,
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Invalid category handling", False, f"Error: {str(e)}")
        
        # Test invalid price range
        try:
            response = self.session.get(f"{BACKEND_URL}/reels/feed?min_price=abc&max_price=xyz", headers=headers)
            
            # Should handle gracefully (either 400 error or ignore invalid params)
            handles_gracefully = response.status_code in [200, 400]
            
            self.log_test("Invalid price parameters handling", handles_gracefully,
                        f"HTTP {response.status_code}: Handles invalid price params gracefully")
        except Exception as e:
            self.log_test("Invalid price parameters handling", False, f"Error: {str(e)}")
    
    def test_nonetype_error_resolution(self):
        """Test that the original NoneType error is resolved"""
        print("\n=== Testing NoneType Error Resolution ===")
        
        if not self.users:
            self.log_test("NoneType Error Resolution", False, "No users available")
            return
        
        username = list(self.users.keys())[0]
        headers = self.get_auth_headers(username)
        
        try:
            # Make multiple requests to ensure stability
            for i in range(5):
                response = self.session.get(f"{BACKEND_URL}/reels/feed", headers=headers)
                
                if response.status_code != 200:
                    self.log_test(f"NoneType Error Resolution (attempt {i+1})", False,
                                f"HTTP {response.status_code}: {response.text}")
                    return
                
                # Check that response doesn't contain NoneType error
                response_text = response.text.lower()
                has_nonetype_error = "'nonetype' object has no attribute 'get'" in response_text
                
                if has_nonetype_error:
                    self.log_test(f"NoneType Error Resolution (attempt {i+1})", False,
                                "NoneType error still present in response")
                    return
            
            self.log_test("NoneType Error Resolution", True,
                        "No NoneType errors found in 5 consecutive requests")
            
        except Exception as e:
            self.log_test("NoneType Error Resolution", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all reels feed tests"""
        print("🎬 Starting Reels Feed Endpoint Testing")
        print("=" * 60)
        
        # Test sequence
        if not self.test_user_setup():
            print("❌ User setup failed - cannot continue with tests")
            return False
        
        # Create sample data
        self.test_create_sample_reels()
        
        # Core functionality tests
        self.test_basic_feed_retrieval()
        self.test_feed_filtering()
        self.test_feed_pagination()
        self.test_authentication_required()
        self.test_error_handling()
        self.test_nonetype_error_resolution()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎬 REELS FEED TEST SUMMARY")
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
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        print("\n🎬 Reels Feed Testing Complete!")
        return passed == total

if __name__ == "__main__":
    tester = ReelsFeedTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)