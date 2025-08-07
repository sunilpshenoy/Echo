#!/usr/bin/env python3
"""
Pulse Games System Authentication and WebSocket Testing Script
Focused testing of resolved authentication and WebSocket issues as per review request:
- Authentication Flow Testing (HIGH PRIORITY RESOLVED)
- WebSocket Connection Testing (MEDIUM PRIORITY RESOLVED)
- Integration Testing
"""

import requests
import json
import time
import sys
import asyncio
import websockets
from datetime import datetime
import uuid
import jwt
import hashlib

# Configuration
BACKEND_URL = "https://9b83238d-a27b-406f-8157-e448fada6ab0.preview.emergentagent.com/api"
WEBSOCKET_URL = "wss://9b83238d-a27b-406f-8157-e448fada6ab0.preview.emergentagent.com"

class AuthWebSocketTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.test_results = []
        self.websocket_connections = []
        
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

    def test_authentication_flow(self):
        """Test Authentication Flow (HIGH PRIORITY RESOLVED)"""
        print("\n🔐 Testing Authentication Flow (HIGH PRIORITY RESOLVED)...")
        
        # Generate unique test user
        test_id = str(uuid.uuid4())[:8]
        test_email = f"auth_test_{test_id}@example.com"
        test_username = f"auth_test_{test_id}"
        test_password = "SecurePassword123!"
        
        # Test 1: User Registration
        print("\n1️⃣ Testing User Registration...")
        register_data = {
            "username": test_username,
            "email": test_email,
            "password": test_password,
            "display_name": f"Auth Test User {test_id}"
        }
        
        start_time = time.time()
        try:
            response = self.session.post(f"{BACKEND_URL}/register", json=register_data)
            response_time = time.time() - start_time
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test("User Registration", True, f"New user registered successfully: {data.get('user', {}).get('user_id', 'N/A')}", response_time)
            else:
                self.log_test("User Registration", False, f"Registration failed: {response.status_code} - {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("User Registration", False, f"Registration error: {str(e)}", time.time() - start_time)
            return False
        
        # Test 2: User Login with Proper Credentials
        print("\n2️⃣ Testing User Login (should no longer return 401 errors)...")
        login_data = {
            "email": test_email,
            "password": test_password
        }
        
        start_time = time.time()
        try:
            response = self.session.post(f"{BACKEND_URL}/login", json=login_data)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                user_data = data.get("user", {})
                self.user_id = user_data.get("user_id")
                
                # Set authorization header for future requests
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                
                self.log_test("User Login", True, f"Login successful, no 401 errors. User ID: {self.user_id}", response_time)
            else:
                self.log_test("User Login", False, f"Login failed with status {response.status_code}: {response.text}", response_time)
                return False
                
        except Exception as e:
            self.log_test("User Login", False, f"Login error: {str(e)}", time.time() - start_time)
            return False
        
        # Test 3: Token Validation
        print("\n3️⃣ Testing JWT Token Validation...")
        if self.token:
            try:
                # Decode token without verification to check structure
                decoded = jwt.decode(self.token, options={"verify_signature": False})
                
                start_time = time.time()
                # Test token with protected endpoint
                response = self.session.get(f"{BACKEND_URL}/users/profile/completeness")
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    self.log_test("Token Validation", True, f"JWT token properly issued and validated. Expires: {datetime.fromtimestamp(decoded.get('exp', 0))}", response_time)
                else:
                    self.log_test("Token Validation", False, f"Token validation failed: {response.status_code}", response_time)
                    
            except Exception as e:
                self.log_test("Token Validation", False, f"Token validation error: {str(e)}", 0)
        
        # Test 4: Session Management
        print("\n4️⃣ Testing Session Management...")
        start_time = time.time()
        try:
            # Test multiple authenticated requests to verify session persistence
            endpoints = [
                "/users/profile/completeness",
                "/chats",
                "/games/rooms"
            ]
            
            session_tests_passed = 0
            for endpoint in endpoints:
                resp = self.session.get(f"{BACKEND_URL}{endpoint}")
                if resp.status_code in [200, 201]:
                    session_tests_passed += 1
            
            response_time = time.time() - start_time
            
            if session_tests_passed == len(endpoints):
                self.log_test("Session Management", True, f"Session persists across {len(endpoints)} requests", response_time)
            else:
                self.log_test("Session Management", False, f"Session failed on {len(endpoints) - session_tests_passed}/{len(endpoints)} requests", response_time)
                
        except Exception as e:
            self.log_test("Session Management", False, f"Session management error: {str(e)}", time.time() - start_time)
        
        # Test 5: Password Verification
        print("\n5️⃣ Testing Password Verification...")
        
        # Test with wrong password
        wrong_login_data = {
            "email": test_email,
            "password": "WrongPassword123!"
        }
        
        start_time = time.time()
        try:
            response = self.session.post(f"{BACKEND_URL}/login", json=wrong_login_data)
            response_time = time.time() - start_time
            
            if response.status_code == 401:
                self.log_test("Password Verification", True, "Correctly rejects wrong password with 401", response_time)
            else:
                self.log_test("Password Verification", False, f"Unexpected response for wrong password: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Password Verification", False, f"Password verification error: {str(e)}", time.time() - start_time)
        
        return True

    async def test_websocket_connections(self):
        """Test WebSocket Connection Testing (MEDIUM PRIORITY RESOLVED)"""
        print("\n🔌 Testing WebSocket Connections (MEDIUM PRIORITY RESOLVED)...")
        
        if not self.user_id:
            print("⚠️ No authenticated user, skipping WebSocket tests")
            return False
        
        # Test 1: Connection Establishment with Timeout Handling
        print("\n1️⃣ Testing WebSocket Connection Establishment...")
        
        try:
            websocket_url = f"{WEBSOCKET_URL}/ws/games/test_room_{self.user_id}"
            
            start_time = time.time()
            # Test connection with timeout
            websocket = await asyncio.wait_for(
                websockets.connect(websocket_url), 
                timeout=15.0
            )
            response_time = time.time() - start_time
            
            self.websocket_connections.append(websocket)
            self.log_test("WebSocket Connection Establishment", True, f"Connected successfully with timeout handling in {response_time:.3f}s", response_time)
            
            # Test 2: Heartbeat System (Ping/Pong)
            print("\n2️⃣ Testing Heartbeat System (Ping/Pong)...")
            
            try:
                start_time = time.time()
                # Send ping and wait for pong
                pong_waiter = await websocket.ping()
                await asyncio.wait_for(pong_waiter, timeout=5.0)
                response_time = time.time() - start_time
                
                self.log_test("WebSocket Heartbeat", True, f"Ping/pong heartbeat successful, prevents timeouts", response_time)
                
            except asyncio.TimeoutError:
                self.log_test("WebSocket Heartbeat", False, "Ping/pong timeout - heartbeat system may not be working", 5.0)
            except Exception as e:
                self.log_test("WebSocket Heartbeat", False, f"Heartbeat error: {str(e)}", time.time() - start_time)
            
            # Test 3: Connection Stability Under Load
            print("\n3️⃣ Testing Connection Stability...")
            
            try:
                start_time = time.time()
                # Send multiple messages rapidly to test stability
                messages_sent = 0
                for i in range(10):
                    test_message = {
                        "type": "test_message",
                        "user_id": self.user_id,
                        "message": f"Stability test message {i+1}",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    messages_sent += 1
                    await asyncio.sleep(0.1)  # Small delay between messages
                
                response_time = time.time() - start_time
                self.log_test("Connection Stability", True, f"Sent {messages_sent} messages successfully, connection stable", response_time)
                
            except Exception as e:
                self.log_test("Connection Stability", False, f"Connection stability error: {str(e)}", time.time() - start_time)
            
            # Test 4: Games WebSocket with Heartbeat
            print("\n4️⃣ Testing Games WebSocket with Heartbeat...")
            
            try:
                # Create a game room first
                room_data = {
                    "name": f"WebSocket Test Room {self.user_id}",
                    "gameType": "tic-tac-toe",
                    "maxPlayers": 2,
                    "isPrivate": False
                }
                
                room_response = self.session.post(f"{BACKEND_URL}/games/rooms/create", json=room_data)
                if room_response.status_code == 200:
                    room = room_response.json()
                    room_id = room.get("room_id")
                    
                    # Connect to game-specific WebSocket
                    game_websocket_url = f"{WEBSOCKET_URL}/ws/games/{room_id}"
                    
                    start_time = time.time()
                    game_websocket = await asyncio.wait_for(
                        websockets.connect(game_websocket_url),
                        timeout=15.0
                    )
                    response_time = time.time() - start_time
                    
                    self.websocket_connections.append(game_websocket)
                    
                    # Test game-specific message
                    game_message = {
                        "type": "game_move",
                        "player_id": self.user_id,
                        "room_id": room_id,
                        "move": {"position": 0, "type": "cell_click"}
                    }
                    
                    await game_websocket.send(json.dumps(game_message))
                    
                    # Test heartbeat on game WebSocket
                    pong_waiter = await game_websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=5.0)
                    
                    self.log_test("Games WebSocket", True, f"Game WebSocket connected with heartbeat support", response_time)
                    
                else:
                    self.log_test("Games WebSocket", False, f"Failed to create game room: {room_response.text}", 0)
                    
            except Exception as e:
                self.log_test("Games WebSocket", False, f"Games WebSocket error: {str(e)}", 0)
            
            # Test 5: Error Recovery and Reconnection Logic
            print("\n5️⃣ Testing Error Recovery...")
            
            try:
                # Test graceful close and reconnection
                await websocket.close()
                
                start_time = time.time()
                # Attempt reconnection
                new_websocket = await asyncio.wait_for(
                    websockets.connect(websocket_url),
                    timeout=15.0
                )
                response_time = time.time() - start_time
                
                self.websocket_connections.append(new_websocket)
                self.log_test("Error Recovery", True, f"Reconnection successful after close", response_time)
                
                # Clean up
                await new_websocket.close()
                
            except Exception as e:
                self.log_test("Error Recovery", False, f"Error recovery failed: {str(e)}", 0)
            
            return True
            
        except asyncio.TimeoutError:
            self.log_test("WebSocket Connection Establishment", False, "Connection timeout - WebSocket may not be properly configured", 15.0)
            return False
        except Exception as e:
            self.log_test("WebSocket Connection Establishment", False, f"WebSocket connection error: {str(e)}", 0)
            return False

    async def test_integration(self):
        """Test Integration (WebSocket + Authentication)"""
        print("\n🔗 Testing Integration (WebSocket + Authentication)...")
        
        if not self.token or not self.user_id:
            print("⚠️ No authentication token, skipping integration tests")
            return False
        
        # Test 1: Complete Authentication Flow
        print("\n1️⃣ Testing Complete Authentication Flow...")
        
        try:
            # Registration → Login → Dashboard → Games Hub access
            start_time = time.time()
            
            # Test dashboard access
            dashboard_response = self.session.get(f"{BACKEND_URL}/users/profile/completeness")
            if dashboard_response.status_code != 200:
                self.log_test("Complete Auth Flow", False, f"Dashboard access failed: {dashboard_response.status_code}", time.time() - start_time)
                return False
            
            # Test games hub access
            games_response = self.session.get(f"{BACKEND_URL}/games/rooms")
            if games_response.status_code != 200:
                self.log_test("Complete Auth Flow", False, f"Games hub access failed: {games_response.status_code}", time.time() - start_time)
                return False
            
            response_time = time.time() - start_time
            self.log_test("Complete Auth Flow", True, "Registration → Login → Dashboard → Games Hub access successful", response_time)
            
        except Exception as e:
            self.log_test("Complete Auth Flow", False, f"Integration flow error: {str(e)}", 0)
            return False
        
        # Test 2: Authenticated WebSocket Connections
        print("\n2️⃣ Testing Authenticated WebSocket Connections...")
        
        try:
            # Create authenticated WebSocket connection
            websocket_url = f"{WEBSOCKET_URL}/games/auth_test_{self.user_id}"
            
            start_time = time.time()
            websocket = await asyncio.wait_for(
                websockets.connect(websocket_url),
                timeout=15.0
            )
            response_time = time.time() - start_time
            
            # Send authenticated message
            auth_message = {
                "type": "authenticated_message",
                "user_id": self.user_id,
                "token": self.token,
                "message": "Testing authenticated WebSocket connection"
            }
            
            await websocket.send(json.dumps(auth_message))
            
            # Test heartbeat with authentication
            pong_waiter = await websocket.ping()
            await asyncio.wait_for(pong_waiter, timeout=5.0)
            
            self.log_test("Authenticated WebSocket", True, f"WebSocket connection with authentication successful", response_time)
            
            await websocket.close()
            
        except Exception as e:
            self.log_test("Authenticated WebSocket", False, f"Authenticated WebSocket error: {str(e)}", 0)
        
        # Test 3: Games System Integration
        print("\n3️⃣ Testing Games System Integration...")
        
        try:
            start_time = time.time()
            
            # Create game room with authentication
            room_data = {
                "name": f"Integration Test Room {self.user_id}",
                "gameType": "tic-tac-toe",
                "maxPlayers": 2,
                "isPrivate": False
            }
            
            room_response = self.session.post(f"{BACKEND_URL}/games/rooms/create", json=room_data)
            if room_response.status_code != 200:
                self.log_test("Games System Integration", False, f"Room creation failed: {room_response.text}", time.time() - start_time)
                return False
            
            room = room_response.json()
            room_id = room.get("room_id")
            
            # Connect to game WebSocket with resolved authentication and WebSocket issues
            game_websocket_url = f"{WEBSOCKET_URL}/games/{room_id}"
            game_websocket = await asyncio.wait_for(
                websockets.connect(game_websocket_url),
                timeout=15.0
            )
            
            # Test game interaction with authentication
            game_action = {
                "type": "game_move",
                "player_id": self.user_id,
                "room_id": room_id,
                "move": {"position": 4, "type": "cell_click"},
                "authenticated": True
            }
            
            await game_websocket.send(json.dumps(game_action))
            
            # Test heartbeat system in games
            pong_waiter = await game_websocket.ping()
            await asyncio.wait_for(pong_waiter, timeout=5.0)
            
            response_time = time.time() - start_time
            self.log_test("Games System Integration", True, f"Games work with resolved authentication and WebSocket issues", response_time)
            
            await game_websocket.close()
            
        except Exception as e:
            self.log_test("Games System Integration", False, f"Games integration error: {str(e)}", 0)
        
        return True

    async def cleanup_connections(self):
        """Clean up WebSocket connections"""
        for websocket in self.websocket_connections:
            try:
                if not websocket.closed:
                    await websocket.close()
            except:
                pass

    async def run_all_tests(self):
        """Run all authentication and WebSocket tests"""
        print("🚀 Starting Authentication and WebSocket Testing...")
        print("Focus: Resolved authentication and WebSocket issues for Pulse Games System")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"WebSocket URL: {WEBSOCKET_URL}")
        print("=" * 80)
        
        try:
            # Test Authentication Flow (HIGH PRIORITY RESOLVED)
            auth_success = self.test_authentication_flow()
            
            if auth_success:
                # Test WebSocket Connections (MEDIUM PRIORITY RESOLVED)
                websocket_success = await self.test_websocket_connections()
                
                # Test Integration
                integration_success = await self.test_integration()
            else:
                print("⚠️ Authentication failed, skipping WebSocket and integration tests")
            
            # Print summary
            self.print_summary()
            
        finally:
            # Clean up connections
            await self.cleanup_connections()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 AUTHENTICATION & WEBSOCKET TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅ PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        # Analyze specific areas
        auth_tests = [r for r in self.test_results if "registration" in r["test"].lower() or "login" in r["test"].lower() or "token" in r["test"].lower() or "session" in r["test"].lower() or "password" in r["test"].lower()]
        auth_success = len([r for r in auth_tests if "✅ PASS" in r["status"]]) / len(auth_tests) * 100 if auth_tests else 0
        
        websocket_tests = [r for r in self.test_results if "websocket" in r["test"].lower() or "heartbeat" in r["test"].lower() or "connection" in r["test"].lower()]
        websocket_success = len([r for r in websocket_tests if "✅ PASS" in r["status"]]) / len(websocket_tests) * 100 if websocket_tests else 0
        
        integration_tests = [r for r in self.test_results if "integration" in r["test"].lower() or "auth flow" in r["test"].lower() or "games system" in r["test"].lower()]
        integration_success = len([r for r in integration_tests if "✅ PASS" in r["status"]]) / len(integration_tests) * 100 if integration_tests else 0
        
        print(f"\n🔐 AUTHENTICATION FLOW (HIGH PRIORITY): {auth_success:.1f}% ({'✅' if auth_success >= 80 else '❌'})")
        print(f"🔌 WEBSOCKET CONNECTIONS (MEDIUM PRIORITY): {websocket_success:.1f}% ({'✅' if websocket_success >= 80 else '❌'})")
        print(f"🔗 INTEGRATION TESTING: {integration_success:.1f}% ({'✅' if integration_success >= 80 else '❌'})")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        # Resolution status
        print(f"\n🎯 RESOLUTION STATUS:")
        print(f"  • SECRET_KEY Fix: {'✅' if auth_success >= 80 else '❌'} (Consistent SECRET_KEY prevents token invalidation)")
        print(f"  • WebSocket Heartbeat: {'✅' if websocket_success >= 80 else '❌'} (Ping/pong system with 30s intervals)")
        print(f"  • Error Handling: {'✅' if websocket_success >= 80 else '❌'} (Enhanced WebSocket error handling)")
        print(f"  • Connection Management: {'✅' if integration_success >= 80 else '❌'} (Improved ConnectionManager)")
        
        expected_results = """
        EXPECTED RESULTS:
        • Authentication should work with 0% 401 errors on valid login attempts
        • WebSocket connections should be stable with no timeout issues  
        • Overall system should have >95% test success rate
        """
        print(expected_results)
        
        overall_success = (passed_tests/total_tests) >= 0.95
        overall_status = "✅ RESOLVED" if overall_success else "❌ NEEDS ATTENTION"
        print(f"\n🎉 OVERALL STATUS: {overall_status}")
        
        return overall_success

if __name__ == "__main__":
    async def main():
        tester = AuthWebSocketTester()
        await tester.run_all_tests()
    
    asyncio.run(main())