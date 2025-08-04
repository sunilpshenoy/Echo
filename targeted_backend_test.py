#!/usr/bin/env python3
"""
Targeted Backend Testing Script - Fix Issues and Retest
"""

import asyncio
import aiohttp
import json
import time
import base64
from datetime import datetime

# Backend URL from environment
BACKEND_URL = "https://d2ce893b-8b01-49a3-8aed-a13ce7bbac25.preview.emergentagent.com/api"

class TargetedBackendTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_user_id = None
        self.results = []
        
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

    async def setup_authentication(self):
        """Setup authentication for testing"""
        print("🔐 SETTING UP AUTHENTICATION")
        
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
            if data and 'access_token' in data:
                self.auth_token = data['access_token']
                if 'user' in data and 'user_id' in data['user']:
                    self.test_user_id = data['user']['user_id']
                    return True
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("User Registration", False, f"Registration failed: {error_msg}", response_time, response.status if response else None)
            return False

    async def test_qr_code_endpoints(self):
        """Test QR code generation endpoints specifically"""
        print("\n📱 TESTING QR CODE ENDPOINTS")
        
        if not self.auth_token:
            self.log_result("QR Code Test", False, "No authentication token available")
            return
            
        # Test basic QR code generation
        response, data, response_time = await self.make_request('GET', '/users/qr-code')
        
        if response and response.status == 200:
            if data and ('qr_code' in data or 'qr_data' in data or 'image' in data or 'data' in data):
                self.log_result("QR Code Generation", True, f"QR code generated successfully. Response keys: {list(data.keys())}", response_time, response.status)
            else:
                self.log_result("QR Code Generation", False, f"QR code data missing. Response: {data}", response_time, response.status)
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("QR Code Generation", False, f"QR code generation failed: {error_msg}", response_time, response.status if response else None)

    async def test_teams_creation_fixed(self):
        """Test Teams creation with proper data structure"""
        print("\n👥 TESTING TEAMS CREATION (FIXED)")
        
        if not self.auth_token:
            self.log_result("Teams Creation", False, "No authentication token available")
            return
            
        # Test team creation with correct structure
        team_data = {
            "name": f"Test Team {int(time.time())}",
            "description": "Test team for backend testing",
            "members": [self.test_user_id] if self.test_user_id else []
        }
        
        response, data, response_time = await self.make_request('POST', '/teams', team_data)
        
        if response and response.status == 200:
            if data:
                self.log_result("Team Creation", True, f"Team created successfully. Response: {data}", response_time, response.status)
                
                # Test team retrieval
                response2, data2, response_time2 = await self.make_request('GET', '/teams')
                if response2 and response2.status == 200:
                    self.log_result("Team Retrieval", True, f"Retrieved teams successfully. Count: {len(data2) if isinstance(data2, list) else 'Unknown'}", response_time2, response2.status)
                else:
                    self.log_result("Team Retrieval", False, f"Team retrieval failed: {data2}", response_time2, response2.status if response2 else None)
            else:
                self.log_result("Team Creation", False, f"Team creation returned empty response", response_time, response.status)
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("Team Creation", False, f"Team creation failed: {error_msg}", response_time, response.status if response else None)

    async def test_chat_creation_fixed(self):
        """Test chat creation with proper parameters"""
        print("\n💬 TESTING CHAT CREATION (FIXED)")
        
        if not self.auth_token:
            self.log_result("Chat Creation", False, "No authentication token available")
            return
            
        # Create a second user for direct chat
        test_email2 = f"test_user2_{int(time.time())}@test.com"
        register_data2 = {
            "username": f"testuser2_{int(time.time())}",
            "email": test_email2,
            "password": "TestPassword123!",
            "display_name": "Test User 2"
        }
        
        response, data, response_time = await self.make_request('POST', '/register', register_data2)
        
        if response and response.status == 200 and data and 'user' in data:
            other_user_id = data['user']['user_id']
            
            # Test direct chat creation
            chat_data = {
                "chat_type": "direct",
                "other_user_id": other_user_id
            }
            
            response2, data2, response_time2 = await self.make_request('POST', '/chats', chat_data)
            
            if response2 and response2.status == 200:
                self.log_result("Direct Chat Creation", True, f"Direct chat created successfully. Response: {data2}", response_time2, response2.status)
            else:
                error_msg = data2.get('detail', 'Unknown error') if data2 else 'No response'
                self.log_result("Direct Chat Creation", False, f"Direct chat creation failed: {error_msg}", response_time2, response2.status if response2 else None)
                
            # Test group chat creation
            group_chat_data = {
                "chat_type": "group",
                "name": f"Test Group {int(time.time())}",
                "members": [self.test_user_id, other_user_id]
            }
            
            response3, data3, response_time3 = await self.make_request('POST', '/chats', group_chat_data)
            
            if response3 and response3.status == 200:
                self.log_result("Group Chat Creation", True, f"Group chat created successfully. Response: {data3}", response_time3, response3.status)
            else:
                error_msg = data3.get('detail', 'Unknown error') if data3 else 'No response'
                self.log_result("Group Chat Creation", False, f"Group chat creation failed: {error_msg}", response_time3, response3.status if response3 else None)
        else:
            self.log_result("Chat Creation Setup", False, "Failed to create second user for chat testing")

    async def test_file_upload_fixed(self):
        """Test file upload with proper multipart form data"""
        print("\n📁 TESTING FILE UPLOAD (FIXED)")
        
        if not self.auth_token:
            self.log_result("File Upload", False, "No authentication token available")
            return
            
        # Create proper multipart form data
        test_file_content = b"Test file content for backend testing"
        
        # Create form data
        form_data = aiohttp.FormData()
        form_data.add_field('file', test_file_content, filename='test_file.txt', content_type='text/plain')
        
        url = f"{BACKEND_URL}/upload"
        headers = {'Authorization': f'Bearer {self.auth_token}'}
        
        start_time = time.time()
        try:
            async with self.session.post(url, data=form_data, headers=headers) as response:
                response_time = time.time() - start_time
                response_data = await response.text()
                try:
                    response_json = json.loads(response_data)
                except:
                    response_json = {'raw_response': response_data}
                    
                if response.status == 200:
                    self.log_result("File Upload", True, f"File uploaded successfully. Response: {response_json}", response_time, response.status)
                else:
                    self.log_result("File Upload", False, f"File upload failed: {response_json}", response_time, response.status)
        except Exception as e:
            response_time = time.time() - start_time
            self.log_result("File Upload", False, f"File upload error: {str(e)}", response_time, None)

    async def test_marketplace_categories_debug(self):
        """Debug marketplace categories endpoint"""
        print("\n🛒 TESTING MARKETPLACE CATEGORIES (DEBUG)")
        
        if not self.auth_token:
            self.log_result("Marketplace Categories", False, "No authentication token available")
            return
            
        response, data, response_time = await self.make_request('GET', '/marketplace/categories')
        
        if response and response.status == 200:
            self.log_result("Marketplace Categories", True, f"Categories response: {data}", response_time, response.status)
        else:
            error_msg = data.get('detail', 'Unknown error') if data else 'No response'
            self.log_result("Marketplace Categories", False, f"Categories failed: {error_msg}", response_time, response.status if response else None)
            
        # Test reels categories
        response2, data2, response_time2 = await self.make_request('GET', '/reels/categories')
        
        if response2 and response2.status == 200:
            self.log_result("Reels Categories", True, f"Reels categories response: {data2}", response_time2, response2.status)
        else:
            error_msg = data2.get('detail', 'Unknown error') if data2 else 'No response'
            self.log_result("Reels Categories", False, f"Reels categories failed: {error_msg}", response_time2, response2.status if response2 else None)

    async def run_targeted_tests(self):
        """Run targeted tests to fix issues"""
        print("🎯 STARTING TARGETED BACKEND TESTING")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        await self.setup_session()
        
        try:
            # Setup authentication first
            auth_success = await self.setup_authentication()
            
            if auth_success:
                # Run targeted tests
                await self.test_qr_code_endpoints()
                await self.test_teams_creation_fixed()
                await self.test_chat_creation_fixed()
                await self.test_file_upload_fixed()
                await self.test_marketplace_categories_debug()
            else:
                print("❌ Authentication failed, skipping other tests")
                
        finally:
            await self.cleanup_session()
            
        # Generate summary
        self.generate_summary()
        
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📋 TARGETED TEST SUMMARY")
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
                    
        print("=" * 60)

async def main():
    """Main function"""
    tester = TargetedBackendTester()
    await tester.run_targeted_tests()

if __name__ == "__main__":
    asyncio.run(main())