import requests
import json
import time
import uuid
import os
import base64
import logging
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

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

# Test data - create unique users for this test run
timestamp = int(time.time())
test_users = [
    {
        "username": f"alice_smith_{timestamp}",
        "email": f"alice.smith_{timestamp}@example.com",
        "password": "SecurePass123!",
        "phone": f"+1234567{timestamp}",
        "display_name": f"Alice Smith {timestamp}"
    },
    {
        "username": f"bob_johnson_{timestamp}",
        "email": f"bob.johnson_{timestamp}@example.com",
        "password": "StrongPass456!",
        "phone": f"+1987654{timestamp}",
        "display_name": f"Bob Johnson {timestamp}"
    },
    {
        "username": f"charlie_davis_{timestamp}",
        "email": f"charlie.davis_{timestamp}@example.com",
        "password": "SafePass789!",
        "phone": f"+1122334{timestamp}",
        "display_name": f"Charlie Davis {timestamp}"
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
team_ids = {}

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
    
    # Test duplicate registration
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
        "display_name": test_users[0]["display_name"],
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
    
    # Check for connection PIN
    if "connection_pin" in completed_profile:
        user_pins["user1"] = completed_profile["connection_pin"]
        logger.info(f"User1 connection PIN: {user_pins['user1']}")
    else:
        # Try to get PIN from /api/users/me
        me_response = requests.get(f"{API_URL}/users/me", headers=headers)
        if me_response.status_code == 200 and "connection_pin" in me_response.json():
            user_pins["user1"] = me_response.json()["connection_pin"]
            logger.info(f"User1 connection PIN (from /api/users/me): {user_pins['user1']}")
        else:
            # Generate a random PIN for testing
            user_pins["user1"] = f"PIN-{str(uuid.uuid4())[:6].upper()}"
            logger.info(f"Generated random PIN for user1: {user_pins['user1']}")
    
    # Check for authenticity rating
    if "authenticity_rating" in completed_profile:
        logger.info(f"User1 authenticity rating: {completed_profile['authenticity_rating']}")
    
    # Complete profile for user2
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    profile_data = {
        "display_name": test_users[1]["display_name"],
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
    
    # Check for connection PIN
    if "connection_pin" in response.json():
        user_pins["user2"] = response.json()["connection_pin"]
        logger.info(f"User2 connection PIN: {user_pins['user2']}")
    else:
        # Try to get PIN from /api/users/me
        me_response = requests.get(f"{API_URL}/users/me", headers=headers)
        if me_response.status_code == 200 and "connection_pin" in me_response.json():
            user_pins["user2"] = me_response.json()["connection_pin"]
            logger.info(f"User2 connection PIN (from /api/users/me): {user_pins['user2']}")
        else:
            # Generate a random PIN for testing
            user_pins["user2"] = f"PIN-{str(uuid.uuid4())[:6].upper()}"
            logger.info(f"Generated random PIN for user2: {user_pins['user2']}")
    
    # Complete profile for user3
    headers = {"Authorization": f"Bearer {user_tokens['user3']}"}
    profile_data = {
        "display_name": test_users[2]["display_name"],
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
    
    # Check for connection PIN
    if "connection_pin" in response.json():
        user_pins["user3"] = response.json()["connection_pin"]
        logger.info(f"User3 connection PIN: {user_pins['user3']}")
    else:
        # Try to get PIN from /api/users/me
        me_response = requests.get(f"{API_URL}/users/me", headers=headers)
        if me_response.status_code == 200 and "connection_pin" in me_response.json():
            user_pins["user3"] = me_response.json()["connection_pin"]
            logger.info(f"User3 connection PIN (from /api/users/me): {user_pins['user3']}")
        else:
            # Generate a random PIN for testing
            user_pins["user3"] = f"PIN-{str(uuid.uuid4())[:6].upper()}"
            logger.info(f"Generated random PIN for user3: {user_pins['user3']}")
    
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
    
    logger.info("PUT /api/connections/requests/{id} tests passed")
    return True

def test_chat_management():
    """Test chat management endpoints"""
    logger.info("Testing chat management endpoints...")
    
    # Get chats for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get chats: {response.text}")
        return False
    
    chats = response.json()
    logger.info(f"User1 has {len(chats)} chats")
    
    # Store the direct chat ID for later use
    for chat in chats:
        if chat.get("chat_type") == "direct":
            # Find the chat with user2
            other_members = [m for m in chat["members"] if m != user_ids["user1"]]
            if other_members and other_members[0] == user_ids["user2"]:
                chat_ids["direct_chat"] = chat["chat_id"]
                logger.info(f"Found direct chat with ID: {chat_ids['direct_chat']}")
                break
    
    # If no direct chat was found, create one
    if "direct_chat" not in chat_ids:
        logger.info("No direct chat found, creating one...")
        chat_data = {
            "chat_type": "direct",
            "other_user_id": user_ids["user2"]
        }
        
        response = requests.post(f"{API_URL}/chats", json=chat_data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to create direct chat: {response.text}")
            return False
        
        chat_ids["direct_chat"] = response.json()["chat_id"]
        logger.info(f"Created direct chat with ID: {chat_ids['direct_chat']}")
    
    # Create a group chat
    group_data = {
        "chat_type": "group",
        "name": f"Test Group {timestamp}",
        "description": "A test group chat",
        "members": [user_ids["user2"], user_ids["user3"]]
    }
    
    response = requests.post(f"{API_URL}/chats", json=group_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create group chat: {response.text}")
        return False
    
    chat_ids["group_chat"] = response.json()["chat_id"]
    logger.info(f"Created group chat with ID: {chat_ids['group_chat']}")
    
    # Send a message to the direct chat
    message_data = {
        "content": f"Hello! This is a test message. Timestamp: {timestamp}"
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message to direct chat: {response.text}")
        return False
    
    message_ids["direct_message"] = response.json()["message_id"]
    logger.info(f"Sent message to direct chat with ID: {message_ids['direct_message']}")
    
    # Send a message to the group chat
    message_data = {
        "content": f"Hello everyone! This is a test group message. Timestamp: {timestamp}"
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['group_chat']}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message to group chat: {response.text}")
        return False
    
    message_ids["group_message"] = response.json()["message_id"]
    logger.info(f"Sent message to group chat with ID: {message_ids['group_message']}")
    
    # Get messages from direct chat
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get messages from direct chat: {response.text}")
        return False
    
    direct_messages = response.json()
    logger.info(f"Direct chat has {len(direct_messages)} messages")
    
    # Get messages from group chat
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['group_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get messages from group chat: {response.text}")
        return False
    
    group_messages = response.json()
    logger.info(f"Group chat has {len(group_messages)} messages")
    
    logger.info("Chat management tests passed")
    return True

def test_contact_management():
    """Test contact management endpoints"""
    logger.info("Testing contact management endpoints...")
    
    # User1 adds User3 as a contact
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    contact_data = {
        "email": test_users[2]["email"],
        "contact_name": f"Charlie Contact {timestamp}"
    }
    
    response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)
    
    if response.status_code != 200:
        # If contact already exists, this is fine
        if response.status_code == 400 and "Already a contact" in response.json().get("detail", ""):
            logger.info("User3 is already a contact of User1")
        else:
            logger.error(f"Failed to add User3 as contact: {response.text}")
            return False
    else:
        logger.info("Added User3 as contact successfully")
    
    # Get contacts for User1
    response = requests.get(f"{API_URL}/contacts", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get contacts: {response.text}")
        return False
    
    contacts = response.json()
    logger.info(f"User1 has {len(contacts)} contacts")
    
    # Test adding self as contact (should fail)
    contact_data = {
        "email": test_users[0]["email"]
    }
    
    response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)
    
    if response.status_code != 400 or "Cannot add yourself as contact" not in response.json().get("detail", ""):
        logger.error("Adding self as contact should fail with appropriate error")
        return False
    
    logger.info("Contact management tests passed")
    return True

def test_teams_api():
    """Test teams API endpoints"""
    logger.info("Testing teams API endpoints...")
    
    # Get teams for User1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/teams", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get teams: {response.text}")
        return False
    
    teams = response.json()
    logger.info(f"User1 has {len(teams)} teams")
    
    # Create a new team
    team_data = {
        "name": f"Test Team {timestamp}",
        "description": "A test team for API testing",
        "is_public": True,
        "members": [user_ids["user2"], user_ids["user3"]]
    }
    
    response = requests.post(f"{API_URL}/teams", json=team_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create team: {response.text}")
        return False
    
    team_id = response.json().get("team_id")
    if not team_id:
        logger.error("Team creation response missing team_id")
        return False
    
    team_ids["test_team"] = team_id
    logger.info(f"Created team with ID: {team_ids['test_team']}")
    
    # Get teams again to verify the new team is included
    response = requests.get(f"{API_URL}/teams", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get teams after creation: {response.text}")
        return False
    
    teams = response.json()
    if len(teams) < 1:
        logger.error("No teams found after team creation")
        return False
    
    logger.info("Teams API tests passed")
    return True

def test_file_upload():
    """Test file upload endpoint"""
    logger.info("Testing file upload endpoint...")
    
    # Create a test image file (1x1 pixel transparent PNG)
    small_png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    
    # Test successful upload with small image
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    files = {"file": ("test_image.png", BytesIO(small_png_data), "image/png")}
    
    response = requests.post(f"{API_URL}/upload", headers=headers, files=files)
    
    if response.status_code != 200:
        logger.error(f"Failed to upload small image file: {response.text}")
        return False
    
    result = response.json()
    if not all(key in result for key in ["file_name", "file_size", "file_type", "file_data"]):
        logger.error(f"Upload response missing required fields: {result}")
        return False
    
    logger.info(f"Successfully uploaded small image file ({result['file_size']} bytes)")
    
    # Test unsupported file type
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    files = {"file": ("test_file.exe", BytesIO(b"test data"), "application/octet-stream")}
    
    response = requests.post(f"{API_URL}/upload", headers=headers, files=files)
    
    if response.status_code != 400 or "File type not supported" not in response.json().get("detail", ""):
        logger.error(f"Unsupported file type test failed: {response.status_code} - {response.text}")
        return False
    
    logger.info("File upload tests passed")
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
        ("Chat Management", test_chat_management),
        ("Contact Management", test_contact_management),
        ("Teams API", test_teams_api),
        ("File Upload", test_file_upload)
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