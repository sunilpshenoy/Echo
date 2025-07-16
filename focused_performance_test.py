#!/usr/bin/env python3
"""
FOCUSED PERFORMANCE AND CACHING BACKEND TESTING SCRIPT
Tests implemented performance optimizations, Redis caching, and monitoring features
"""

import requests
import json
import time
import uuid
from datetime import datetime
import os

# Configuration
BACKEND_URL = "https://1345bce5-cc7d-477e-8431-d11bc6e77861.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class FocusedPerformanceTester:
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
        test_email = f"focustest_{int(time.time())}@test.com"
        test_username = f"focususer_{int(time.time())}"
        
        # Register test user
        register_data = {
            "username": test_username,
            "email": test_email,
            "password": "testpass123",
            "display_name": "Focus Test User"
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
    
    def test_performance_monitoring(self):
        """Test performance monitoring system"""
        print("\n📊 Testing Performance Monitoring System...")
        
        # Test admin performance endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/performance")
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['cache_stats', 'performance_stats', 'redis_available']
                has_all_fields = all(field in data for field in expected_fields)
                
                # Check cache stats structure
                cache_stats = data.get('cache_stats', {})
                cache_fields = ['hits', 'misses', 'sets', 'hit_rate', 'total_requests']
                has_cache_fields = all(field in cache_stats for field in cache_fields)
                
                # Check performance stats structure
                perf_stats = data.get('performance_stats', {})
                perf_fields = ['active_requests', 'slow_queries', 'recent_slow_queries', 'error_counts']
                has_perf_fields = all(field in perf_stats for field in perf_fields)
                
                success = has_all_fields and has_cache_fields and has_perf_fields
                self.log_test("Performance Monitoring System", success, 
                            f"Redis Available: {data.get('redis_available')}, Cache Hit Rate: {cache_stats.get('hit_rate', 0)}%")
            else:
                self.log_test("Performance Monitoring System", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Performance Monitoring System", False, f"Exception: {str(e)}")
    
    def test_cache_management(self):
        """Test cache management system"""
        print("\n🗄️ Testing Cache Management System...")
        
        # Test cache clear endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/admin/cache/clear")
            if response.status_code == 200:
                data = response.json()
                has_message = 'message' in data
                self.log_test("Cache Management System", has_message, 
                            f"Cache clear response: {data.get('message', 'No message')}")
            else:
                self.log_test("Cache Management System", False, 
                            f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_test("Cache Management System", False, f"Exception: {str(e)}")
    
    def test_cached_user_profile(self):
        """Test cached user profile endpoint performance"""
        print("\n👤 Testing Cached User Profile Performance...")
        
        try:
            # Make multiple requests to test caching
            response_times = []
            for i in range(3):
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/users/profile")
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code != 200:
                    self.log_test("Cached User Profile Performance", False, 
                                f"Request {i+1} failed: {response.status_code}")
                    return
                
                time.sleep(0.1)  # Small delay between requests
            
            avg_response_time = sum(response_times) / len(response_times)
            performance_good = avg_response_time < 0.5  # Should be under 500ms
            
            self.log_test("Cached User Profile Performance", performance_good, 
                        f"Average response time: {avg_response_time:.3f}s (Times: {[f'{t:.3f}s' for t in response_times]})")
        except Exception as e:
            self.log_test("Cached User Profile Performance", False, f"Exception: {str(e)}")
    
    def test_cached_chats_list(self):
        """Test cached chats list endpoint performance"""
        print("\n💬 Testing Cached Chats List Performance...")
        
        try:
            # Make multiple requests to test caching
            response_times = []
            for i in range(3):
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/chats")
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response.status_code != 200:
                    self.log_test("Cached Chats List Performance", False, 
                                f"Request {i+1} failed: {response.status_code}")
                    return
                
                time.sleep(0.1)  # Small delay between requests
            
            avg_response_time = sum(response_times) / len(response_times)
            performance_good = avg_response_time < 0.5  # Should be under 500ms
            
            self.log_test("Cached Chats List Performance", performance_good, 
                        f"Average response time: {avg_response_time:.3f}s (Times: {[f'{t:.3f}s' for t in response_times]})")
        except Exception as e:
            self.log_test("Cached Chats List Performance", False, f"Exception: {str(e)}")
    
    def test_message_editing_deletion(self):
        """Test message editing and deletion features"""
        print("\n✏️ Testing Message Editing and Deletion...")
        
        try:
            # Create a second user for direct chat
            test_email2 = f"focustest2_{int(time.time())}@test.com"
            test_username2 = f"focususer2_{int(time.time())}"
            
            register_data2 = {
                "username": test_username2,
                "email": test_email2,
                "password": "testpass123",
                "display_name": "Focus Test User 2"
            }
            
            register_response = self.session.post(f"{BACKEND_URL}/register", json=register_data2)
            if register_response.status_code == 200:
                other_user_id = register_response.json().get("user", {}).get("user_id")
                
                # Create a direct chat
                chat_data = {
                    "chat_type": "direct",
                    "other_user_id": other_user_id
                }
                chat_response = self.session.post(f"{BACKEND_URL}/chats", json=chat_data)
                
                if chat_response.status_code == 200:
                    chat_id = chat_response.json().get("chat_id")
                    
                    # Send a test message
                    message_data = {
                        "content": "Original message content for testing",
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
                        
                        edit_success = edit_response.status_code == 200
                        
                        # Test message deletion
                        delete_response = self.session.delete(f"{BACKEND_URL}/messages/{message_id}")
                        delete_success = delete_response.status_code == 200
                        
                        overall_success = edit_success and delete_success
                        self.log_test("Message Editing and Deletion", overall_success, 
                                    f"Edit: {'✅' if edit_success else '❌'}, Delete: {'✅' if delete_success else '❌'}")
                    else:
                        self.log_test("Message Editing and Deletion", False, 
                                    f"Message creation failed: {message_response.status_code}")
                else:
                    self.log_test("Message Editing and Deletion", False, 
                                f"Chat creation failed: {chat_response.status_code}")
            else:
                self.log_test("Message Editing and Deletion", False, 
                            f"Second user registration failed: {register_response.status_code}")
        except Exception as e:
            self.log_test("Message Editing and Deletion", False, f"Exception: {str(e)}")
    
    def test_message_search_caching(self):
        """Test cached message search functionality"""
        print("\n🔍 Testing Cached Message Search...")
        
        try:
            # Create a second user for direct chat
            test_email2 = f"focustest3_{int(time.time())}@test.com"
            test_username2 = f"focususer3_{int(time.time())}"
            
            register_data2 = {
                "username": test_username2,
                "email": test_email2,
                "password": "testpass123",
                "display_name": "Focus Test User 3"
            }
            
            register_response = self.session.post(f"{BACKEND_URL}/register", json=register_data2)
            if register_response.status_code == 200:
                other_user_id = register_response.json().get("user", {}).get("user_id")
                
                # Create a direct chat
                chat_data = {
                    "chat_type": "direct",
                    "other_user_id": other_user_id
                }
                chat_response = self.session.post(f"{BACKEND_URL}/chats", json=chat_data)
                
                if chat_response.status_code == 200:
                    chat_id = chat_response.json().get("chat_id")
                    
                    # Send multiple test messages
                    messages = [
                        "Hello world, this is a test message",
                        "Another message for search testing",
                        "Final message with unique content"
                    ]
                    
                    for msg_content in messages:
                        message_data = {
                            "content": msg_content,
                            "message_type": "text"
                        }
                        self.session.post(f"{BACKEND_URL}/chats/{chat_id}/messages", json=message_data)
                    
                    # Test cached message search
                    search_query = "test"
                    
                    # Make multiple search requests to test caching
                    response_times = []
                    for i in range(3):
                        start_time = time.time()
                        response = self.session.get(f"{BACKEND_URL}/chats/{chat_id}/messages/search?query={search_query}")
                        response_time = time.time() - start_time
                        response_times.append(response_time)
                        
                        if response.status_code != 200:
                            self.log_test("Cached Message Search", False, 
                                        f"Search request {i+1} failed: {response.status_code}")
                            return
                        
                        time.sleep(0.1)  # Small delay between requests
                    
                    avg_response_time = sum(response_times) / len(response_times)
                    performance_good = avg_response_time < 0.5  # Should be under 500ms
                    
                    self.log_test("Cached Message Search", performance_good, 
                                f"Average search time: {avg_response_time:.3f}s (Times: {[f'{t:.3f}s' for t in response_times]})")
                else:
                    self.log_test("Cached Message Search", False, 
                                f"Chat creation failed: {chat_response.status_code}")
            else:
                self.log_test("Cached Message Search", False, 
                            f"Second user registration failed: {register_response.status_code}")
        except Exception as e:
            self.log_test("Cached Message Search", False, f"Exception: {str(e)}")
    
    def test_redis_fallback_system(self):
        """Test Redis fallback mechanism"""
        print("\n🔄 Testing Redis Fallback System...")
        
        try:
            # Test multiple cache-dependent operations
            operations = [
                ("User Profile", f"{BACKEND_URL}/users/profile"),
                ("Chats List", f"{BACKEND_URL}/chats"),
                ("Performance Stats", f"{BACKEND_URL}/admin/performance"),
            ]
            
            all_success = True
            results = []
            
            for name, url in operations:
                response = self.session.get(url)
                success = response.status_code == 200
                results.append(f"{name}: {'✅' if success else '❌'}")
                if not success:
                    all_success = False
            
            self.log_test("Redis Fallback System", all_success, 
                        f"Operations: {', '.join(results)}")
        except Exception as e:
            self.log_test("Redis Fallback System", False, f"Exception: {str(e)}")
    
    def test_performance_middleware(self):
        """Test performance monitoring middleware"""
        print("\n⚡ Testing Performance Monitoring Middleware...")
        
        try:
            # Make requests to different endpoints and check for performance headers
            test_endpoints = [
                f"{BACKEND_URL}/users/me",
                f"{BACKEND_URL}/chats",
                f"{BACKEND_URL}/users/profile"
            ]
            
            response_times = []
            has_headers = []
            
            for endpoint in test_endpoints:
                start_time = time.time()
                response = self.session.get(endpoint)
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                # Check if performance headers are present
                has_process_time = 'X-Process-Time' in response.headers
                has_headers.append(has_process_time)
                
                if response.status_code != 200:
                    self.log_test("Performance Monitoring Middleware", False, 
                                f"Request to {endpoint} failed: {response.status_code}")
                    return
            
            avg_response_time = sum(response_times) / len(response_times)
            performance_good = avg_response_time < 1.0  # Should be under 1 second
            headers_present = all(has_headers)
            
            success = performance_good and headers_present
            self.log_test("Performance Monitoring Middleware", success, 
                        f"Avg time: {avg_response_time:.3f}s, Headers: {'✅' if headers_present else '❌'}")
        except Exception as e:
            self.log_test("Performance Monitoring Middleware", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all focused performance and caching tests"""
        print("🚀 Starting Focused Performance and Caching Backend Tests...")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Timeout: {TEST_TIMEOUT}s")
        
        # Setup authentication
        if not self.setup_authentication():
            print("❌ Authentication setup failed. Cannot proceed with tests.")
            return
        
        # Run all tests
        self.test_performance_monitoring()
        self.test_cache_management()
        self.test_cached_user_profile()
        self.test_cached_chats_list()
        self.test_message_editing_deletion()
        self.test_message_search_caching()
        self.test_redis_fallback_system()
        self.test_performance_middleware()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("🎯 FOCUSED PERFORMANCE AND CACHING TEST SUMMARY")
        print("="*70)
        
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
        
        print("\n" + "="*70)
        
        if success_rate >= 90:
            print("🎉 PERFORMANCE AND CACHING SYSTEM IS EXCELLENT!")
        elif success_rate >= 75:
            print("✅ PERFORMANCE AND CACHING SYSTEM IS WORKING WELL!")
        elif success_rate >= 60:
            print("⚠️ PERFORMANCE AND CACHING SYSTEM HAS SOME ISSUES")
        else:
            print("🚨 PERFORMANCE AND CACHING SYSTEM NEEDS ATTENTION")

if __name__ == "__main__":
    tester = FocusedPerformanceTester()
    tester.run_all_tests()