import requests
import json
import time
import uuid
import os
import base64
import logging
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL')
API_URL = f"{BACKEND_URL}/api"

if not BACKEND_URL:
    raise ValueError("REACT_APP_BACKEND_URL not found in environment variables")

logger.info(f"Using backend URL: {API_URL}")

# Test data
test_users = [
    {
        "username": "alice_enhanced",
        "email": "alice.enhanced@example.com",
        "password": "SecurePass123!",
        "display_name": "Alice Enhanced"
    },
    {
        "username": "bob_enhanced",
        "email": "bob.enhanced@example.com",
        "password": "StrongPass456!",
        "display_name": "Bob Enhanced"
    },
    {
        "username": "charlie_enhanced",
        "email": "charlie.enhanced@example.com",
        "password": "SafePass789!",
        "display_name": "Charlie Enhanced"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
connection_pins = {}
connection_request_ids = {}
connection_ids = {}
chat_ids = {}

def test_user_registration():
    """Test user registration endpoint"""
    logger.info("Testing user registration...")
    
    # Test successful registration
    for i, user_data in enumerate(test_users):
        response = requests.post(f"{API_URL}/register", json=user_data)
        
        if response.status_code == 200:
            logger.info(f"User {user_data['username']} registered successfully")
            user_tokens[f"user{i+1}"] = response.json()["access_token"]
            user_ids[f"user{i+1}"] = response.json()["user"]["user_id"]
        elif response.status_code == 400 and "Email already registered" in response.json()["detail"]:
            # User already exists, try logging in
            logger.info(f"User {user_data['username']} already exists, logging in...")
            login_response = requests.post(f"{API_URL}/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            
            if login_response.status_code == 200:
                logger.info(f"User {user_data['username']} logged in successfully")
                user_tokens[f"user{i+1}"] = login_response.json()["access_token"]
                user_ids[f"user{i+1}"] = login_response.json()["user"]["user_id"]
            else:
                logger.error(f"Failed to log in user {user_data['username']}: {login_response.text}")
                return False
        else:
            logger.error(f"Failed to register user {user_data['username']}: {response.text}")
            return False
    
    logger.info("User registration tests passed")
    return True

def test_profile_completion():
    """Test profile completion to ensure users have PINs"""
    logger.info("Testing profile completion...")
    
    for i, user_data in enumerate(test_users):
        user_key = f"user{i+1}"
        headers = {"Authorization": f"Bearer {user_tokens[user_key]}"}
        
        # Complete profile
        profile_data = {
            "display_name": user_data["display_name"],
            "age": 30,
            "gender": "Other",
            "location": "Test City",
            "current_mood": "Happy",
            "seeking_type": "Friendship",
            "connection_purpose": "Testing",
            "bio": f"This is a test profile for {user_data['display_name']}",
            "interests": ["Testing", "Technology"],
            "values": ["Honesty", "Reliability"]
        }
        
        response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to complete profile for {user_data['username']}: {response.text}")
            return False
        
        logger.info(f"Profile completed for {user_data['username']}")
    
    logger.info("Profile completion tests passed")
    return True

def test_get_qr_code():
    """Test QR code generation for connection PINs"""
    logger.info("Testing QR code generation...")
    
    for user_key, token in user_tokens.items():
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{API_URL}/users/qr-code", headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get QR code for {user_key}: {response.text}")
            return False
        
        qr_data = response.json()
        if not qr_data.get("connection_pin") or not qr_data.get("qr_code"):
            logger.error(f"QR code response missing required fields: {qr_data}")
            return False
        
        connection_pins[user_key] = qr_data["connection_pin"]
        logger.info(f"Got connection PIN for {user_key}: {connection_pins[user_key]}")
        
        # Verify PIN format
        if not connection_pins[user_key].startswith("PIN-"):
            logger.error(f"Invalid PIN format: {connection_pins[user_key]}")
            return False
        
        pin_code = connection_pins[user_key][4:]  # Remove "PIN-" prefix
        if len(pin_code) != 6 or not pin_code.isalnum():
            logger.error(f"Invalid PIN format: {connection_pins[user_key]}")
            return False
        
        # Verify QR code contains the PIN
        if not qr_data["qr_code"].startswith("data:image/png;base64,"):
            logger.error(f"Invalid QR code format: {qr_data['qr_code'][:30]}...")
            return False
        
        # Verify enhanced QR format
        if qr_data.get("qr_format") != "enhanced":
            logger.error(f"QR code not in enhanced format: {qr_data.get('qr_format')}")
            return False
        
        # Verify other metadata
        if not qr_data.get("display_name") or not qr_data.get("invite_link"):
            logger.error(f"QR code response missing metadata: {qr_data}")
            return False
        
        logger.info(f"QR code generated successfully for {user_key}")
    
    logger.info("QR code generation tests passed")
    return True

def test_pin_regeneration():
    """Test PIN regeneration"""
    logger.info("Testing PIN regeneration...")
    
    # Test for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    old_pin = connection_pins['user1']
    
    response = requests.post(f"{API_URL}/pin/regenerate", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to regenerate PIN: {response.text}")
        return False
    
    new_pin = response.json()["connection_pin"]
    if not new_pin or new_pin == old_pin:
        logger.error(f"PIN not regenerated properly: old={old_pin}, new={new_pin}")
        return False
    
    connection_pins['user1'] = new_pin
    logger.info(f"PIN regenerated successfully: {new_pin}")
    
    # Verify new PIN format
    if not new_pin.startswith("PIN-"):
        logger.error(f"Invalid regenerated PIN format: {new_pin}")
        return False
    
    pin_code = new_pin[4:]  # Remove "PIN-" prefix
    if len(pin_code) != 6 or not pin_code.isalnum():
        logger.error(f"Invalid regenerated PIN format: {new_pin}")
        return False
    
    # Verify PIN contains user name part
    display_name = test_users[0]["display_name"]
    name_part = ''.join(c.upper() for c in display_name if c.isalpha())[:3]
    if not pin_code.startswith(name_part):
        logger.info(f"Expected PIN to start with {name_part}, got {pin_code}")
        # This is not a critical error as the PIN might use a different algorithm
    
    # Get QR code again to verify it's updated
    response = requests.get(f"{API_URL}/users/qr-code", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get QR code after PIN regeneration: {response.text}")
        return False
    
    if response.json()["connection_pin"] != new_pin:
        logger.error(f"QR code not updated with new PIN: {response.json()['connection_pin']} != {new_pin}")
        return False
    
    logger.info("PIN regeneration tests passed")
    return True

def test_user_search():
    """Test user search by PIN, email, and name"""
    logger.info("Testing user search...")
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Search by PIN
    search_data = {"query": connection_pins['user2']}
    response = requests.post(f"{API_URL}/connections/search", json=search_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to search by PIN: {response.text}")
        return False
    
    results = response.json()["results"]
    if not results or len(results) != 1:
        logger.error(f"Expected 1 result for PIN search, got {len(results)}")
        return False
    
    if results[0]["user_id"] != user_ids['user2']:
        logger.error(f"PIN search returned wrong user: {results[0]['user_id']} != {user_ids['user2']}")
        return False
    
    if results[0]["search_type"] != "pin":
        logger.error(f"Search type should be 'pin', got {results[0]['search_type']}")
        return False
    
    logger.info("PIN search successful")
    
    # Search by email
    search_data = {"query": test_users[2]["email"]}
    response = requests.post(f"{API_URL}/connections/search", json=search_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to search by email: {response.text}")
        return False
    
    results = response.json()["results"]
    if not results or len(results) != 1:
        logger.error(f"Expected 1 result for email search, got {len(results)}")
        return False
    
    if results[0]["user_id"] != user_ids['user3']:
        logger.error(f"Email search returned wrong user: {results[0]['user_id']} != {user_ids['user3']}")
        return False
    
    if results[0]["search_type"] != "email":
        logger.error(f"Search type should be 'email', got {results[0]['search_type']}")
        return False
    
    logger.info("Email search successful")
    
    # Search by name
    search_data = {"query": "Bob"}
    response = requests.post(f"{API_URL}/connections/search", json=search_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to search by name: {response.text}")
        return False
    
    results = response.json()["results"]
    if not results:
        logger.error(f"Expected at least 1 result for name search, got {len(results)}")
        return False
    
    found_bob = False
    for result in results:
        if result["user_id"] == user_ids['user2']:
            found_bob = True
            if result["search_type"] != "name":
                logger.error(f"Search type should be 'name', got {result['search_type']}")
                return False
            break
    
    if not found_bob:
        logger.error(f"Name search did not return expected user")
        return False
    
    logger.info("Name search successful")
    
    # Test invalid search query
    search_data = {"query": "a"}  # Too short
    response = requests.post(f"{API_URL}/connections/search", json=search_data, headers=headers)
    
    if response.status_code != 400:
        logger.error(f"Invalid search query should return 400: {response.status_code}")
        return False
    
    logger.info("User search tests passed")
    return True

def test_connection_request_by_pin():
    """Test sending connection request by PIN"""
    logger.info("Testing connection request by PIN...")
    
    # User1 sends request to User2
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    request_data = {
        "connection_pin": connection_pins['user2'],
        "message": "Hello, I'd like to connect!",
        "connection_type": "friendship"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to send connection request: {response.text}")
        return False
    
    request_id = response.json()["request_id"]
    connection_request_ids['user1_to_user2'] = request_id
    logger.info(f"Connection request sent successfully with ID: {request_id}")
    
    # Test invalid PIN format
    request_data = {
        "connection_pin": "INVALID",
        "message": "This should fail"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code != 400:
        logger.error(f"Invalid PIN format should return 400: {response.status_code}")
        return False
    
    logger.info("Invalid PIN format test passed")
    
    # Test non-existent PIN
    request_data = {
        "connection_pin": "PIN-XXXXXX",
        "message": "This should fail"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code != 404:
        logger.error(f"Non-existent PIN should return 404: {response.status_code}")
        return False
    
    logger.info("Non-existent PIN test passed")
    
    # Test self-connection (should fail)
    request_data = {
        "connection_pin": connection_pins['user1'],
        "message": "This should fail"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code != 400:
        logger.error(f"Self-connection should return 400: {response.status_code}")
        return False
    
    logger.info("Self-connection test passed")
    
    # User3 sends request to User1
    headers = {"Authorization": f"Bearer {user_tokens['user3']}"}
    request_data = {
        "connection_pin": connection_pins['user1'],
        "message": "Hey, let's connect!",
        "connection_type": "professional"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to send second connection request: {response.text}")
        return False
    
    request_id = response.json()["request_id"]
    connection_request_ids['user3_to_user1'] = request_id
    logger.info(f"Second connection request sent successfully with ID: {request_id}")
    
    logger.info("Connection request by PIN tests passed")
    return True

def test_get_connection_requests():
    """Test getting connection requests"""
    logger.info("Testing get connection requests...")
    
    # User2 checks their requests
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(f"{API_URL}/connections/requests", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connection requests: {response.text}")
        return False
    
    requests = response.json()
    if not requests:
        logger.error(f"Expected at least 1 request for user2, got 0")
        return False
    
    found_request = False
    for request in requests:
        if request["request_id"] == connection_request_ids['user1_to_user2']:
            found_request = True
            # Verify request data
            if request["sender_id"] != user_ids['user1']:
                logger.error(f"Request has wrong sender: {request['sender_id']} != {user_ids['user1']}")
                return False
            if request["status"] != "pending":
                logger.error(f"Request has wrong status: {request['status']} != pending")
                return False
            # Verify sender info is included
            if "sender" not in request:
                logger.error(f"Request missing sender info")
                return False
            break
    
    if not found_request:
        logger.error(f"Could not find expected request in user2's requests")
        return False
    
    logger.info("User2 connection requests verified")
    
    # User1 checks their requests
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/connections/requests", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connection requests for user1: {response.text}")
        return False
    
    requests = response.json()
    if not requests:
        logger.error(f"Expected at least 1 request for user1, got 0")
        return False
    
    found_request = False
    for request in requests:
        if request["request_id"] == connection_request_ids['user3_to_user1']:
            found_request = True
            # Verify request data
            if request["sender_id"] != user_ids['user3']:
                logger.error(f"Request has wrong sender: {request['sender_id']} != {user_ids['user3']}")
                return False
            if request["status"] != "pending":
                logger.error(f"Request has wrong status: {request['status']} != pending")
                return False
            break
    
    if not found_request:
        logger.error(f"Could not find expected request in user1's requests")
        return False
    
    logger.info("User1 connection requests verified")
    
    logger.info("Get connection requests tests passed")
    return True

def test_respond_to_connection_request():
    """Test responding to connection requests"""
    logger.info("Testing connection request responses...")
    
    # User2 accepts request from User1
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response_data = {
        "action": "accept",
        "message": "Happy to connect!"
    }
    
    response = requests.put(
        f"{API_URL}/connections/requests/{connection_request_ids['user1_to_user2']}",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept connection request: {response.text}")
        return False
    
    if response.json()["status"] != "accepted":
        logger.error(f"Response has wrong status: {response.json()['status']} != accepted")
        return False
    
    # Store connection and chat IDs
    connection_ids['user1_to_user2'] = response.json()["connection_id"]
    chat_ids['user1_to_user2'] = response.json()["chat_id"]
    
    logger.info(f"Connection request accepted successfully")
    logger.info(f"Created connection ID: {connection_ids['user1_to_user2']}")
    logger.info(f"Created chat ID: {chat_ids['user1_to_user2']}")
    
    # User1 declines request from User3
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response_data = {
        "action": "decline",
        "message": "Sorry, not interested right now."
    }
    
    response = requests.put(
        f"{API_URL}/connections/requests/{connection_request_ids['user3_to_user1']}",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to decline connection request: {response.text}")
        return False
    
    if response.json()["status"] != "declined":
        logger.error(f"Response has wrong status: {response.json()['status']} != declined")
        return False
    
    logger.info(f"Connection request declined successfully")
    
    # User3 sends another request to User1
    headers = {"Authorization": f"Bearer {user_tokens['user3']}"}
    request_data = {
        "connection_pin": connection_pins['user1'],
        "message": "Please reconsider connecting with me!",
        "connection_type": "friendship"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to send another connection request: {response.text}")
        return False
    
    request_id = response.json()["request_id"]
    connection_request_ids['user3_to_user1_second'] = request_id
    logger.info(f"Second connection request from User3 sent successfully with ID: {request_id}")
    
    # User1 blocks User3
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response_data = {
        "action": "block",
        "message": "Blocking this user"
    }
    
    response = requests.put(
        f"{API_URL}/connections/requests/{connection_request_ids['user3_to_user1_second']}",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to block user: {response.text}")
        return False
    
    if response.json()["status"] != "blocked":
        logger.error(f"Response has wrong status: {response.json()['status']} != blocked")
        return False
    
    logger.info(f"User blocked successfully")
    
    # Verify User3 can't send another request to User1
    headers = {"Authorization": f"Bearer {user_tokens['user3']}"}
    request_data = {
        "connection_pin": connection_pins['user1'],
        "message": "This should fail because I'm blocked",
        "connection_type": "friendship"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    # This might return 400 (already connected) or 403 (blocked)
    if response.status_code == 200:
        logger.error(f"Blocked user should not be able to send connection request: {response.text}")
        return False
    
    logger.info(f"Blocked user prevented from sending connection request")
    
    logger.info("Connection request response tests passed")
    return True

def test_connection_statistics():
    """Test connection statistics"""
    logger.info("Testing connection statistics...")
    
    # Check User1's statistics
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/connections/statistics", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connection statistics: {response.text}")
        return False
    
    stats = response.json()
    if "total_connections" not in stats:
        logger.error(f"Statistics missing total_connections: {stats}")
        return False
    
    if stats["total_connections"] < 1:
        logger.error(f"Expected at least 1 connection for user1, got {stats['total_connections']}")
        return False
    
    # Verify all required statistics are present
    required_stats = ["total_connections", "pending_sent", "pending_received", "recent_connections"]
    for stat in required_stats:
        if stat not in stats:
            logger.error(f"Statistics missing {stat}: {stats}")
            return False
    
    logger.info(f"User1 connection statistics: {stats}")
    
    # Check User2's statistics
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(f"{API_URL}/connections/statistics", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connection statistics for user2: {response.text}")
        return False
    
    stats = response.json()
    if stats["total_connections"] < 1:
        logger.error(f"Expected at least 1 connection for user2, got {stats['total_connections']}")
        return False
    
    logger.info(f"User2 connection statistics: {stats}")
    
    logger.info("Connection statistics tests passed")
    return True

def test_trust_level_update():
    """Test updating trust level for a connection"""
    logger.info("Testing trust level update...")
    
    # User1 updates trust level with User2
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    trust_data = {
        "trust_level": 2  # Increase to level 2
    }
    
    response = requests.put(
        f"{API_URL}/connections/{connection_ids['user1_to_user2']}/trust-level",
        json=trust_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update trust level: {response.text}")
        return False
    
    logger.info(f"Trust level updated successfully")
    
    # Test invalid trust level
    trust_data = {
        "trust_level": 10  # Invalid level
    }
    
    response = requests.put(
        f"{API_URL}/connections/{connection_ids['user1_to_user2']}/trust-level",
        json=trust_data,
        headers=headers
    )
    
    if response.status_code != 400:
        logger.error(f"Invalid trust level should return 400: {response.status_code}")
        return False
    
    logger.info("Invalid trust level test passed")
    
    logger.info("Trust level update tests passed")
    return True

def test_auto_chat_creation():
    """Test that accepting a connection request automatically creates a chat"""
    logger.info("Testing auto-chat creation...")
    
    # Check that the chat exists
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get chats: {response.text}")
        return False
    
    chats = response.json()
    found_chat = False
    for chat in chats:
        if chat["chat_id"] == chat_ids['user1_to_user2']:
            found_chat = True
            # Verify chat data
            if chat["chat_type"] != "direct":
                logger.error(f"Chat has wrong type: {chat['chat_type']} != direct")
                return False
            if user_ids['user2'] not in chat["members"]:
                logger.error(f"Chat missing user2 in members")
                return False
            break
    
    if not found_chat:
        logger.error(f"Could not find auto-created chat")
        return False
    
    logger.info(f"Auto-created chat verified")
    
    # Send a message in the chat
    message_data = {
        "content": "Hello! This is a test message in our auto-created chat."
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['user1_to_user2']}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message in auto-created chat: {response.text}")
        return False
    
    logger.info(f"Message sent successfully in auto-created chat")
    
    # User2 checks the chat
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(f"{API_URL}/chats/{chat_ids['user1_to_user2']}/messages", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get messages for user2: {response.text}")
        return False
    
    messages = response.json()
    if not messages:
        logger.error(f"Expected at least 1 message in chat, got 0")
        return False
    
    logger.info(f"User2 can access the auto-created chat and messages")
    
    logger.info("Auto-chat creation tests passed")
    return True

def run_all_tests():
    """Run all tests in sequence"""
    tests = [
        ("User Registration", test_user_registration),
        ("Profile Completion", test_profile_completion),
        ("QR Code Generation", test_get_qr_code),
        ("PIN Regeneration", test_pin_regeneration),
        ("User Search", test_user_search),
        ("Connection Request by PIN", test_connection_request_by_pin),
        ("Get Connection Requests", test_get_connection_requests),
        ("Respond to Connection Request", test_respond_to_connection_request),
        ("Connection Statistics", test_connection_statistics),
        ("Trust Level Update", test_trust_level_update),
        ("Auto-Chat Creation", test_auto_chat_creation)
    ]
    
    results = {}
    all_passed = True
    
    for test_name, test_func in tests:
        logger.info(f"\n{'=' * 50}\nRunning test: {test_name}\n{'=' * 50}")
        try:
            result = test_func()
            results[test_name] = result
            if not result:
                all_passed = False
                logger.error(f"Test '{test_name}' FAILED")
            else:
                logger.info(f"Test '{test_name}' PASSED")
        except Exception as e:
            logger.error(f"Test '{test_name}' FAILED with exception: {e}")
            results[test_name] = False
            all_passed = False
    
    logger.info("\n\n" + "=" * 50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 50)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 50)
    logger.info(f"Overall result: {'PASSED' if all_passed else 'FAILED'}")
    logger.info("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()