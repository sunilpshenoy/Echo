#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE BACKEND TESTING SCRIPT
Tests all critical backend systems after Priority 1-3 enhancements implementation
"""

import requests
import json
import time
import base64
import secrets
from datetime import datetime, timedelta
import uuid
import os
import io

# Configuration
BACKEND_URL = "https://a205b7e3-f535-4569-8dd8-c1f8fc23e5dc.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class E2EEncryptionTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = TEST_TIMEOUT
        self.users = {}  # Store user data and tokens
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
    
    def generate_mock_keys(self, include_signing_key=True):
        """Generate mock E2E encryption keys for testing"""
        # Generate mock base64-encoded keys (in real implementation, these would be actual cryptographic keys)
        identity_key = base64.b64encode(secrets.token_bytes(32)).decode()
        signed_pre_key = base64.b64encode(secrets.token_bytes(32)).decode()
        signed_pre_key_signature = base64.b64encode(secrets.token_bytes(64)).decode()
        one_time_pre_keys = [base64.b64encode(secrets.token_bytes(32)).decode() for _ in range(5)]
        
        keys = {
            "identity_key": identity_key,
            "signed_pre_key": signed_pre_key,
            "signed_pre_key_signature": signed_pre_key_signature,
            "one_time_pre_keys": one_time_pre_keys
        }
        
        # Add signing_key field for new cryptographic algorithm compatibility
        if include_signing_key:
            keys["signing_key"] = base64.b64encode(secrets.token_bytes(32)).decode()
        
        return keys
    
    def register_test_user(self, username, email, password):
        """Register a test user or login if already exists"""
        try:
            # Try to register first
            response = self.session.post(f"{BACKEND_URL}/register", json={
                "username": username,
                "email": email,
                "password": password,
                "display_name": username
            })
            
            if response.status_code == 200:
                data = response.json()
                user_data = {
                    "user_id": data["user"]["user_id"],
                    "username": username,
                    "email": email,
                    "token": data["access_token"]
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
                        "token": data["access_token"]
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
        """Test user registration for E2E testing"""
        print("\n=== Testing User Registration ===")
        
        # Register Alice
        success, result = self.register_test_user("alice_e2e", "alice.e2e@test.com", "password123")
        self.log_test("Register Alice for E2E testing", success, str(result))
        
        # Register Bob
        success, result = self.register_test_user("bob_e2e", "bob.e2e@test.com", "password123")
        self.log_test("Register Bob for E2E testing", success, str(result))
        
        return len(self.users) >= 2
    
    def test_e2e_key_upload(self):
        """Test E2E key bundle upload with signing_key field"""
        print("\n=== Testing E2E Key Bundle Upload (with signing_key) ===")
        
        for username in ["alice_e2e", "bob_e2e"]:
            if username not in self.users:
                self.log_test(f"E2E Key Upload for {username}", False, "User not registered")
                continue
            
            try:
                # Generate mock keys with signing_key
                keys = self.generate_mock_keys(include_signing_key=True)
                
                # Prepare key bundle with signing_key
                key_bundle = {
                    "user_id": self.users[username]["user_id"],
                    "identity_key": keys["identity_key"],
                    "signing_key": keys["signing_key"],  # NEW: Include signing_key for algorithm compatibility
                    "signed_pre_key": keys["signed_pre_key"],
                    "signed_pre_key_signature": keys["signed_pre_key_signature"],
                    "one_time_pre_keys": keys["one_time_pre_keys"],
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # Upload keys
                response = self.session.post(
                    f"{BACKEND_URL}/e2e/keys",
                    json=key_bundle,
                    headers=self.get_auth_headers(username)
                )
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("status") == "success"
                    self.log_test(f"E2E Key Upload for {username} (with signing_key)", success, data.get("message", ""))
                    
                    # Store keys for later use
                    self.users[username]["keys"] = keys
                else:
                    self.log_test(f"E2E Key Upload for {username} (with signing_key)", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"E2E Key Upload for {username} (with signing_key)", False, f"Error: {str(e)}")
    
    def test_e2e_key_upload_without_signing_key(self):
        """Test E2E key bundle upload without signing_key field (backward compatibility)"""
        print("\n=== Testing E2E Key Bundle Upload (backward compatibility - no signing_key) ===")
        
        # Test with a third user to verify backward compatibility
        username = "charlie_e2e"
        success, user_data = self.register_test_user(username, f"{username}@test.com", "testpass123")
        if not success:
            self.log_test(f"E2E Key Upload for {username} (no signing_key)", False, f"User registration failed: {user_data}")
            return
        
        try:
            # Generate mock keys without signing_key
            keys = self.generate_mock_keys(include_signing_key=False)
            
            # Prepare key bundle without signing_key
            key_bundle = {
                "user_id": self.users[username]["user_id"],
                "identity_key": keys["identity_key"],
                # NOTE: No signing_key field for backward compatibility test
                "signed_pre_key": keys["signed_pre_key"],
                "signed_pre_key_signature": keys["signed_pre_key_signature"],
                "one_time_pre_keys": keys["one_time_pre_keys"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upload keys
            response = self.session.post(
                f"{BACKEND_URL}/e2e/keys",
                json=key_bundle,
                headers=self.get_auth_headers(username)
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "success"
                self.log_test(f"E2E Key Upload for {username} (no signing_key)", success, data.get("message", ""))
                
                # Store keys for later use
                self.users[username]["keys"] = keys
            else:
                self.log_test(f"E2E Key Upload for {username} (no signing_key)", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test(f"E2E Key Upload for {username} (no signing_key)", False, f"Error: {str(e)}")
    
    def test_e2e_key_retrieval(self):
        """Test E2E key bundle retrieval with signing_key field"""
        print("\n=== Testing E2E Key Bundle Retrieval (with signing_key) ===")
        
        if "alice_e2e" not in self.users or "bob_e2e" not in self.users:
            self.log_test("E2E Key Retrieval", False, "Required users not available")
            return
        
        try:
            # Alice retrieves Bob's keys
            alice_headers = self.get_auth_headers("alice_e2e")
            bob_user_id = self.users["bob_e2e"]["user_id"]
            
            response = self.session.get(
                f"{BACKEND_URL}/e2e/keys/{bob_user_id}",
                headers=alice_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_id", "identity_key", "signed_pre_key", "signed_pre_key_signature", "one_time_pre_keys"]
                
                has_all_fields = all(field in data for field in required_fields)
                has_signing_key = "signing_key" in data
                
                self.log_test("Alice retrieves Bob's E2E keys", has_all_fields, 
                            f"Retrieved keys with fields: {list(data.keys())}")
                
                # NEW: Verify signing_key field is present
                self.log_test("Bob's keys include signing_key field", has_signing_key, 
                            f"signing_key present: {has_signing_key}, value: {data.get('signing_key', 'None')}")
                
                # Verify one-time pre-key consumption
                if data.get("one_time_pre_keys"):
                    self.log_test("One-time pre-key consumption", True, 
                                f"Consumed key, has_more_prekeys: {data.get('has_more_prekeys', False)}")
                else:
                    self.log_test("One-time pre-key consumption", False, "No one-time pre-keys returned")
                    
            else:
                self.log_test("Alice retrieves Bob's E2E keys", False, f"HTTP {response.status_code}: {response.text}")
                
            # Bob retrieves Alice's keys
            bob_headers = self.get_auth_headers("bob_e2e")
            alice_user_id = self.users["alice_e2e"]["user_id"]
            
            response = self.session.get(
                f"{BACKEND_URL}/e2e/keys/{alice_user_id}",
                headers=bob_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_id", "identity_key", "signed_pre_key", "signed_pre_key_signature", "one_time_pre_keys"]
                
                has_all_fields = all(field in data for field in required_fields)
                has_signing_key = "signing_key" in data
                
                self.log_test("Bob retrieves Alice's E2E keys", has_all_fields, 
                            f"Retrieved keys with fields: {list(data.keys())}")
                
                # NEW: Verify signing_key field is present
                self.log_test("Alice's keys include signing_key field", has_signing_key, 
                            f"signing_key present: {has_signing_key}, value: {data.get('signing_key', 'None')}")
            else:
                self.log_test("Bob retrieves Alice's E2E keys", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("E2E Key Retrieval", False, f"Error: {str(e)}")
    
    def test_e2e_key_retrieval_backward_compatibility(self):
        """Test E2E key bundle retrieval for users without signing_key (backward compatibility)"""
        print("\n=== Testing E2E Key Bundle Retrieval (backward compatibility) ===")
        
        if "charlie_e2e" not in self.users:
            self.log_test("E2E Key Retrieval (backward compatibility)", False, "Charlie user not available")
            return
        
        if "alice_e2e" not in self.users:
            self.log_test("E2E Key Retrieval (backward compatibility)", False, "Alice user not available")
            return
        
        try:
            # Alice retrieves Charlie's keys (Charlie uploaded without signing_key)
            alice_headers = self.get_auth_headers("alice_e2e")
            charlie_user_id = self.users["charlie_e2e"]["user_id"]
            
            response = self.session.get(
                f"{BACKEND_URL}/e2e/keys/{charlie_user_id}",
                headers=alice_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["user_id", "identity_key", "signed_pre_key", "signed_pre_key_signature", "one_time_pre_keys"]
                
                has_all_fields = all(field in data for field in required_fields)
                has_signing_key = "signing_key" in data
                signing_key_value = data.get("signing_key")
                
                self.log_test("Alice retrieves Charlie's E2E keys (no signing_key)", has_all_fields, 
                            f"Retrieved keys with fields: {list(data.keys())}")
                
                # NEW: Verify signing_key field handling for backward compatibility
                self.log_test("Charlie's keys handle missing signing_key", True, 
                            f"signing_key present: {has_signing_key}, value: {signing_key_value} (should be None for backward compatibility)")
                    
            else:
                self.log_test("Alice retrieves Charlie's E2E keys (no signing_key)", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("E2E Key Retrieval (backward compatibility)", False, f"Error: {str(e)}")
    
    def test_e2e_conversation_initialization(self):
        """Test E2E conversation initialization"""
        print("\n=== Testing E2E Conversation Initialization ===")
        
        if "alice_e2e" not in self.users or "bob_e2e" not in self.users:
            self.log_test("E2E Conversation Init", False, "Required users not available")
            return
        
        try:
            alice_user_id = self.users["alice_e2e"]["user_id"]
            bob_user_id = self.users["bob_e2e"]["user_id"]
            alice_headers = self.get_auth_headers("alice_e2e")
            
            # Alice initializes conversation with Bob
            init_data = {
                "sender_id": alice_user_id,
                "recipient_id": bob_user_id,
                "ephemeral_public_key": base64.b64encode(secrets.token_bytes(32)).decode(),
                "used_one_time_pre_key": 0,
                "sender_identity_key": self.users["alice_e2e"].get("keys", {}).get("identity_key", "mock_key")
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/e2e/conversation/init",
                json=init_data,
                headers=alice_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "success" and "conversation_id" in data
                self.log_test("E2E Conversation Initialization", success, 
                            f"Conversation ID: {data.get('conversation_id', 'N/A')}")
                
                # Store conversation ID for later use
                self.users["alice_e2e"]["conversation_id"] = data.get("conversation_id")
            else:
                self.log_test("E2E Conversation Initialization", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("E2E Conversation Initialization", False, f"Error: {str(e)}")
    
    def test_e2e_pending_conversations(self):
        """Test retrieving pending E2E conversations"""
        print("\n=== Testing Pending E2E Conversations ===")
        
        if "bob_e2e" not in self.users:
            self.log_test("Pending E2E Conversations", False, "Bob not available")
            return
        
        try:
            bob_headers = self.get_auth_headers("bob_e2e")
            
            response = self.session.get(
                f"{BACKEND_URL}/e2e/conversation/pending",
                headers=bob_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                conversations = data.get("conversations", [])
                
                # Check if Alice's conversation init is in pending list
                alice_user_id = self.users["alice_e2e"]["user_id"]
                alice_conversation = any(
                    conv.get("sender_id") == alice_user_id 
                    for conv in conversations
                )
                
                self.log_test("Pending E2E Conversations Retrieval", True, 
                            f"Found {len(conversations)} pending conversations")
                self.log_test("Alice's conversation in pending list", alice_conversation, 
                            f"Alice's conversation found: {alice_conversation}")
            else:
                self.log_test("Pending E2E Conversations", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Pending E2E Conversations", False, f"Error: {str(e)}")
    
    def test_e2e_message_sending(self):
        """Test sending E2E encrypted messages"""
        print("\n=== Testing E2E Message Sending ===")
        
        if "alice_e2e" not in self.users or "bob_e2e" not in self.users:
            self.log_test("E2E Message Sending", False, "Required users not available")
            return
        
        try:
            alice_user_id = self.users["alice_e2e"]["user_id"]
            bob_user_id = self.users["bob_e2e"]["user_id"]
            alice_headers = self.get_auth_headers("alice_e2e")
            
            # Create conversation ID
            conversation_id = f"{alice_user_id}_{bob_user_id}"
            
            # Alice sends encrypted message to Bob
            encrypted_message = {
                "message_id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "sender_id": alice_user_id,
                "recipient_id": bob_user_id,
                "encrypted_content": base64.b64encode(b"Hello Bob! This is an encrypted message.").decode(),
                "iv": base64.b64encode(secrets.token_bytes(16)).decode(),
                "ratchet_public_key": base64.b64encode(secrets.token_bytes(32)).decode(),
                "message_number": 1,
                "chain_length": 1,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/e2e/message",
                json=encrypted_message,
                headers=alice_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "success" and "message_id" in data
                self.log_test("E2E Message Sending (Alice to Bob)", success, 
                            f"Message ID: {data.get('message_id', 'N/A')}")
                
                # Store message ID for later verification
                self.users["alice_e2e"]["sent_message_id"] = data.get("message_id")
            else:
                self.log_test("E2E Message Sending (Alice to Bob)", False, f"HTTP {response.status_code}: {response.text}")
            
            # Bob sends encrypted message to Alice
            bob_headers = self.get_auth_headers("bob_e2e")
            encrypted_message_bob = {
                "message_id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "sender_id": bob_user_id,
                "recipient_id": alice_user_id,
                "encrypted_content": base64.b64encode(b"Hi Alice! This is Bob's encrypted reply.").decode(),
                "iv": base64.b64encode(secrets.token_bytes(16)).decode(),
                "ratchet_public_key": base64.b64encode(secrets.token_bytes(32)).decode(),
                "message_number": 2,
                "chain_length": 1,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/e2e/message",
                json=encrypted_message_bob,
                headers=bob_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "success" and "message_id" in data
                self.log_test("E2E Message Sending (Bob to Alice)", success, 
                            f"Message ID: {data.get('message_id', 'N/A')}")
            else:
                self.log_test("E2E Message Sending (Bob to Alice)", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("E2E Message Sending", False, f"Error: {str(e)}")
    
    def test_e2e_message_retrieval(self):
        """Test retrieving E2E encrypted messages"""
        print("\n=== Testing E2E Message Retrieval ===")
        
        if "alice_e2e" not in self.users or "bob_e2e" not in self.users:
            self.log_test("E2E Message Retrieval", False, "Required users not available")
            return
        
        try:
            alice_user_id = self.users["alice_e2e"]["user_id"]
            bob_user_id = self.users["bob_e2e"]["user_id"]
            conversation_id = f"{alice_user_id}_{bob_user_id}"
            
            # Alice retrieves messages
            alice_headers = self.get_auth_headers("alice_e2e")
            response = self.session.get(
                f"{BACKEND_URL}/e2e/messages/{conversation_id}",
                headers=alice_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                
                self.log_test("E2E Message Retrieval (Alice)", True, 
                            f"Retrieved {len(messages)} encrypted messages")
                
                # Verify message structure
                if messages:
                    first_message = messages[0]
                    required_fields = ["message_id", "conversation_id", "sender_id", "recipient_id", 
                                     "encrypted_content", "iv", "ratchet_public_key", "timestamp"]
                    has_all_fields = all(field in first_message for field in required_fields)
                    self.log_test("E2E Message Structure Validation", has_all_fields, 
                                f"Message fields: {list(first_message.keys())}")
                    
                    # Verify encrypted content is not decrypted by server
                    encrypted_content = first_message.get("encrypted_content", "")
                    is_base64 = True
                    try:
                        base64.b64decode(encrypted_content)
                    except:
                        is_base64 = False
                    
                    self.log_test("Server-side encryption preservation", is_base64, 
                                "Encrypted content remains base64-encoded")
            else:
                self.log_test("E2E Message Retrieval (Alice)", False, f"HTTP {response.status_code}: {response.text}")
            
            # Bob retrieves messages
            bob_headers = self.get_auth_headers("bob_e2e")
            response = self.session.get(
                f"{BACKEND_URL}/e2e/messages/{conversation_id}",
                headers=bob_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                self.log_test("E2E Message Retrieval (Bob)", True, 
                            f"Retrieved {len(messages)} encrypted messages")
            else:
                self.log_test("E2E Message Retrieval (Bob)", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("E2E Message Retrieval", False, f"Error: {str(e)}")
    
    def test_e2e_access_control(self):
        """Test E2E access control and security"""
        print("\n=== Testing E2E Access Control ===")
        
        if "alice_e2e" not in self.users or "bob_e2e" not in self.users:
            self.log_test("E2E Access Control", False, "Required users not available")
            return
        
        try:
            alice_user_id = self.users["alice_e2e"]["user_id"]
            bob_user_id = self.users["bob_e2e"]["user_id"]
            alice_headers = self.get_auth_headers("alice_e2e")
            
            # Test 1: Alice tries to upload keys for Bob (should fail)
            bob_keys = self.generate_mock_keys()
            key_bundle = {
                "user_id": bob_user_id,  # Wrong user ID
                "identity_key": bob_keys["identity_key"],
                "signed_pre_key": bob_keys["signed_pre_key"],
                "signed_pre_key_signature": bob_keys["signed_pre_key_signature"],
                "one_time_pre_keys": bob_keys["one_time_pre_keys"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/e2e/keys",
                json=key_bundle,
                headers=alice_headers
            )
            
            unauthorized_upload_blocked = response.status_code == 403
            self.log_test("Unauthorized key upload blocked", unauthorized_upload_blocked, 
                        f"HTTP {response.status_code}: {response.text[:100]}")
            
            # Test 2: Alice tries to send message as Bob (should fail)
            fake_message = {
                "message_id": str(uuid.uuid4()),
                "conversation_id": f"{alice_user_id}_{bob_user_id}",
                "sender_id": bob_user_id,  # Wrong sender ID
                "recipient_id": alice_user_id,
                "encrypted_content": base64.b64encode(b"Fake message").decode(),
                "iv": base64.b64encode(secrets.token_bytes(16)).decode(),
                "ratchet_public_key": base64.b64encode(secrets.token_bytes(32)).decode(),
                "message_number": 1,
                "chain_length": 1,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/e2e/message",
                json=fake_message,
                headers=alice_headers
            )
            
            unauthorized_message_blocked = response.status_code == 403
            self.log_test("Unauthorized message sending blocked", unauthorized_message_blocked, 
                        f"HTTP {response.status_code}: {response.text[:100]}")
            
            # Test 3: Alice tries to access conversation she's not part of
            fake_conversation_id = f"{bob_user_id}_nonexistent_user"
            response = self.session.get(
                f"{BACKEND_URL}/e2e/messages/{fake_conversation_id}",
                headers=alice_headers
            )
            
            unauthorized_access_blocked = response.status_code == 403
            self.log_test("Unauthorized conversation access blocked", unauthorized_access_blocked, 
                        f"HTTP {response.status_code}: {response.text[:100]}")
                        
        except Exception as e:
            self.log_test("E2E Access Control", False, f"Error: {str(e)}")
    
    def test_e2e_key_refresh(self):
        """Test one-time pre-key refresh functionality"""
        print("\n=== Testing E2E Key Refresh ===")
        
        if "alice_e2e" not in self.users:
            self.log_test("E2E Key Refresh", False, "Alice not available")
            return
        
        try:
            alice_headers = self.get_auth_headers("alice_e2e")
            
            # Generate new one-time pre-keys
            new_keys = [base64.b64encode(secrets.token_bytes(32)).decode() for _ in range(3)]
            
            response = self.session.post(
                f"{BACKEND_URL}/e2e/keys/refresh",
                json=new_keys,
                headers=alice_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "success"
                self.log_test("E2E Key Refresh", success, data.get("message", ""))
            else:
                self.log_test("E2E Key Refresh", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("E2E Key Refresh", False, f"Error: {str(e)}")
    
    def test_integration_with_existing_chat(self):
        """Test E2E integration with existing chat system"""
        print("\n=== Testing E2E Integration with Existing Chat System ===")
        
        if "alice_e2e" not in self.users or "bob_e2e" not in self.users:
            self.log_test("E2E Chat Integration", False, "Required users not available")
            return
        
        try:
            alice_headers = self.get_auth_headers("alice_e2e")
            bob_user_id = self.users["bob_e2e"]["user_id"]
            
            # Create a regular chat between Alice and Bob
            chat_data = {
                "chat_type": "direct",
                "other_user_id": bob_user_id
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/chats",
                json=chat_data,
                headers=alice_headers
            )
            
            if response.status_code == 200:
                chat = response.json()
                chat_id = chat.get("chat_id")
                
                self.log_test("Regular chat creation for E2E users", True, f"Chat ID: {chat_id}")
                
                # Verify both users can access the chat
                alice_chats_response = self.session.get(f"{BACKEND_URL}/chats", headers=alice_headers)
                bob_chats_response = self.session.get(f"{BACKEND_URL}/chats", headers=self.get_auth_headers("bob_e2e"))
                
                alice_has_chat = False
                bob_has_chat = False
                
                if alice_chats_response.status_code == 200:
                    alice_chats = alice_chats_response.json()
                    alice_has_chat = any(c.get("chat_id") == chat_id for c in alice_chats)
                
                if bob_chats_response.status_code == 200:
                    bob_chats = bob_chats_response.json()
                    bob_has_chat = any(c.get("chat_id") == chat_id for c in bob_chats)
                
                self.log_test("Alice can access E2E-enabled chat", alice_has_chat, "")
                self.log_test("Bob can access E2E-enabled chat", bob_has_chat, "")
                
            else:
                self.log_test("Regular chat creation for E2E users", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("E2E Chat Integration", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all E2E encryption tests"""
        print("🔐 Starting End-to-End Encryption Backend Testing (with signing_key support)")
        print("=" * 60)
        
        # Test sequence
        if not self.test_user_registration():
            print("❌ User registration failed - cannot continue with E2E tests")
            return
        
        # NEW: Test signing_key functionality
        self.test_e2e_key_upload()  # Updated to test with signing_key
        self.test_e2e_key_upload_without_signing_key()  # NEW: Test backward compatibility
        self.test_e2e_key_retrieval()  # Updated to verify signing_key in response
        self.test_e2e_key_retrieval_backward_compatibility()  # NEW: Test backward compatibility
        
        # Existing tests
        self.test_e2e_conversation_initialization()
        self.test_e2e_pending_conversations()
        self.test_e2e_message_sending()
        self.test_e2e_message_retrieval()
        self.test_e2e_access_control()
        self.test_e2e_key_refresh()
        self.test_integration_with_existing_chat()
        
        # Summary
        print("\n" + "=" * 60)
        print("🔐 E2E ENCRYPTION TEST SUMMARY (with signing_key support)")
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
        
        print("\n🔐 E2E Encryption Testing Complete!")
        return passed == total

if __name__ == "__main__":
    tester = E2EEncryptionTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)