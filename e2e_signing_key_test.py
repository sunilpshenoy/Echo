#!/usr/bin/env python3
"""
E2E Encryption Signing Key Backend Testing Script
Tests the updated key bundle format with signing_key field support
"""

import requests
import json
import time
import base64
import secrets
from datetime import datetime, timedelta
import uuid

# Configuration
BACKEND_URL = "https://a205b7e3-f535-4569-8dd8-c1f8fc23e5dc.preview.emergentagent.com/api"
TEST_TIMEOUT = 30

class E2ESigningKeyTester:
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
    
    def generate_mock_keys_with_signing(self):
        """Generate mock E2E encryption keys including signing_key for testing"""
        # Generate mock base64-encoded keys (in real implementation, these would be actual cryptographic keys)
        identity_key = base64.b64encode(secrets.token_bytes(32)).decode()
        signing_key = base64.b64encode(secrets.token_bytes(32)).decode()  # NEW FIELD
        signed_pre_key = base64.b64encode(secrets.token_bytes(32)).decode()
        signed_pre_key_signature = base64.b64encode(secrets.token_bytes(64)).decode()
        one_time_pre_keys = [base64.b64encode(secrets.token_bytes(32)).decode() for _ in range(5)]
        
        return {
            "identity_key": identity_key,
            "signing_key": signing_key,  # NEW FIELD
            "signed_pre_key": signed_pre_key,
            "signed_pre_key_signature": signed_pre_key_signature,
            "one_time_pre_keys": one_time_pre_keys
        }
    
    def generate_mock_keys_legacy(self):
        """Generate mock E2E encryption keys without signing_key for backward compatibility testing"""
        identity_key = base64.b64encode(secrets.token_bytes(32)).decode()
        signed_pre_key = base64.b64encode(secrets.token_bytes(32)).decode()
        signed_pre_key_signature = base64.b64encode(secrets.token_bytes(64)).decode()
        one_time_pre_keys = [base64.b64encode(secrets.token_bytes(32)).decode() for _ in range(5)]
        
        return {
            "identity_key": identity_key,
            "signed_pre_key": signed_pre_key,
            "signed_pre_key_signature": signed_pre_key_signature,
            "one_time_pre_keys": one_time_pre_keys
        }
    
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
        """Test user registration for E2E signing key testing"""
        print("\n=== Testing User Registration ===")
        
        # Register Alice
        success, result = self.register_test_user("alice_signing", "alice.signing@test.com", "password123")
        self.log_test("Register Alice for signing key testing", success, str(result))
        
        # Register Bob
        success, result = self.register_test_user("bob_signing", "bob.signing@test.com", "password123")
        self.log_test("Register Bob for signing key testing", success, str(result))
        
        # Register Charlie (for legacy testing)
        success, result = self.register_test_user("charlie_legacy", "charlie.legacy@test.com", "password123")
        self.log_test("Register Charlie for legacy testing", success, str(result))
        
        return len(self.users) >= 3
    
    def test_key_bundle_with_signing_key(self):
        """Test uploading key bundle with new signing_key field"""
        print("\n=== Testing Key Bundle Upload with Signing Key ===")
        
        if "alice_signing" not in self.users:
            self.log_test("Key Bundle with Signing Key", False, "Alice not registered")
            return
        
        try:
            # Generate keys with signing_key
            keys = self.generate_mock_keys_with_signing()
            
            # Prepare key bundle with signing_key
            key_bundle = {
                "user_id": self.users["alice_signing"]["user_id"],
                "identity_key": keys["identity_key"],
                "signing_key": keys["signing_key"],  # NEW FIELD
                "signed_pre_key": keys["signed_pre_key"],
                "signed_pre_key_signature": keys["signed_pre_key_signature"],
                "one_time_pre_keys": keys["one_time_pre_keys"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upload keys
            response = self.session.post(
                f"{BACKEND_URL}/e2e/keys",  # Use correct endpoint
                json=key_bundle,
                headers=self.get_auth_headers("alice_signing")
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "success"
                self.log_test("Upload key bundle with signing_key", success, 
                            f"Response: {data.get('message', '')}")
                
                # Store keys for later use
                self.users["alice_signing"]["keys"] = keys
                return True
            elif response.status_code == 422:
                # Validation error - signing_key field not supported yet
                self.log_test("Upload key bundle with signing_key", False, 
                            f"Validation error (signing_key not supported): {response.text}")
                return False
            else:
                self.log_test("Upload key bundle with signing_key", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Upload key bundle with signing_key", False, f"Error: {str(e)}")
            return False
    
    def test_key_bundle_backward_compatibility(self):
        """Test uploading key bundle without signing_key (backward compatibility)"""
        print("\n=== Testing Backward Compatibility (No Signing Key) ===")
        
        if "charlie_legacy" not in self.users:
            self.log_test("Backward Compatibility Test", False, "Charlie not registered")
            return
        
        try:
            # Generate keys without signing_key
            keys = self.generate_mock_keys_legacy()
            
            # Prepare key bundle without signing_key
            key_bundle = {
                "user_id": self.users["charlie_legacy"]["user_id"],
                "identity_key": keys["identity_key"],
                # NO signing_key field
                "signed_pre_key": keys["signed_pre_key"],
                "signed_pre_key_signature": keys["signed_pre_key_signature"],
                "one_time_pre_keys": keys["one_time_pre_keys"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upload keys
            response = self.session.post(
                f"{BACKEND_URL}/e2e/keys",  # Use correct endpoint
                json=key_bundle,
                headers=self.get_auth_headers("charlie_legacy")
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "success"
                self.log_test("Upload legacy key bundle (no signing_key)", success, 
                            f"Response: {data.get('message', '')}")
                
                # Store keys for later use
                self.users["charlie_legacy"]["keys"] = keys
                return True
            else:
                self.log_test("Upload legacy key bundle (no signing_key)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Upload legacy key bundle (no signing_key)", False, f"Error: {str(e)}")
            return False
    
    def test_key_bundle_retrieval_with_signing_key(self):
        """Test retrieving key bundle that includes signing_key"""
        print("\n=== Testing Key Bundle Retrieval with Signing Key ===")
        
        if "alice_signing" not in self.users or "bob_signing" not in self.users:
            self.log_test("Key Bundle Retrieval with Signing Key", False, "Required users not available")
            return
        
        try:
            # Bob retrieves Alice's keys (which should include signing_key)
            bob_headers = self.get_auth_headers("bob_signing")
            alice_user_id = self.users["alice_signing"]["user_id"]
            
            response = self.session.get(
                f"{BACKEND_URL}/e2e/keys/{alice_user_id}",  # Use correct endpoint
                headers=bob_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required fields including signing_key
                required_fields = ["user_id", "identity_key", "signed_pre_key", 
                                 "signed_pre_key_signature", "one_time_pre_keys"]
                optional_fields = ["signing_key"]  # This should be present if backend supports it
                
                has_required_fields = all(field in data for field in required_fields)
                has_signing_key = "signing_key" in data
                
                self.log_test("Retrieved key bundle has required fields", has_required_fields, 
                            f"Fields present: {list(data.keys())}")
                
                self.log_test("Retrieved key bundle includes signing_key", has_signing_key, 
                            f"signing_key present: {has_signing_key}")
                
                if has_signing_key:
                    # Verify signing_key is a valid base64 string
                    try:
                        signing_key_bytes = base64.b64decode(data["signing_key"])
                        valid_signing_key = len(signing_key_bytes) > 0
                        self.log_test("Signing key is valid base64", valid_signing_key, 
                                    f"Signing key length: {len(signing_key_bytes)} bytes")
                    except Exception as e:
                        self.log_test("Signing key is valid base64", False, f"Error: {str(e)}")
                
                return has_required_fields and has_signing_key
            else:
                self.log_test("Key Bundle Retrieval with Signing Key", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Key Bundle Retrieval with Signing Key", False, f"Error: {str(e)}")
            return False
    
    def test_key_bundle_retrieval_legacy(self):
        """Test retrieving legacy key bundle (without signing_key)"""
        print("\n=== Testing Legacy Key Bundle Retrieval ===")
        
        if "charlie_legacy" not in self.users or "bob_signing" not in self.users:
            self.log_test("Legacy Key Bundle Retrieval", False, "Required users not available")
            return
        
        try:
            # Bob retrieves Charlie's keys (which should not have signing_key)
            bob_headers = self.get_auth_headers("bob_signing")
            charlie_user_id = self.users["charlie_legacy"]["user_id"]
            
            response = self.session.get(
                f"{BACKEND_URL}/e2e/keys/{charlie_user_id}",  # Use correct endpoint
                headers=bob_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for required fields
                required_fields = ["user_id", "identity_key", "signed_pre_key", 
                                 "signed_pre_key_signature", "one_time_pre_keys"]
                
                has_required_fields = all(field in data for field in required_fields)
                has_signing_key = "signing_key" in data
                
                self.log_test("Legacy key bundle has required fields", has_required_fields, 
                            f"Fields present: {list(data.keys())}")
                
                # For legacy bundles, signing_key should either be missing or null
                if has_signing_key:
                    signing_key_value = data["signing_key"]
                    is_null_or_empty = signing_key_value is None or signing_key_value == ""
                    self.log_test("Legacy bundle signing_key handling", is_null_or_empty, 
                                f"signing_key value: {signing_key_value}")
                else:
                    self.log_test("Legacy bundle signing_key handling", True, 
                                "signing_key field not present (expected for legacy)")
                
                return has_required_fields
            else:
                self.log_test("Legacy Key Bundle Retrieval", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Legacy Key Bundle Retrieval", False, f"Error: {str(e)}")
            return False
    
    def test_database_storage_verification(self):
        """Test that signing_key is properly stored in database"""
        print("\n=== Testing Database Storage Verification ===")
        
        # This test verifies that when we upload a key bundle with signing_key,
        # and then retrieve it, the signing_key is preserved
        
        if "bob_signing" not in self.users:
            self.log_test("Database Storage Verification", False, "Bob not registered")
            return
        
        try:
            # Generate unique keys for Bob
            keys = self.generate_mock_keys_with_signing()
            original_signing_key = keys["signing_key"]
            
            # Upload Bob's keys with signing_key
            key_bundle = {
                "user_id": self.users["bob_signing"]["user_id"],
                "identity_key": keys["identity_key"],
                "signing_key": keys["signing_key"],
                "signed_pre_key": keys["signed_pre_key"],
                "signed_pre_key_signature": keys["signed_pre_key_signature"],
                "one_time_pre_keys": keys["one_time_pre_keys"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Upload keys
            upload_response = self.session.post(
                f"{BACKEND_URL}/e2e/keys",  # Use correct endpoint
                json=key_bundle,
                headers=self.get_auth_headers("bob_signing")
            )
            
            if upload_response.status_code != 200:
                self.log_test("Database Storage - Upload", False, 
                            f"Upload failed: {upload_response.status_code}")
                return False
            
            # Wait a moment for database consistency
            time.sleep(1)
            
            # Retrieve Bob's keys using Alice's account
            alice_headers = self.get_auth_headers("alice_signing")
            bob_user_id = self.users["bob_signing"]["user_id"]
            
            retrieve_response = self.session.get(
                f"{BACKEND_URL}/e2e/key-bundle/{bob_user_id}",
                headers=alice_headers
            )
            
            # Check if endpoint exists (might be /e2e/keys instead)
            if retrieve_response.status_code == 404:
                retrieve_response = self.session.get(
                    f"{BACKEND_URL}/e2e/keys/{bob_user_id}",
                    headers=alice_headers
                )
            
            if retrieve_response.status_code == 200:
                retrieved_data = retrieve_response.json()
                retrieved_signing_key = retrieved_data.get("signing_key")
                
                # Verify the signing_key matches what we uploaded
                keys_match = retrieved_signing_key == original_signing_key
                
                self.log_test("Database Storage - Signing Key Persistence", keys_match, 
                            f"Original: {original_signing_key[:20]}..., Retrieved: {str(retrieved_signing_key)[:20]}...")
                
                return keys_match
            else:
                self.log_test("Database Storage - Retrieval", False, 
                            f"Retrieval failed: {retrieve_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Database Storage Verification", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all signing key tests"""
        print("🔐 Starting E2E Encryption Signing Key Backend Testing")
        print("=" * 70)
        
        # Test sequence
        if not self.test_user_registration():
            print("❌ User registration failed - cannot continue with signing key tests")
            return False
        
        # Test the new signing_key functionality
        signing_key_upload_success = self.test_key_bundle_with_signing_key()
        
        # Test backward compatibility
        legacy_upload_success = self.test_key_bundle_backward_compatibility()
        
        # Test retrieval with signing_key
        if signing_key_upload_success:
            self.test_key_bundle_retrieval_with_signing_key()
        
        # Test legacy retrieval
        if legacy_upload_success:
            self.test_key_bundle_retrieval_legacy()
        
        # Test database storage
        if signing_key_upload_success:
            self.test_database_storage_verification()
        
        # Summary
        print("\n" + "=" * 70)
        print("🔐 E2E SIGNING KEY TEST SUMMARY")
        print("=" * 70)
        
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
        
        print("\n🔐 E2E Signing Key Testing Complete!")
        return passed == total

if __name__ == "__main__":
    tester = E2ESigningKeyTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)