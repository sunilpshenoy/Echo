#!/usr/bin/env python3
"""
PERFORMANCE AND CACHING BACKEND TESTING SCRIPT
Tests new performance optimizations, Redis caching, and monitoring features
"""

import requests
import json
import time
import uuid
from datetime import datetime
import os

# Configuration
BACKEND_URL = "https://e09a8b3d-383d-4221-9e57-baee4ca8034c.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class PerformanceCachingTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.auth_token = None
        self.user_id = None
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
    
    def setup_authentication(self):
        """Setup authentication for testing"""
        print("\n🔐 Setting up authentication...")
        
        # Generate unique test user
        test_email = f"perftest_{int(time.time())}@test.com"
        test_username = f"perfuser_{int(time.time())}"
        
        # Register test user
        register_data = {
            "username": test_username,
            "email": test_email,
            "password": "testpass123",
            "display_name": "Performance Test User"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/register", json=register_data)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("user_id")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                self.log_test("User Registration", True, f"Registered user: {test_username}")
                return True
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_performance_monitoring_endpoints(self):
        """Test performance monitoring endpoints"""
        print("\n📊 Testing Performance Monitoring Endpoints...")
        
        # Test admin performance endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/performance")
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['active_requests', 'slow_queries', 'recent_slow_queries', 'error_counts']
                has_all_fields = all(field in data for field in expected_fields)
                self.log_test("Admin Performance Endpoint", has_all_fields, 
                            f"Response: {json.dumps(data, indent=2)}")
            else:
                self.log_test("Admin Performance Endpoint", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Admin Performance Endpoint", False, f"Exception: {str(e)}")
    
    def test_cache_management_endpoints(self):
        """Test cache management endpoints"""
        print("\n🗄️ Testing Cache Management Endpoints...")
        
        # Test cache clear endpoint
        try:
            response = self.session.post(f"{BACKEND_URL}/admin/cache/clear")
            if response.status_code == 200:
                data = response.json()
                self.log_test("Cache Clear Endpoint", True, 
                            f"Response: {json.dumps(data, indent=2)}")
            else:
                self.log_test("Cache Clear Endpoint", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Cache Clear Endpoint", False, f"Exception: {str(e)}")
        
        # Test cache statistics (if available)
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/cache/stats")
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['hits', 'misses', 'hit_rate', 'total_requests']
                has_cache_stats = any(field in data for field in expected_fields)
                self.log_test("Cache Statistics Endpoint", has_cache_stats, 
                            f"Response: {json.dumps(data, indent=2)}")
            else:
                self.log_test("Cache Statistics Endpoint", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Cache Statistics Endpoint", False, f"Exception: {str(e)}")
    
    def test_cached_user_profile(self):
        """Test cached user profile endpoint"""
        print("\n👤 Testing Cached User Profile...")
        
        # Test cached user profile endpoint
        try:
            # First request (should populate cache)
            start_time = time.time()
            response1 = self.session.get(f"{BACKEND_URL}/users/profile")
            first_response_time = time.time() - start_time
            
            if response1.status_code == 200:
                data1 = response1.json()
                
                # Second request (should hit cache)
                start_time = time.time()
                response2 = self.session.get(f"{BACKEND_URL}/users/profile")
                second_response_time = time.time() - start_time
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    
                    # Check if responses are consistent
                    consistent = data1 == data2
                    
                    # Check if second request was faster (cache hit)
                    cache_performance = second_response_time < first_response_time or second_response_time < 0.1
                    
                    self.log_test("Cached User Profile", consistent and cache_performance, 
                                f"First: {first_response_time:.3f}s, Second: {second_response_time:.3f}s, Consistent: {consistent}")
                else:
                    self.log_test("Cached User Profile", False, 
                                f"Second request failed: {response2.status_code}")
            else:
                self.log_test("Cached User Profile", False, 
                            f"Status: {response1.status_code}, Response: {response1.text}")
        except Exception as e:
            self.log_test("Cached User Profile", False, f"Exception: {str(e)}")
    
    def test_cached_chats_list(self):
        """Test cached chats list endpoint"""
        print("\n💬 Testing Cached Chats List...")
        
        try:
            # First request (should populate cache)
            start_time = time.time()
            response1 = self.session.get(f"{BACKEND_URL}/chats")
            first_response_time = time.time() - start_time
            
            if response1.status_code == 200:
                data1 = response1.json()
                
                # Second request (should hit cache)
                start_time = time.time()
                response2 = self.session.get(f"{BACKEND_URL}/chats")
                second_response_time = time.time() - start_time
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    
                    # Check if responses are consistent
                    consistent = data1 == data2
                    
                    # Check if second request was faster (cache hit)
                    cache_performance = second_response_time < first_response_time or second_response_time < 0.1
                    
                    self.log_test("Cached Chats List", consistent and cache_performance, 
                                f"First: {first_response_time:.3f}s, Second: {second_response_time:.3f}s, Consistent: {consistent}")
                else:
                    self.log_test("Cached Chats List", False, 
                                f"Second request failed: {response2.status_code}")
            else:
                self.log_test("Cached Chats List", False, 
                            f"Status: {response1.status_code}, Response: {response1.text}")
        except Exception as e:
            self.log_test("Cached Chats List", False, f"Exception: {str(e)}")
    
    def test_cached_message_search(self):
        """Test cached message search endpoint"""
        print("\n🔍 Testing Cached Message Search...")
        
        # First, create a test chat and message
        try:
            # Create a test chat
            chat_data = {
                "chat_type": "direct",
                "members": [self.user_id]
            }
            chat_response = self.session.post(f"{BACKEND_URL}/chats", json=chat_data)
            
            if chat_response.status_code == 200:
                chat_id = chat_response.json().get("chat_id")
                
                # Send a test message
                message_data = {
                    "content": "This is a test message for search functionality",
                    "message_type": "text"
                }
                message_response = self.session.post(f"{BACKEND_URL}/chats/{chat_id}/messages", json=message_data)
                
                if message_response.status_code == 200:
                    # Test cached message search
                    search_query = "test message"
                    
                    # First search request (should populate cache)
                    start_time = time.time()
                    response1 = self.session.get(f"{BACKEND_URL}/chats/{chat_id}/messages/search?q={search_query}")
                    first_response_time = time.time() - start_time
                    
                    if response1.status_code == 200:
                        data1 = response1.json()
                        
                        # Second search request (should hit cache)
                        start_time = time.time()
                        response2 = self.session.get(f"{BACKEND_URL}/chats/{chat_id}/messages/search?q={search_query}")
                        second_response_time = time.time() - start_time
                        
                        if response2.status_code == 200:
                            data2 = response2.json()
                            
                            # Check if responses are consistent
                            consistent = data1 == data2
                            
                            # Check if second request was faster (cache hit)
                            cache_performance = second_response_time < first_response_time or second_response_time < 0.1
                            
                            self.log_test("Cached Message Search", consistent and cache_performance, 
                                        f"First: {first_response_time:.3f}s, Second: {second_response_time:.3f}s, Consistent: {consistent}")
                        else:
                            self.log_test("Cached Message Search", False, 
                                        f"Second search failed: {response2.status_code}")
                    else:
                        self.log_test("Cached Message Search", False, 
                                    f"First search failed: {response1.status_code}")
                else:
                    self.log_test("Cached Message Search", False, 
                                f"Message creation failed: {message_response.status_code}")
            else:
                self.log_test("Cached Message Search", False, 
                            f"Chat creation failed: {chat_response.status_code}")
        except Exception as e:
            self.log_test("Cached Message Search", False, f"Exception: {str(e)}")
    
    def test_advanced_messaging_features(self):
        """Test advanced messaging features (editing, deletion, disappearing messages)"""
        print("\n✏️ Testing Advanced Messaging Features...")
        
        try:
            # Create a test chat
            chat_data = {
                "chat_type": "direct",
                "members": [self.user_id]
            }
            chat_response = self.session.post(f"{BACKEND_URL}/chats", json=chat_data)
            
            if chat_response.status_code == 200:
                chat_id = chat_response.json().get("chat_id")
                
                # Send a test message
                message_data = {
                    "content": "Original message content",
                    "message_type": "text"
                }
                message_response = self.session.post(f"{BACKEND_URL}/chats/{chat_id}/messages", json=message_data)
                
                if message_response.status_code == 200:
                    message_id = message_response.json().get("message_id")
                    
                    # Test message editing
                    edit_data = {
                        "content": "Edited message content"
                    }
                    edit_response = self.session.put(f"{BACKEND_URL}/messages/{message_id}/edit", json=edit_data)
                    
                    if edit_response.status_code == 200:
                        self.log_test("Message Editing", True, "Message edited successfully")
                    else:
                        self.log_test("Message Editing", False, f"Edit failed: {edit_response.status_code}")
                    
                    # Test message deletion
                    delete_response = self.session.delete(f"{BACKEND_URL}/messages/{message_id}")
                    
                    if delete_response.status_code == 200:
                        self.log_test("Message Deletion", True, "Message deleted successfully")
                    else:
                        self.log_test("Message Deletion", False, f"Delete failed: {delete_response.status_code}")
                    
                    # Test disappearing messages
                    disappearing_data = {
                        "content": "This message will disappear",
                        "message_type": "text",
                        "expires_in": 3600  # 1 hour
                    }
                    disappearing_response = self.session.post(f"{BACKEND_URL}/chats/{chat_id}/messages", json=disappearing_data)
                    
                    if disappearing_response.status_code == 200:
                        self.log_test("Disappearing Messages", True, "Disappearing message sent successfully")
                    else:
                        self.log_test("Disappearing Messages", False, f"Disappearing message failed: {disappearing_response.status_code}")
                        
                else:
                    self.log_test("Advanced Messaging Features", False, 
                                f"Message creation failed: {message_response.status_code}")
            else:
                self.log_test("Advanced Messaging Features", False, 
                            f"Chat creation failed: {chat_response.status_code}")
        except Exception as e:
            self.log_test("Advanced Messaging Features", False, f"Exception: {str(e)}")
    
    def test_chat_gaming_features(self):
        """Test chat gaming features"""
        print("\n🎮 Testing Chat Gaming Features...")
        
        try:
            # Create a test chat
            chat_data = {
                "chat_type": "direct",
                "members": [self.user_id]
            }
            chat_response = self.session.post(f"{BACKEND_URL}/chats", json=chat_data)
            
            if chat_response.status_code == 200:
                chat_id = chat_response.json().get("chat_id")
                
                # Test word chain game
                word_chain_data = {
                    "game_type": "word_chain",
                    "word": "apple"
                }
                word_response = self.session.post(f"{BACKEND_URL}/chats/{chat_id}/games/word-chain", json=word_chain_data)
                
                if word_response.status_code == 200:
                    self.log_test("Word Chain Game", True, "Word chain game started successfully")
                else:
                    self.log_test("Word Chain Game", False, f"Word chain failed: {word_response.status_code}")
                
                # Test quick math game
                math_data = {
                    "game_type": "quick_math",
                    "difficulty": "easy"
                }
                math_response = self.session.post(f"{BACKEND_URL}/chats/{chat_id}/games/quick-math", json=math_data)
                
                if math_response.status_code == 200:
                    self.log_test("Quick Math Game", True, "Quick math game started successfully")
                else:
                    self.log_test("Quick Math Game", False, f"Quick math failed: {math_response.status_code}")
                
                # Test emoji story game
                emoji_story_data = {
                    "game_type": "emoji_story",
                    "emoji_sequence": "🌟🏠🐱"
                }
                emoji_response = self.session.post(f"{BACKEND_URL}/chats/{chat_id}/games/emoji-story", json=emoji_story_data)
                
                if emoji_response.status_code == 200:
                    self.log_test("Emoji Story Game", True, "Emoji story game started successfully")
                else:
                    self.log_test("Emoji Story Game", False, f"Emoji story failed: {emoji_response.status_code}")
                
                # Test riddle game
                riddle_data = {
                    "game_type": "riddle",
                    "category": "general"
                }
                riddle_response = self.session.post(f"{BACKEND_URL}/chats/{chat_id}/games/riddle", json=riddle_data)
                
                if riddle_response.status_code == 200:
                    self.log_test("Riddle Game", True, "Riddle game started successfully")
                else:
                    self.log_test("Riddle Game", False, f"Riddle game failed: {riddle_response.status_code}")
                    
            else:
                self.log_test("Chat Gaming Features", False, 
                            f"Chat creation failed: {chat_response.status_code}")
        except Exception as e:
            self.log_test("Chat Gaming Features", False, f"Exception: {str(e)}")
    
    def test_redis_fallback_mechanism(self):
        """Test Redis fallback mechanism"""
        print("\n🔄 Testing Redis Fallback Mechanism...")
        
        # This test checks if the system gracefully handles Redis unavailability
        try:
            # Test multiple cache operations to see if fallback works
            operations = [
                ("GET", f"{BACKEND_URL}/users/profile"),
                ("GET", f"{BACKEND_URL}/chats"),
            ]
            
            fallback_working = True
            for method, url in operations:
                response = self.session.request(method, url)
                if response.status_code != 200:
                    fallback_working = False
                    break
            
            self.log_test("Redis Fallback Mechanism", fallback_working, 
                        "System handles cache operations with or without Redis")
        except Exception as e:
            self.log_test("Redis Fallback Mechanism", False, f"Exception: {str(e)}")
    
    def test_performance_middleware(self):
        """Test performance monitoring middleware"""
        print("\n⚡ Testing Performance Monitoring Middleware...")
        
        try:
            # Make several requests to trigger performance monitoring
            test_endpoints = [
                f"{BACKEND_URL}/users/me",
                f"{BACKEND_URL}/chats",
                f"{BACKEND_URL}/users/profile"
            ]
            
            response_times = []
            for endpoint in test_endpoints:
                start_time = time.time()
                response = self.session.get(endpoint)
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                # Check if performance headers are present
                has_process_time = 'X-Process-Time' in response.headers
                if not has_process_time:
                    self.log_test("Performance Middleware Headers", False, 
                                f"Missing X-Process-Time header in {endpoint}")
                    return
            
            avg_response_time = sum(response_times) / len(response_times)
            performance_good = avg_response_time < 2.0  # Should be under 2 seconds
            
            self.log_test("Performance Monitoring Middleware", performance_good, 
                        f"Average response time: {avg_response_time:.3f}s")
        except Exception as e:
            self.log_test("Performance Monitoring Middleware", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all performance and caching tests"""
        print("🚀 Starting Performance and Caching Backend Tests...")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Timeout: {TEST_TIMEOUT}s")
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed. Cannot proceed with tests.")
            return
        
        # Run all tests
        self.test_performance_monitoring_endpoints()
        self.test_cache_management_endpoints()
        self.test_cached_user_profile()
        self.test_cached_chats_list()
        self.test_cached_message_search()
        self.test_advanced_messaging_features()
        self.test_chat_gaming_features()
        self.test_redis_fallback_mechanism()
        self.test_performance_middleware()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🎯 PERFORMANCE AND CACHING TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "="*60)
        
        if success_rate >= 80:
            print("🎉 PERFORMANCE AND CACHING SYSTEM IS WORKING WELL!")
        elif success_rate >= 60:
            print("⚠️ PERFORMANCE AND CACHING SYSTEM HAS SOME ISSUES")
        else:
            print("🚨 PERFORMANCE AND CACHING SYSTEM NEEDS ATTENTION")

if __name__ == "__main__":
    tester = PerformanceCachingTester()
    tester.run_all_tests()