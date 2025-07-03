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
user_pins = {}
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

def test_user_authentication():
    """Test user registration, login, and token validation"""
    logger.info("Testing user authentication system...")
    
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
    
    # Test duplicate registration (should fail)
    response = requests.post(f"{API_URL}/register", json=test_users[0])
    if response.status_code != 400 or "Email already registered" not in response.json()["detail"]:
        logger.error("Duplicate registration test failed")
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
        
        # Verify profile_completed status is returned
        if "profile_completed" not in response.json()["user"]:
            logger.error(f"Login response missing profile_completed status")
            return False
    
    # Test invalid login credentials
    response = requests.post(f"{API_URL}/login", json={
        "email": "nonexistent@example.com",
        "password": "WrongPassword123"
    })
    
    if response.status_code != 401:
        logger.error("Invalid credentials test failed")
        return False
    
    # Test token validation with /api/users/me endpoint
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to validate token: {response.text}")
        return False
    
    user_data = response.json()
    required_fields = ["user_id", "username", "email", "profile_completed"]
    for field in required_fields:
        if field not in user_data:
            logger.error(f"User data missing required field: {field}")
            return False
    
    logger.info("User authentication system tests passed")
    return True

def test_profile_completion():
    """Test profile completion and PIN generation"""
    logger.info("Testing profile completion system...")
    
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
    
    user_pins["user2"] = response.json()["connection_pin"]
    logger.info(f"User2 connection PIN: {user_pins['user2']}")
    
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
    
    user_pins["user3"] = response.json()["connection_pin"]
    logger.info(f"User3 connection PIN: {user_pins['user3']}")
    
    # Test getting QR code for PIN
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
    
    logger.info("Profile completion system tests passed")
    return True

