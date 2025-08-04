#!/usr/bin/env python3
"""
Comprehensive test script for Temporary Chat functionality
Tests all temporary chat endpoints as requested in the review.
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys

# Configuration
BACKEND_URL = "https://d2ce893b-8b01-49a3-8aed-a13ce7bbac25.preview.emergentagent.com/api"

class TemporaryChatTester:
    def __init__(self):
        self.session = requests.Session()
        self.user1_token = None
        self.user2_token = None
        self.user1_id = None
        self.user2_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and isinstance(response_data, dict):
            if success:
                print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
            else:
                print(f"   Error Response: {response_data}")
        print()
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
    
    def setup_test_users(self):
        """Create and authenticate test users"""
        print("🔧 Setting up test users...")
        
        # Create test users
        timestamp = int(time.time())
        user1_data = {
            "username": f"temp_chat_user1_{timestamp}",
            "email": f"temp_chat_user1_{timestamp}@test.com",
            "password": "testpass123",
            "display_name": "Temp Chat User 1"
        }
        
        user2_data = {
            "username": f"temp_chat_user2_{timestamp}",
            "email": f"temp_chat_user2_{timestamp}@test.com", 
            "password": "testpass123",
            "display_name": "Temp Chat User 2"
        }
        
        # Register users
        try:
            # Register user 1
            response1 = self.session.post(f"{BACKEND_URL}/register", json=user1_data)
            if response1.status_code == 200:
                data1 = response1.json()
                self.user1_token = data1.get("access_token")
                self.user1_id = data1.get("user", {}).get("user_id")
                print(f"✅ User 1 registered: {user1_data['username']}")
            else:
                print(f"❌ Failed to register user 1: {response1.text}")
                return False
                
            # Register user 2
            response2 = self.session.post(f"{BACKEND_URL}/register", json=user2_data)
            if response2.status_code == 200:
                data2 = response2.json()
                self.user2_token = data2.get("access_token")
                self.user2_id = data2.get("user", {}).get("user_id")
                print(f"✅ User 2 registered: {user2_data['username']}")
            else:
                print(f"❌ Failed to register user 2: {response2.text}")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Error setting up users: {e}")
            return False
    
    def test_create_temporary_chat_1hour_group(self):
        """Test creating a 1-hour temporary group chat"""
        print("🧪 Testing: Create 1-hour temporary group chat...")
        
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        chat_data = {
            "name": "Holiday Planning",
            "description": "Planning our holiday trip",
            "members": [self.user2_id],
            "chat_type": "group",
            "expiry_duration": "1hour"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chats/temporary",
                json=chat_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                chat = data.get("chat", {})
                
                # Verify response structure
                required_fields = ["chat_id", "name", "is_temporary", "expires_at", "expiry_duration"]
                missing_fields = [field for field in required_fields if field not in chat]
                
                if missing_fields:
                    self.log_result(
                        "Create 1-hour temporary group chat",
                        False,
                        f"Missing fields in response: {missing_fields}",
                        data
                    )
                    return None
                
                # Verify chat properties
                if (chat["name"].startswith("T ") and 
                    chat["is_temporary"] == True and
                    chat["expiry_duration"] == "1hour" and
                    data.get("expires_at") and
                    data.get("time_remaining")):
                    
                    self.log_result(
                        "Create 1-hour temporary group chat",
                        True,
                        f"Chat created with ID: {chat['chat_id']}, expires in: {data['time_remaining']}",
                        data
                    )
                    return chat["chat_id"]
                else:
                    self.log_result(
                        "Create 1-hour temporary group chat",
                        False,
                        "Chat properties don't match expected values",
                        data
                    )
                    return None
            else:
                self.log_result(
                    "Create 1-hour temporary group chat",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    None
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Create 1-hour temporary group chat",
                False,
                f"Exception: {str(e)}",
                None
            )
            return None
    
    def test_create_temporary_chat_1day_direct(self):
        """Test creating a 1-day temporary direct chat"""
        print("🧪 Testing: Create 1-day temporary direct chat...")
        
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        chat_data = {
            "name": "Quick Discussion",
            "description": "Quick chat about project",
            "members": [self.user2_id],
            "chat_type": "direct",
            "expiry_duration": "1day"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chats/temporary",
                json=chat_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                chat = data.get("chat", {})
                
                # Verify response structure and properties
                if (chat.get("name", "").startswith("T ") and 
                    chat.get("is_temporary") == True and
                    chat.get("expiry_duration") == "1day" and
                    chat.get("chat_type") == "direct" and
                    len(chat.get("members", [])) == 2):
                    
                    self.log_result(
                        "Create 1-day temporary direct chat",
                        True,
                        f"Direct chat created with ID: {chat['chat_id']}, expires in: {data['time_remaining']}",
                        data
                    )
                    return chat["chat_id"]
                else:
                    self.log_result(
                        "Create 1-day temporary direct chat",
                        False,
                        "Chat properties don't match expected values for direct chat",
                        data
                    )
                    return None
            else:
                self.log_result(
                    "Create 1-day temporary direct chat",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    None
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Create 1-day temporary direct chat",
                False,
                f"Exception: {str(e)}",
                None
            )
            return None
    
    def test_extend_temporary_chat(self, chat_id):
        """Test extending a temporary chat"""
        if not chat_id:
            self.log_result(
                "Extend temporary chat",
                False,
                "No chat_id provided for extension test",
                None
            )
            return False
            
        print(f"🧪 Testing: Extend temporary chat {chat_id}...")
        
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        extend_data = {
            "chat_id": chat_id,
            "extension_duration": "1day"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chats/{chat_id}/extend",
                json=extend_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["success", "new_expires_at", "time_remaining", "extended_by"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Extend temporary chat",
                        False,
                        f"Missing fields in response: {missing_fields}",
                        data
                    )
                    return False
                
                if (data.get("success") == True and
                    data.get("extended_by") == "1day" and
                    data.get("new_expires_at") and
                    data.get("time_remaining")):
                    
                    self.log_result(
                        "Extend temporary chat",
                        True,
                        f"Chat extended by 1 day, new expiry: {data['time_remaining']}",
                        data
                    )
                    return True
                else:
                    self.log_result(
                        "Extend temporary chat",
                        False,
                        "Extension response doesn't match expected values",
                        data
                    )
                    return False
            else:
                self.log_result(
                    "Extend temporary chat",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    None
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Extend temporary chat",
                False,
                f"Exception: {str(e)}",
                None
            )
            return False
    
    def test_get_chat_status(self, chat_id):
        """Test getting chat status"""
        if not chat_id:
            self.log_result(
                "Get chat status",
                False,
                "No chat_id provided for status test",
                None
            )
            return False
            
        print(f"🧪 Testing: Get chat status for {chat_id}...")
        
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/chats/{chat_id}/status",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure for temporary chat
                required_fields = ["chat_id", "is_temporary", "chat_type", "name", "members_count"]
                temp_fields = ["expires_at", "time_remaining", "expiry_duration", "is_expired", "created_by"]
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Get chat status",
                        False,
                        f"Missing required fields: {missing_fields}",
                        data
                    )
                    return False
                
                # For temporary chats, check temporary-specific fields
                if data.get("is_temporary"):
                    missing_temp_fields = [field for field in temp_fields if field not in data]
                    if missing_temp_fields:
                        self.log_result(
                            "Get chat status",
                            False,
                            f"Missing temporary chat fields: {missing_temp_fields}",
                            data
                        )
                        return False
                
                self.log_result(
                    "Get chat status",
                    True,
                    f"Status retrieved - Temporary: {data['is_temporary']}, Type: {data['chat_type']}, Members: {data['members_count']}",
                    data
                )
                return True
            else:
                self.log_result(
                    "Get chat status",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    None
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Get chat status",
                False,
                f"Exception: {str(e)}",
                None
            )
            return False
    
    def test_list_chats_with_temporary_info(self):
        """Test listing chats and verify temporary info is included"""
        print("🧪 Testing: List chats with temporary info...")
        
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/chats",
                headers=headers
            )
            
            if response.status_code == 200:
                chats = response.json()
                
                if not isinstance(chats, list):
                    self.log_result(
                        "List chats with temporary info",
                        False,
                        "Response is not a list of chats",
                        chats
                    )
                    return False
                
                # Find temporary chats and verify they have temporary_info
                temporary_chats = [chat for chat in chats if chat.get("is_temporary")]
                
                if not temporary_chats:
                    self.log_result(
                        "List chats with temporary info",
                        False,
                        "No temporary chats found in chat list",
                        {"total_chats": len(chats)}
                    )
                    return False
                
                # Verify temporary chats have proper info
                all_have_temp_info = True
                all_have_t_prefix = True
                
                for chat in temporary_chats:
                    if "temporary_info" not in chat:
                        all_have_temp_info = False
                    if not chat.get("name", "").startswith("T "):
                        all_have_t_prefix = False
                    
                    # Verify temporary_info structure
                    temp_info = chat.get("temporary_info", {})
                    required_temp_fields = ["expires_at", "time_remaining", "expiry_duration", "is_expired"]
                    missing_temp_fields = [field for field in required_temp_fields if field not in temp_info]
                    
                    if missing_temp_fields:
                        self.log_result(
                            "List chats with temporary info",
                            False,
                            f"Temporary chat missing temp_info fields: {missing_temp_fields}",
                            chat
                        )
                        return False
                
                if all_have_temp_info and all_have_t_prefix:
                    self.log_result(
                        "List chats with temporary info",
                        True,
                        f"Found {len(temporary_chats)} temporary chats with proper temporary_info and 'T' prefix",
                        {"temporary_chats_count": len(temporary_chats), "total_chats": len(chats)}
                    )
                    return True
                else:
                    issues = []
                    if not all_have_temp_info:
                        issues.append("missing temporary_info")
                    if not all_have_t_prefix:
                        issues.append("missing 'T' prefix")
                    
                    self.log_result(
                        "List chats with temporary info",
                        False,
                        f"Issues found: {', '.join(issues)}",
                        {"temporary_chats": temporary_chats}
                    )
                    return False
            else:
                self.log_result(
                    "List chats with temporary info",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    None
                )
                return False
                
        except Exception as e:
            self.log_result(
                "List chats with temporary info",
                False,
                f"Exception: {str(e)}",
                None
            )
            return False
    
    def test_invalid_duration(self):
        """Test creating temporary chat with invalid duration"""
        print("🧪 Testing: Create temporary chat with invalid duration...")
        
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        chat_data = {
            "name": "Invalid Duration Test",
            "description": "Testing invalid duration",
            "members": [self.user2_id],
            "chat_type": "group",
            "expiry_duration": "invalid_duration"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chats/temporary",
                json=chat_data,
                headers=headers
            )
            
            if response.status_code == 400:
                self.log_result(
                    "Invalid duration validation",
                    True,
                    "Correctly rejected invalid duration with 400 error",
                    {"status_code": response.status_code, "response": response.text}
                )
                return True
            else:
                self.log_result(
                    "Invalid duration validation",
                    False,
                    f"Expected 400 error but got {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Invalid duration validation",
                False,
                f"Exception: {str(e)}",
                None
            )
            return False
    
    def test_1week_duration(self):
        """Test creating temporary chat with 1week duration"""
        print("🧪 Testing: Create 1-week temporary chat...")
        
        headers = {"Authorization": f"Bearer {self.user1_token}"}
        chat_data = {
            "name": "Weekly Project Chat",
            "description": "One week project discussion",
            "members": [self.user2_id],
            "chat_type": "group",
            "expiry_duration": "1week"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/chats/temporary",
                json=chat_data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                chat = data.get("chat", {})
                
                if (chat.get("expiry_duration") == "1week" and
                    chat.get("is_temporary") == True):
                    
                    self.log_result(
                        "Create 1-week temporary chat",
                        True,
                        f"1-week chat created successfully, expires in: {data.get('time_remaining')}",
                        data
                    )
                    return chat.get("chat_id")
                else:
                    self.log_result(
                        "Create 1-week temporary chat",
                        False,
                        "1-week duration not properly set",
                        data
                    )
                    return None
            else:
                self.log_result(
                    "Create 1-week temporary chat",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    None
                )
                return None
                
        except Exception as e:
            self.log_result(
                "Create 1-week temporary chat",
                False,
                f"Exception: {str(e)}",
                None
            )
            return None
    
    def run_all_tests(self):
        """Run all temporary chat tests"""
        print("🚀 Starting Temporary Chat Functionality Tests")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_users():
            print("❌ Failed to setup test users. Aborting tests.")
            return
        
        print("\n📋 Running Test Scenarios:")
        print("-" * 40)
        
        # Test Scenario 1: Create 1-hour temporary group chat
        group_chat_id = self.test_create_temporary_chat_1hour_group()
        
        # Test Scenario 2: Create 1-day temporary direct chat  
        direct_chat_id = self.test_create_temporary_chat_1day_direct()
        
        # Test Scenario 3: Extend the 1-hour chat by 1 day
        if group_chat_id:
            self.test_extend_temporary_chat(group_chat_id)
        
        # Test Scenario 4: Check status of both temporary chats
        if group_chat_id:
            self.test_get_chat_status(group_chat_id)
        if direct_chat_id:
            self.test_get_chat_status(direct_chat_id)
        
        # Test Scenario 5: List all chats and verify temporary chat information
        self.test_list_chats_with_temporary_info()
        
        # Additional Tests
        print("\n🔍 Additional Validation Tests:")
        print("-" * 40)
        
        # Test invalid duration
        self.test_invalid_duration()
        
        # Test 1week duration
        self.test_1week_duration()
        
        # Print Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        print("\n✅ Passed Tests:")
        for result in self.test_results:
            if result["success"]:
                print(f"  • {result['test']}")
        
        print("\n" + "=" * 60)
        
        # Overall result
        if passed == total:
            print("🎉 ALL TESTS PASSED! Temporary chat functionality is working correctly.")
        elif passed >= total * 0.8:
            print("⚠️  MOSTLY WORKING: Most tests passed but some issues found.")
        else:
            print("❌ CRITICAL ISSUES: Multiple test failures detected.")

def main():
    """Main function"""
    print("🧪 Temporary Chat Backend API Testing")
    print("Testing all temporary chat endpoints as requested")
    print()
    
    tester = TemporaryChatTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()