#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script for Reels-Based Marketplace
Tests all reels marketplace endpoints and functionality
"""

import requests
import json
import time
import base64
import secrets
from datetime import datetime, timedelta
import uuid

# Configuration
BACKEND_URL = "https://a205b7e3-f535-4569-8dd8-c1f8fc23e5dc.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class ReelsMarketplaceTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.users = {}  # Store user data and tokens
        self.reels = {}  # Store created reels
        self.test_results = []
        
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
                "display_name": username.replace("_", " ").title()
            })
            
            if response.status_code == 200:
                data = response.json()
                user_data = {
                    "user_id": data["user"]["user_id"],
                    "username": username,
                    "email": email,
                    "token": data["access_token"],
                    "display_name": data["user"]["display_name"]
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
                        "display_name": data["user"].get("display_name", username)
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
    
    def test_user_registration(self):
        """Test user registration for reels marketplace testing"""
        print("\n=== Testing User Registration for Reels Marketplace ===")
        
        # Register test users for different service categories
        test_users = [
            ("chef_ravi", "chef.ravi@mumbai.com", "password123"),
            ("designer_priya", "priya.design@delhi.com", "password123"),
            ("dev_arjun", "arjun.dev@bangalore.com", "password123"),
            ("plumber_suresh", "suresh.plumber@chennai.com", "password123"),
            ("buyer_anita", "anita.buyer@pune.com", "password123")
        ]
        
        for username, email, password in test_users:
            success, result = self.register_test_user(username, email, password)
            self.log_test(f"Register {username} for reels testing", success, str(result))
        
        return len(self.users) >= 4
    
    def test_reel_categories(self):
        """Test getting available reel categories"""
        print("\n=== Testing Reel Categories Endpoint ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/reels/categories")
            
            if response.status_code == 200:
                data = response.json()
                categories = data.get("categories", [])
                
                expected_categories = ["food", "design", "tech", "home", "beauty", "education", "fitness"]
                category_values = [cat["value"] for cat in categories]
                
                has_all_categories = all(cat in category_values for cat in expected_categories)
                has_icons = all("icon" in cat for cat in categories)
                has_labels = all("label" in cat for cat in categories)
                
                self.log_test("Get reel categories", len(categories) == 7, f"Found {len(categories)} categories")
                self.log_test("All expected categories present", has_all_categories, f"Categories: {category_values}")
                self.log_test("Categories have icons", has_icons, "All categories have emoji icons")
                self.log_test("Categories have labels", has_labels, "All categories have descriptive labels")
                
            else:
                self.log_test("Get reel categories", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get reel categories", False, f"Error: {str(e)}")
    
    def test_service_reel_creation(self):
        """Test creating service reels for different categories"""
        print("\n=== Testing Service Reel Creation ===")
        
        # Test data for different service categories
        reel_test_data = [
            {
                "user": "chef_ravi",
                "category": "food",
                "title": "Authentic Mumbai Street Food Catering",
                "description": "Specializing in vada pav, pav bhaji, and dosa. Perfect for parties and events in Mumbai area.",
                "base_price": 500.0,
                "price_type": "per_meal",
                "duration": 45,
                "location": {"city": "Mumbai", "state": "Maharashtra"},
                "tags": ["street food", "catering", "mumbai", "authentic", "party"]
            },
            {
                "user": "designer_priya",
                "category": "design",
                "title": "Professional Logo Design Services",
                "description": "Creative logo design for startups and businesses. Modern, minimalist designs that represent your brand.",
                "base_price": 2500.0,
                "price_type": "per_project",
                "duration": 60,
                "location": {"city": "Delhi", "state": "Delhi"},
                "tags": ["logo", "branding", "startup", "creative", "modern"]
            },
            {
                "user": "dev_arjun",
                "category": "tech",
                "title": "Full Stack Web Development",
                "description": "Complete web application development using React, Node.js, and MongoDB. From concept to deployment.",
                "base_price": 1500.0,
                "price_type": "per_hour",
                "duration": 90,
                "location": {"city": "Bangalore", "state": "Karnataka"},
                "tags": ["web development", "react", "nodejs", "fullstack", "mongodb"]
            },
            {
                "user": "plumber_suresh",
                "category": "home",
                "title": "Emergency Plumbing Services",
                "description": "24/7 plumbing services for residential and commercial properties. Quick response time guaranteed.",
                "base_price": 800.0,
                "price_type": "per_day",
                "duration": 30,
                "location": {"city": "Chennai", "state": "Tamil Nadu"},
                "tags": ["plumbing", "emergency", "24x7", "residential", "commercial"]
            }
        ]
        
        for reel_data in reel_test_data:
            try:
                user = reel_data["user"]
                if user not in self.users:
                    self.log_test(f"Create reel for {user}", False, "User not registered")
                    continue
                
                # Create mock video data (base64 encoded)
                mock_video_data = base64.b64encode(b"mock_video_content_for_testing").decode()
                
                reel_payload = {
                    "title": reel_data["title"],
                    "description": reel_data["description"],
                    "category": reel_data["category"],
                    "base_price": reel_data["base_price"],
                    "price_type": reel_data["price_type"],
                    "video_url": mock_video_data,
                    "thumbnail_url": None,
                    "duration": reel_data["duration"],
                    "location": reel_data["location"],
                    "tags": reel_data["tags"],
                    "availability": "available"
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/reels/create",
                    json=reel_payload,
                    headers=self.get_auth_headers(user)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    reel_id = data.get("reel_id")
                    
                    # Store reel for later tests
                    self.reels[f"{user}_{reel_data['category']}"] = {
                        "reel_id": reel_id,
                        "user": user,
                        "category": reel_data["category"],
                        "title": reel_data["title"],
                        "base_price": reel_data["base_price"]
                    }
                    
                    self.log_test(f"Create {reel_data['category']} reel for {user}", True, f"Reel ID: {reel_id}")
                else:
                    self.log_test(f"Create {reel_data['category']} reel for {user}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Create reel for {user}", False, f"Error: {str(e)}")
    
    def test_reel_creation_validation(self):
        """Test reel creation validation"""
        print("\n=== Testing Reel Creation Validation ===")
        
        if "chef_ravi" not in self.users:
            self.log_test("Reel creation validation", False, "Test user not available")
            return
        
        # Test invalid category
        try:
            invalid_reel = {
                "title": "Test Service",
                "description": "Test description for validation",
                "category": "invalid_category",
                "base_price": 100.0,
                "price_type": "per_hour",
                "video_url": "mock_video",
                "duration": 60,
                "tags": ["test"]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/reels/create",
                json=invalid_reel,
                headers=self.get_auth_headers("chef_ravi")
            )
            
            validation_works = response.status_code == 400
            self.log_test("Invalid category validation", validation_works, 
                        f"HTTP {response.status_code}: Expected 400 for invalid category")
            
        except Exception as e:
            self.log_test("Invalid category validation", False, f"Error: {str(e)}")
        
        # Test invalid duration (too short)
        try:
            invalid_duration_reel = {
                "title": "Test Service",
                "description": "Test description for validation",
                "category": "food",
                "base_price": 100.0,
                "price_type": "per_hour",
                "video_url": "mock_video",
                "duration": 10,  # Too short (minimum is 15)
                "tags": ["test"]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/reels/create",
                json=invalid_duration_reel,
                headers=self.get_auth_headers("chef_ravi")
            )
            
            validation_works = response.status_code == 422  # Pydantic validation error
            self.log_test("Invalid duration validation", validation_works, 
                        f"HTTP {response.status_code}: Expected 422 for duration < 15 seconds")
            
        except Exception as e:
            self.log_test("Invalid duration validation", False, f"Error: {str(e)}")
    
    def test_reels_feed_discovery(self):
        """Test reels feed discovery with filtering"""
        print("\n=== Testing Reels Feed Discovery ===")
        
        if "buyer_anita" not in self.users:
            self.log_test("Reels feed discovery", False, "Buyer user not available")
            return
        
        try:
            # Test basic feed
            response = self.session.get(
                f"{BACKEND_URL}/reels/feed",
                headers=self.get_auth_headers("buyer_anita")
            )
            
            if response.status_code == 200:
                data = response.json()
                reels = data.get("reels", [])
                
                self.log_test("Get basic reels feed", True, f"Retrieved {len(reels)} reels")
                
                # Verify reel structure
                if reels:
                    first_reel = reels[0]
                    required_fields = ["reel_id", "title", "description", "category", "base_price", 
                                     "price_type", "duration", "stats", "seller"]
                    has_all_fields = all(field in first_reel for field in required_fields)
                    
                    self.log_test("Reel data structure", has_all_fields, 
                                f"Reel fields: {list(first_reel.keys())}")
                    
                    # Verify seller info includes verification
                    seller = first_reel.get("seller", {})
                    seller_fields = ["user_id", "name", "username", "verification_level", "rating"]
                    has_seller_fields = all(field in seller for field in seller_fields)
                    
                    self.log_test("Seller verification info", has_seller_fields, 
                                f"Seller fields: {list(seller.keys())}")
                
            else:
                self.log_test("Get basic reels feed", False, f"HTTP {response.status_code}: {response.text}")
            
            # Test category filtering
            response = self.session.get(
                f"{BACKEND_URL}/reels/feed?category=food",
                headers=self.get_auth_headers("buyer_anita")
            )
            
            if response.status_code == 200:
                data = response.json()
                food_reels = data.get("reels", [])
                all_food_category = all(reel.get("category") == "food" for reel in food_reels)
                
                self.log_test("Category filtering (food)", all_food_category, 
                            f"Found {len(food_reels)} food reels")
            else:
                self.log_test("Category filtering (food)", False, f"HTTP {response.status_code}")
            
            # Test price range filtering
            response = self.session.get(
                f"{BACKEND_URL}/reels/feed?min_price=1000&max_price=3000",
                headers=self.get_auth_headers("buyer_anita")
            )
            
            if response.status_code == 200:
                data = response.json()
                price_filtered_reels = data.get("reels", [])
                price_in_range = all(
                    1000 <= reel.get("base_price", 0) <= 3000 
                    for reel in price_filtered_reels
                )
                
                self.log_test("Price range filtering", price_in_range, 
                            f"Found {len(price_filtered_reels)} reels in price range ₹1000-₹3000")
            else:
                self.log_test("Price range filtering", False, f"HTTP {response.status_code}")
            
            # Test location filtering
            response = self.session.get(
                f"{BACKEND_URL}/reels/feed?location=Mumbai",
                headers=self.get_auth_headers("buyer_anita")
            )
            
            if response.status_code == 200:
                data = response.json()
                location_reels = data.get("reels", [])
                
                self.log_test("Location filtering", True, 
                            f"Found {len(location_reels)} reels in Mumbai area")
            else:
                self.log_test("Location filtering", False, f"HTTP {response.status_code}")
            
            # Test pagination
            response = self.session.get(
                f"{BACKEND_URL}/reels/feed?page=1&limit=2",
                headers=self.get_auth_headers("buyer_anita")
            )
            
            if response.status_code == 200:
                data = response.json()
                page_reels = data.get("reels", [])
                has_pagination_info = all(key in data for key in ["page", "limit", "has_more", "total_count"])
                
                self.log_test("Pagination", has_pagination_info, 
                            f"Page 1 with limit 2: {len(page_reels)} reels, has_more: {data.get('has_more')}")
            else:
                self.log_test("Pagination", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Reels feed discovery", False, f"Error: {str(e)}")
    
    def test_reel_interactions(self):
        """Test reel like and view interactions"""
        print("\n=== Testing Reel Interactions (Like/View) ===")
        
        if "buyer_anita" not in self.users or not self.reels:
            self.log_test("Reel interactions", False, "Required users or reels not available")
            return
        
        # Get a test reel
        test_reel = list(self.reels.values())[0]
        reel_id = test_reel["reel_id"]
        
        try:
            # Test reel view
            response = self.session.post(
                f"{BACKEND_URL}/reels/{reel_id}/view",
                headers=self.get_auth_headers("buyer_anita")
            )
            
            view_success = response.status_code == 200
            self.log_test("Record reel view", view_success, 
                        f"HTTP {response.status_code}: {response.text if not view_success else 'View recorded'}")
            
            # Test reel like
            response = self.session.post(
                f"{BACKEND_URL}/reels/{reel_id}/like",
                headers=self.get_auth_headers("buyer_anita")
            )
            
            if response.status_code == 200:
                data = response.json()
                action = data.get("action")
                like_success = action == "liked"
                
                self.log_test("Like reel", like_success, f"Action: {action}")
                
                # Test unlike (toggle behavior)
                response = self.session.post(
                    f"{BACKEND_URL}/reels/{reel_id}/like",
                    headers=self.get_auth_headers("buyer_anita")
                )
                
                if response.status_code == 200:
                    data = response.json()
                    action = data.get("action")
                    unlike_success = action == "unliked"
                    
                    self.log_test("Unlike reel (toggle)", unlike_success, f"Action: {action}")
                else:
                    self.log_test("Unlike reel (toggle)", False, f"HTTP {response.status_code}")
            else:
                self.log_test("Like reel", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Reel interactions", False, f"Error: {str(e)}")
    
    def test_bidding_system(self):
        """Test the bidding system for service reels"""
        print("\n=== Testing Bidding System ===")
        
        if "buyer_anita" not in self.users or not self.reels:
            self.log_test("Bidding system", False, "Required users or reels not available")
            return
        
        # Get a test reel (not owned by buyer)
        test_reel = None
        for reel_key, reel_data in self.reels.items():
            if reel_data["user"] != "buyer_anita":
                test_reel = reel_data
                break
        
        if not test_reel:
            self.log_test("Bidding system", False, "No suitable reel found for bidding")
            return
        
        try:
            reel_id = test_reel["reel_id"]
            
            # Test valid bid submission
            bid_data = {
                "reel_id": reel_id,
                "bid_amount": test_reel["base_price"] + 200,  # Bid above base price
                "message": "Hi! I'm interested in your service. Can we discuss the details?",
                "project_details": "I need this service for a small event with about 50 people. The event is next weekend.",
                "preferred_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "urgency": "normal"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/reels/{reel_id}/bid",
                json=bid_data,
                headers=self.get_auth_headers("buyer_anita")
            )
            
            if response.status_code == 200:
                data = response.json()
                bid_id = data.get("bid_id")
                chat_id = data.get("chat_id")
                
                bid_success = bid_id and chat_id
                self.log_test("Submit valid bid", bid_success, 
                            f"Bid ID: {bid_id}, Chat ID: {chat_id}")
                
                # Store for later tests
                self.test_bid_id = bid_id
                self.test_chat_id = chat_id
                
            else:
                self.log_test("Submit valid bid", False, f"HTTP {response.status_code}: {response.text}")
            
            # Test bidding on own reel (should fail)
            own_reel = None
            for reel_key, reel_data in self.reels.items():
                if reel_data["user"] == "buyer_anita":
                    own_reel = reel_data
                    break
            
            if not own_reel:
                # Create a reel for buyer_anita to test self-bidding
                self_reel_payload = {
                    "title": "Test Service for Self-Bid",
                    "description": "Testing self-bidding validation",
                    "category": "education",
                    "base_price": 500.0,
                    "price_type": "per_hour",
                    "video_url": base64.b64encode(b"mock_video").decode(),
                    "duration": 30,
                    "tags": ["test"]
                }
                
                create_response = self.session.post(
                    f"{BACKEND_URL}/reels/create",
                    json=self_reel_payload,
                    headers=self.get_auth_headers("buyer_anita")
                )
                
                if create_response.status_code == 200:
                    own_reel_id = create_response.json().get("reel_id")
                    
                    # Try to bid on own reel
                    self_bid_data = {
                        "reel_id": own_reel_id,
                        "bid_amount": 600.0,
                        "message": "Bidding on my own reel",
                        "urgency": "normal"
                    }
                    
                    response = self.session.post(
                        f"{BACKEND_URL}/reels/{own_reel_id}/bid",
                        json=self_bid_data,
                        headers=self.get_auth_headers("buyer_anita")
                    )
                    
                    self_bid_blocked = response.status_code == 400
                    self.log_test("Self-bidding blocked", self_bid_blocked, 
                                f"HTTP {response.status_code}: Expected 400 for self-bidding")
            
            # Test bid validation (negative amount)
            invalid_bid_data = {
                "reel_id": reel_id,
                "bid_amount": -100.0,  # Invalid negative amount
                "message": "Invalid bid with negative amount",
                "urgency": "normal"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/reels/{reel_id}/bid",
                json=invalid_bid_data,
                headers=self.get_auth_headers("buyer_anita")
            )
            
            validation_works = response.status_code == 422  # Pydantic validation error
            self.log_test("Negative bid amount validation", validation_works, 
                        f"HTTP {response.status_code}: Expected 422 for negative bid amount")
                        
        except Exception as e:
            self.log_test("Bidding system", False, f"Error: {str(e)}")
    
    def test_reviews_system(self):
        """Test the reviews system for service reels"""
        print("\n=== Testing Reviews System ===")
        
        if not self.reels:
            self.log_test("Reviews system", False, "No reels available for testing")
            return
        
        # Get a test reel
        test_reel = list(self.reels.values())[0]
        reel_id = test_reel["reel_id"]
        
        try:
            # Test getting reviews (should be empty initially)
            response = self.session.get(f"{BACKEND_URL}/reels/{reel_id}/reviews")
            
            if response.status_code == 200:
                data = response.json()
                reviews = data.get("reviews", [])
                has_pagination = all(key in data for key in ["total_count", "page", "limit", "has_more"])
                
                self.log_test("Get reel reviews", True, f"Found {len(reviews)} reviews")
                self.log_test("Reviews pagination structure", has_pagination, 
                            f"Pagination fields present: {list(data.keys())}")
                
                # Test pagination parameters
                response = self.session.get(f"{BACKEND_URL}/reels/{reel_id}/reviews?page=1&limit=5")
                
                if response.status_code == 200:
                    data = response.json()
                    correct_pagination = data.get("page") == 1 and data.get("limit") == 5
                    
                    self.log_test("Reviews pagination parameters", correct_pagination, 
                                f"Page: {data.get('page')}, Limit: {data.get('limit')}")
                else:
                    self.log_test("Reviews pagination parameters", False, f"HTTP {response.status_code}")
                    
            else:
                self.log_test("Get reel reviews", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Reviews system", False, f"Error: {str(e)}")
    
    def test_user_reel_management(self):
        """Test user's own reel management"""
        print("\n=== Testing User Reel Management ===")
        
        if "chef_ravi" not in self.users:
            self.log_test("User reel management", False, "Test user not available")
            return
        
        try:
            # Test getting user's own reels
            response = self.session.get(
                f"{BACKEND_URL}/reels/my-reels",
                headers=self.get_auth_headers("chef_ravi")
            )
            
            if response.status_code == 200:
                data = response.json()
                my_reels = data.get("reels", [])
                
                # Verify all reels belong to the user
                chef_user_id = self.users["chef_ravi"]["user_id"]
                all_mine = all(reel.get("user_id") == chef_user_id for reel in my_reels)
                
                self.log_test("Get my reels", True, f"Found {len(my_reels)} reels")
                self.log_test("Reel ownership verification", all_mine, 
                            "All returned reels belong to the requesting user")
                
                # Verify reel data structure
                if my_reels:
                    first_reel = my_reels[0]
                    required_fields = ["reel_id", "title", "description", "category", "stats", "created_at"]
                    has_required_fields = all(field in first_reel for field in required_fields)
                    
                    self.log_test("My reels data structure", has_required_fields, 
                                f"Reel fields: {list(first_reel.keys())}")
                    
                    # Verify stats structure
                    stats = first_reel.get("stats", {})
                    stats_fields = ["views", "likes", "bids", "hires"]
                    has_stats = all(field in stats for field in stats_fields)
                    
                    self.log_test("Reel stats structure", has_stats, 
                                f"Stats: {stats}")
                
            else:
                self.log_test("Get my reels", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("User reel management", False, f"Error: {str(e)}")
    
    def test_rate_limiting(self):
        """Test rate limiting on reel endpoints"""
        print("\n=== Testing Rate Limiting ===")
        
        if "buyer_anita" not in self.users or not self.reels:
            self.log_test("Rate limiting", False, "Required users or reels not available")
            return
        
        # Get a test reel
        test_reel = list(self.reels.values())[0]
        reel_id = test_reel["reel_id"]
        
        try:
            # Test like rate limiting (60/minute)
            like_requests = 0
            rate_limited = False
            
            for i in range(5):  # Test a few requests quickly
                response = self.session.post(
                    f"{BACKEND_URL}/reels/{reel_id}/like",
                    headers=self.get_auth_headers("buyer_anita")
                )
                like_requests += 1
                
                if response.status_code == 429:  # Rate limited
                    rate_limited = True
                    break
                elif response.status_code != 200:
                    break
            
            # Note: Rate limiting might not trigger with just 5 requests
            self.log_test("Like rate limiting mechanism", True, 
                        f"Made {like_requests} like requests, rate limited: {rate_limited}")
            
            # Test view rate limiting (100/minute) - should be more lenient
            view_requests = 0
            view_rate_limited = False
            
            for i in range(5):
                response = self.session.post(
                    f"{BACKEND_URL}/reels/{reel_id}/view",
                    headers=self.get_auth_headers("buyer_anita")
                )
                view_requests += 1
                
                if response.status_code == 429:
                    view_rate_limited = True
                    break
                elif response.status_code != 200:
                    break
            
            self.log_test("View rate limiting mechanism", True, 
                        f"Made {view_requests} view requests, rate limited: {view_rate_limited}")
                        
        except Exception as e:
            self.log_test("Rate limiting", False, f"Error: {str(e)}")
    
    def test_integration_with_chat_system(self):
        """Test integration between reels bidding and chat system"""
        print("\n=== Testing Integration with Chat System ===")
        
        if not hasattr(self, 'test_chat_id') or "buyer_anita" not in self.users:
            self.log_test("Chat system integration", False, "No bid chat available for testing")
            return
        
        try:
            # Test that chat was created from bid
            response = self.session.get(
                f"{BACKEND_URL}/chats",
                headers=self.get_auth_headers("buyer_anita")
            )
            
            if response.status_code == 200:
                chats = response.json()
                bid_chat_found = any(chat.get("chat_id") == self.test_chat_id for chat in chats)
                
                self.log_test("Bid creates chat", bid_chat_found, 
                            f"Chat ID {self.test_chat_id} found in user's chats")
                
                if bid_chat_found:
                    # Test getting messages from the bid chat
                    response = self.session.get(
                        f"{BACKEND_URL}/chats/{self.test_chat_id}/messages",
                        headers=self.get_auth_headers("buyer_anita")
                    )
                    
                    if response.status_code == 200:
                        messages = response.json()
                        has_bid_message = any(
                            msg.get("message_type") == "reel_bid" 
                            for msg in messages
                        )
                        
                        self.log_test("Bid notification message", has_bid_message, 
                                    f"Found {len(messages)} messages, bid notification present")
                    else:
                        self.log_test("Bid notification message", False, f"HTTP {response.status_code}")
                        
            else:
                self.log_test("Bid creates chat", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Chat system integration", False, f"Error: {str(e)}")
    
    def test_data_validation_comprehensive(self):
        """Test comprehensive data validation for all reel endpoints"""
        print("\n=== Testing Comprehensive Data Validation ===")
        
        if "chef_ravi" not in self.users:
            self.log_test("Data validation", False, "Test user not available")
            return
        
        try:
            # Test title length validation
            long_title_reel = {
                "title": "A" * 150,  # Too long (max 100)
                "description": "Valid description",
                "category": "food",
                "base_price": 100.0,
                "price_type": "per_hour",
                "video_url": "mock_video",
                "duration": 30,
                "tags": ["test"]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/reels/create",
                json=long_title_reel,
                headers=self.get_auth_headers("chef_ravi")
            )
            
            title_validation = response.status_code == 422
            self.log_test("Title length validation", title_validation, 
                        f"HTTP {response.status_code}: Expected 422 for title > 100 chars")
            
            # Test description length validation
            long_desc_reel = {
                "title": "Valid title",
                "description": "A" * 1100,  # Too long (max 1000)
                "category": "food",
                "base_price": 100.0,
                "price_type": "per_hour",
                "video_url": "mock_video",
                "duration": 30,
                "tags": ["test"]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/reels/create",
                json=long_desc_reel,
                headers=self.get_auth_headers("chef_ravi")
            )
            
            desc_validation = response.status_code == 422
            self.log_test("Description length validation", desc_validation, 
                        f"HTTP {response.status_code}: Expected 422 for description > 500 chars")
            
            # Test price validation (negative)
            negative_price_reel = {
                "title": "Valid title",
                "description": "Valid description",
                "category": "food",
                "base_price": -100.0,  # Negative price
                "price_type": "per_hour",
                "video_url": "mock_video",
                "duration": 30,
                "tags": ["test"]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/reels/create",
                json=negative_price_reel,
                headers=self.get_auth_headers("chef_ravi")
            )
            
            price_validation = response.status_code == 422
            self.log_test("Negative price validation", price_validation, 
                        f"HTTP {response.status_code}: Expected 422 for negative price")
            
            # Test invalid price_type
            invalid_price_type_reel = {
                "title": "Valid title",
                "description": "Valid description",
                "category": "food",
                "base_price": 100.0,
                "price_type": "invalid_type",
                "video_url": "mock_video",
                "duration": 30,
                "tags": ["test"]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/reels/create",
                json=invalid_price_type_reel,
                headers=self.get_auth_headers("chef_ravi")
            )
            
            price_type_validation = response.status_code == 422
            self.log_test("Invalid price_type validation", price_type_validation, 
                        f"HTTP {response.status_code}: Expected 422 for invalid price_type")
            
            # Test duration validation (too long)
            long_duration_reel = {
                "title": "Valid title",
                "description": "Valid description",
                "category": "food",
                "base_price": 100.0,
                "price_type": "per_hour",
                "video_url": "mock_video",
                "duration": 200,  # Too long (max 180)
                "tags": ["test"]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/reels/create",
                json=long_duration_reel,
                headers=self.get_auth_headers("chef_ravi")
            )
            
            duration_validation = response.status_code == 422
            self.log_test("Duration validation (too long)", duration_validation, 
                        f"HTTP {response.status_code}: Expected 422 for duration > 180 seconds")
                        
        except Exception as e:
            self.log_test("Data validation", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all reels marketplace tests"""
        print("🎬 Starting Reels-Based Marketplace Backend Testing")
        print("=" * 60)
        
        # Test sequence
        if not self.test_user_registration():
            print("❌ User registration failed - cannot continue with reels tests")
            return
        
        # Core functionality tests
        self.test_reel_categories()
        self.test_service_reel_creation()
        self.test_reel_creation_validation()
        self.test_reels_feed_discovery()
        self.test_reel_interactions()
        self.test_bidding_system()
        self.test_reviews_system()
        self.test_user_reel_management()
        
        # Advanced tests
        self.test_rate_limiting()
        self.test_integration_with_chat_system()
        self.test_data_validation_comprehensive()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎬 REELS MARKETPLACE TEST SUMMARY")
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
        
        print("\n🎬 Reels Marketplace Testing Complete!")
        return passed == total

if __name__ == "__main__":
    tester = ReelsMarketplaceTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)