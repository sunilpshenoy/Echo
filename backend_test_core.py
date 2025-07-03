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
    """Test profile completion"""
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
    
    logger.info("Profile Completion tests passed")
    return True

def test_authenticity_rating():
    """Test authenticity rating system"""
    logger.info("Testing Authenticity Rating System...")
    
    # Get authenticity details
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
    
    logger.info(f"User1 authenticity rating: {details['total_rating']}, level: {details['level']}")
    
    # Update authenticity rating
    response = requests.put(f"{API_URL}/authenticity/update", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update authenticity rating: {response.text}")
        return False
    
    update_result = response.json()
    if "new_rating" not in update_result or "level" not in update_result:
        logger.error(f"Authenticity update response missing required fields: {update_result}")
        return False
    
    logger.info(f"Updated authenticity rating: {update_result['new_rating']}, level: {update_result['level']}")
    
    logger.info("Authenticity Rating System tests passed")
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
        logger.error(f"Failed to add contact by email: {response.text}")
        return False
    
    logger.info("Successfully added contact by email")
    
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
    
    # Get messages from group chat
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['group_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get messages from group chat: {response.text}")
        return False
    
    messages = response.json()
    if len(messages) < 1:
        logger.error(f"Expected at least 1 message in group chat, got {len(messages)}")
        return False
    
    logger.info(f"Retrieved {len(messages)} messages from group chat")
    
    logger.info("Chat System tests passed")
    return True

def test_file_upload():
    """Test file upload endpoint"""
    logger.info("Testing File Upload...")
    
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
    required_fields = ["file_name", "file_size", "file_type", "file_data"]
    for field in required_fields:
        if field not in file_data:
            logger.error(f"File upload response missing required field: {field}")
            return False
    
    logger.info(f"Successfully uploaded image file: {file_data['file_name']}")
    
    logger.info("File Upload tests passed")
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

def test_voice_rooms():
    """Test voice rooms"""
    logger.info("Testing Voice Rooms...")
    
    # Create a voice room
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    room_data = {
        "name": f"Test Voice Room {timestamp}",
        "description": "A test voice room for API testing",
        "max_participants": 10
    }
    
    response = requests.post(f"{API_URL}/voice/rooms", json=room_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create voice room: {response.text}")
        return False
    
    room_id = response.json().get("room_id")
    if not room_id:
        logger.error(f"Voice room creation response missing room_id: {response.json()}")
        return False
    
    logger.info(f"Created voice room with ID: {room_id}")
    
    # Get voice rooms
    response = requests.get(f"{API_URL}/voice/rooms", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get voice rooms: {response.text}")
        return False
    
    rooms = response.json()
    if len(rooms) < 1:
        logger.error(f"Expected at least 1 voice room, got {len(rooms)}")
        return False
    
    logger.info(f"Retrieved {len(rooms)} voice rooms")
    
    # Join voice room
    response = requests.post(f"{API_URL}/voice/rooms/{room_id}/join", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to join voice room: {response.text}")
        return False
    
    logger.info("Successfully joined voice room")
    
    logger.info("Voice Rooms tests passed")
    return True

def test_stories_feature():
    """Test stories feature"""
    logger.info("Testing Stories Feature...")
    
    # Create a text story
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    story_data = {
        "content": f"This is a test story. Timestamp: {timestamp}",
        "media_type": "text",
        "background_color": "#3498db",
        "text_color": "#ffffff"
    }
    
    response = requests.post(f"{API_URL}/stories", json=story_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create story: {response.text}")
        return False
    
    story_id = response.json().get("story_id")
    if not story_id:
        logger.error(f"Story creation response missing story_id: {response.json()}")
        return False
    
    logger.info(f"Created text story with ID: {story_id}")
    
    # Get stories
    response = requests.get(f"{API_URL}/stories", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get stories: {response.text}")
        return False
    
    stories = response.json()
    if len(stories) < 1:
        logger.error(f"Expected at least 1 story, got {len(stories)}")
        return False
    
    logger.info(f"Retrieved {len(stories)} stories")
    
    logger.info("Stories Feature tests passed")
    return True

def test_channels_feature():
    """Test channels feature"""
    logger.info("Testing Channels Feature...")
    
    # Create a channel
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    channel_data = {
        "name": f"Test Channel {timestamp}",
        "description": "A test channel for API testing",
        "is_public": True,
        "category": "general"
    }
    
    response = requests.post(f"{API_URL}/channels", json=channel_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create channel: {response.text}")
        return False
    
    channel_id = response.json().get("channel_id")
    if not channel_id:
        logger.error(f"Channel creation response missing channel_id: {response.json()}")
        return False
    
    logger.info(f"Created channel with ID: {channel_id}")
    
    # Get channels
    response = requests.get(f"{API_URL}/channels", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get channels: {response.text}")
        return False
    
    channels = response.json()
    if len(channels) < 1:
        logger.error(f"Expected at least 1 channel, got {len(channels)}")
        return False
    
    logger.info(f"Retrieved {len(channels)} channels")
    
    # Subscribe to channel (User2 subscribes to User1's channel)
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.post(f"{API_URL}/channels/{channel_id}/subscribe", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to subscribe to channel: {response.text}")
        return False
    
    logger.info("Successfully subscribed to channel")
    
    logger.info("Channels Feature tests passed")
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
        ("Authenticity Rating System", test_authenticity_rating),
        ("Contact Management", test_contact_management),
        ("Chat System", test_chat_system),
        ("File Upload", test_file_upload),
        ("Teams API", test_teams_api),
        ("Voice/Video Calls", test_voice_video_calls),
        ("Voice Rooms", test_voice_rooms),
        ("Stories Feature", test_stories_feature),
        ("Channels Feature", test_channels_feature),
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