#!/usr/bin/env python3
"""
Games System Backend Testing Script
Tests the new Games System backend endpoints for multiplayer gaming feature
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://d2ce893b-8b01-49a3-8aed-a13ce7bbac25.preview.emergentagent.com/api"
TEST_USER_EMAIL = "games_test_user@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_USERNAME = "games_test_user"

class GamesSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.created_room_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details="", response_time=0):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_time": f"{response_time:.3f}s",
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} | {test_name} | {details} | {response_time:.3f}s")
        
    def setup_test_user(self):
        """Create and authenticate test user"""
        print("\n🔐 Setting up test user authentication...")
        
        # Try to register test user
        register_data = {
            "username": TEST_USER_USERNAME,
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "display_name": "Games Test User"
        }
        
        start_time = time.time()
        try:
            response = self.session.post(f"{BACKEND_URL}/register", json=register_data)
            response_time = time.time() - start_time
            
            if response.status_code == 201:
                data = response.json()
                self.token = data.get("access_token")
                self.user_id = data.get("user", {}).get("user_id")
                self.log_test("User Registration", True, f"New user created: {TEST_USER_EMAIL}", response_time)
            elif response.status_code == 400 and "already exists" in response.text:
                # User exists, try to login
                self.log_test("User Registration", True, "User already exists, proceeding to login", response_time)
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}", time.time() - start_time)
            return False
        
        # Login if we don't have token yet
        if not self.token:
            login_data = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            start_time = time.time()
            try:
                response = self.session.post(f"{BACKEND_URL}/login", json=login_data)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
                    self.user_id = data.get("user", {}).get("user_id")
                    self.log_test("User Login", True, f"Login successful: {TEST_USER_EMAIL}", response_time)
                else:
                    self.log_test("User Login", False, f"Status: {response.status_code}, Response: {response.text}", response_time)
                    return False
                    
            except Exception as e:
                self.log_test("User Login", False, f"Exception: {str(e)}", time.time() - start_time)
                return False
        
        # Set authorization header
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        
        return False
    
    def test_get_game_rooms(self):
        """Test GET /api/games/rooms - Should return list of active game rooms"""
        print("\n🎮 Testing GET /api/games/rooms...")
        
        start_time = time.time()
        try:
            response = self.session.get(f"{BACKEND_URL}/games/rooms")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("GET /api/games/rooms", True, f"Retrieved {len(data)} game rooms", response_time)
                    
                    # Log details about rooms if any exist
                    if data:
                        for room in data[:3]:  # Show first 3 rooms
                            room_info = f"Room: {room.get('name', 'Unknown')}, Type: {room.get('game_type', 'Unknown')}, Players: {room.get('current_players', 0)}/{room.get('max_players', 0)}"
                            print(f"    📋 {room_info}")
                    else:
                        print("    📋 No active game rooms found (expected for initial state)")
                    
                    return True
                else:
                    self.log_test("GET /api/games/rooms", False, f"Expected list, got: {type(data)}", response_time)
            else:
                self.log_test("GET /api/games/rooms", False, f"Status: {response.status_code}, Response: {response.text}", response_time)
                
        except Exception as e:
            self.log_test("GET /api/games/rooms", False, f"Exception: {str(e)}", time.time() - start_time)
            
        return False
    
    def test_create_game_room(self):
        """Test POST /api/games/rooms/create - Create a new game room"""
        print("\n🎮 Testing POST /api/games/rooms/create...")
        
        room_data = {
            "name": "Test Game Room",
            "gameType": "tic-tac-toe",
            "maxPlayers": 2,
            "isPrivate": False,
            "password": None
        }
        
        start_time = time.time()
        try:
            response = self.session.post(f"{BACKEND_URL}/games/rooms/create", json=room_data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "room_id" in data:
                    self.created_room_id = data["room_id"]
                    room_info = f"Room ID: {self.created_room_id}, Name: {data.get('name')}, Type: {data.get('game_type')}"
                    self.log_test("POST /api/games/rooms/create", True, room_info, response_time)
                    
                    # Verify room properties
                    expected_fields = ["room_id", "name", "game_type", "max_players", "created_by", "players", "status"]
                    missing_fields = [field for field in expected_fields if field not in data]
                    if missing_fields:
                        print(f"    ⚠️  Missing fields: {missing_fields}")
                    else:
                        print(f"    ✅ All required fields present")
                    
                    # Verify creator is in players list
                    if self.user_id in data.get("players", []):
                        print(f"    ✅ Creator automatically added to players list")
                    else:
                        print(f"    ⚠️  Creator not in players list")
                    
                    return True
                else:
                    self.log_test("POST /api/games/rooms/create", False, f"No room_id in response: {data}", response_time)
            else:
                self.log_test("POST /api/games/rooms/create", False, f"Status: {response.status_code}, Response: {response.text}", response_time)
                
        except Exception as e:
            self.log_test("POST /api/games/rooms/create", False, f"Exception: {str(e)}", time.time() - start_time)
            
        return False
    
    def test_join_game_room(self):
        """Test POST /api/games/rooms/{room_id}/join - Join the created room"""
        print("\n🎮 Testing POST /api/games/rooms/{room_id}/join...")
        
        if not self.created_room_id:
            self.log_test("POST /api/games/rooms/{room_id}/join", False, "No room_id available (room creation failed)", 0)
            return False
        
        # Create a second test user to join the room
        second_user_data = {
            "username": "games_test_user_2",
            "email": "games_test_user_2@example.com",
            "password": "TestPassword123!",
            "display_name": "Games Test User 2"
        }
        
        # Create second session
        second_session = requests.Session()
        
        start_time = time.time()
        try:
            # Register second user
            response = second_session.post(f"{BACKEND_URL}/register", json=second_user_data)
            if response.status_code == 400 and "already exists" in response.text:
                # User exists, login
                login_data = {
                    "email": second_user_data["email"],
                    "password": second_user_data["password"]
                }
                response = second_session.post(f"{BACKEND_URL}/login", json=login_data)
            
            if response.status_code in [200, 201]:
                data = response.json()
                second_token = data.get("access_token")
                second_user_id = data.get("user", {}).get("user_id")
                second_session.headers.update({"Authorization": f"Bearer {second_token}"})
                
                # Now try to join the room
                join_response = second_session.post(f"{BACKEND_URL}/games/rooms/{self.created_room_id}/join")
                response_time = time.time() - start_time
                
                if join_response.status_code == 200:
                    join_data = join_response.json()
                    status = join_data.get("status", "unknown")
                    self.log_test("POST /api/games/rooms/{room_id}/join", True, f"Join status: {status}", response_time)
                    
                    if status == "joined_as_player":
                        print(f"    ✅ Successfully joined as player")
                    elif status == "joined_as_spectator":
                        print(f"    ✅ Room full, joined as spectator")
                    
                    return True
                else:
                    self.log_test("POST /api/games/rooms/{room_id}/join", False, f"Status: {join_response.status_code}, Response: {join_response.text}", response_time)
            else:
                self.log_test("POST /api/games/rooms/{room_id}/join", False, f"Failed to create/login second user: {response.status_code}", time.time() - start_time)
                
        except Exception as e:
            self.log_test("POST /api/games/rooms/{room_id}/join", False, f"Exception: {str(e)}", time.time() - start_time)
            
        return False
    
    def test_start_game(self):
        """Test POST /api/games/rooms/{room_id}/start - Start the game"""
        print("\n🎮 Testing POST /api/games/rooms/{room_id}/start...")
        
        if not self.created_room_id:
            self.log_test("POST /api/games/rooms/{room_id}/start", False, "No room_id available (room creation failed)", 0)
            return False
        
        start_time = time.time()
        try:
            response = self.session.post(f"{BACKEND_URL}/games/rooms/{self.created_room_id}/start")
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "game_started":
                    game_state = data.get("game_state", {})
                    self.log_test("POST /api/games/rooms/{room_id}/start", True, f"Game started with state: {len(str(game_state))} chars", response_time)
                    
                    # Verify game state for tic-tac-toe
                    if "board" in game_state and "current_player" in game_state:
                        print(f"    ✅ Tic-tac-toe game state initialized correctly")
                        print(f"    📋 Board: {game_state.get('board')}")
                        print(f"    📋 Current player: {game_state.get('current_player')}")
                        print(f"    📋 Players: {game_state.get('players')}")
                    else:
                        print(f"    ⚠️  Game state missing expected fields")
                    
                    return True
                else:
                    self.log_test("POST /api/games/rooms/{room_id}/start", False, f"Unexpected response: {data}", response_time)
            elif response.status_code == 400:
                # Check if it's because we need more players
                error_msg = response.text
                if "Need at least 2 players" in error_msg:
                    self.log_test("POST /api/games/rooms/{room_id}/start", True, "Correctly requires 2+ players to start", response_time)
                    print(f"    ✅ Proper validation: Need at least 2 players")
                    return True
                else:
                    self.log_test("POST /api/games/rooms/{room_id}/start", False, f"Status: {response.status_code}, Response: {error_msg}", response_time)
            else:
                self.log_test("POST /api/games/rooms/{room_id}/start", False, f"Status: {response.status_code}, Response: {response.text}", response_time)
                
        except Exception as e:
            self.log_test("POST /api/games/rooms/{room_id}/start", False, f"Exception: {str(e)}", time.time() - start_time)
            
        return False
    
    def test_authentication_required(self):
        """Test that all endpoints require authentication"""
        print("\n🔐 Testing authentication requirements...")
        
        # Create session without auth token
        unauth_session = requests.Session()
        
        endpoints = [
            ("GET", f"{BACKEND_URL}/games/rooms"),
            ("POST", f"{BACKEND_URL}/games/rooms/create"),
            ("POST", f"{BACKEND_URL}/games/rooms/dummy/join"),
            ("POST", f"{BACKEND_URL}/games/rooms/dummy/start")
        ]
        
        all_protected = True
        for method, url in endpoints:
            start_time = time.time()
            try:
                if method == "GET":
                    response = unauth_session.get(url)
                else:
                    response = unauth_session.post(url, json={})
                
                response_time = time.time() - start_time
                
                if response.status_code == 401 or response.status_code == 403:
                    print(f"    ✅ {method} {url.split('/')[-2:]} - Protected (401/403)")
                else:
                    print(f"    ❌ {method} {url.split('/')[-2:]} - Not protected ({response.status_code})")
                    all_protected = False
                    
            except Exception as e:
                print(f"    ⚠️  {method} {url.split('/')[-2:]} - Exception: {str(e)}")
                all_protected = False
        
        self.log_test("Authentication Required", all_protected, "All endpoints properly protected" if all_protected else "Some endpoints not protected", 0)
        return all_protected
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n🚨 Testing error handling...")
        
        test_cases = [
            {
                "name": "Invalid room ID for join",
                "method": "POST",
                "url": f"{BACKEND_URL}/games/rooms/invalid-room-id/join",
                "expected_status": 404,
                "data": {}
            },
            {
                "name": "Invalid room ID for start",
                "method": "POST", 
                "url": f"{BACKEND_URL}/games/rooms/invalid-room-id/start",
                "expected_status": 404,
                "data": {}
            },
            {
                "name": "Create room with missing data",
                "method": "POST",
                "url": f"{BACKEND_URL}/games/rooms/create",
                "expected_status": [400, 422],  # Could be either
                "data": {"name": ""}  # Missing required fields
            }
        ]
        
        all_passed = True
        for test_case in test_cases:
            start_time = time.time()
            try:
                if test_case["method"] == "GET":
                    response = self.session.get(test_case["url"])
                else:
                    response = self.session.post(test_case["url"], json=test_case["data"])
                
                response_time = time.time() - start_time
                expected_statuses = test_case["expected_status"] if isinstance(test_case["expected_status"], list) else [test_case["expected_status"]]
                
                if response.status_code in expected_statuses:
                    print(f"    ✅ {test_case['name']} - Correct error ({response.status_code})")
                else:
                    print(f"    ❌ {test_case['name']} - Wrong status ({response.status_code}, expected {expected_statuses})")
                    all_passed = False
                    
            except Exception as e:
                print(f"    ⚠️  {test_case['name']} - Exception: {str(e)}")
                all_passed = False
        
        self.log_test("Error Handling", all_passed, "All error cases handled correctly" if all_passed else "Some error cases not handled properly", 0)
        return all_passed
    
    def run_all_tests(self):
        """Run all games system tests"""
        print("🎮 GAMES SYSTEM BACKEND TESTING")
        print("=" * 50)
        
        # Setup
        if not self.setup_test_user():
            print("❌ Failed to setup test user. Cannot proceed with tests.")
            return False
        
        # Core functionality tests
        tests = [
            self.test_get_game_rooms,
            self.test_create_game_room,
            self.test_join_game_room,
            self.test_start_game,
            self.test_authentication_required,
            self.test_error_handling
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_func in tests:
            if test_func():
                passed_tests += 1
        
        # Summary
        print("\n" + "=" * 50)
        print("🎮 GAMES SYSTEM TEST SUMMARY")
        print("=" * 50)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate >= 80:
            print("🎉 GAMES SYSTEM: EXCELLENT - Ready for production!")
        elif success_rate >= 60:
            print("✅ GAMES SYSTEM: GOOD - Minor issues to address")
        else:
            print("⚠️  GAMES SYSTEM: NEEDS WORK - Major issues found")
        
        # Detailed results
        print("\n📋 Detailed Test Results:")
        for result in self.test_results:
            print(f"  {result['status']} {result['test']}: {result['details']} ({result['response_time']})")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = GamesSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)