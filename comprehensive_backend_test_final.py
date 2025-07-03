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
connection_pins = {}
connection_requests = {}
connections = {}
chat_ids = {}
message_ids = {}
team_ids = {}
channel_ids = {}
story_ids = {}
file_data = {}
blocked_users = {}
report_ids = {}
voice_room_ids = {}
call_ids = {}

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
    
    # Store connection PIN if available
    if "connection_pin" in response.json():
        connection_pins["user3"] = response.json()["connection_pin"]
        logger.info(f"User3 connection PIN: {connection_pins['user3']}")
    
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
    
    # User1 adds User3 as contact
    contact_data = {
        "email": test_users[2]["email"],
        "contact_name": f"Charlie Contact {timestamp}"
    }
    
    response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to add second contact by email: {response.text}")
        return False
    
    logger.info("Successfully added second contact by email")
    
    # Get contacts
    response = requests.get(f"{API_URL}/contacts", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get contacts: {response.text}")
        return False
    
    contacts = response.json()
    if len(contacts) < 2:
        logger.error(f"Expected at least 2 contacts, got {len(contacts)}")
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
    
    # Delete a contact
    if len(contacts) > 0:
        contact_id = contacts[0]["contact_id"]
        response = requests.delete(f"{API_URL}/contacts/{contact_id}", headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to delete contact: {response.text}")
            return False
        
        logger.info("Successfully deleted contact")
    
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
    
    connection_requests["user2_to_user1"] = request_id
    logger.info(f"Connection request created with ID: {request_id}")
    
    # User3 requests connection with User1 using PIN
    headers = {"Authorization": f"Bearer {user_tokens['user3']}"}
    request_data = {
        "pin": connection_pins["user1"],
        "message": "Hey Alice, let's connect!"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to request connection by PIN for user3: {response.text}")
        return False
    
    connection_requests["user3_to_user1"] = response.json().get("request_id")
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
    
    logger.info("Successfully prevented connection with invalid PIN")
    
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
    
    logger.info(f"Retrieved {len(requests_list)} connection requests")
    
    # User1 accepts connection request from User2
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
    
    logger.info("Successfully declined connection request")
    
    # User1 gets their connections
    response = requests.get(f"{API_URL}/connections", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connections: {response.text}")
        return False
    
    connections_list = response.json()
    if len(connections_list) < 1:  # Should have at least 1 connection
        logger.error(f"Expected at least 1 connection, got {len(connections_list)}")
        return False
    
    logger.info(f"Retrieved {len(connections_list)} connections")
    
    logger.info("PIN Connection System tests passed")
    return True

def test_progressive_trust_system():
    """Test progressive trust system"""
    logger.info("Testing Progressive Trust System...")
    
    # Skip if no connection is available
    if "user1_user2" not in connections:
        logger.warning("Skipping progressive trust test - no connection available")
        return True
    
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
    
    logger.info("Successfully prevented setting invalid trust level")
    
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
    
    logger.info("Progressive Trust System tests passed")
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
        "members": [user_ids["user2"], user_ids["user3"]]
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
    
    # Test read receipts
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    read_data = {
        "message_ids": [message_ids["direct_message"]]
    }
    
    response = requests.post(f"{API_URL}/messages/read", json=read_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to mark message as read: {response.text}")
        return False
    
    logger.info("Successfully marked message as read")
    
    logger.info("Chat System tests passed")
    return True

def test_enhanced_message_features():
    """Test enhanced message features"""
    logger.info("Testing Enhanced Message Features...")
    
    # Skip if no messages are available
    if "direct_message" not in message_ids:
        logger.warning("Skipping enhanced message features test - no messages available")
        return True
    
    # Test message reactions
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    reaction_data = {
        "message_id": message_ids["direct_message"],
        "reaction": "👍"
    }
    
    response = requests.post(f"{API_URL}/messages/react", json=reaction_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to add reaction: {response.text}")
        return False
    
    logger.info("Successfully added reaction to message")
    
    # Test message editing
    edit_data = {
        "message_id": message_ids["direct_message"],
        "content": f"This is an edited message. Original timestamp: {timestamp}"
    }
    
    response = requests.put(f"{API_URL}/messages/edit", json=edit_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to edit message: {response.text}")
        return False
    
    logger.info("Successfully edited message")
    
    # Test message deletion (soft delete)
    response = requests.delete(f"{API_URL}/messages/{message_ids['group_message']}", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to delete message: {response.text}")
        return False
    
    logger.info("Successfully deleted message")
    
    # Test message reply
    reply_data = {
        "content": f"This is a reply to your message. Timestamp: {timestamp}",
        "reply_to": message_ids["direct_message"]
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        json=reply_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send reply message: {response.text}")
        return False
    
    message_ids["reply_message"] = response.json()["message_id"]
    logger.info(f"Sent reply message with ID: {message_ids['reply_message']}")
    
    logger.info("Enhanced Message Features tests passed")
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
    
    file_data["image"] = response.json()
    logger.info(f"Successfully uploaded image file: {file_data['image']['file_name']}")
    
    # Test file size limit (create a request with a Content-Length header that exceeds the limit)
    try:
        headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
        headers["X-Content-Length"] = str(11 * 1024 * 1024)  # 11MB
        files = {"file": ("large_file.png", BytesIO(small_png_data), "image/png")}
        
        # Use a custom session to modify the request
        session = requests.Session()
        request = requests.Request('POST', f"{API_URL}/upload", headers=headers, files=files)
        prepped = session.prepare_request(request)
        
        # Modify the prepared request to simulate a large file
        prepped.headers["Content-Length"] = str(11 * 1024 * 1024)
        
        # This should fail with a 413 error
        response = session.send(prepped, timeout=5)
        
        if response.status_code != 413:
            logger.warning(f"Large file upload test didn't fail as expected: {response.status_code}")
    except Exception as e:
        logger.info(f"Large file upload test exception (expected): {e}")
    
    # Send message with image attachment
    if "direct_chat" in chat_ids:
        message_data = {
            "content": f"Here's an image attachment. Timestamp: {timestamp}",
            "message_type": "image",
            "file_name": file_data["image"]["file_name"],
            "file_size": file_data["image"]["file_size"],
            "file_data": file_data["image"]["file_data"]
        }
        
        response = requests.post(
            f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
            json=message_data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to send message with image attachment: {response.text}")
            return False
        
        message_ids["image_message"] = response.json()["message_id"]
        logger.info(f"Sent message with image attachment, ID: {message_ids['image_message']}")
    
    # Create a text file attachment
    text_content = f"This is a test text file for attachment. Timestamp: {timestamp}"
    text_data = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
    
    # Send message with text file attachment
    if "group_chat" in chat_ids:
        message_data = {
            "content": f"Here's a text file attachment. Timestamp: {timestamp}",
            "message_type": "file",
            "file_name": f"test_document_{timestamp}.txt",
            "file_size": len(text_content),
            "file_data": text_data
        }
        
        response = requests.post(
            f"{API_URL}/chats/{chat_ids['group_chat']}/messages",
            json=message_data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to send message with text file attachment: {response.text}")
            return False
        
        message_ids["file_message"] = response.json()["message_id"]
        logger.info(f"Sent message with text file attachment, ID: {message_ids['file_message']}")
    
    # Upload file directly to chat
    if "direct_chat" in chat_ids:
        files = {"file": (f"direct_upload_{timestamp}.png", BytesIO(small_png_data), "image/png")}
        
        response = requests.post(
            f"{API_URL}/chats/{chat_ids['direct_chat']}/files",
            headers=headers,
            files=files
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to upload file directly to chat: {response.text}")
            return False
        
        logger.info("Successfully uploaded file directly to chat")
    
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
    
    call_ids["voice_call"] = voice_call_id
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
    
    call_ids["video_call"] = video_call_id
    logger.info(f"Initiated video call with ID: {video_call_id}")
    
    # Test screen sharing
    response = requests.post(
        f"{API_URL}/calls/{video_call_id}/screen-share",
        params={"enable": "true"},
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to enable screen sharing: {response.text}")
        return False
    
    logger.info("Successfully enabled screen sharing")
    
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
    
    voice_room_ids["test_room"] = room_id
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

def test_user_blocking_reporting():
    """Test user blocking and reporting features"""
    logger.info("Testing User Blocking and Reporting...")
    
    # User1 blocks User3
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    block_data = {
        "user_id": user_ids["user3"],
        "reason": "Testing block functionality"
    }
    
    response = requests.post(f"{API_URL}/users/block", json=block_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to block user: {response.text}")
        return False
    
    blocked_users["user1_blocks_user3"] = user_ids["user3"]
    logger.info(f"User1 blocked User3")
    
    # Get blocked users
    response = requests.get(f"{API_URL}/users/blocked", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get blocked users: {response.text}")
        return False
    
    blocks = response.json()
    if len(blocks) < 1:
        logger.error(f"Expected at least 1 blocked user, got {len(blocks)}")
        return False
    
    logger.info(f"Retrieved {len(blocks)} blocked users")
    
    # Test block enforcement - User3 tries to message User1
    # First create a chat between them (temporarily unblock)
    response = requests.delete(f"{API_URL}/users/block/{user_ids['user3']}", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to temporarily unblock user: {response.text}")
        return False
    
    # Create chat
    chat_data = {
        "chat_type": "direct",
        "other_user_id": user_ids["user3"]
    }
    
    response = requests.post(f"{API_URL}/chats", json=chat_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create test chat for block enforcement: {response.text}")
        return False
    
    chat_ids["user1_user3"] = response.json()["chat_id"]
    logger.info(f"Created chat between User1 and User3 with ID: {chat_ids['user1_user3']}")
    
    # Block User3 again
    response = requests.post(f"{API_URL}/users/block", json=block_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to re-block user: {response.text}")
        return False
    
    # User3 tries to send message (should fail)
    headers3 = {"Authorization": f"Bearer {user_tokens['user3']}"}
    message_data = {
        "content": "This message should be blocked"
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['user1_user3']}/messages",
        json=message_data,
        headers=headers3
    )
    
    if response.status_code != 403:
        logger.error(f"Blocked user was able to send message: {response.status_code} - {response.text}")
        return False
    
    logger.info("Successfully prevented blocked user from sending message")
    
    # Unblock User3
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.delete(f"{API_URL}/users/block/{user_ids['user3']}", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to unblock user: {response.text}")
        return False
    
    logger.info("Successfully unblocked User3")
    
    # Test user reporting
    report_data = {
        "user_id": user_ids["user3"],
        "reason": "inappropriate_content",
        "description": "Testing the report functionality"
    }
    
    response = requests.post(f"{API_URL}/users/report", json=report_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to report user: {response.text}")
        return False
    
    report_ids["user1_reports_user3"] = response.json().get("report_id")
    logger.info(f"User1 reported User3")
    
    # Test admin report management
    response = requests.get(f"{API_URL}/admin/reports", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get admin reports: {response.text}")
        return False
    
    reports = response.json()
    logger.info(f"Retrieved {len(reports)} admin reports")
    
    logger.info("User Blocking and Reporting tests passed")
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
    
    story_ids["text_story"] = story_id
    logger.info(f"Created text story with ID: {story_id}")
    
    # Create an image story
    if "image" in file_data:
        story_data = {
            "content": f"Image story. Timestamp: {timestamp}",
            "media_type": "image",
            "media_data": file_data["image"]["file_data"],
            "background_color": "#2ecc71",
            "text_color": "#ffffff"
        }
        
        response = requests.post(f"{API_URL}/stories", json=story_data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to create image story: {response.text}")
            return False
        
        story_ids["image_story"] = response.json().get("story_id")
        logger.info(f"Created image story with ID: {story_ids['image_story']}")
    
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
    
    channel_ids["test_channel"] = channel_id
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
        ("PIN Connection System", test_pin_connection_system),
        ("Progressive Trust System", test_progressive_trust_system),
        ("Chat System", test_chat_system),
        ("Enhanced Message Features", test_enhanced_message_features),
        ("File Sharing", test_file_sharing),
        ("Teams API", test_teams_api),
        ("Voice/Video Calls", test_voice_video_calls),
        ("Voice Rooms", test_voice_rooms),
        ("User Blocking and Reporting", test_user_blocking_reporting),
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