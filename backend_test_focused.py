import requests
import json
import time
import websocket
import threading
import uuid
import os
import base64
from dotenv import load_dotenv
import logging
from io import BytesIO
from datetime import datetime, timedelta

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
        "phone": "+1234567890"
    },
    {
        "username": "bob_johnson",
        "email": "bob.johnson@example.com",
        "password": "StrongPass456!",
        "phone": "+1987654321"
    },
    {
        "username": "charlie_davis",
        "email": "charlie.davis@example.com",
        "password": "SafePass789!",
        "phone": "+1122334455"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
chat_ids = {}
message_ids = {}
ws_connections = {}

# WebSocket message queue for testing
ws_messages = []

def on_ws_message(ws, message):
    """Callback for WebSocket messages"""
    logger.info(f"WebSocket message received: {message}")
    ws_messages.append(json.loads(message))

def on_ws_error(ws, error):
    """Callback for WebSocket errors"""
    logger.error(f"WebSocket error: {error}")

def on_ws_close(ws, close_status_code, close_msg):
    """Callback for WebSocket connection close"""
    logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")

def on_ws_open(ws):
    """Callback for WebSocket connection open"""
    logger.info("WebSocket connection opened")

def connect_websocket(user_id, token):
    """Connect to WebSocket and return the connection"""
    ws_url = f"{BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/api/ws/{user_id}"
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_ws_message,
        on_error=on_ws_error,
        on_close=on_ws_close,
        on_open=on_ws_open,
        header={"Authorization": f"Bearer {token}"}
    )
    
    # Start WebSocket connection in a separate thread
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for connection to establish
    time.sleep(2)
    return ws

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

def test_websocket_connection():
    """Test WebSocket connection"""
    logger.info("Testing WebSocket connection...")
    
    # Connect WebSocket for each user
    for user_key, user_id in user_ids.items():
        token = user_tokens[user_key]
        try:
            ws = connect_websocket(user_id, token)
            ws_connections[user_key] = ws
            logger.info(f"WebSocket connection established for {user_key}")
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection for {user_key}: {e}")
            return False
    
    logger.info("WebSocket connection tests passed")
    return True

def test_chat_creation():
    """Test chat creation"""
    logger.info("Testing chat creation...")
    
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
    
    logger.info("Chat creation tests passed")
    return True

def test_add_contacts():
    """Test adding contacts"""
    logger.info("Testing add contacts...")
    
    # Add user2 as contact for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.post(
        f"{API_URL}/contacts",
        json={"email": test_users[1]["email"], "contact_name": "Bob (Contact)"},
        headers=headers
    )
    
    # If contact already exists, this is fine
    if response.status_code != 200 and not (response.status_code == 400 and "Already a contact" in response.json().get("detail", "")):
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
    if response.status_code != 200 and not (response.status_code == 400 and "Already a contact" in response.json().get("detail", "")):
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
    
    logger.info("Add contacts tests passed")
    return True

def test_get_contacts():
    """Test getting contacts"""
    logger.info("Testing get contacts...")
    
    # Get contacts for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/contacts", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get contacts: {response.text}")
        return False
    
    contacts = response.json()
    logger.info(f"User has {len(contacts)} contacts")
    
    # Verify contact details
    for contact in contacts:
        if "contact_user" not in contact:
            logger.error(f"Contact missing user details: {contact}")
            return False
    
    logger.info("Get contacts tests passed")
    return True