def test_contact_management():
    """Test contact management system"""
    logger.info("Testing contact management system...")
    
    # User1 adds User2 as contact by email
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
    
    # User1 adds User3 as contact by email
    contact_data = {
        "email": test_users[2]["email"],
        "contact_name": f"Charlie Contact {timestamp}"
    }
    
    response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to add second contact by email: {response.text}")
        return False
    
    logger.info("Successfully added second contact by email")
    
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
    
    # Test getting contacts
    response = requests.get(f"{API_URL}/contacts", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get contacts: {response.text}")
        return False
    
    contacts = response.json()
    if len(contacts) < 2:
        logger.error(f"Expected at least 2 contacts, got {len(contacts)}")
        return False
    
    logger.info(f"Successfully retrieved {len(contacts)} contacts")
    
    # Test deleting a contact
    if len(contacts) > 0:
        contact_id = contacts[0]["contact_id"]
        response = requests.delete(f"{API_URL}/contacts/{contact_id}", headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to delete contact: {response.text}")
            return False
        
        logger.info("Successfully deleted contact")
        
        # Verify contact was deleted
        response = requests.get(f"{API_URL}/contacts", headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get contacts after deletion: {response.text}")
            return False
        
        updated_contacts = response.json()
        if len(updated_contacts) != len(contacts) - 1:
            logger.error(f"Contact not deleted properly. Expected {len(contacts) - 1} contacts, got {len(updated_contacts)}")
            return False
        
        logger.info("Contact deletion verified")
    
    logger.info("Contact management system tests passed")
    return True

def test_pin_connection_system():
    """Test PIN-based connection system"""
    logger.info("Testing PIN-based connection system...")
    
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
    
    logger.info(f"Successfully retrieved {len(requests_list)} connection requests")
    
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
    
    logger.info(f"Successfully retrieved {len(connections_list)} connections")
    
    logger.info("PIN-based connection system tests passed")
    return True

def test_progressive_trust_system():
    """Test progressive trust system"""
    logger.info("Testing progressive trust system...")
    
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
    
    # Test authenticity rating system
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
    
    logger.info("Progressive trust system tests passed")
    return True

def test_chat_system():
    """Test chat system"""
    logger.info("Testing chat system...")
    
    # Get chats for User1
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
    
    # Create a group chat
    group_data = {
        "chat_type": "group",
        "name": f"Test Group {timestamp}",
        "description": "A test group chat",
        "members": [user_ids["user2"]]  # User1 will be added automatically
    }
    
    response = requests.post(f"{API_URL}/chats", json=group_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create group chat: {response.text}")
        return False
    
    chat_ids["group_chat"] = response.json()["chat_id"]
    logger.info(f"Created group chat with ID: {chat_ids['group_chat']}")
    
    # Send a message to direct chat
    message_data = {
        "content": f"Hello Bob! This is a test message from Alice. Timestamp: {timestamp}"
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message to direct chat: {response.text}")
        return False
    
    message_ids["user1_to_user2"] = response.json()["message_id"]
    logger.info(f"Sent message to direct chat with ID: {message_ids['user1_to_user2']}")
    
    # Send a message to group chat
    message_data = {
        "content": f"Hello everyone! This is a test message to the group. Timestamp: {timestamp}"
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['group_chat']}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message to group chat: {response.text}")
        return False
    
    message_ids["user1_to_group"] = response.json()["message_id"]
    logger.info(f"Sent message to group chat with ID: {message_ids['user1_to_group']}")
    
    # User2 sends a message to direct chat
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
    logger.info(f"User2 sent message with ID: {message_ids['user2_to_user1']}")
    
    # Get messages from direct chat
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get messages from direct chat: {response.text}")
        return False
    
    messages = response.json()
    if len(messages) < 2:  # Should have at least 2 messages
        logger.error(f"Expected at least 2 messages in direct chat, got {len(messages)}")
        return False
    
    logger.info(f"Retrieved {len(messages)} messages from direct chat")
    
    # Test read receipts
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    read_data = {
        "message_ids": [message_ids["user1_to_user2"]]
    }
    
    response = requests.post(f"{API_URL}/messages/read", json=read_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to mark message as read: {response.text}")
        return False
    
    logger.info("Successfully marked message as read")
    
    logger.info("Chat system tests passed")
    return True

def test_file_sharing():
    """Test file upload and sharing"""
    logger.info("Testing file sharing system...")
    
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
    message_data = {
        "content": f"Here's an image attachment. Timestamp: {timestamp}",
        "message_type": "image",
        "file_name": file_data["image"]["file_name"],
        "file_size": file_data["image"]["file_size"],
        "file_data": file_data["image"]["file_data"]
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/messages",
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
    files = {"file": (f"direct_upload_{timestamp}.png", BytesIO(small_png_data), "image/png")}
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/files",
        headers=headers,
        files=files
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to upload file directly to chat: {response.text}")
        return False
    
    logger.info("Successfully uploaded file directly to chat")
    
    logger.info("File sharing system tests passed")
    return True

def test_teams_api():
    """Test teams API"""
    logger.info("Testing teams API...")
    
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
    
    team_response = response.json()
    if "team_id" not in team_response:
        logger.error(f"Team creation response missing team_id: {team_response}")
        return False
    
    team_ids["test_team"] = team_response["team_id"]
    logger.info(f"Created team with ID: {team_ids['test_team']}")
    
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
    logger.info("Testing voice/video call APIs...")
    
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
    
    voice_room_ids["test_room"] = response.json()["room_id"]
    logger.info(f"Created voice room with ID: {voice_room_ids['test_room']}")
    
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
    response = requests.post(f"{API_URL}/voice/rooms/{voice_room_ids['test_room']}/join", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to join voice room: {response.text}")
        return False
    
    logger.info("Successfully joined voice room")
    
    # Initiate a voice call
    call_data = {
        "chat_id": chat_ids["user1_user2"],
        "call_type": "voice"
    }
    
    response = requests.post(f"{API_URL}/calls/initiate", json=call_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to initiate voice call: {response.text}")
        return False
    
    call_ids["voice_call"] = response.json()["call_id"]
    logger.info(f"Initiated voice call with ID: {call_ids['voice_call']}")
    
    # Initiate a video call
    call_data = {
        "chat_id": chat_ids["user1_user2"],
        "call_type": "video"
    }
    
    response = requests.post(f"{API_URL}/calls/initiate", json=call_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to initiate video call: {response.text}")
        return False
    
    call_ids["video_call"] = response.json()["call_id"]
    logger.info(f"Initiated video call with ID: {call_ids['video_call']}")
    
    # Test screen sharing
    response = requests.post(
        f"{API_URL}/calls/{call_ids['video_call']}/screen-share",
        params={"enable": "true"},
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to enable screen sharing: {response.text}")
        return False
    
    logger.info("Successfully enabled screen sharing")
    
    logger.info("Voice/video call APIs tests passed")
    return True

def test_user_blocking_reporting():
    """Test user blocking and reporting features"""
    logger.info("Testing user blocking and reporting features...")
    
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
    
    logger.info("User blocking and reporting features tests passed")
    return True

def test_enhanced_message_features():
    """Test enhanced message features"""
    logger.info("Testing enhanced message features...")
    
    # Test message reactions
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    reaction_data = {
        "message_id": message_ids["user2_to_user1"],
        "reaction": "👍"
    }
    
    response = requests.post(f"{API_URL}/messages/react", json=reaction_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to add reaction: {response.text}")
        return False
    
    logger.info("Successfully added reaction to message")
    
    # Test message editing
    edit_data = {
        "message_id": message_ids["user1_to_user2"],
        "content": f"This is an edited message. Original timestamp: {timestamp}"
    }
    
    response = requests.put(f"{API_URL}/messages/edit", json=edit_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to edit message: {response.text}")
        return False
    
    logger.info("Successfully edited message")
    
    # Test message deletion (soft delete)
    response = requests.delete(f"{API_URL}/messages/{message_ids['user1_to_group']}", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to delete message: {response.text}")
        return False
    
    logger.info("Successfully deleted message")
    
    # Test message reply
    reply_data = {
        "content": f"This is a reply to your message. Timestamp: {timestamp}",
        "reply_to": message_ids["user2_to_user1"]
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/messages",
        json=reply_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send reply message: {response.text}")
        return False
    
    message_ids["reply_message"] = response.json()["message_id"]
    logger.info(f"Sent reply message with ID: {message_ids['reply_message']}")
    
    logger.info("Enhanced message features tests passed")
    return True

def test_stories_feature():
    """Test stories feature"""
    logger.info("Testing stories feature...")
    
    # Create a story
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
    
    story_ids["text_story"] = response.json()["story_id"]
    logger.info(f"Created text story with ID: {story_ids['text_story']}")
    
    # Create an image story
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
    
    story_ids["image_story"] = response.json()["story_id"]
    logger.info(f"Created image story with ID: {story_ids['image_story']}")
    
    # Get stories
    response = requests.get(f"{API_URL}/stories", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get stories: {response.text}")
        return False
    
    stories = response.json()
    if len(stories) < 2:
        logger.error(f"Expected at least 2 stories, got {len(stories)}")
        return False
    
    logger.info(f"Retrieved {len(stories)} stories")
    
    # View a story (User2 views User1's story)
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.post(f"{API_URL}/stories/{story_ids['text_story']}/view", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to view story: {response.text}")
        return False
    
    logger.info("Successfully viewed story")
    
    # Get story viewers
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/stories/{story_ids['text_story']}/viewers", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get story viewers: {response.text}")
        return False
    
    viewers = response.json()
    if len(viewers) < 1:
        logger.error(f"Expected at least 1 viewer, got {len(viewers)}")
        return False
    
    logger.info(f"Retrieved {len(viewers)} story viewers")
    
    logger.info("Stories feature tests passed")
    return True

def test_channels_feature():
    """Test channels feature"""
    logger.info("Testing channels feature...")
    
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
    
    channel_ids["test_channel"] = response.json()["channel_id"]
    logger.info(f"Created channel with ID: {channel_ids['test_channel']}")
    
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
    response = requests.post(f"{API_URL}/channels/{channel_ids['test_channel']}/subscribe", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to subscribe to channel: {response.text}")
        return False
    
    logger.info("Successfully subscribed to channel")
    
    # Get channel subscribers
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/channels/{channel_ids['test_channel']}/subscribers", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get channel subscribers: {response.text}")
        return False
    
    subscribers = response.json()
    if len(subscribers) < 1:
        logger.error(f"Expected at least 1 subscriber, got {len(subscribers)}")
        return False
    
    logger.info(f"Retrieved {len(subscribers)} channel subscribers")
    
    # Post to channel
    post_data = {
        "content": f"This is a test channel post. Timestamp: {timestamp}"
    }
    
    response = requests.post(f"{API_URL}/channels/{channel_ids['test_channel']}/posts", json=post_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to post to channel: {response.text}")
        return False
    
    logger.info("Successfully posted to channel")
    
    # Get channel posts
    response = requests.get(f"{API_URL}/channels/{channel_ids['test_channel']}/posts", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get channel posts: {response.text}")
        return False
    
    posts = response.json()
    if len(posts) < 1:
        logger.error(f"Expected at least 1 post, got {len(posts)}")
        return False
    
    logger.info(f"Retrieved {len(posts)} channel posts")
    
    logger.info("Channels feature tests passed")
    return True

def test_genie_command_processing():
    """Test Genie command processing"""
    logger.info("Testing Genie command processing...")
    
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
    
    logger.info("Genie command processing tests passed")
    return True

def run_all_tests():
    """Run all tests in sequence"""
    tests = [
        ("User Authentication System", test_user_authentication),
        ("Profile Completion System", test_profile_completion),
        ("Contact Management System", test_contact_management),
        ("PIN-Based Connection System", test_pin_connection_system),
        ("Progressive Trust System", test_progressive_trust_system),
        ("Chat System", test_chat_system),
        ("File Sharing System", test_file_sharing),
        ("Teams API", test_teams_api),
        ("Voice/Video Call APIs", test_voice_video_calls),
        ("User Blocking and Reporting", test_user_blocking_reporting),
        ("Enhanced Message Features", test_enhanced_message_features),
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
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 80)
    logger.info(f"OVERALL RESULT: {'PASSED' if all_passed else 'FAILED'}")
    logger.info("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()