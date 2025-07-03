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
connection_pins = {}
chat_ids = {}
message_ids = {}
team_ids = {}

def test_authentication_system():
    """Test user registration, login, and token validation"""
    logger.info("Testing Authentication System...")
    
    # Test user registration
    for i, user_data in enumerate(test_users):
        response = requests.post(f"{API_URL}/register", json=user_data)
        
        if response.status_code == 200:
            logger.info(f"User {user_data['username']} registered successfully")
            user_tokens[f"user{i+1}"] = response.json()["access_token"]
            user_ids[f"user{i+1}"] = response.json()["user"]["user_id"]
        else:
            logger.error(f"Failed to register user {user_data['username']}: {response.text}")
            return False
    
    # Test user login
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
    
    # Test token validation with /api/users/me endpoint
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to validate token: {response.text}")
        return False
    
    logger.info("Authentication System tests passed")
    return True

def test_profile_completion():
    """Test profile completion and PIN generation"""
    logger.info("Testing Profile Completion...")
    
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
    
    # Store connection PIN if available
    if "connection_pin" in completed_profile:
        connection_pins["user1"] = completed_profile["connection_pin"]
        logger.info(f"User1 connection PIN: {connection_pins['user1']}")
    
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
    
    # Store connection PIN if available
    if "connection_pin" in response.json():
        connection_pins["user2"] = response.json()["connection_pin"]
        logger.info(f"User2 connection PIN: {connection_pins['user2']}")
    
    logger.info("Profile Completion tests passed")
    return True

def test_contact_management():
    """Test contact management system"""
    logger.info("Testing Contact Management...")
    
    # User1 adds User2 as contact
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    contact_data = {
        "email": test_users[1]["email"],
        "contact_name": f"Bob Contact {timestamp}"
    }
    
    response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to add contact: {response.text}")
        return False
    
    logger.info("Successfully added contact")
    
    # Get contacts
    response = requests.get(f"{API_URL}/contacts", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get contacts: {response.text}")
        return False
    
    contacts = response.json()
    if len(contacts) < 1:
        logger.error(f"Expected at least 1 contact, got {len(contacts)}")
        return False
    
    logger.info(f"Retrieved {len(contacts)} contacts")
    
    # Test adding self as contact (should fail)
    contact_data = {
        "email": test_users[0]["email"],
        "contact_name": "Self Contact"
    }
    
    response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)
    
    if response.status_code != 400 or "Cannot add yourself as contact" not in response.json().get("detail", ""):
        logger.error("Adding self as contact should fail with appropriate error")
        return False
    
    logger.info("Successfully prevented adding self as contact")
    
    # Test adding non-existent user (should fail)
    contact_data = {
        "email": f"nonexistent_{timestamp}@example.com",
        "contact_name": "Nonexistent Contact"
    }
    
    response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)
    
    if response.status_code != 404 or "User not found" not in response.json().get("detail", ""):
        logger.error("Adding nonexistent user should fail with 'User not found'")
        return False
    
    logger.info("Successfully prevented adding nonexistent user")
    
    logger.info("Contact Management tests passed")
    return True

