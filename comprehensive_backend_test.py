import requests
import json
import time
import uuid
import os
import base64
import logging
from io import BytesIO
from datetime import datetime, timedelta
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from frontend/.env
from dotenv import load_dotenv
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL')
API_URL = f"{BACKEND_URL}/api"

if not BACKEND_URL:
    raise ValueError("REACT_APP_BACKEND_URL not found in environment variables")

logger.info(f"Using backend URL: {API_URL}")

# Test data - create unique users for this test run
timestamp = int(time.time())
test_users = [
    {
        "username": f"alice_smith_{timestamp}",
        "email": f"alice.smith_{timestamp}@example.com",
        "password": "SecurePass123!",
        "phone": f"+1234567{timestamp}"
    },
    {
        "username": f"bob_johnson_{timestamp}",
        "email": f"bob.johnson_{timestamp}@example.com",
        "password": "StrongPass456!",
        "phone": f"+1987654{timestamp}"
    },
    {
        "username": f"charlie_davis_{timestamp}",
        "email": f"charlie.davis_{timestamp}@example.com",
        "password": "SafePass789!",
        "phone": f"+1122334{timestamp}"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
user_pins = {}
connection_requests = {}
connections = {}
chat_ids = {}
message_ids = {}

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
        else:
            logger.error(f"Failed to register user {user_data['username']}: {response.text}")
            return False
    
    # Test duplicate registration (should fail)
    response = requests.post(f"{API_URL}/register", json=test_users[0])
    if response.status_code != 400 or "Email already registered" not in response.json()["detail"]:
        logger.error("Duplicate registration test failed")
        return False
    
    logger.info("User registration tests passed")
    return True

def test_user_login():
    """Test user login endpoint"""
    logger.info("Testing user login...")
    
    # Test successful login
    for i, user_data in enumerate(test_users):
        response = requests.post(f"{API_URL}/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        if response.status_code != 200:
            logger.error(f"Failed to log in user {user_data['username']}: {response.text}")
            return False
        
        logger.info(f"User {user_data['username']} logged in successfully")
        user_tokens[f"user{i+1}"] = response.json()["access_token"]
        user_ids[f"user{i+1}"] = response.json()["user"]["user_id"]
        
        # Verify profile_completed status is returned
        if "profile_completed" not in response.json()["user"]:
            logger.error(f"Login response missing profile_completed status")
            return False
    
    # Test invalid credentials
    response = requests.post(f"{API_URL}/login", json={
        "email": "nonexistent@example.com",
        "password": "WrongPassword123"
    })
    
    if response.status_code != 401:
        logger.error("Invalid credentials test failed")
        return False
    
    logger.info("User login tests passed")
    return True

def test_get_current_user():
    """Test GET /api/users/me endpoint"""
    logger.info("Testing GET /api/users/me endpoint...")
    
    # Test with valid token
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get current user: {response.text}")
        return False
    
    user_data = response.json()
    required_fields = ["user_id", "username", "email", "profile_completed"]
    for field in required_fields:
        if field not in user_data:
            logger.error(f"User data missing required field: {field}")
            return False
    
    logger.info("Current user data retrieved successfully")
    
    # Test with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 401:
        logger.error("Invalid token test failed")
        return False
    
    logger.info("GET /api/users/me tests passed")
    return True

def test_profile_completion():
    """Test PUT /api/profile/complete endpoint"""
    logger.info("Testing PUT /api/profile/complete endpoint...")
    
    # Complete profile for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    profile_data = {
        "display_name": f"Alice Smith {timestamp}",
        "age": 28,
        "gender": "female",
        "location": "New York, NY",
        "current_mood": "Excited",
        "mood_reason": "Testing this awesome app",
        "seeking_type": "Friendship",
        "seeking_age_range": "25-35",
        "seeking_gender": "Any",
        "seeking_location_preference": "Nearby",
        "connection_purpose": "Networking",
        "additional_requirements": "Tech enthusiasts preferred",
        "bio": "Software engineer who loves hiking and photography",
        "interests": ["technology", "hiking", "photography", "travel"],
        "values": ["honesty", "creativity", "growth"]
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to complete profile: {response.text}")
        return False
    
    # Verify profile was completed
    completed_profile = response.json()
    if not completed_profile.get("profile_completed"):
        logger.error("Profile not marked as completed")
        return False
    
    # Verify connection PIN was generated
    if "connection_pin" not in completed_profile:
        logger.error("Connection PIN not generated")
        return False
    
    user_pins["user1"] = completed_profile["connection_pin"]
    logger.info(f"User1 connection PIN: {user_pins['user1']}")
    
    # Verify authenticity rating was calculated
    if "authenticity_rating" not in completed_profile:
        logger.error("Authenticity rating not calculated")
        return False
    
    logger.info(f"User1 authenticity rating: {completed_profile['authenticity_rating']}")
    
    # Complete profile for user2
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    profile_data = {
        "display_name": f"Bob Johnson {timestamp}",
        "age": 32,
        "gender": "male",
        "location": "San Francisco, CA",
        "current_mood": "Curious",
        "mood_reason": "Exploring new connections",
        "seeking_type": "Professional",
        "seeking_age_range": "25-40",
        "seeking_gender": "Any",
        "seeking_location_preference": "Any",
        "connection_purpose": "Career growth",
        "additional_requirements": "Tech industry professionals",
        "bio": "Product manager with a passion for AI and machine learning",
        "interests": ["artificial intelligence", "product management", "startups", "hiking"],
        "values": ["innovation", "integrity", "teamwork"]
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to complete profile for user2: {response.text}")
        return False
    
    user_pins["user2"] = response.json()["connection_pin"]
    logger.info(f"User2 connection PIN: {user_pins['user2']}")
    
    # Complete profile for user3
    headers = {"Authorization": f"Bearer {user_tokens['user3']}"}
    profile_data = {
        "display_name": f"Charlie Davis {timestamp}",
        "age": 30,
        "gender": "non-binary",
        "location": "Austin, TX",
        "current_mood": "Relaxed",
        "mood_reason": "Just chilling",
        "seeking_type": "Friendship",
        "seeking_age_range": "25-35",
        "seeking_gender": "Any",
        "seeking_location_preference": "Any",
        "connection_purpose": "Social",
        "additional_requirements": "Music lovers",
        "bio": "Music producer and DJ who loves to travel",
        "interests": ["music", "travel", "food", "art"],
        "values": ["creativity", "freedom", "authenticity"]
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to complete profile for user3: {response.text}")
        return False
    
    user_pins["user3"] = response.json()["connection_pin"]
    logger.info(f"User3 connection PIN: {user_pins['user3']}")
    
    logger.info("PUT /api/profile/complete tests passed")
    return True

def test_get_qr_code():
    """Test GET /api/users/qr-code endpoint"""
    logger.info("Testing GET /api/users/qr-code endpoint...")
    
    # Get QR code for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/users/qr-code", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get QR code: {response.text}")
        return False
    
    qr_data = response.json()
    if "qr_code" not in qr_data or "connection_pin" not in qr_data:
        logger.error(f"QR code response missing required fields: {qr_data}")
        return False
    
    # Verify the connection PIN matches
    if qr_data["connection_pin"] != user_pins["user1"]:
        logger.error(f"QR code PIN doesn't match user's PIN: {qr_data['connection_pin']} vs {user_pins['user1']}")
        return False
    
    logger.info("GET /api/users/qr-code tests passed")
    return True

def test_connection_request_by_pin():
    """Test POST /api/connections/request-by-pin endpoint"""
    logger.info("Testing POST /api/connections/request-by-pin endpoint...")
    
    # User2 requests connection with User1 using PIN
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    request_data = {
        "pin": user_pins["user1"],
        "message": "Hi Alice, I'd like to connect!"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to request connection by PIN: {response.text}")
        return False
    
    connection_request = response.json()
    if "request_id" not in connection_request or "status" not in connection_request:
        logger.error(f"Connection request response missing required fields: {connection_request}")
        return False
    
    if connection_request["status"] != "pending":
        logger.error(f"Connection request has incorrect status: {connection_request['status']}")
        return False
    
    connection_requests["user2_to_user1"] = connection_request["request_id"]
    logger.info(f"Connection request created with ID: {connection_requests['user2_to_user1']}")
    
    # User3 requests connection with User1 using PIN
    headers = {"Authorization": f"Bearer {user_tokens['user3']}"}
    request_data = {
        "pin": user_pins["user1"],
        "message": "Hey Alice, let's connect!"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to request connection by PIN for user3: {response.text}")
        return False
    
    connection_requests["user3_to_user1"] = response.json()["request_id"]
    logger.info(f"Connection request created with ID: {connection_requests['user3_to_user1']}")
    
    # Test with invalid PIN
    request_data = {
        "pin": "INVALID-PIN",
        "message": "This should fail"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code != 404:
        logger.error(f"Invalid PIN test failed: {response.status_code} - {response.text}")
        return False
    
    logger.info("POST /api/connections/request-by-pin tests passed")
    return True

def test_get_connection_requests():
    """Test GET /api/connections/requests endpoint"""
    logger.info("Testing GET /api/connections/requests endpoint...")
    
    # User1 gets their connection requests
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/connections/requests", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connection requests: {response.text}")
        return False
    
    requests_list = response.json()
    if len(requests_list) < 2:  # Should have at least 2 requests
        logger.error(f"Expected at least 2 connection requests, got {len(requests_list)}")
        return False
    
    # Verify request details
    for request in requests_list:
        if "request_id" not in request or "status" not in request or "requester_id" not in request:
            logger.error(f"Connection request missing required fields: {request}")
            return False
        
        if request["status"] != "pending":
            logger.error(f"Connection request has incorrect status: {request['status']}")
            return False
    
    logger.info(f"User1 has {len(requests_list)} connection requests")
    
    # Test filtering by status
    response = requests.get(f"{API_URL}/connections/requests?status=pending", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get filtered connection requests: {response.text}")
        return False
    
    pending_requests = response.json()
    if len(pending_requests) < 2:
        logger.error(f"Expected at least 2 pending requests, got {len(pending_requests)}")
        return False
    
    logger.info("GET /api/connections/requests tests passed")
    return True

def test_respond_to_connection_request():
    """Test PUT /api/connections/requests/{id} endpoint"""
    logger.info("Testing PUT /api/connections/requests/{id} endpoint...")
    
    # User1 accepts connection request from User2
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response_data = {
        "action": "accept"
    }
    
    response = requests.put(
        f"{API_URL}/connections/requests/{connection_requests['user2_to_user1']}",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept connection request: {response.text}")
        return False
    
    connection_data = response.json()
    if "connection_id" not in connection_data or "status" not in connection_data:
        logger.error(f"Connection response missing required fields: {connection_data}")
        return False
    
    if connection_data["status"] != "connected":
        logger.error(f"Connection has incorrect status: {connection_data['status']}")
        return False
    
    connections["user1_user2"] = connection_data["connection_id"]
    logger.info(f"Connection created with ID: {connections['user1_user2']}")
    
    # User1 declines connection request from User3
    response_data = {
        "action": "decline"
    }
    
    response = requests.put(
        f"{API_URL}/connections/requests/{connection_requests['user3_to_user1']}",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to decline connection request: {response.text}")
        return False
    
    declined_data = response.json()
    if declined_data["status"] != "declined":
        logger.error(f"Declined connection has incorrect status: {declined_data['status']}")
        return False
    
    logger.info("Connection request declined successfully")
    
    # Test with invalid action
    response_data = {
        "action": "invalid_action"
    }
    
    response = requests.put(
        f"{API_URL}/connections/requests/{connection_requests['user2_to_user1']}",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 400:
        logger.error(f"Invalid action test failed: {response.status_code} - {response.text}")
        return False
    
    logger.info("PUT /api/connections/requests/{id} tests passed")
    return True

def test_get_connections():
    """Test GET /api/connections endpoint"""
    logger.info("Testing GET /api/connections endpoint...")
    
    # User1 gets their connections
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/connections", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connections: {response.text}")
        return False
    
    connections_list = response.json()
    if len(connections_list) < 1:  # Should have at least 1 connection
        logger.error(f"Expected at least 1 connection, got {len(connections_list)}")
        return False
    
    # Verify connection details
    for connection in connections_list:
        if "connection_id" not in connection or "status" not in connection or "trust_level" not in connection:
            logger.error(f"Connection missing required fields: {connection}")
            return False
        
        if connection["status"] != "connected":
            logger.error(f"Connection has incorrect status: {connection['status']}")
            return False
    
    logger.info(f"User1 has {len(connections_list)} connections")
    
    # User2 gets their connections
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(f"{API_URL}/connections", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connections for user2: {response.text}")
        return False
    
    connections_list = response.json()
    if len(connections_list) < 1:
        logger.error(f"Expected at least 1 connection for user2, got {len(connections_list)}")
        return False
    
    logger.info("GET /api/connections tests passed")
    return True

def test_update_trust_level():
    """Test PUT /api/connections/{id}/trust-level endpoint"""
    logger.info("Testing PUT /api/connections/{id}/trust-level endpoint...")
    
    # User1 updates trust level with User2
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    trust_data = {
        "trust_level": 2  # Text Chat level
    }
    
    response = requests.put(
        f"{API_URL}/connections/{connections['user1_user2']}/trust-level",
        json=trust_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update trust level: {response.text}")
        return False
    
    updated_connection = response.json()
    if updated_connection["trust_level"] != 2:
        logger.error(f"Trust level not updated correctly: {updated_connection['trust_level']}")
        return False
    
    logger.info(f"Trust level updated to {updated_connection['trust_level']}")
    
    # Test with invalid trust level
    trust_data = {
        "trust_level": 10  # Invalid level
    }
    
    response = requests.put(
        f"{API_URL}/connections/{connections['user1_user2']}/trust-level",
        json=trust_data,
        headers=headers
    )
    
    if response.status_code != 400:
        logger.error(f"Invalid trust level test failed: {response.status_code} - {response.text}")
        return False
    
    # Update to higher level
    trust_data = {
        "trust_level": 3  # Voice Call level
    }
    
    response = requests.put(
        f"{API_URL}/connections/{connections['user1_user2']}/trust-level",
        json=trust_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update to higher trust level: {response.text}")
        return False
    
    updated_connection = response.json()
    if updated_connection["trust_level"] != 3:
        logger.error(f"Higher trust level not updated correctly: {updated_connection['trust_level']}")
        return False
    
    logger.info(f"Trust level updated to {updated_connection['trust_level']}")
    
    logger.info("PUT /api/connections/{id}/trust-level tests passed")
    return True

def test_get_chats():
    """Test GET /api/chats endpoint"""
    logger.info("Testing GET /api/chats endpoint...")
    
    # User1 gets their chats
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get chats: {response.text}")
        return False
    
    chats = response.json()
    if len(chats) < 1:  # Should have at least 1 chat (created when connection was accepted)
        logger.error(f"Expected at least 1 chat, got {len(chats)}")
        return False
    
    # Store the chat ID for later use
    for chat in chats:
        if "chat_type" in chat and chat["chat_type"] == "direct":
            # Find the chat with user2
            other_members = [m for m in chat["members"] if m != user_ids["user1"]]
            if other_members and other_members[0] == user_ids["user2"]:
                chat_ids["user1_user2"] = chat["chat_id"]
                logger.info(f"Found chat between user1 and user2 with ID: {chat_ids['user1_user2']}")
                break
    
    if "user1_user2" not in chat_ids:
        logger.error("Could not find chat between user1 and user2")
        return False
    
    # User2 gets their chats
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get chats for user2: {response.text}")
        return False
    
    chats = response.json()
    if len(chats) < 1:
        logger.error(f"Expected at least 1 chat for user2, got {len(chats)}")
        return False
    
    logger.info("GET /api/chats tests passed")
    return True

def test_send_messages():
    """Test POST /api/chats/{id}/messages endpoint"""
    logger.info("Testing POST /api/chats/{id}/messages endpoint...")
    
    # User1 sends a message to User2
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    message_data = {
        "content": f"Hello Bob! This is a test message from Alice. Timestamp: {timestamp}"
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message: {response.text}")
        return False
    
    message = response.json()
    if "message_id" not in message or "content" not in message:
        logger.error(f"Message response missing required fields: {message}")
        return False
    
    message_ids["user1_to_user2"] = message["message_id"]
    logger.info(f"Message sent with ID: {message_ids['user1_to_user2']}")
    
    # User2 sends a message to User1
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    message_data = {
        "content": f"Hi Alice! Thanks for your message. Timestamp: {timestamp}"
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message from user2: {response.text}")
        return False
    
    message_ids["user2_to_user1"] = response.json()["message_id"]
    logger.info(f"Message sent from user2 with ID: {message_ids['user2_to_user1']}")
    
    logger.info("POST /api/chats/{id}/messages tests passed")
    return True

def test_get_chat_messages():
    """Test GET /api/chats/{id}/messages endpoint"""
    logger.info("Testing GET /api/chats/{id}/messages endpoint...")
    
    # User1 gets messages from chat with User2
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get chat messages: {response.text}")
        return False
    
    messages = response.json()
    if len(messages) < 2:  # Should have at least 2 messages
        logger.error(f"Expected at least 2 messages, got {len(messages)}")
        return False
    
    # Verify message content
    message1 = next((m for m in messages if m["message_id"] == message_ids["user1_to_user2"]), None)
    message2 = next((m for m in messages if m["message_id"] == message_ids["user2_to_user1"]), None)
    
    if not message1 or not message2:
        logger.error("Could not find expected messages in chat history")
        return False
    
    logger.info(f"Retrieved {len(messages)} messages from chat")
    
    # User2 gets messages from chat with User1
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get chat messages for user2: {response.text}")
        return False
    
    messages = response.json()
    if len(messages) < 2:
        logger.error(f"Expected at least 2 messages for user2, got {len(messages)}")
        return False
    
    logger.info("GET /api/chats/{id}/messages tests passed")
    return True

def test_authenticity_details():
    """Test GET /api/authenticity/details endpoint"""
    logger.info("Testing GET /api/authenticity/details endpoint...")
    
    # User1 gets authenticity details
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/authenticity/details", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get authenticity details: {response.text}")
        return False
    
    details = response.json()
    required_fields = ["total_rating", "max_rating", "factors", "level", "next_milestone"]
    for field in required_fields:
        if field not in details:
            logger.error(f"Authenticity details missing required field: {field}")
            return False
    
    # Verify factors are included
    required_factors = ["profile_completeness", "verification_status", "interaction_quality", 
                        "consistency", "community_feedback"]
    for factor in required_factors:
        if factor not in details["factors"]:
            logger.error(f"Authenticity factors missing required factor: {factor}")
            return False
    
    logger.info(f"User1 authenticity rating: {details['total_rating']}, level: {details['level']}")
    
    logger.info("GET /api/authenticity/details tests passed")
    return True

def test_update_authenticity():
    """Test PUT /api/authenticity/update endpoint"""
    logger.info("Testing PUT /api/authenticity/update endpoint...")
    
    # User1 updates authenticity rating
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.put(f"{API_URL}/authenticity/update", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update authenticity rating: {response.text}")
        return False
    
    update_result = response.json()
    if "new_rating" not in update_result or "level" not in update_result:
        logger.error(f"Authenticity update response missing required fields: {update_result}")
        return False
    
    logger.info(f"Updated authenticity rating: {update_result['new_rating']}, level: {update_result['level']}")
    
    # Verify the update is reflected in user profile
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get user profile after authenticity update: {response.text}")
        return False
    
    user_data = response.json()
    if "authenticity_rating" not in user_data:
        logger.error("User profile missing authenticity_rating after update")
        return False
    
    if abs(user_data["authenticity_rating"] - update_result["new_rating"]) > 0.1:
        logger.error(f"Authenticity rating in profile ({user_data['authenticity_rating']}) doesn't match update result ({update_result['new_rating']})")
        return False
    
    logger.info("PUT /api/authenticity/update tests passed")
    return True

def run_all_tests():
    """Run all tests in sequence"""
    tests = [
        ("User Registration", test_user_registration),
        ("User Login", test_user_login),
        ("Get Current User", test_get_current_user),
        ("Profile Completion", test_profile_completion),
        ("Get QR Code", test_get_qr_code),
        ("Connection Request by PIN", test_connection_request_by_pin),
        ("Get Connection Requests", test_get_connection_requests),
        ("Respond to Connection Request", test_respond_to_connection_request),
        ("Get Connections", test_get_connections),
        ("Update Trust Level", test_update_trust_level),
        ("Get Chats", test_get_chats),
        ("Send Messages", test_send_messages),
        ("Get Chat Messages", test_get_chat_messages),
        ("Authenticity Details", test_authenticity_details),
        ("Update Authenticity", test_update_authenticity)
    ]
    
    results = {}
    all_passed = True
    
    for test_name, test_func in tests:
        logger.info(f"\n{'=' * 80}\nRunning test: {test_name}\n{'=' * 80}")
        try:
            result = test_func()
            results[test_name] = result
            if not result:
                all_passed = False
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
            all_passed = False
    
    # Print summary
    logger.info("\n\n" + "=" * 80)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 80)
    logger.info(f"OVERALL RESULT: {'PASSED' if all_passed else 'FAILED'}")
    logger.info("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()