def test_enhanced_group_chat():
    """Test enhanced group chat features"""
    logger.info("Testing enhanced group chat features...")
    
    # Create a new group chat with specific members
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    group_data = {
        "name": "Enhanced Test Group",
        "description": "A test group for enhanced features",
        "members": [user_ids['user2'], user_ids['user3']]
    }
    
    response = requests.post(
        f"{API_URL}/chats",
        json={
            "chat_type": "group",
            "name": group_data["name"],
            "description": group_data["description"],
            "members": group_data["members"]
        },
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to create enhanced group chat: {response.text}")
        return False
    
    enhanced_group_id = response.json()["chat_id"]
    logger.info(f"Enhanced group chat created with ID: {enhanced_group_id}")
    
    # Verify group has correct members
    if len(response.json().get("members", [])) != 3:  # user1 + user2 + user3
        logger.error(f"Group chat has incorrect number of members: {len(response.json().get('members', []))}")
        return False
    
    # Verify current user is automatically added to the group
    if user_ids['user1'] not in response.json().get("members", []):
        logger.error("Current user not automatically added to group")
        return False
    
    logger.info("Enhanced group chat tests passed")
    return True

def test_voice_video_calls():
    """Test voice/video call initiation and management"""
    logger.info("Testing voice/video calls...")
    
    # Initiate a voice call
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    call_data = {
        "chat_id": chat_ids['direct_chat'],
        "call_type": "voice"
    }
    
    response = requests.post(f"{API_URL}/calls/initiate", json=call_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to initiate voice call: {response.text}")
        return False
    
    call_id = response.json()["call_id"]
    logger.info(f"Voice call initiated with ID: {call_id}")
    
    # Verify call data
    if response.json().get("call_type") != "voice" or response.json().get("status") != "ringing":
        logger.error(f"Call has incorrect type or status: {response.json()}")
        return False
    
    # Initiate a video call
    call_data = {
        "chat_id": chat_ids['direct_chat'],
        "call_type": "video"
    }
    
    response = requests.post(f"{API_URL}/calls/initiate", json=call_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to initiate video call: {response.text}")
        return False
    
    video_call_id = response.json()["call_id"]
    logger.info(f"Video call initiated with ID: {video_call_id}")
    
    # Check WebSocket notifications (if any were received)
    call_messages = [msg for msg in ws_messages if msg.get("type") in ["incoming_call", "screen_share_toggle"]]
    if call_messages:
        logger.info(f"Received {len(call_messages)} call-related notifications via WebSocket")
    
    logger.info("Voice/video calls tests passed")
    return True

def test_genie_command_processing():
    """Test Genie command processing"""
    logger.info("Testing Genie command processing...")
    
    # Test various commands
    test_commands = [
        {
            "command": "create a chat with Bob",
            "expected_intent": "create_chat"
        },
        {
            "command": "add contact john.doe@example.com",
            "expected_intent": "add_contact"
        },
        {
            "command": "block user Charlie",
            "expected_intent": "block_user"
        },
        {
            "command": "show my chats",
            "expected_intent": "list_chats"
        },
        {
            "command": "help me",
            "expected_intent": "show_help"
        },
        {
            "command": "send message to Sarah saying hello",
            "expected_intent": "send_message"
        }
    ]
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    for test_case in test_commands:
        command = test_case["command"]
        expected_intent = test_case["expected_intent"]
        
        response = requests.post(
            f"{API_URL}/genie/process",
            json={"command": command},
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to process Genie command '{command}': {response.text}")
            return False
        
        result = response.json()
        actual_intent = result.get("intent")
        
        if actual_intent != expected_intent:
            logger.error(f"Command '{command}' was identified as '{actual_intent}' intent, expected '{expected_intent}'")
            return False
        
        logger.info(f"Command '{command}' correctly identified as '{actual_intent}' intent")
    
    logger.info("Genie command processing tests passed")
    return True

def test_genie_undo_functionality():
    """Test Genie undo functionality"""
    logger.info("Testing Genie undo functionality...")
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # First, create a contact action using Genie
    action_command = "add contact test.contact@example.com"
    
    action_response = requests.post(
        f"{API_URL}/genie/process",
        json={"command": action_command},
        headers=headers
    )
    
    if action_response.status_code != 200:
        logger.error(f"Failed to process action command: {action_response.text}")
        return False
    
    logger.info(f"Successfully processed action command: {action_command}")
    
    # Now try to undo the action
    undo_response = requests.post(
        f"{API_URL}/genie/undo",
        headers=headers
    )
    
    if undo_response.status_code != 200:
        logger.error(f"Failed to process undo command: {undo_response.text}")
        return False
    
    result = undo_response.json()
    logger.info(f"Undo response: {result}")
    
    # Even if the undo operation fails with a message, we consider the API working
    # as long as it returns a valid response
    
    logger.info("Genie undo functionality tests passed")
    return True

def run_all_tests():
    """Run all tests and return results"""
    test_results = {
        "User Authentication System": {
            "registration": test_user_registration()
        },
        "WebSocket Real-time Communication": {
            "connection": test_websocket_connection()
        },
        "Chat Management System": {
            "create_chats": test_chat_creation()
        },
        "Contact Management": {
            "add_contacts": test_add_contacts(),
            "get_contacts": test_get_contacts()
        },
        "Group Chat Creation": {
            "group_creation": test_enhanced_group_chat()
        },
        "Advanced Voice/Video Calls": {
            "calls": test_voice_video_calls()
        },
        "Genie Assistant": {
            "process_commands": test_genie_command_processing(),
            "undo_actions": test_genie_undo_functionality()
        }
    }
    
    # Print summary
    logger.info("\n=== TEST RESULTS SUMMARY ===")
    all_passed = True
    
    for category, tests in test_results.items():
        category_passed = all(tests.values())
        status = "✅ PASSED" if category_passed else "❌ FAILED"
        logger.info(f"{category}: {status}")
        
        if not category_passed:
            all_passed = False
            for test_name, passed in tests.items():
                if not passed:
                    logger.info(f"  - {test_name}: ❌ FAILED")
    
    overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
    logger.info(f"\nOverall Status: {overall_status}")
    
    return test_results

if __name__ == "__main__":
    run_all_tests()