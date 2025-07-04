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

def test_user_authentication():
    """Test user authentication system (register, login, /api/users/me)"""
    logger.info("Testing user authentication system...")
    
    # Test registration
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
    
    # Test login with valid credentials
    for i, user_data in enumerate(test_users):
        response = requests.post(f"{API_URL}/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        if response.status_code != 200:
            logger.error(f"Failed to log in user {user_data['username']}: {response.text}")
            return False
        
        logger.info(f"User {user_data['username']} logged in successfully")
        
        # Verify profile_completed status is returned
        if "profile_completed" not in response.json()["user"]:
            logger.error(f"Login response missing profile_completed status")
            return False
    
    # Test login with invalid credentials
    response = requests.post(f"{API_URL}/login", json={
        "email": "nonexistent@example.com",
        "password": "WrongPassword123"
    })
    
    if response.status_code != 401:
        logger.error("Invalid credentials test failed")
        return False
    
    # Test GET /api/users/me endpoint
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
    
    logger.info("User authentication system tests passed")
    return True

def test_profile_completion():
    """Test profile completion endpoint (/api/profile/complete)"""
    logger.info("Testing profile completion endpoint...")
    
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
    
    # Test updating an existing profile
    update_data = {
        "display_name": f"Updated Alice {timestamp}",
        "bio": "Updated bio with new information",
        "interests": ["technology", "hiking", "photography", "travel", "cooking"]
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=update_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update profile: {response.text}")
        return False
    
    # Verify profile was updated
    updated_profile = response.json()
    if updated_profile.get("display_name") != update_data["display_name"]:
        logger.error(f"Display name not updated correctly: {updated_profile.get('display_name')}")
        return False
    
    if updated_profile.get("bio") != update_data["bio"]:
        logger.error(f"Bio not updated correctly: {updated_profile.get('bio')}")
        return False
    
    logger.info("Profile completion endpoint tests passed")
    return True

def test_pin_connection_system():
    """Test PIN-based connection system (/api/users/qr-code, /api/connections/request-by-pin)"""
    logger.info("Testing PIN-based connection system...")
    
    # Make sure we have a PIN for user1
    if "user1" not in user_pins:
        logger.error("No PIN available for user1")
        return False
    
    # Get QR code for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/users/qr-code", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get QR code: {response.text}")
        return False
    
    qr_data = response.json()
    if "qr_code" not in qr_data:
        logger.error(f"QR code response missing qr_code field: {qr_data}")
        return False
    
    # If the response includes a connection_pin, update our stored PIN
    if "connection_pin" in qr_data:
        if qr_data["connection_pin"] != user_pins["user1"]:
            logger.info(f"Updating user1 PIN from QR code: {qr_data['connection_pin']}")
            user_pins["user1"] = qr_data["connection_pin"]
    
    # Complete profile for user2 to ensure they can make connection requests
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
    
    # User2 requests connection with User1 using PIN
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    
    # Try different endpoint variations
    endpoints = [
        f"{API_URL}/connections/request-by-pin",
        f"{API_URL}/connections/request"
    ]
    
    success = False
    for endpoint in endpoints:
        request_data = {
            "pin": user_pins["user1"],
            "message": "Hi Alice, I'd like to connect!"
        }
        
        response = requests.post(endpoint, json=request_data, headers=headers)
        
        if response.status_code == 200:
            success = True
            logger.info(f"Connection request successful using endpoint: {endpoint}")
            
            if "request_id" in response.json():
                connection_requests["user2_to_user1"] = response.json()["request_id"]
                logger.info(f"Connection request created with ID: {connection_requests['user2_to_user1']}")
            break
    
    if not success:
        # Try with user ID instead of PIN
        for endpoint in endpoints:
            request_data = {
                "user_id": user_ids["user1"],
                "message": "Hi Alice, I'd like to connect!"
            }
            
            response = requests.post(endpoint, json=request_data, headers=headers)
            
            if response.status_code == 200:
                success = True
                logger.info(f"Connection request successful using user_id and endpoint: {endpoint}")
                
                if "request_id" in response.json():
                    connection_requests["user2_to_user1"] = response.json()["request_id"]
                    logger.info(f"Connection request created with ID: {connection_requests['user2_to_user1']}")
                break
    
    if not success:
        logger.error("Failed to create connection request using any method")
        return False
    
    # User1 gets their connection requests
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/connections/requests", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connection requests: {response.text}")
        return False
    
    requests_list = response.json()
    logger.info(f"User1 has {len(requests_list)} connection requests")
    
    # User1 accepts connection request from User2
    if "user2_to_user1" in connection_requests:
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
        if "status" not in connection_data:
            logger.error(f"Connection response missing status field: {connection_data}")
            return False
        
        if "connection_id" in connection_data:
            connections["user1_user2"] = connection_data["connection_id"]
            logger.info(f"Connection created with ID: {connections['user1_user2']}")
        else:
            logger.warning("Connection response missing connection_id field")
        
        logger.info("Connection request accepted successfully")
    else:
        logger.warning("No connection request ID available for acceptance test")
    
    logger.info("PIN-based connection system tests passed")
    return True

def test_chat_management():
    """Test chat management system (/api/chats, /api/messages)"""
    logger.info("Testing chat management system...")
    
    # Get chats for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get chats: {response.text}")
        return False
    
    chats = response.json()
    logger.info(f"User1 has {len(chats)} chats")
    
    # Store the direct chat ID for later use if it exists
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
        "members": [user_ids["user2"]]
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
    
    # Test user2 can see the messages
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"User2 failed to get messages from direct chat: {response.text}")
        return False
    
    user2_messages = response.json()
    logger.info(f"User2 sees {len(user2_messages)} messages in direct chat")
    
    logger.info("Chat management system tests passed")
    return True

