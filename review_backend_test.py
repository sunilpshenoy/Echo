#!/usr/bin/env python3
"""
Comprehensive Backend Testing Script - Focus on Review Request Areas
Focus Areas:
1. QRCode generation endpoints - check if /api/qr-code endpoints work
2. Groups/Teams creation functionality - test POST /api/teams endpoint
3. Authentication performance - test login/register endpoints
4. Overall API response times and performance
5. Any runtime errors or issues with the backend
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
import base64

# Backend URL from environment
BACKEND_URL = "https://1345bce5-cc7d-477e-8431-d11bc6e77861.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_user_id = None
        self.results = []
        self.performance_metrics = []
        
    async def setup_session(self):
        """Setup HTTP session"""
        self.session = aiohttp.ClientSession()
        
    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()
            
    def log_result(self, test_name, success, message, response_time=None, status_code=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'response_time': response_time,
            'status_code': status_code,
            'timestamp': datetime.now().isoformat()
        }
        self.results.append(result)
        
        if response_time:
            self.performance_metrics.append({
                'endpoint': test_name,
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            })
        
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.3f}s)" if response_time else ""
        status_info = f" [HTTP {status_code}]" if status_code else ""
        print(f"{status} {test_name}{time_info}{status_info}: {message}")
        
    async def make_request(self, method, endpoint, data=None, headers=None, files=None):
        """Make HTTP request with timing"""
        url = f"{BACKEND_URL}{endpoint}"
        start_time = time.time()
        
        try:
            if headers is None:
                headers = {}
                
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
                
            if files:
                # For file uploads
                async with self.session.request(method, url, data=data, headers=headers) as response:
                    response_time = time.time() - start_time
                    response_data = await response.text()
                    try:
                        response_json = json.loads(response_data)
                    except:
                        response_json = {'raw_response': response_data}
                    return response, response_json, response_time
            else:
                # For JSON requests
                if data:
                    headers['Content-Type'] = 'application/json'
                    
                async with self.session.request(method, url, json=data, headers=headers) as response:
                    response_time = time.time() - start_time
                    response_data = await response.text()
                    try:
                        response_json = json.loads(response_data)
                    except:
                        response_json = {'raw_response': response_data}
                    return response, response_json, response_time
                    
        except Exception as e:
            response_time = time.time() - start_time
            return None, {'error': str(e)}, response_time

    async def test_authentication_performance(self):
        """Test authentication endpoints for performance and functionality"""
        print("\n🔐 TESTING AUTHENTICATION PERFORMANCE")
        
        # Test user registration
        test_email = f"test_user_{int(time.time())}@test.com"
        register_data = {
            "username": f"testuser_{int(time.time())}",
            "email": test_email,
            "password": "TestPassword123!",
            "display_name": "Test User"
        }
        
        response, data, response_time = await self.make_request('POST', '/register', register_data)
        
        if response and response.status == 200:
            self.log_result("User Registration", True, f"Successfully registered user {test_email}", response_time, response.status)
            if 'access_token' in data:
                self.auth_token = data['access_token']
                if 'user' in data and 'user_id' in data['user']:
                    self.test_user_id = data['user']['user_id']
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("User Registration", False, f"Registration failed: {error_msg}", response_time, response.status if response else None)
            
        # Test user login performance
        login_data = {
            "email": test_email,
            "password": "TestPassword123!"
        }
        
        response, data, response_time = await self.make_request('POST', '/login', login_data)
        
        if response and response.status == 200:
            self.log_result("User Login", True, f"Successfully logged in user {test_email}", response_time, response.status)
            if 'access_token' in data:
                self.auth_token = data['access_token']
                if 'user' in data and 'user_id' in data['user']:
                    self.test_user_id = data['user']['user_id']
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("User Login", False, f"Login failed: {error_msg}", response_time, response.status if response else None)
            
        # Test token validation
        if self.auth_token:
            response, data, response_time = await self.make_request('GET', '/users/me')
            
            if response and response.status == 200:
                self.log_result("Token Validation", True, f"Token validation successful", response_time, response.status)
            else:
                error_msg = data.get('detail', 'Unknown error') if data else 'No response'
                self.log_result("Token Validation", False, f"Token validation failed: {error_msg}", response_time, response.status if response else None)

    async def test_qr_code_generation(self):
        """Test QR code generation endpoints"""
        print("\n📱 TESTING QR CODE GENERATION")
        
        if not self.auth_token:
            self.log_result("QR Code Generation", False, "No authentication token available")
            return
            
        # Test QR code generation for user
        response, data, response_time = await self.make_request('GET', '/users/qr-code')
        
        if response and response.status == 200:
            if data and ('qr_code' in data or 'qr_data' in data or 'image' in data):
                self.log_result("QR Code Generation", True, "QR code generated successfully", response_time, response.status)
            else:
                self.log_result("QR Code Generation", False, f"QR code data missing in response: {list(data.keys()) if data else 'No data'}", response_time, response.status)
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("QR Code Generation", False, f"QR code generation failed: {error_msg}", response_time, response.status if response else None)
            
        # Test QR code with PIN (if available)
        response, data, response_time = await self.make_request('GET', '/users/me')
        if response and response.status == 200 and 'connection_pin' in data:
            pin = data['connection_pin']
            response, qr_data, response_time = await self.make_request('GET', f'/users/qr-code?pin={pin}')
            
            if response and response.status == 200:
                self.log_result("QR Code with PIN", True, f"QR code with PIN generated successfully", response_time, response.status)
            else:
                error_msg = qr_data.get('detail', 'Unknown error') if qr_data else 'No response'
                self.log_result("QR Code with PIN", False, f"QR code with PIN failed: {error_msg}", response_time, response.status if response else None)

    async def test_teams_functionality(self):
        """Test Teams/Groups creation and management"""
        print("\n👥 TESTING TEAMS/GROUPS FUNCTIONALITY")
        
        if not self.auth_token:
            self.log_result("Teams Functionality", False, "No authentication token available")
            return
            
        # Test team creation
        team_data = {
            "name": f"Test Team {int(time.time())}",
            "description": "Test team for backend testing",
            "members": [self.test_user_id] if self.test_user_id else [],
            "chat_type": "group"
        }
        
        response, data, response_time = await self.make_request('POST', '/teams', team_data)
        
        team_id = None
        if response and response.status == 200:
            if data and 'team_id' in data:
                team_id = data['team_id']
                self.log_result("Team Creation", True, f"Team created successfully with ID: {team_id}", response_time, response.status)
            else:
                self.log_result("Team Creation", False, f"Team creation response missing team_id: {list(data.keys()) if data else 'No data'}", response_time, response.status)
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("Team Creation", False, f"Team creation failed: {error_msg}", response_time, response.status if response else None)
            
        # Test team retrieval
        response, data, response_time = await self.make_request('GET', '/teams')
        
        if response and response.status == 200:
            if isinstance(data, list):
                self.log_result("Team Retrieval", True, f"Retrieved {len(data)} teams", response_time, response.status)
            else:
                self.log_result("Team Retrieval", False, f"Unexpected response format: {type(data)}", response_time, response.status)
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("Team Retrieval", False, f"Team retrieval failed: {error_msg}", response_time, response.status if response else None)
            
        # Test team messaging (if team was created)
        if team_id:
            message_data = {
                "content": "Test message for team",
                "message_type": "text"
            }
            
            response, data, response_time = await self.make_request('POST', f'/teams/{team_id}/messages', message_data)
            
            if response and response.status == 200:
                self.log_result("Team Messaging", True, "Team message sent successfully", response_time, response.status)
            else:
                error_msg = data.get('detail', 'Unknown error') if data else 'No response'
                self.log_result("Team Messaging", False, f"Team messaging failed: {error_msg}", response_time, response.status if response else None)
                
            # Test team message retrieval
            response, data, response_time = await self.make_request('GET', f'/teams/{team_id}/messages')
            
            if response and response.status == 200:
                if isinstance(data, list):
                    self.log_result("Team Message Retrieval", True, f"Retrieved {len(data)} team messages", response_time, response.status)
                else:
                    self.log_result("Team Message Retrieval", False, f"Unexpected response format: {type(data)}", response_time, response.status)
            else:
                error_msg = data.get('detail', 'Unknown error') if data else 'No response'
                self.log_result("Team Message Retrieval", False, f"Team message retrieval failed: {error_msg}", response_time, response.status if response else None)

    async def test_core_functionality(self):
        """Test core backend functionality"""
        print("\n🔧 TESTING CORE FUNCTIONALITY")
        
        if not self.auth_token:
            self.log_result("Core Functionality", False, "No authentication token available")
            return
            
        # Test chat creation
        chat_data = {
            "chat_type": "direct",
            "members": [self.test_user_id] if self.test_user_id else []
        }
        
        response, data, response_time = await self.make_request('POST', '/chats', chat_data)
        
        chat_id = None
        if response and response.status == 200:
            if data and 'chat_id' in data:
                chat_id = data['chat_id']
                self.log_result("Chat Creation", True, f"Chat created successfully with ID: {chat_id}", response_time, response.status)
            else:
                self.log_result("Chat Creation", False, f"Chat creation response missing chat_id: {list(data.keys()) if data else 'No data'}", response_time, response.status)
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("Chat Creation", False, f"Chat creation failed: {error_msg}", response_time, response.status if response else None)
            
        # Test message sending
        if chat_id:
            message_data = {
                "content": "Test message for backend testing",
                "message_type": "text"
            }
            
            response, data, response_time = await self.make_request('POST', f'/chats/{chat_id}/messages', message_data)
            
            if response and response.status == 200:
                self.log_result("Message Sending", True, "Message sent successfully", response_time, response.status)
            else:
                error_msg = data.get('detail', 'Unknown error') if data else 'No response'
                self.log_result("Message Sending", False, f"Message sending failed: {error_msg}", response_time, response.status if response else None)
                
        # Test file upload
        test_file_content = "Test file content for backend testing"
        test_file_data = base64.b64encode(test_file_content.encode()).decode()
        
        file_data = {
            "file_name": "test_file.txt",
            "file_data": test_file_data,
            "file_type": "text/plain"
        }
        
        response, data, response_time = await self.make_request('POST', '/upload', file_data)
        
        if response and response.status == 200:
            if 'file_id' in data:
                self.log_result("File Upload", True, f"File uploaded successfully with ID: {data['file_id']}", response_time, response.status)
            else:
                self.log_result("File Upload", False, f"File upload response missing file_id: {list(data.keys())}", response_time, response.status)
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("File Upload", False, f"File upload failed: {error_msg}", response_time, response.status if response else None)

    async def test_marketplace_functionality(self):
        """Test marketplace functionality"""
        print("\n🛒 TESTING MARKETPLACE FUNCTIONALITY")
        
        if not self.auth_token:
            self.log_result("Marketplace Functionality", False, "No authentication token available")
            return
            
        # Test marketplace categories
        response, data, response_time = await self.make_request('GET', '/marketplace/categories')
        
        if response and response.status == 200:
            if isinstance(data, list) and len(data) > 0:
                self.log_result("Marketplace Categories", True, f"Retrieved {len(data)} categories", response_time, response.status)
            else:
                self.log_result("Marketplace Categories", False, f"No categories found or invalid format", response_time, response.status)
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("Marketplace Categories", False, f"Categories retrieval failed: {error_msg}", response_time, response.status if response else None)
            
        # Test reels categories
        response, data, response_time = await self.make_request('GET', '/reels/categories')
        
        if response and response.status == 200:
            if isinstance(data, list) and len(data) > 0:
                self.log_result("Reels Categories", True, f"Retrieved {len(data)} reel categories", response_time, response.status)
            else:
                self.log_result("Reels Categories", False, f"No reel categories found or invalid format", response_time, response.status)
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("Reels Categories", False, f"Reels categories retrieval failed: {error_msg}", response_time, response.status if response else None)
            
        # Test reels feed
        response, data, response_time = await self.make_request('GET', '/reels/feed')
        
        if response and response.status == 200:
            if 'reels' in data and isinstance(data['reels'], list):
                self.log_result("Reels Feed", True, f"Retrieved {len(data['reels'])} reels", response_time, response.status)
            else:
                self.log_result("Reels Feed", False, f"Invalid reels feed format: {list(data.keys()) if data else 'No data'}", response_time, response.status)
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("Reels Feed", False, f"Reels feed retrieval failed: {error_msg}", response_time, response.status if response else None)

    async def test_performance_metrics(self):
        """Analyze performance metrics"""
        print("\n📊 PERFORMANCE ANALYSIS")
        
        if not self.performance_metrics:
            self.log_result("Performance Analysis", False, "No performance metrics collected")
            return
            
        # Calculate average response times
        total_time = sum(metric['response_time'] for metric in self.performance_metrics)
        avg_time = total_time / len(self.performance_metrics)
        
        # Find slowest endpoint
        slowest = max(self.performance_metrics, key=lambda x: x['response_time'])
        
        # Find fastest endpoint
        fastest = min(self.performance_metrics, key=lambda x: x['response_time'])
        
        # Count slow responses (> 2 seconds)
        slow_responses = [m for m in self.performance_metrics if m['response_time'] > 2.0]
        
        performance_summary = f"Average: {avg_time:.3f}s, Slowest: {slowest['endpoint']} ({slowest['response_time']:.3f}s), Fastest: {fastest['endpoint']} ({fastest['response_time']:.3f}s), Slow responses: {len(slow_responses)}/{len(self.performance_metrics)}"
        
        # Performance is good if average < 1s and no responses > 5s
        performance_good = avg_time < 1.0 and all(m['response_time'] < 5.0 for m in self.performance_metrics)
        
        self.log_result("Performance Analysis", performance_good, performance_summary)

    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 STARTING COMPREHENSIVE BACKEND TESTING")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Run all test suites
            await self.test_authentication_performance()
            await self.test_qr_code_generation()
            await self.test_teams_functionality()
            await self.test_core_functionality()
            await self.test_marketplace_functionality()
            await self.test_performance_metrics()
            
        finally:
            await self.cleanup_session()
            
        # Generate summary
        self.generate_summary()
        
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r['success']])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
                    
        # Critical issues
        critical_issues = []
        auth_failed = any(not r['success'] and 'Authentication' in r['test'] for r in self.results)
        qr_failed = any(not r['success'] and 'QR Code' in r['test'] for r in self.results)
        teams_failed = any(not r['success'] and 'Team' in r['test'] for r in self.results)
        
        if auth_failed:
            critical_issues.append("Authentication system issues detected")
        if qr_failed:
            critical_issues.append("QR Code generation not working")
        if teams_failed:
            critical_issues.append("Teams/Groups functionality issues")
            
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in critical_issues:
                print(f"  - {issue}")
        else:
            print(f"\n✅ NO CRITICAL ISSUES DETECTED")
            
        # Performance summary
        if self.performance_metrics:
            avg_time = sum(m['response_time'] for m in self.performance_metrics) / len(self.performance_metrics)
            print(f"\n⚡ PERFORMANCE: Average response time: {avg_time:.3f}s")
            
        print("=" * 60)

async def main():
    """Main function"""
    tester = BackendTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())