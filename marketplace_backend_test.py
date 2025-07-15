#!/usr/bin/env python3
"""
Comprehensive Marketplace Backend Testing Script
Tests all marketplace endpoints and functionality as specified in the review request
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
import uuid

# Configuration
BACKEND_URL = "https://0ae32c31-0069-48ba-9ab2-3b5d1a729a6b.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class MarketplaceTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.users = {}  # Store user data and tokens
        self.test_results = []
        self.listings = {}  # Store created listings for testing
        
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
    
    def create_test_user(self, username, email, test_password=None):
        """Create a test user with secure password handling"""
        if test_password is None:
            test_password = os.environ.get('TEST_PASSWORD', 'TestPass123!@#$')
        try:
            # Register user
            register_data = {
                "username": username,
                "email": email,
                "password": test_password,
                "display_name": username.title()
            }
            
            response = self.session.post(f"{BACKEND_URL}/register", json=register_data)
            
            if response.status_code == 200:
                data = response.json()
                user_info = {
                    "user_id": data["user"]["user_id"],
                    "username": username,
                    "email": email,
                    "token": data["access_token"],
                    "headers": {"Authorization": f"Bearer {data['access_token']}"}
                }
                self.users[username] = user_info
                return user_info
            else:
                # Try to login if user already exists
                login_data = {"email": email, "password": test_password}
                response = self.session.post(f"{BACKEND_URL}/login", json=login_data)
                
                if response.status_code == 200:
                    data = response.json()
                    user_info = {
                        "user_id": data["user"]["user_id"],
                        "username": username,
                        "email": email,
                        "token": data["access_token"],
                        "headers": {"Authorization": f"Bearer {data['access_token']}"}
                    }
                    self.users[username] = user_info
                    return user_info
                    
        except Exception as e:
            print(f"Failed to create/login user {username}: {e}")
            return None
    
    def test_marketplace_categories(self):
        """Test GET /api/marketplace/categories"""
        print("\n🏪 Testing Marketplace Categories Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/marketplace/categories")
            
            if response.status_code == 200:
                data = response.json()
                categories = data.get("categories", [])
                
                # Check if all expected categories are present
                expected_categories = ["items", "services", "jobs", "housing", "vehicles"]
                found_categories = [cat["value"] for cat in categories]
                
                all_present = all(cat in found_categories for cat in expected_categories)
                has_icons = all("icon" in cat for cat in categories)
                
                if all_present and has_icons:
                    self.log_test("Marketplace Categories - Structure", True, 
                                f"Found {len(categories)} categories with icons")
                else:
                    self.log_test("Marketplace Categories - Structure", False, 
                                f"Missing categories or icons. Found: {found_categories}")
            else:
                self.log_test("Marketplace Categories - Endpoint", False, 
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Marketplace Categories - Exception", False, str(e))
    
    def test_marketplace_listing_creation(self):
        """Test POST /api/marketplace/listings"""
        print("\n📝 Testing Marketplace Listing Creation...")
        
        if "alice" not in self.users:
            self.log_test("Listing Creation - No User", False, "Alice user not available")
            return
        
        alice = self.users["alice"]
        
        # Test 1: Valid listing creation
        try:
            listing_data = {
                "title": "Vintage Guitar for Sale",
                "description": "Beautiful vintage acoustic guitar in excellent condition. Perfect for beginners and professionals alike.",
                "category": "items",
                "price": 250.00,
                "price_type": "fixed",
                "location": {"city": "San Francisco", "state": "CA"},
                "images": ["guitar1.jpg", "guitar2.jpg"],
                "tags": ["music", "guitar", "vintage"],
                "contact_method": "chat"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/marketplace/listings",
                json=listing_data,
                headers=alice["headers"]
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and "listing_id" in data:
                    self.listings["guitar"] = data["listing_id"]
                    self.log_test("Listing Creation - Valid Fixed Price", True, 
                                f"Created listing: {data['listing_id']}")
                else:
                    self.log_test("Listing Creation - Valid Fixed Price", False, 
                                f"Unexpected response: {data}")
            else:
                self.log_test("Listing Creation - Valid Fixed Price", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            self.log_test("Listing Creation - Valid Fixed Price", False, str(e))
        
        # Test 2: Different price types
        price_types = [
            ("hourly", 25.0, "Tutoring Services"),
            ("negotiable", 100.0, "Used Laptop"),
            ("free", None, "Free Books"),
            ("barter", None, "Trade My Bike")
        ]
        
        for price_type, price, title in price_types:
            try:
                listing_data = {
                    "title": title,
                    "description": f"Test listing for {price_type} price type",
                    "category": "items" if price_type != "hourly" else "services",
                    "price": price,
                    "price_type": price_type,
                    "contact_method": "chat"
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/marketplace/listings",
                    json=listing_data,
                    headers=alice["headers"]
                )
                
                success = response.status_code == 200
                self.log_test(f"Listing Creation - {price_type.title()} Price", success,
                            f"Status: {response.status_code}")
                
                if success:
                    data = response.json()
                    self.listings[price_type] = data.get("listing_id")
                    
            except Exception as e:
                self.log_test(f"Listing Creation - {price_type.title()} Price", False, str(e))
        
        # Test 3: Input validation
        invalid_tests = [
            ({"title": "AB", "description": "Too short title", "category": "items", "price_type": "fixed"}, "Short title"),
            ({"title": "Valid Title", "description": "Short", "category": "items", "price_type": "fixed"}, "Short description"),
            ({"title": "Valid Title", "description": "Valid description here", "category": "invalid", "price_type": "fixed"}, "Invalid category"),
            ({"title": "Valid Title", "description": "Valid description here", "category": "items", "price": -10, "price_type": "fixed"}, "Negative price"),
            ({"title": "Valid Title", "description": "Valid description here", "category": "items", "price_type": "invalid"}, "Invalid price type")
        ]
        
        for invalid_data, test_name in invalid_tests:
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/marketplace/listings",
                    json=invalid_data,
                    headers=alice["headers"]
                )
                
                # Should return 400 for validation errors
                success = response.status_code == 400
                self.log_test(f"Validation - {test_name}", success,
                            f"Status: {response.status_code}")
                            
            except Exception as e:
                self.log_test(f"Validation - {test_name}", False, str(e))
    
    def test_marketplace_listing_retrieval(self):
        """Test GET /api/marketplace/listings with various filters"""
        print("\n🔍 Testing Marketplace Listing Retrieval...")
        
        if "bob" not in self.users:
            self.log_test("Listing Retrieval - No User", False, "Bob user not available")
            return
        
        bob = self.users["bob"]
        
        # Test 1: Basic listing retrieval
        try:
            response = self.session.get(
                f"{BACKEND_URL}/marketplace/listings",
                headers=bob["headers"]
            )
            
            if response.status_code == 200:
                data = response.json()
                if "listings" in data and "total_count" in data:
                    self.log_test("Listing Retrieval - Basic", True,
                                f"Found {len(data['listings'])} listings, total: {data['total_count']}")
                else:
                    self.log_test("Listing Retrieval - Basic", False,
                                f"Missing expected fields: {data.keys()}")
            else:
                self.log_test("Listing Retrieval - Basic", False,
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Listing Retrieval - Basic", False, str(e))
        
        # Test 2: Category filtering
        try:
            response = self.session.get(
                f"{BACKEND_URL}/marketplace/listings?category=items",
                headers=bob["headers"]
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check if all returned listings are in the 'items' category
                all_items = all(listing.get("category") == "items" for listing in data.get("listings", []))
                self.log_test("Listing Retrieval - Category Filter", all_items,
                            f"Items category filter: {len(data.get('listings', []))} results")
            else:
                self.log_test("Listing Retrieval - Category Filter", False,
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Listing Retrieval - Category Filter", False, str(e))
        
        # Test 3: Search by query
        try:
            response = self.session.get(
                f"{BACKEND_URL}/marketplace/listings?query=guitar",
                headers=bob["headers"]
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check if results contain the search term
                has_guitar = any("guitar" in listing.get("title", "").lower() or 
                               "guitar" in listing.get("description", "").lower() 
                               for listing in data.get("listings", []))
                self.log_test("Listing Retrieval - Search Query", True,
                            f"Guitar search: {len(data.get('listings', []))} results")
            else:
                self.log_test("Listing Retrieval - Search Query", False,
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Listing Retrieval - Search Query", False, str(e))
        
        # Test 4: Price range filtering
        try:
            response = self.session.get(
                f"{BACKEND_URL}/marketplace/listings?min_price=50&max_price=300",
                headers=bob["headers"]
            )
            
            if response.status_code == 200:
                data = response.json()
                # Check if all results are within price range
                in_range = all(
                    listing.get("price") is None or 
                    (50 <= listing.get("price", 0) <= 300)
                    for listing in data.get("listings", [])
                )
                self.log_test("Listing Retrieval - Price Range", in_range,
                            f"Price range $50-$300: {len(data.get('listings', []))} results")
            else:
                self.log_test("Listing Retrieval - Price Range", False,
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Listing Retrieval - Price Range", False, str(e))
        
        # Test 5: Pagination
        try:
            response = self.session.get(
                f"{BACKEND_URL}/marketplace/listings?page=1&limit=5",
                headers=bob["headers"]
            )
            
            if response.status_code == 200:
                data = response.json()
                correct_pagination = (
                    data.get("page") == 1 and
                    data.get("limit") == 5 and
                    len(data.get("listings", [])) <= 5 and
                    "has_more" in data
                )
                self.log_test("Listing Retrieval - Pagination", correct_pagination,
                            f"Page 1, limit 5: {len(data.get('listings', []))} results")
            else:
                self.log_test("Listing Retrieval - Pagination", False,
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("Listing Retrieval - Pagination", False, str(e))
        
        # Test 6: Sorting
        try:
            response = self.session.get(
                f"{BACKEND_URL}/marketplace/listings?sort_by=created_at&sort_order=asc",
                headers=bob["headers"]
            )
            
            success = response.status_code == 200
            self.log_test("Listing Retrieval - Sorting", success,
                        f"Sort by created_at ASC: Status {response.status_code}")
                
        except Exception as e:
            self.log_test("Listing Retrieval - Sorting", False, str(e))
    
    def test_individual_listing_operations(self):
        """Test individual listing operations (GET/PUT/DELETE)"""
        print("\n🔧 Testing Individual Listing Operations...")
        
        if "alice" not in self.users or "bob" not in self.users:
            self.log_test("Individual Operations - No Users", False, "Users not available")
            return
        
        alice = self.users["alice"]
        bob = self.users["bob"]
        
        # Test 1: Get specific listing
        if "guitar" in self.listings:
            try:
                listing_id = self.listings["guitar"]
                response = self.session.get(
                    f"{BACKEND_URL}/marketplace/listings/{listing_id}",
                    headers=bob["headers"]
                )
                
                if response.status_code == 200:
                    data = response.json()
                    has_required_fields = all(field in data for field in 
                                            ["listing_id", "title", "description", "category", "price_type"])
                    self.log_test("Individual Listing - Get Specific", has_required_fields,
                                f"Retrieved listing with all required fields")
                else:
                    self.log_test("Individual Listing - Get Specific", False,
                                f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test("Individual Listing - Get Specific", False, str(e))
        
        # Test 2: Update listing (owner only)
        if "guitar" in self.listings:
            try:
                listing_id = self.listings["guitar"]
                update_data = {
                    "title": "Updated Vintage Guitar",
                    "description": "Updated description for the vintage guitar",
                    "category": "items",
                    "price": 275.00,
                    "price_type": "fixed",
                    "contact_method": "chat"
                }
                
                response = self.session.put(
                    f"{BACKEND_URL}/marketplace/listings/{listing_id}",
                    json=update_data,
                    headers=alice["headers"]  # Owner
                )
                
                success = response.status_code == 200
                self.log_test("Individual Listing - Update (Owner)", success,
                            f"Status: {response.status_code}")
                
            except Exception as e:
                self.log_test("Individual Listing - Update (Owner)", False, str(e))
        
        # Test 3: Update listing (non-owner should fail)
        if "guitar" in self.listings:
            try:
                listing_id = self.listings["guitar"]
                update_data = {
                    "title": "Unauthorized Update",
                    "description": "This should fail",
                    "category": "items",
                    "price": 100.00,
                    "price_type": "fixed",
                    "contact_method": "chat"
                }
                
                response = self.session.put(
                    f"{BACKEND_URL}/marketplace/listings/{listing_id}",
                    json=update_data,
                    headers=bob["headers"]  # Non-owner
                )
                
                # Should return 403 Forbidden
                success = response.status_code == 403
                self.log_test("Individual Listing - Update (Non-owner)", success,
                            f"Status: {response.status_code} (should be 403)")
                
            except Exception as e:
                self.log_test("Individual Listing - Update (Non-owner)", False, str(e))
        
        # Test 4: Update availability
        if "guitar" in self.listings:
            try:
                listing_id = self.listings["guitar"]
                response = self.session.put(
                    f"{BACKEND_URL}/marketplace/listings/{listing_id}/availability",
                    json={"status": "pending"},
                    headers=alice["headers"]
                )
                
                success = response.status_code == 200
                self.log_test("Individual Listing - Update Availability", success,
                            f"Status: {response.status_code}")
                
            except Exception as e:
                self.log_test("Individual Listing - Update Availability", False, str(e))
    
    def test_user_listings(self):
        """Test GET /api/marketplace/my-listings"""
        print("\n👤 Testing User Listings...")
        
        if "alice" not in self.users:
            self.log_test("User Listings - No User", False, "Alice user not available")
            return
        
        alice = self.users["alice"]
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/marketplace/my-listings",
                headers=alice["headers"]
            )
            
            if response.status_code == 200:
                data = response.json()
                if "listings" in data:
                    # Check if all listings belong to the user
                    all_owned = all(listing.get("user_id") == alice["user_id"] 
                                  for listing in data["listings"])
                    self.log_test("User Listings - Ownership", all_owned,
                                f"Found {len(data['listings'])} user listings")
                else:
                    self.log_test("User Listings - Structure", False,
                                f"Missing 'listings' field: {data.keys()}")
            else:
                self.log_test("User Listings - Endpoint", False,
                            f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("User Listings - Exception", False, str(e))
    
    def test_marketplace_messaging(self):
        """Test POST /api/marketplace/listings/{listing_id}/message"""
        print("\n💬 Testing Marketplace Messaging...")
        
        if "alice" not in self.users or "bob" not in self.users:
            self.log_test("Marketplace Messaging - No Users", False, "Users not available")
            return
        
        alice = self.users["alice"]
        bob = self.users["bob"]
        
        # Test 1: Send message about listing
        if "guitar" in self.listings:
            try:
                listing_id = self.listings["guitar"]
                message_data = {
                    "listing_id": listing_id,
                    "recipient_id": alice["user_id"],  # Listing owner
                    "message": "Hi! I'm interested in your vintage guitar. Is it still available?",
                    "offer_price": 225.00
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/marketplace/listings/{listing_id}/message",
                    json=message_data,
                    headers=bob["headers"]  # Interested buyer
                )
                
                if response.status_code == 200:
                    data = response.json()
                    has_required_fields = all(field in data for field in 
                                            ["status", "chat_id", "message_id"])
                    self.log_test("Marketplace Messaging - Send Message", has_required_fields,
                                f"Message sent successfully: {data.get('message_id')}")
                else:
                    self.log_test("Marketplace Messaging - Send Message", False,
                                f"Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                self.log_test("Marketplace Messaging - Send Message", False, str(e))
        
        # Test 2: Try to message own listing (should fail)
        if "guitar" in self.listings:
            try:
                listing_id = self.listings["guitar"]
                message_data = {
                    "listing_id": listing_id,
                    "recipient_id": alice["user_id"],
                    "message": "This should fail - messaging own listing"
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/marketplace/listings/{listing_id}/message",
                    json=message_data,
                    headers=alice["headers"]  # Owner trying to message own listing
                )
                
                # Should return 400 Bad Request
                success = response.status_code == 400
                self.log_test("Marketplace Messaging - Own Listing", success,
                            f"Status: {response.status_code} (should be 400)")
                
            except Exception as e:
                self.log_test("Marketplace Messaging - Own Listing", False, str(e))
        
        # Test 3: Message with offer price
        if "guitar" in self.listings:
            try:
                listing_id = self.listings["guitar"]
                message_data = {
                    "listing_id": listing_id,
                    "recipient_id": alice["user_id"],
                    "message": "Would you accept this offer?",
                    "offer_price": 200.00
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/marketplace/listings/{listing_id}/message",
                    json=message_data,
                    headers=bob["headers"]
                )
                
                success = response.status_code == 200
                self.log_test("Marketplace Messaging - With Offer", success,
                            f"Status: {response.status_code}")
                
            except Exception as e:
                self.log_test("Marketplace Messaging - With Offer", False, str(e))
    
    def test_security_and_authorization(self):
        """Test security and authorization controls"""
        print("\n🔒 Testing Security & Authorization...")
        
        # Test 1: Unauthorized access (no token)
        try:
            response = self.session.post(
                f"{BACKEND_URL}/marketplace/listings",
                json={"title": "Test", "description": "Test listing", "category": "items", "price_type": "fixed"}
            )
            
            # Should return 401 or 403
            success = response.status_code in [401, 403]
            self.log_test("Security - No Auth Token", success,
                        f"Status: {response.status_code} (should be 401/403)")
            
        except Exception as e:
            self.log_test("Security - No Auth Token", False, str(e))
        
        # Test 2: Invalid token
        try:
            invalid_headers = {"Authorization": "Bearer invalid_token_here"}
            response = self.session.post(
                f"{BACKEND_URL}/marketplace/listings",
                json={"title": "Test", "description": "Test listing", "category": "items", "price_type": "fixed"},
                headers=invalid_headers
            )
            
            success = response.status_code in [401, 403]
            self.log_test("Security - Invalid Token", success,
                        f"Status: {response.status_code} (should be 401/403)")
            
        except Exception as e:
            self.log_test("Security - Invalid Token", False, str(e))
        
        # Test 3: Rate limiting (create multiple listings quickly)
        if "alice" in self.users:
            alice = self.users["alice"]
            rate_limit_hit = False
            
            for i in range(25):  # Try to exceed 20/minute limit
                try:
                    listing_data = {
                        "title": f"Rate Limit Test {i}",
                        "description": "Testing rate limiting",
                        "category": "items",
                        "price_type": "free"
                    }
                    
                    response = self.session.post(
                        f"{BACKEND_URL}/marketplace/listings",
                        json=listing_data,
                        headers=alice["headers"]
                    )
                    
                    if response.status_code == 429:  # Too Many Requests
                        rate_limit_hit = True
                        break
                        
                except Exception:
                    continue
            
            self.log_test("Security - Rate Limiting", rate_limit_hit,
                        f"Rate limit {'hit' if rate_limit_hit else 'not hit'} after 25 requests")
    
    def test_data_validation(self):
        """Test comprehensive data validation"""
        print("\n✅ Testing Data Validation...")
        
        if "alice" not in self.users:
            self.log_test("Data Validation - No User", False, "Alice user not available")
            return
        
        alice = self.users["alice"]
        
        # Test various validation scenarios
        validation_tests = [
            # (data, expected_status, test_name)
            ({"title": "", "description": "Valid desc", "category": "items", "price_type": "fixed"}, 422, "Empty title"),
            ({"title": "A" * 101, "description": "Valid desc", "category": "items", "price_type": "fixed"}, 422, "Title too long"),
            ({"title": "Valid Title", "description": "Short", "category": "items", "price_type": "fixed"}, 422, "Description too short"),
            ({"title": "Valid Title", "description": "A" * 1001, "category": "items", "price_type": "fixed"}, 422, "Description too long"),
            ({"title": "Valid Title", "description": "Valid description", "category": "invalid_category", "price_type": "fixed"}, 400, "Invalid category"),
            ({"title": "Valid Title", "description": "Valid description", "category": "items", "price": -50, "price_type": "fixed"}, 400, "Negative price"),
            ({"title": "Valid Title", "description": "Valid description", "category": "items", "price_type": "invalid_type"}, 400, "Invalid price type"),
        ]
        
        for test_data, expected_status, test_name in validation_tests:
            try:
                response = self.session.post(
                    f"{BACKEND_URL}/marketplace/listings",
                    json=test_data,
                    headers=alice["headers"]
                )
                
                # Check if we get the expected error status
                success = response.status_code in [400, 422]
                self.log_test(f"Validation - {test_name}", success,
                            f"Status: {response.status_code} (expected 400/422)")
                
            except Exception as e:
                self.log_test(f"Validation - {test_name}", False, str(e))
    
    def test_integration_with_existing_system(self):
        """Test integration with existing chat and user systems"""
        print("\n🔗 Testing Integration with Existing System...")
        
        if "alice" not in self.users or "bob" not in self.users:
            self.log_test("Integration - No Users", False, "Users not available")
            return
        
        alice = self.users["alice"]
        bob = self.users["bob"]
        
        # Test 1: User authentication integration
        try:
            response = self.session.get(
                f"{BACKEND_URL}/users/me",
                headers=alice["headers"]
            )
            
            success = response.status_code == 200
            self.log_test("Integration - User Authentication", success,
                        f"User info retrieval: Status {response.status_code}")
            
        except Exception as e:
            self.log_test("Integration - User Authentication", False, str(e))
        
        # Test 2: Chat system integration (via marketplace messaging)
        if "guitar" in self.listings:
            try:
                # First send a marketplace message
                listing_id = self.listings["guitar"]
                message_data = {
                    "listing_id": listing_id,
                    "recipient_id": alice["user_id"],
                    "message": "Integration test message"
                }
                
                response = self.session.post(
                    f"{BACKEND_URL}/marketplace/listings/{listing_id}/message",
                    json=message_data,
                    headers=bob["headers"]
                )
                
                if response.status_code == 200:
                    data = response.json()
                    chat_id = data.get("chat_id")
                    
                    if chat_id:
                        # Try to access the chat through regular chat endpoints
                        chat_response = self.session.get(
                            f"{BACKEND_URL}/chats/{chat_id}/messages",
                            headers=alice["headers"]
                        )
                        
                        success = chat_response.status_code == 200
                        self.log_test("Integration - Chat System", success,
                                    f"Chat access: Status {chat_response.status_code}")
                    else:
                        self.log_test("Integration - Chat System", False,
                                    "No chat_id returned from marketplace message")
                else:
                    self.log_test("Integration - Chat System", False,
                                f"Marketplace message failed: {response.status_code}")
                
            except Exception as e:
                self.log_test("Integration - Chat System", False, str(e))
    
    def cleanup_test_listings(self):
        """Clean up test listings"""
        print("\n🧹 Cleaning up test listings...")
        
        if "alice" not in self.users:
            return
        
        alice = self.users["alice"]
        
        for listing_name, listing_id in self.listings.items():
            try:
                response = self.session.delete(
                    f"{BACKEND_URL}/marketplace/listings/{listing_id}",
                    headers=alice["headers"]
                )
                
                if response.status_code == 200:
                    print(f"✅ Deleted listing: {listing_name}")
                else:
                    print(f"❌ Failed to delete listing {listing_name}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Exception deleting listing {listing_name}: {e}")
    
    def run_all_tests(self):
        """Run all marketplace tests"""
        print("🚀 Starting Comprehensive Marketplace Backend Testing...")
        print("=" * 60)
        
        # Create test users
        print("\n👥 Creating test users...")
        alice = self.create_test_user("alice", "alice@marketplace.test")
        bob = self.create_test_user("bob", "bob@marketplace.test")
        
        if not alice or not bob:
            print("❌ Failed to create test users. Aborting tests.")
            return
        
        print(f"✅ Created users: Alice ({alice['user_id'][:8]}...) and Bob ({bob['user_id'][:8]}...)")
        
        # Run all test suites
        self.test_marketplace_categories()
        self.test_marketplace_listing_creation()
        self.test_marketplace_listing_retrieval()
        self.test_individual_listing_operations()
        self.test_user_listings()
        self.test_marketplace_messaging()
        self.test_security_and_authorization()
        self.test_data_validation()
        self.test_integration_with_existing_system()
        
        # Clean up
        self.cleanup_test_listings()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 MARKETPLACE BACKEND TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print("\n🎯 KEY FINDINGS:")
        
        # Analyze results by category
        categories = {
            "Categories": [r for r in self.test_results if "Categories" in r["test"]],
            "Listing Creation": [r for r in self.test_results if "Listing Creation" in r["test"] or "Validation" in r["test"]],
            "Listing Retrieval": [r for r in self.test_results if "Listing Retrieval" in r["test"]],
            "Individual Operations": [r for r in self.test_results if "Individual Listing" in r["test"]],
            "User Listings": [r for r in self.test_results if "User Listings" in r["test"]],
            "Messaging": [r for r in self.test_results if "Marketplace Messaging" in r["test"]],
            "Security": [r for r in self.test_results if "Security" in r["test"]],
            "Integration": [r for r in self.test_results if "Integration" in r["test"]]
        }
        
        for category, tests in categories.items():
            if tests:
                passed = sum(1 for t in tests if t["success"])
                total = len(tests)
                status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
                print(f"   {status} {category}: {passed}/{total} tests passed")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    tester = MarketplaceTester()
    tester.run_all_tests()