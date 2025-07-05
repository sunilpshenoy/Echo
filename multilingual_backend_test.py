import requests
import json
import time
import os
import logging
import uuid
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

# Test data
test_users = [
    {
        "username": "alice_smith",
        "email": "alice.smith@example.com",
        "password": "SecurePass123!",
        "display_name": "Alice Smith"
    },
    {
        "username": "bob_johnson",
        "email": "bob.johnson@example.com",
        "password": "StrongPass456!",
        "display_name": "Bob Johnson"
    },
    {
        "username": "charlie_davis",
        "email": "charlie.davis@example.com",
        "password": "SafePass789!",
        "display_name": "Charlie Davis"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
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

def test_token_validation():
    """Test token validation with /api/users/me endpoint"""
    logger.info("Testing token validation...")
    
    # Test with valid token
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Token validation failed: {response.text}")
        return False
    
    user_data = response.json()
    if user_data["user_id"] != user_ids["user1"]:
        logger.error(f"User ID mismatch: {user_data['user_id']} != {user_ids['user1']}")
        return False
    
    # Test with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 401:
        logger.error(f"Invalid token test failed: {response.status_code}")
        return False
    
    logger.info("Token validation tests passed")
    return True

def test_profile_completion():
    """Test profile completion endpoint"""
    logger.info("Testing profile completion...")
    
    # Complete profile for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    profile_data = {
        "display_name": "Alice Smith",
        "age": 28,
        "gender": "female",
        "location": "New York",
        "current_mood": "Excited",
        "mood_reason": "Testing the app",
        "seeking_type": "Friendship",
        "seeking_age_range": "25-35",
        "seeking_gender": "Any",
        "seeking_location_preference": "Nearby",
        "connection_purpose": "Networking",
        "additional_requirements": "Tech enthusiasts",
        "bio": "Software engineer passionate about building great apps",
        "interests": ["coding", "hiking", "reading"],
        "values": ["honesty", "creativity", "growth"]
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Profile completion failed: {response.text}")
        return False
    
    result = response.json()
    if not result.get("profile_completed"):
        logger.error("Profile not marked as completed")
        return False
    
    # Verify profile data was saved
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get user profile: {response.text}")
        return False
    
    user_data = response.json()
    for key, value in profile_data.items():
        if key in user_data and user_data[key] != value:
            logger.error(f"Profile field {key} mismatch: {user_data[key]} != {value}")
            return False
    
    logger.info("Profile completion tests passed")
    return True

def test_teams_api():
    """Test Teams API endpoints"""
    logger.info("Testing Teams API endpoints...")
    
    # Test GET /api/teams
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/teams", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"GET /api/teams failed: {response.text}")
        return False
    
    teams = response.json()
    logger.info(f"User has {len(teams)} teams")
    
    # Test POST /api/teams
    team_data = {
        "name": f"Test Team {uuid.uuid4().hex[:8]}",
        "description": "A team for testing the API",
        "type": "group"
    }
    
    response = requests.post(f"{API_URL}/teams", json=team_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"POST /api/teams failed: {response.text}")
        return False
    
    team = response.json()
    if "team_id" not in team:
        logger.error(f"Team creation response missing team_id: {team}")
        return False
    
    team_ids["test_team"] = team["team_id"]
    logger.info(f"Created team with ID: {team_ids['test_team']}")
    
    # Verify team was created by getting teams again
    response = requests.get(f"{API_URL}/teams", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"GET /api/teams after creation failed: {response.text}")
        return False
    
    teams = response.json()
    if not any(t.get("team_id") == team_ids["test_team"] for t in teams):
        logger.error(f"Created team not found in teams list")
        return False
    
    logger.info("Teams API tests passed")
    return True

def test_chat_functionality():
    """Test core chat functionality"""
    logger.info("Testing chat functionality...")
    
    # Create direct chat between user1 and user2
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.post(
        f"{API_URL}/chats",
        json={"chat_type": "direct", "other_user_id": user_ids['user2']},
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to create direct chat: {response.text}")
        return False
    
    chat_ids['direct_chat'] = response.json()["chat_id"]
    logger.info(f"Direct chat created with ID: {chat_ids['direct_chat']}")
    
    # Create group chat with all users
    response = requests.post(
        f"{API_URL}/chats",
        json={
            "chat_type": "group",
            "name": "Test Group Chat",
            "members": [user_ids['user2'], user_ids['user3']]
        },
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to create group chat: {response.text}")
        return False
    
    chat_ids['group_chat'] = response.json()["chat_id"]
    logger.info(f"Group chat created with ID: {chat_ids['group_chat']}")
    
    # Send message to direct chat
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        json={"content": "Hello from user1 to user2!"},
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message to direct chat: {response.text}")
        return False
    
    message_ids['direct_message'] = response.json()["message_id"]
    logger.info(f"Message sent to direct chat with ID: {message_ids['direct_message']}")
    
    # Send message to group chat
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['group_chat']}/messages",
        json={"content": "Hello everyone in the group chat!"},
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message to group chat: {response.text}")
        return False
    
    message_ids['group_message'] = response.json()["message_id"]
    logger.info(f"Message sent to group chat with ID: {message_ids['group_message']}")
    
    # Get messages for direct chat
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get direct chat messages: {response.text}")
        return False
    
    messages = response.json()
    if len(messages) < 1:
        logger.error(f"Expected at least 1 message in direct chat, got {len(messages)}")
        return False
    
    logger.info(f"Direct chat has {len(messages)} messages")
    
    # Get messages for group chat
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['group_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get group chat messages: {response.text}")
        return False
    
    messages = response.json()
    if len(messages) < 1:
        logger.error(f"Expected at least 1 message in group chat, got {len(messages)}")
        return False
    
    logger.info(f"Group chat has {len(messages)} messages")
    
    logger.info("Chat functionality tests passed")
    return True

def test_profile_management():
    """Test profile management endpoints"""
    logger.info("Testing profile management...")
    
    # Test GET /api/users/me
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"GET /api/users/me failed: {response.text}")
        return False
    
    user_data = response.json()
    if user_data["user_id"] != user_ids["user1"]:
        logger.error(f"User ID mismatch: {user_data['user_id']} != {user_ids['user1']}")
        return False
    
    # Test PUT /api/profile
    profile_update = {
        "display_name": f"Alice Smith Updated {uuid.uuid4().hex[:4]}",
        "status_message": "Testing profile updates"
    }
    
    response = requests.put(f"{API_URL}/profile", json=profile_update, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"PUT /api/profile failed: {response.text}")
        return False
    
    updated_profile = response.json()
    if updated_profile["display_name"] != profile_update["display_name"]:
        logger.error(f"Display name not updated: {updated_profile['display_name']} != {profile_update['display_name']}")
        return False
    
    if updated_profile["status_message"] != profile_update["status_message"]:
        logger.error(f"Status message not updated: {updated_profile['status_message']} != {profile_update['status_message']}")
        return False
    
    logger.info("Profile management tests passed")
    return True

def test_contact_management():
    """Test contact management endpoints"""
    logger.info("Testing contact management...")
    
    # Add user2 as contact for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.post(
        f"{API_URL}/contacts",
        json={"email": test_users[1]["email"], "contact_name": "Bob (Contact)"},
        headers=headers
    )
    
    # If contact already exists, this is fine
    if response.status_code != 200 and not (response.status_code == 400 and ("Already a contact" in response.json().get("detail", "") or "Contact already exists" in response.json().get("detail", ""))):
        logger.error(f"Failed to add contact: {response.text}")
        return False
    
    logger.info("Contact added successfully or already exists")
    
    # Add user3 as contact for user1
    response = requests.post(
        f"{API_URL}/contacts",
        json={"email": test_users[2]["email"], "contact_name": "Charlie (Contact)"},
        headers=headers
    )
    
    # If contact already exists, this is fine
    if response.status_code != 200 and not (response.status_code == 400 and ("Already a contact" in response.json().get("detail", "") or "Contact already exists" in response.json().get("detail", ""))):
        logger.error(f"Failed to add second contact: {response.text}")
        return False
    
    logger.info("Second contact added successfully or already exists")
    
    # Test adding self as contact (should fail)
    response = requests.post(
        f"{API_URL}/contacts",
        json={"email": test_users[0]["email"]},
        headers=headers
    )
    
    if response.status_code != 400 or "Cannot add yourself as contact" not in response.json().get("detail", ""):
        logger.error("Adding self as contact should fail with appropriate error")
        return False
    
    # Test adding invalid email (should fail)
    response = requests.post(
        f"{API_URL}/contacts",
        json={"email": "nonexistent@example.com"},
        headers=headers
    )
    
    if response.status_code != 404 or "User not found" not in response.json().get("detail", ""):
        logger.error("Adding nonexistent email should fail with 'User not found'")
        return False
    
    # Get contacts for user1
    response = requests.get(f"{API_URL}/contacts", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get contacts: {response.text}")
        return False
    
    contacts = response.json()
    logger.info(f"User has {len(contacts)} contacts")
    
    logger.info("Contact management tests passed")
    return True

def test_connection_requests():
    """Test connection request endpoints"""
    logger.info("Testing connection requests...")
    
    # Get user1's connection PIN
    headers1 = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/users/me", headers=headers1)
    
    if response.status_code != 200:
        logger.error(f"Failed to get user1 data: {response.text}")
        return False
    
    user1_data = response.json()
    connection_pin = user1_data.get("connection_pin")
    
    if not connection_pin:
        logger.error("User1 does not have a connection PIN")
        return False
    
    logger.info(f"User1 connection PIN: {connection_pin}")
    
    # User2 sends connection request to user1 using PIN
    headers2 = {"Authorization": f"Bearer {user_tokens['user2']}"}
    
    # Try the request-by-pin endpoint
    try:
        response = requests.post(
            f"{API_URL}/connections/request-by-pin",
            json={"pin": connection_pin, "message": "Hello, I'd like to connect!"},
            headers=headers2
        )
        
        # This might fail if they're already connected, which is fine
        if response.status_code != 200 and not (response.status_code == 400 and ("already connected" in response.json().get("detail", "").lower() or "Target PIN required" in response.json().get("detail", ""))):
            logger.error(f"Failed to send connection request by PIN: {response.text}")
            return False
        
        logger.info("Connection request sent successfully or users already connected")
    except Exception as e:
        logger.warning(f"Error with request-by-pin endpoint: {str(e)}")
        logger.info("Trying alternative connection request method...")
        
        # Try direct connection request as fallback
        response = requests.post(
            f"{API_URL}/connections/request",
            json={"user_id": user_ids['user1'], "message": "Hello, I'd like to connect!"},
            headers=headers2
        )
        
        # This might fail if they're already connected, which is fine
        if response.status_code != 200 and not (response.status_code == 400 and "already connected" in response.json().get("detail", "").lower()):
            logger.error(f"Failed to send direct connection request: {response.text}")
            return False
        
        logger.info("Direct connection request sent successfully or users already connected")
    
    # Get connection requests for user1
    response = requests.get(f"{API_URL}/connections/requests", headers=headers1)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connection requests: {response.text}")
        return False
    
    requests_list = response.json()
    logger.info(f"User1 has {len(requests_list)} connection requests")
    
    # Try getting connections instead of requests
    response = requests.get(f"{API_URL}/connections", headers=headers1)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connections: {response.text}")
        return False
    
    connections = response.json()
    logger.info(f"User1 has {len(connections)} connections")
    
    logger.info("Connection requests tests passed")
    return True

def run_all_tests():
    """Run all backend API tests"""
    tests = [
        ("User Registration", test_user_registration),
        ("User Login", test_user_login),
        ("Token Validation", test_token_validation),
        ("Profile Completion", test_profile_completion),
        ("Teams API", test_teams_api),
        ("Chat Functionality", test_chat_functionality),
        ("Profile Management", test_profile_management),
        ("Contact Management", test_contact_management),
        ("Connection Requests", test_connection_requests)
    ]
    
    results = {}
    all_passed = True
    
    for name, test_func in tests:
        logger.info(f"\n{'=' * 50}\nRunning test: {name}\n{'=' * 50}")
        try:
            result = test_func()
            results[name] = result
            if not result:
                all_passed = False
        except Exception as e:
            logger.error(f"Error in {name} test: {str(e)}")
            results[name] = False
            all_passed = False
    
    logger.info("\n\n" + "=" * 50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 50)
    
    for name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{name}: {status}")
    
    logger.info("=" * 50)
    logger.info(f"Overall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    logger.info("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()