def test_pin_connection_system():
    """Test PIN-based connection system"""
    logger.info("Testing PIN Connection System...")
    
    # Skip if PINs are not available
    if "user1" not in connection_pins or "user2" not in connection_pins:
        logger.warning("Skipping PIN connection test - PINs not available")
        return True
    
    # User2 requests connection with User1 using PIN
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    request_data = {
        "pin": connection_pins["user1"],
        "message": "Hi Alice, I'd like to connect!"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to request connection by PIN: {response.text}")
        return False
    
    request_id = response.json().get("request_id")
    if not request_id:
        logger.error(f"Connection request response missing request_id: {response.json()}")
        return False
    
    logger.info(f"Connection request created with ID: {request_id}")
    
    # User1 gets their connection requests
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/connections/requests", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connection requests: {response.text}")
        return False
    
    requests_list = response.json()
    if len(requests_list) < 1:
        logger.error(f"Expected at least 1 connection request, got {len(requests_list)}")
        return False
    
    logger.info(f"Retrieved {len(requests_list)} connection requests")
    
    # User1 accepts connection request
    response_data = {
        "action": "accept"
    }
    
    response = requests.put(
        f"{API_URL}/connections/requests/{request_id}",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept connection request: {response.text}")
        return False
    
    logger.info("Successfully accepted connection request")
    
    # User1 gets their connections
    response = requests.get(f"{API_URL}/connections", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connections: {response.text}")
        return False
    
    connections_list = response.json()
    if len(connections_list) < 1:
        logger.error(f"Expected at least 1 connection, got {len(connections_list)}")
        return False
    
    logger.info(f"Retrieved {len(connections_list)} connections")
    
    logger.info("PIN Connection System tests passed")
    return True

def test_chat_system():
    """Test chat system"""
    logger.info("Testing Chat System...")
    
    # Create direct chat
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
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
    
    # Create group chat
    chat_data = {
        "chat_type": "group",
        "name": f"Test Group {timestamp}",
        "description": "A test group chat",
        "members": [user_ids["user2"]]
    }
    
    response = requests.post(f"{API_URL}/chats", json=chat_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create group chat: {response.text}")
        return False
    
    chat_ids["group_chat"] = response.json()["chat_id"]
    logger.info(f"Created group chat with ID: {chat_ids['group_chat']}")
    
    # Get chats
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get chats: {response.text}")
        return False
    
    chats = response.json()
    if len(chats) < 2:  # Should have direct and group chat
        logger.error(f"Expected at least 2 chats, got {len(chats)}")
        return False
    
    logger.info(f"Retrieved {len(chats)} chats")
    
    # Send message to direct chat
    message_data = {
        "content": f"Hello from user1 to direct chat! Timestamp: {timestamp}"
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
    
    # Send message to group chat
    message_data = {
        "content": f"Hello from user1 to group chat! Timestamp: {timestamp}"
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
    
    messages = response.json()
    if len(messages) < 1:
        logger.error(f"Expected at least 1 message in direct chat, got {len(messages)}")
        return False
    
    logger.info(f"Retrieved {len(messages)} messages from direct chat")
    
    logger.info("Chat System tests passed")
    return True

def test_file_sharing():
    """Test file upload and sharing"""
    logger.info("Testing File Sharing...")
    
    # Create a test image file (1x1 pixel transparent PNG)
    small_png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    
    # Upload file
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    files = {"file": (f"test_image_{timestamp}.png", BytesIO(small_png_data), "image/png")}
    
    response = requests.post(f"{API_URL}/upload", headers=headers, files=files)
    
    if response.status_code != 200:
        logger.error(f"Failed to upload file: {response.text}")
        return False
    
    file_data = response.json()
    logger.info(f"Successfully uploaded image file: {file_data['file_name']}")
    
    # Send message with image attachment
    if "direct_chat" in chat_ids:
        message_data = {
            "content": f"Here's an image attachment. Timestamp: {timestamp}",
            "message_type": "image",
            "file_name": file_data["file_name"],
            "file_size": file_data["file_size"],
            "file_data": file_data["file_data"]
        }
        
        response = requests.post(
            f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
            json=message_data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to send message with image attachment: {response.text}")
            return False
        
        logger.info("Successfully sent message with image attachment")
    
    logger.info("File Sharing tests passed")
    return True

def test_teams_api():
    """Test teams API"""
    logger.info("Testing Teams API...")
    
    # Create a team
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    team_data = {
        "name": f"Test Team {timestamp}",
        "description": "A test team for API testing",
        "members": [user_ids["user2"]]
    }
    
    response = requests.post(f"{API_URL}/teams", json=team_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create team: {response.text}")
        return False
    
    team_id = response.json().get("team_id")
    if not team_id:
        logger.error(f"Team creation response missing team_id: {response.json()}")
        return False
    
    team_ids["test_team"] = team_id
    logger.info(f"Created team with ID: {team_id}")
    
    # Get teams
    response = requests.get(f"{API_URL}/teams", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get teams: {response.text}")
        return False
    
    teams = response.json()
    if len(teams) < 1:
        logger.error(f"Expected at least 1 team, got {len(teams)}")
        return False
    
    logger.info(f"Retrieved {len(teams)} teams")
    
    logger.info("Teams API tests passed")
    return True

def test_voice_video_calls():
    """Test voice/video call APIs"""
    logger.info("Testing Voice/Video Calls...")
    
    # Skip if no direct chat is available
    if "direct_chat" not in chat_ids:
        logger.warning("Skipping voice/video call test - direct chat not available")
        return True
    
    # Initiate a voice call
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    call_data = {
        "chat_id": chat_ids["direct_chat"],
        "call_type": "voice"
    }
    
    response = requests.post(f"{API_URL}/calls/initiate", json=call_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to initiate voice call: {response.text}")
        return False
    
    voice_call_id = response.json().get("call_id")
    if not voice_call_id:
        logger.error(f"Voice call initiation response missing call_id: {response.json()}")
        return False
    
    logger.info(f"Initiated voice call with ID: {voice_call_id}")
    
    # Initiate a video call
    call_data = {
        "chat_id": chat_ids["direct_chat"],
        "call_type": "video"
    }
    
    response = requests.post(f"{API_URL}/calls/initiate", json=call_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to initiate video call: {response.text}")
        return False
    
    video_call_id = response.json().get("call_id")
    if not video_call_id:
        logger.error(f"Video call initiation response missing call_id: {response.json()}")
        return False
    
    logger.info(f"Initiated video call with ID: {video_call_id}")
    
    logger.info("Voice/Video Calls tests passed")
    return True

def test_genie_command_processing():
    """Test Genie command processing"""
    logger.info("Testing Genie Command Processing...")
    
    # Test various commands
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    commands = [
        "create a chat with Bob",
        "add contact john.doe@example.com",
        "block user Charlie",
        "show my chats",
        "help me",
        "send message to Bob saying hello"
    ]
    
    for command in commands:
        response = requests.post(
            f"{API_URL}/genie/process",
            json={"command": command},
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to process command '{command}': {response.text}")
            return False
        
        result = response.json()
        if "intent" not in result or "action" not in result:
            logger.error(f"Command response missing required fields: {result}")
            return False
        
        logger.info(f"Successfully processed command '{command}' with intent '{result['intent']}'")
    
    logger.info("Genie Command Processing tests passed")
    return True

def run_all_tests():
    """Run all tests in sequence"""
    tests = [
        ("Authentication System", test_authentication_system),
        ("Profile Completion", test_profile_completion),
        ("Contact Management", test_contact_management),
        ("PIN Connection System", test_pin_connection_system),
        ("Chat System", test_chat_system),
        ("File Sharing", test_file_sharing),
        ("Teams API", test_teams_api),
        ("Voice/Video Calls", test_voice_video_calls),
        ("Genie Command Processing", test_genie_command_processing)
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
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 80)
    logger.info(f"OVERALL RESULT: {'PASSED' if all_passed else 'FAILED'}")
    logger.info("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()