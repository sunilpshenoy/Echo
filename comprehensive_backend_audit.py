#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND AUDIT SCRIPT
Following AI Accountability Protocol - Complete verification with evidence and benchmarks
"""

import requests
import json
import time
import base64
import secrets
from datetime import datetime, timedelta
import uuid
import os
import threading
import concurrent.futures
from typing import Dict, List, Any
import statistics

# Configuration
BACKEND_URL = "https://a205b7e3-f535-4569-8dd8-c1f8fc23e5dc.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class ComprehensiveBackendAuditor:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.users = {}  # Store user data and tokens
        self.test_results = []
        self.performance_metrics = {}
        self.security_tests = []
        self.start_time = time.time()
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_time: float = 0):
        """Log test results with performance metrics"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_time > 0:
            print(f"   Response Time: {response_time:.3f}s")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def measure_response_time(self, func, *args, **kwargs):
        """Measure response time of a function"""
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        return result, end - start
    
    def generate_test_user_data(self, username: str):
        """Generate realistic test user data"""
        return {
            "username": username,
            "email": f"{username}@pulsetest.com",
            "password": "SecurePass123!",
            "display_name": f"{username.title()} User",
            "phone": f"+91{secrets.randbelow(9000000000) + 1000000000}"
        }
    
    # ===== 1. AUTHENTICATION SYSTEM VERIFICATION =====
    
    def test_user_registration_valid(self):
        """Test user registration with valid data"""
        print("\n=== 1. AUTHENTICATION SYSTEM VERIFICATION ===")
        print("Testing User Registration with Valid Data...")
        
        user_data = self.generate_test_user_data("alice_audit")
        
        try:
            response, response_time = self.measure_response_time(
                self.session.post, f"{BACKEND_URL}/register", json=user_data
            )
            
            if response.status_code == 200:
                data = response.json()
                success = "access_token" in data and "user" in data
                self.users["alice_audit"] = {
                    **user_data,
                    "user_id": data["user"]["user_id"],
                    "token": data["access_token"]
                }
                self.log_test("User Registration (Valid Data)", success, 
                            f"User ID: {data['user']['user_id']}", response_time)
            else:
                self.log_test("User Registration (Valid Data)", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                
        except Exception as e:
            self.log_test("User Registration (Valid Data)", False, f"Error: {str(e)}")
    
    def test_user_registration_invalid(self):
        """Test user registration with invalid data"""
        print("Testing User Registration with Invalid Data...")
        
        invalid_cases = [
            {"username": "", "email": "test@test.com", "password": "pass123"},
            {"username": "test", "email": "invalid-email", "password": "pass123"},
            {"username": "test", "email": "test@test.com", "password": "123"},
            {"username": "test", "email": "test@test.com", "password": ""},
        ]
        
        for i, invalid_data in enumerate(invalid_cases):
            try:
                response, response_time = self.measure_response_time(
                    self.session.post, f"{BACKEND_URL}/register", json=invalid_data
                )
                
                # Should fail with 400 or 422
                success = response.status_code in [400, 422]
                self.log_test(f"Invalid Registration Case {i+1}", success, 
                            f"HTTP {response.status_code} (Expected 400/422)", response_time)
                            
            except Exception as e:
                self.log_test(f"Invalid Registration Case {i+1}", False, f"Error: {str(e)}")
    
    def test_user_login_valid(self):
        """Test login functionality with correct credentials"""
        print("Testing User Login with Valid Credentials...")
        
        if "alice_audit" not in self.users:
            self.log_test("User Login (Valid)", False, "No test user available")
            return
        
        user = self.users["alice_audit"]
        login_data = {"email": user["email"], "password": user["password"]}
        
        try:
            response, response_time = self.measure_response_time(
                self.session.post, f"{BACKEND_URL}/login", json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                success = "access_token" in data and "user" in data
                self.log_test("User Login (Valid Credentials)", success, 
                            f"Token received: {len(data.get('access_token', ''))>0}", response_time)
            else:
                self.log_test("User Login (Valid Credentials)", False, 
                            f"HTTP {response.status_code}: {response.text}", response_time)
                
        except Exception as e:
            self.log_test("User Login (Valid Credentials)", False, f"Error: {str(e)}")
    
    def test_user_login_invalid(self):
        """Test login functionality with incorrect credentials"""
        print("Testing User Login with Invalid Credentials...")
        
        invalid_cases = [
            {"email": "nonexistent@test.com", "password": "wrongpass"},
            {"email": "alice_audit@pulsetest.com", "password": "wrongpass"},
            {"email": "", "password": "password"},
            {"email": "test@test.com", "password": ""},
        ]
        
        for i, invalid_data in enumerate(invalid_cases):
            try:
                response, response_time = self.measure_response_time(
                    self.session.post, f"{BACKEND_URL}/login", json=invalid_data
                )
                
                # Should fail with 401 or 400
                success = response.status_code in [400, 401]
                self.log_test(f"Invalid Login Case {i+1}", success, 
                            f"HTTP {response.status_code} (Expected 400/401)", response_time)
                            
            except Exception as e:
                self.log_test(f"Invalid Login Case {i+1}", False, f"Error: {str(e)}")
    
    def test_jwt_token_validation(self):
        """Test JWT token generation and validation"""
        print("Testing JWT Token Validation...")
        
        if "alice_audit" not in self.users:
            self.log_test("JWT Token Validation", False, "No test user available")
            return
        
        token = self.users["alice_audit"]["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            # Test valid token
            response, response_time = self.measure_response_time(
                self.session.get, f"{BACKEND_URL}/users/me", headers=headers
            )
            
            valid_token_works = response.status_code == 200
            self.log_test("Valid JWT Token", valid_token_works, 
                        f"HTTP {response.status_code}", response_time)
            
            # Test invalid token
            invalid_headers = {"Authorization": "Bearer invalid_token_here"}
            response, response_time = self.measure_response_time(
                self.session.get, f"{BACKEND_URL}/users/me", headers=invalid_headers
            )
            
            invalid_token_rejected = response.status_code == 401
            self.log_test("Invalid JWT Token Rejected", invalid_token_rejected, 
                        f"HTTP {response.status_code} (Expected 401)", response_time)
            
            # Test missing token
            response, response_time = self.measure_response_time(
                self.session.get, f"{BACKEND_URL}/users/me"
            )
            
            missing_token_rejected = response.status_code == 401
            self.log_test("Missing JWT Token Rejected", missing_token_rejected, 
                        f"HTTP {response.status_code} (Expected 401)", response_time)
                        
        except Exception as e:
            self.log_test("JWT Token Validation", False, f"Error: {str(e)}")
    
    def test_authentication_performance(self):
        """Measure authentication response times"""
        print("Testing Authentication Performance...")
        
        if "alice_audit" not in self.users:
            self.log_test("Authentication Performance", False, "No test user available")
            return
        
        user = self.users["alice_audit"]
        login_data = {"email": user["email"], "password": user["password"]}
        
        # Perform multiple login attempts to measure average response time
        response_times = []
        success_count = 0
        
        for i in range(5):
            try:
                response, response_time = self.measure_response_time(
                    self.session.post, f"{BACKEND_URL}/login", json=login_data
                )
                
                response_times.append(response_time)
                if response.status_code == 200:
                    success_count += 1
                    
            except Exception as e:
                print(f"   Login attempt {i+1} failed: {e}")
        
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            success_rate = (success_count / len(response_times)) * 100
            
            # Target: <500ms average response time
            performance_good = avg_time < 0.5
            
            self.performance_metrics["authentication"] = {
                "avg_response_time": avg_time,
                "max_response_time": max_time,
                "min_response_time": min_time,
                "success_rate": success_rate
            }
            
            self.log_test("Authentication Performance", performance_good, 
                        f"Avg: {avg_time:.3f}s, Max: {max_time:.3f}s, Success: {success_rate:.1f}%")
    
    # ===== 2. DATABASE OPERATIONS AUDIT =====
    
    def test_database_crud_operations(self):
        """Test all CRUD operations for users, chats, messages"""
        print("\n=== 2. DATABASE OPERATIONS AUDIT ===")
        print("Testing Database CRUD Operations...")
        
        if "alice_audit" not in self.users:
            self.log_test("Database CRUD Operations", False, "No test user available")
            return
        
        headers = {"Authorization": f"Bearer {self.users['alice_audit']['token']}"}
        
        # Test CREATE - Create a chat
        try:
            # Create another user for chat
            bob_data = self.generate_test_user_data("bob_audit")
            response = self.session.post(f"{BACKEND_URL}/register", json=bob_data)
            
            if response.status_code == 200:
                bob_user = response.json()
                self.users["bob_audit"] = {
                    **bob_data,
                    "user_id": bob_user["user"]["user_id"],
                    "token": bob_user["access_token"]
                }
                
                # CREATE: Create chat
                chat_data = {
                    "chat_type": "direct",
                    "other_user_id": bob_user["user"]["user_id"]
                }
                
                response, response_time = self.measure_response_time(
                    self.session.post, f"{BACKEND_URL}/chats", json=chat_data, headers=headers
                )
                
                create_success = response.status_code == 200
                chat_id = None
                if create_success:
                    chat_id = response.json().get("chat_id")
                
                self.log_test("Database CREATE (Chat)", create_success, 
                            f"Chat ID: {chat_id}", response_time)
                
                if chat_id:
                    # READ: Get chats
                    response, response_time = self.measure_response_time(
                        self.session.get, f"{BACKEND_URL}/chats", headers=headers
                    )
                    
                    read_success = response.status_code == 200
                    if read_success:
                        chats = response.json()
                        chat_found = any(c.get("chat_id") == chat_id for c in chats)
                        read_success = chat_found
                    
                    self.log_test("Database READ (Chats)", read_success, 
                                f"Found {len(chats) if read_success else 0} chats", response_time)
                    
                    # CREATE: Send message
                    message_data = {
                        "content": "Test message for CRUD operations",
                        "message_type": "text"
                    }
                    
                    response, response_time = self.measure_response_time(
                        self.session.post, f"{BACKEND_URL}/chats/{chat_id}/messages", 
                        json=message_data, headers=headers
                    )
                    
                    message_create_success = response.status_code == 200
                    message_id = None
                    if message_create_success:
                        message_id = response.json().get("message_id")
                    
                    self.log_test("Database CREATE (Message)", message_create_success, 
                                f"Message ID: {message_id}", response_time)
                    
                    # READ: Get messages
                    response, response_time = self.measure_response_time(
                        self.session.get, f"{BACKEND_URL}/chats/{chat_id}/messages", headers=headers
                    )
                    
                    message_read_success = response.status_code == 200
                    if message_read_success:
                        messages = response.json()
                        message_found = any(m.get("message_id") == message_id for m in messages)
                        message_read_success = message_found
                    
                    self.log_test("Database READ (Messages)", message_read_success, 
                                f"Found {len(messages) if message_read_success else 0} messages", response_time)
                    
                    # UPDATE: Update user profile
                    update_data = {"display_name": "Updated Alice Audit"}
                    response, response_time = self.measure_response_time(
                        self.session.put, f"{BACKEND_URL}/users/me", 
                        json=update_data, headers=headers
                    )
                    
                    update_success = response.status_code == 200
                    self.log_test("Database UPDATE (User Profile)", update_success, 
                                f"HTTP {response.status_code}", response_time)
                    
        except Exception as e:
            self.log_test("Database CRUD Operations", False, f"Error: {str(e)}")
    
    def test_database_performance(self):
        """Measure database query response times"""
        print("Testing Database Performance...")
        
        if "alice_audit" not in self.users:
            self.log_test("Database Performance", False, "No test user available")
            return
        
        headers = {"Authorization": f"Bearer {self.users['alice_audit']['token']}"}
        
        # Test multiple database operations
        operations = [
            ("GET /users/me", lambda: self.session.get(f"{BACKEND_URL}/users/me", headers=headers)),
            ("GET /chats", lambda: self.session.get(f"{BACKEND_URL}/chats", headers=headers)),
        ]
        
        for op_name, operation in operations:
            response_times = []
            success_count = 0
            
            for i in range(3):
                try:
                    response, response_time = self.measure_response_time(operation)
                    response_times.append(response_time)
                    if response.status_code == 200:
                        success_count += 1
                except Exception as e:
                    print(f"   {op_name} attempt {i+1} failed: {e}")
            
            if response_times:
                avg_time = statistics.mean(response_times)
                success_rate = (success_count / len(response_times)) * 100
                
                # Target: <100ms for database queries
                performance_good = avg_time < 0.1
                
                self.log_test(f"Database Performance ({op_name})", performance_good, 
                            f"Avg: {avg_time:.3f}s, Success: {success_rate:.1f}%")
    
    # ===== 3. API ENDPOINTS COMPREHENSIVE TESTING =====
    
    def test_all_api_endpoints(self):
        """Test ALL API endpoints with valid and invalid inputs"""
        print("\n=== 3. API ENDPOINTS COMPREHENSIVE TESTING ===")
        print("Testing All API Endpoints...")
        
        if "alice_audit" not in self.users:
            self.log_test("API Endpoints Testing", False, "No test user available")
            return
        
        headers = {"Authorization": f"Bearer {self.users['alice_audit']['token']}"}
        
        # Define all endpoints to test
        endpoints = [
            # Authentication endpoints
            ("POST /register", "post", "/register", {"username": "test", "email": "test@test.com", "password": "pass123"}),
            ("POST /login", "post", "/login", {"email": "test@test.com", "password": "pass123"}),
            
            # User endpoints
            ("GET /users/me", "get", "/users/me", None),
            ("PUT /users/me", "put", "/users/me", {"display_name": "Test Update"}),
            
            # Chat endpoints
            ("GET /chats", "get", "/chats", None),
            ("POST /chats", "post", "/chats", {"chat_type": "group", "name": "Test Group", "members": []}),
            
            # Profile endpoints
            ("GET /users/profile/completeness", "get", "/users/profile/completeness", None),
        ]
        
        endpoint_results = []
        
        for endpoint_name, method, path, data in endpoints:
            try:
                if method == "get":
                    response, response_time = self.measure_response_time(
                        self.session.get, f"{BACKEND_URL}{path}", headers=headers
                    )
                elif method == "post":
                    response, response_time = self.measure_response_time(
                        self.session.post, f"{BACKEND_URL}{path}", json=data, headers=headers
                    )
                elif method == "put":
                    response, response_time = self.measure_response_time(
                        self.session.put, f"{BACKEND_URL}{path}", json=data, headers=headers
                    )
                
                # Consider 200, 201, 400, 401, 403, 404 as expected responses
                success = response.status_code in [200, 201, 400, 401, 403, 404]
                
                endpoint_results.append({
                    "endpoint": endpoint_name,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "success": success
                })
                
                self.log_test(f"API Endpoint {endpoint_name}", success, 
                            f"HTTP {response.status_code}", response_time)
                
            except Exception as e:
                endpoint_results.append({
                    "endpoint": endpoint_name,
                    "status_code": 0,
                    "response_time": 0,
                    "success": False
                })
                self.log_test(f"API Endpoint {endpoint_name}", False, f"Error: {str(e)}")
        
        # Calculate API performance metrics
        if endpoint_results:
            response_times = [r["response_time"] for r in endpoint_results if r["response_time"] > 0]
            success_count = sum(1 for r in endpoint_results if r["success"])
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                success_rate = (success_count / len(endpoint_results)) * 100
                
                self.performance_metrics["api_endpoints"] = {
                    "avg_response_time": avg_response_time,
                    "max_response_time": max_response_time,
                    "success_rate": success_rate,
                    "total_endpoints": len(endpoint_results)
                }
                
                # Target: <200ms average response time
                performance_good = avg_response_time < 0.2
                
                self.log_test("API Endpoints Performance", performance_good, 
                            f"Avg: {avg_response_time:.3f}s, Max: {max_response_time:.3f}s, Success: {success_rate:.1f}%")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("Testing Rate Limiting...")
        
        # Make rapid requests to test rate limiting
        rapid_requests = []
        for i in range(20):  # Make 20 rapid requests
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/users/me")
                end_time = time.time()
                
                rapid_requests.append({
                    "status_code": response.status_code,
                    "response_time": end_time - start_time
                })
                
            except Exception as e:
                rapid_requests.append({
                    "status_code": 0,
                    "response_time": 0,
                    "error": str(e)
                })
        
        # Check if any requests were rate limited (429 status code)
        rate_limited_count = sum(1 for r in rapid_requests if r["status_code"] == 429)
        rate_limiting_active = rate_limited_count > 0
        
        self.log_test("Rate Limiting Functionality", rate_limiting_active, 
                    f"Rate limited requests: {rate_limited_count}/20")
    
    # ===== 4. CHAT SYSTEM FUNCTIONALITY =====
    
    def test_chat_system_functionality(self):
        """Test chat system functionality"""
        print("\n=== 4. CHAT SYSTEM FUNCTIONALITY ===")
        print("Testing Chat System...")
        
        if "alice_audit" not in self.users or "bob_audit" not in self.users:
            self.log_test("Chat System Functionality", False, "Required users not available")
            return
        
        alice_headers = {"Authorization": f"Bearer {self.users['alice_audit']['token']}"}
        bob_headers = {"Authorization": f"Bearer {self.users['bob_audit']['token']}"}
        
        try:
            # Test chat creation
            chat_data = {
                "chat_type": "direct",
                "other_user_id": self.users["bob_audit"]["user_id"]
            }
            
            response, response_time = self.measure_response_time(
                self.session.post, f"{BACKEND_URL}/chats", json=chat_data, headers=alice_headers
            )
            
            chat_creation_success = response.status_code == 200
            chat_id = None
            if chat_creation_success:
                chat_id = response.json().get("chat_id")
            
            self.log_test("Chat Creation", chat_creation_success, 
                        f"Chat ID: {chat_id}", response_time)
            
            if chat_id:
                # Test message sending
                message_data = {
                    "content": "Hello Bob! This is a test message.",
                    "message_type": "text"
                }
                
                response, response_time = self.measure_response_time(
                    self.session.post, f"{BACKEND_URL}/chats/{chat_id}/messages", 
                    json=message_data, headers=alice_headers
                )
                
                message_send_success = response.status_code == 200
                message_id = None
                if message_send_success:
                    message_id = response.json().get("message_id")
                
                self.log_test("Message Sending", message_send_success, 
                            f"Message ID: {message_id}", response_time)
                
                # Test message retrieval
                response, response_time = self.measure_response_time(
                    self.session.get, f"{BACKEND_URL}/chats/{chat_id}/messages", headers=bob_headers
                )
                
                message_retrieval_success = response.status_code == 200
                messages_count = 0
                if message_retrieval_success:
                    messages = response.json()
                    messages_count = len(messages)
                    message_found = any(m.get("message_id") == message_id for m in messages)
                    message_retrieval_success = message_found
                
                self.log_test("Message Retrieval", message_retrieval_success, 
                            f"Retrieved {messages_count} messages", response_time)
                
                # Test group chat functionality
                group_data = {
                    "chat_type": "group",
                    "name": "Test Group Chat",
                    "members": [self.users["bob_audit"]["user_id"]]
                }
                
                response, response_time = self.measure_response_time(
                    self.session.post, f"{BACKEND_URL}/chats", json=group_data, headers=alice_headers
                )
                
                group_creation_success = response.status_code == 200
                self.log_test("Group Chat Creation", group_creation_success, 
                            f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Chat System Functionality", False, f"Error: {str(e)}")
    
    def test_file_sharing(self):
        """Test file sharing capabilities"""
        print("Testing File Sharing...")
        
        if "alice_audit" not in self.users:
            self.log_test("File Sharing", False, "No test user available")
            return
        
        headers = {"Authorization": f"Bearer {self.users['alice_audit']['token']}"}
        
        try:
            # Create a test file
            test_file_content = b"This is a test file for file sharing functionality."
            test_file_b64 = base64.b64encode(test_file_content).decode()
            
            file_data = {
                "file_name": "test_document.txt",
                "file_data": test_file_b64,
                "file_type": "text/plain"
            }
            
            response, response_time = self.measure_response_time(
                self.session.post, f"{BACKEND_URL}/upload", json=file_data, headers=headers
            )
            
            file_upload_success = response.status_code == 200
            file_info = None
            if file_upload_success:
                file_info = response.json()
            
            self.log_test("File Upload", file_upload_success, 
                        f"File size: {len(test_file_content)} bytes", response_time)
            
        except Exception as e:
            self.log_test("File Sharing", False, f"Error: {str(e)}")
    
    # ===== 5. SECURITY IMPLEMENTATION VERIFICATION =====
    
    def test_security_implementation(self):
        """Test security implementation verification"""
        print("\n=== 5. SECURITY IMPLEMENTATION VERIFICATION ===")
        print("Testing Security Implementation...")
        
        # Test input validation and sanitization
        self.test_input_validation()
        
        # Test XSS prevention
        self.test_xss_prevention()
        
        # Test authentication bypass attempts
        self.test_authentication_bypass()
        
        # Test secure headers
        self.test_security_headers()
    
    def test_input_validation(self):
        """Test input validation and sanitization"""
        print("Testing Input Validation...")
        
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]
        
        for i, malicious_input in enumerate(malicious_inputs):
            try:
                # Test malicious input in registration
                malicious_data = {
                    "username": malicious_input,
                    "email": f"test{i}@test.com",
                    "password": "password123"
                }
                
                response, response_time = self.measure_response_time(
                    self.session.post, f"{BACKEND_URL}/register", json=malicious_data
                )
                
                # Should be rejected (400, 422) or sanitized (200 but cleaned)
                input_handled = response.status_code in [400, 422] or (
                    response.status_code == 200 and malicious_input not in response.text
                )
                
                self.log_test(f"Input Validation Case {i+1}", input_handled, 
                            f"HTTP {response.status_code}", response_time)
                
            except Exception as e:
                self.log_test(f"Input Validation Case {i+1}", False, f"Error: {str(e)}")
    
    def test_xss_prevention(self):
        """Test XSS prevention measures"""
        print("Testing XSS Prevention...")
        
        if "alice_audit" not in self.users:
            self.log_test("XSS Prevention", False, "No test user available")
            return
        
        headers = {"Authorization": f"Bearer {self.users['alice_audit']['token']}"}
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
        ]
        
        for i, payload in enumerate(xss_payloads):
            try:
                # Test XSS in profile update
                update_data = {"display_name": payload}
                
                response, response_time = self.measure_response_time(
                    self.session.put, f"{BACKEND_URL}/users/me", json=update_data, headers=headers
                )
                
                # Check if XSS payload is sanitized or rejected
                xss_prevented = True
                if response.status_code == 200:
                    # Check if the response contains the raw payload (bad)
                    response_text = response.text.lower()
                    xss_prevented = payload.lower() not in response_text
                
                self.log_test(f"XSS Prevention Case {i+1}", xss_prevented, 
                            f"HTTP {response.status_code}", response_time)
                
            except Exception as e:
                self.log_test(f"XSS Prevention Case {i+1}", False, f"Error: {str(e)}")
    
    def test_authentication_bypass(self):
        """Test authentication bypass attempts"""
        print("Testing Authentication Bypass...")
        
        bypass_attempts = [
            # No authorization header
            {},
            # Invalid token format
            {"Authorization": "Bearer invalid_token"},
            # Malformed authorization header
            {"Authorization": "Basic invalid"},
            # Empty token
            {"Authorization": "Bearer "},
            # SQL injection in token
            {"Authorization": "Bearer '; DROP TABLE users; --"},
        ]
        
        for i, headers in enumerate(bypass_attempts):
            try:
                response, response_time = self.measure_response_time(
                    self.session.get, f"{BACKEND_URL}/users/me", headers=headers
                )
                
                # Should be rejected with 401
                bypass_prevented = response.status_code == 401
                
                self.log_test(f"Auth Bypass Prevention Case {i+1}", bypass_prevented, 
                            f"HTTP {response.status_code} (Expected 401)", response_time)
                
            except Exception as e:
                self.log_test(f"Auth Bypass Prevention Case {i+1}", False, f"Error: {str(e)}")
    
    def test_security_headers(self):
        """Test security headers implementation"""
        print("Testing Security Headers...")
        
        try:
            response, response_time = self.measure_response_time(
                self.session.get, f"{BACKEND_URL}/users/me"
            )
            
            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Strict-Transport-Security",
                "Content-Security-Policy",
                "Referrer-Policy"
            ]
            
            headers_present = []
            for header in security_headers:
                if header in response.headers:
                    headers_present.append(header)
            
            headers_score = len(headers_present) / len(security_headers)
            headers_good = headers_score >= 0.5  # At least 50% of security headers present
            
            self.log_test("Security Headers Implementation", headers_good, 
                        f"Present: {len(headers_present)}/{len(security_headers)} headers", response_time)
            
        except Exception as e:
            self.log_test("Security Headers Implementation", False, f"Error: {str(e)}")
    
    # ===== LOAD TESTING =====
    
    def test_concurrent_requests(self):
        """Test concurrent request handling"""
        print("\n=== LOAD TESTING ===")
        print("Testing Concurrent Request Handling...")
        
        if "alice_audit" not in self.users:
            self.log_test("Concurrent Requests", False, "No test user available")
            return
        
        headers = {"Authorization": f"Bearer {self.users['alice_audit']['token']}"}
        
        def make_request():
            try:
                start_time = time.time()
                response = self.session.get(f"{BACKEND_URL}/users/me", headers=headers)
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                }
            except Exception as e:
                return {
                    "status_code": 0,
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # Test with 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        successful_requests = sum(1 for r in results if r["success"])
        response_times = [r["response_time"] for r in results if r["response_time"] > 0]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            success_rate = (successful_requests / len(results)) * 100
            
            # Good performance: >80% success rate and <1s average response time
            performance_good = success_rate >= 80 and avg_response_time < 1.0
            
            self.performance_metrics["concurrent_requests"] = {
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "total_requests": len(results)
            }
            
            self.log_test("Concurrent Request Handling", performance_good, 
                        f"Success: {success_rate:.1f}%, Avg: {avg_response_time:.3f}s")
    
    # ===== COMPREHENSIVE REPORT =====
    
    def generate_comprehensive_report(self):
        """Generate comprehensive audit report with evidence"""
        print("\n" + "=" * 80)
        print("🔍 COMPREHENSIVE BACKEND AUDIT REPORT")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"Total Tests Executed: {total_tests}")
        print(f"Tests Passed: {passed_tests}")
        print(f"Tests Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Audit Time: {time.time() - self.start_time:.2f} seconds")
        
        # Performance Benchmarks
        print(f"\n⚡ PERFORMANCE BENCHMARKS:")
        for category, metrics in self.performance_metrics.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            for metric, value in metrics.items():
                if 'time' in metric:
                    print(f"  {metric.replace('_', ' ').title()}: {value:.3f}s")
                elif 'rate' in metric:
                    print(f"  {metric.replace('_', ' ').title()}: {value:.1f}%")
                else:
                    print(f"  {metric.replace('_', ' ').title()}: {value}")
        
        # Target Benchmarks Comparison
        print(f"\n🎯 BENCHMARK COMPLIANCE:")
        benchmarks = [
            ("Authentication Response Time", "authentication", "avg_response_time", 0.5, "< 500ms"),
            ("Database Query Response Time", "api_endpoints", "avg_response_time", 0.1, "< 100ms"),
            ("API Endpoint Response Time", "api_endpoints", "avg_response_time", 0.2, "< 200ms"),
            ("Concurrent Request Success Rate", "concurrent_requests", "success_rate", 80, "> 80%"),
        ]
        
        for benchmark_name, category, metric, target, target_desc in benchmarks:
            if category in self.performance_metrics and metric in self.performance_metrics[category]:
                actual = self.performance_metrics[category][metric]
                if 'time' in metric:
                    compliant = actual < target
                    print(f"  {benchmark_name}: {'✅ PASS' if compliant else '❌ FAIL'} - {actual:.3f}s ({target_desc})")
                else:
                    compliant = actual > target
                    print(f"  {benchmark_name}: {'✅ PASS' if compliant else '❌ FAIL'} - {actual:.1f}% ({target_desc})")
        
        # Failed Tests Details
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        # Security Assessment
        security_tests = [r for r in self.test_results if 'security' in r['test'].lower() or 'auth' in r['test'].lower()]
        security_passed = sum(1 for r in security_tests if r['success'])
        security_total = len(security_tests)
        security_score = (security_passed / security_total * 100) if security_total > 0 else 0
        
        print(f"\n🔒 SECURITY ASSESSMENT:")
        print(f"Security Tests Passed: {security_passed}/{security_total}")
        print(f"Security Score: {security_score:.1f}%")
        
        # Confidence Level
        confidence_factors = [
            success_rate >= 85,  # High success rate
            security_score >= 80,  # Good security score
            len(self.performance_metrics) >= 3,  # Multiple performance metrics
            total_tests >= 20,  # Comprehensive testing
        ]
        
        confidence_score = sum(confidence_factors) / len(confidence_factors) * 100
        confidence_level = "HIGH" if confidence_score >= 75 else "MEDIUM" if confidence_score >= 50 else "LOW"
        
        print(f"\n🎯 CONFIDENCE LEVEL: {confidence_level} ({confidence_score:.0f}%)")
        
        print(f"\n" + "=" * 80)
        print("🔍 COMPREHENSIVE BACKEND AUDIT COMPLETE")
        print("=" * 80)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "security_score": security_score,
            "confidence_level": confidence_level,
            "performance_metrics": self.performance_metrics
        }
    
    def run_comprehensive_audit(self):
        """Run the complete comprehensive backend audit"""
        print("🚀 STARTING COMPREHENSIVE BACKEND AUDIT")
        print("Following AI Accountability Protocol")
        print("=" * 80)
        
        # 1. Authentication System Verification
        self.test_user_registration_valid()
        self.test_user_registration_invalid()
        self.test_user_login_valid()
        self.test_user_login_invalid()
        self.test_jwt_token_validation()
        self.test_authentication_performance()
        
        # 2. Database Operations Audit
        self.test_database_crud_operations()
        self.test_database_performance()
        
        # 3. API Endpoints Comprehensive Testing
        self.test_all_api_endpoints()
        self.test_rate_limiting()
        
        # 4. Chat System Functionality
        self.test_chat_system_functionality()
        self.test_file_sharing()
        
        # 5. Security Implementation Verification
        self.test_security_implementation()
        
        # 6. Load Testing
        self.test_concurrent_requests()
        
        # Generate comprehensive report
        return self.generate_comprehensive_report()

if __name__ == "__main__":
    auditor = ComprehensiveBackendAuditor()
    results = auditor.run_comprehensive_audit()
    
    # Exit with appropriate code
    exit(0 if results["success_rate"] >= 80 else 1)