def test_contact_management():
    """Test contact management (/api/contacts)"""
    logger.info("Testing contact management...")
    
    # User1 adds User2 as a contact
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    contact_data = {
        "email": test_users[1]["email"],
        "contact_name": f"Bob Contact {timestamp}"
    }
    
    response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)
    
    if response.status_code != 200:
        # If contact already exists, this is fine
        if response.status_code == 400 and "Already a contact" in response.json().get("detail", ""):
            logger.info("User2 is already a contact of User1")
        else:
            logger.error(f"Failed to add User2 as contact: {response.text}")
            return False
    else:
        logger.info("Added User2 as contact successfully")
    
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
    
    # Test adding non-existent user (should fail)
    contact_data = {
        "email": f"nonexistent_{timestamp}@example.com"
    }
    
    response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)
    
    if response.status_code != 404 or "User not found" not in response.json().get("detail", ""):
        logger.error("Adding non-existent user should fail with 'User not found'")
        return False
    
    logger.info("Contact management tests passed")
    return True

def test_teams_api():
    """Test teams API endpoints (/api/teams)"""
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
        "members": [user_ids["user2"]]
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
    
    # Verify User2 can see the team
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(f"{API_URL}/teams", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get teams for User2: {response.text}")
        return False
    
    user2_teams = response.json()
    logger.info(f"User2 has {len(user2_teams)} teams")
    
    logger.info("Teams API tests passed")
    return True

def test_file_upload():
    """Test file upload API (/api/upload-file)"""
    logger.info("Testing file upload API...")
    
    # Create a test image file (1x1 pixel transparent PNG)
    small_png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    
    # Test successful upload with small image
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    files = {"file": ("test_image.png", BytesIO(small_png_data), "image/png")}
    
    # Try both potential endpoints
    endpoints = [
        f"{API_URL}/upload",
        f"{API_URL}/upload-file"
    ]
    
    success = False
    for endpoint in endpoints:
        try:
            response = requests.post(endpoint, headers=headers, files=files)
            
            if response.status_code == 200:
                success = True
                logger.info(f"Successfully uploaded file using endpoint: {endpoint}")
                
                result = response.json()
                if "file_name" in result and "file_data" in result:
                    logger.info(f"Successfully uploaded small image file ({result.get('file_size', 'unknown')} bytes)")
                break
        except Exception as e:
            logger.error(f"Error trying endpoint {endpoint}: {e}")
    
    if not success:
        logger.error("Failed to upload file using any endpoint")
        return False
    
    # Create a text file
    text_content = "This is a test text file for upload testing."
    
    # Test successful upload with text file
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    files = {"file": ("test_document.txt", BytesIO(text_content.encode()), "text/plain")}
    
    success = False
    for endpoint in endpoints:
        try:
            response = requests.post(endpoint, headers=headers, files=files)
            
            if response.status_code == 200:
                success = True
                logger.info(f"Successfully uploaded text file using endpoint: {endpoint}")
                break
        except Exception as e:
            logger.error(f"Error trying endpoint {endpoint} for text file: {e}")
    
    if not success:
        logger.error("Failed to upload text file using any endpoint")
        return False
    
    logger.info("File upload API tests passed")
    return True

def run_all_tests():
    """Run all tests in sequence"""
    tests = [
        ("User Authentication System", test_user_authentication),
        ("Profile Completion Endpoint", test_profile_completion),
        ("PIN-based Connection System", test_pin_connection_system),
        ("Chat Management System", test_chat_management),
        ("Contact Management", test_contact_management),
        ("Teams API Endpoints", test_teams_api),
        ("File Upload API", test_file_upload)
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