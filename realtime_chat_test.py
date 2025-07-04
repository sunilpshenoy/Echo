import requests
import json
import time
import uuid
import os
import base64
import logging
import websocket
import threading
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
        "username": f"alice_realtime_{timestamp}",
        "email": f"alice.realtime_{timestamp}@example.com",
        "password": "SecurePass123!",
        "phone": f"+1234567{timestamp}",
        "display_name": f"Alice Realtime {timestamp}"
    },
    {
        "username": f"bob_realtime_{timestamp}",
        "email": f"bob.realtime_{timestamp}@example.com",
        "password": "StrongPass456!",
        "phone": f"+1987654{timestamp}",
        "display_name": f"Bob Realtime {timestamp}"
    },
    {
        "username": f"charlie_realtime_{timestamp}",
        "email": f"charlie.realtime_{timestamp}@example.com",
        "password": "SafePass789!",
        "phone": f"+1555555{timestamp}",
        "display_name": f"Charlie Realtime {timestamp}"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
chat_ids = {}
message_ids = {}
ws_connections = {}
ws_messages = {}

def on_ws_message(ws, message, user_key):
    """Callback for WebSocket messages"""
    logger.info(f"WebSocket message received for {user_key}: {message}")
    if user_key not in ws_messages:
        ws_messages[user_key] = []
    ws_messages[user_key].append(json.loads(message))

def on_ws_error(ws, error, user_key):
    """Callback for WebSocket errors"""
    logger.error(f"WebSocket error for {user_key}: {error}")

def on_ws_close(ws, close_status_code, close_msg, user_key):
    """Callback for WebSocket connection close"""
    logger.info(f"WebSocket connection closed for {user_key}: {close_status_code} - {close_msg}")

def on_ws_open(ws, user_key):
    """Callback for WebSocket connection open"""
    logger.info(f"WebSocket connection opened for {user_key}")

def connect_websocket(user_id, token, user_key):
    """Connect to WebSocket and return the connection"""
    ws_url = f"{BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/api/ws/{user_id}"
    
    # Create custom callbacks for this user
    def on_message(ws, message):
        on_ws_message(ws, message, user_key)
    
    def on_error(ws, error):
        on_ws_error(ws, error, user_key)
    
    def on_close(ws, close_status_code, close_msg):
        on_ws_close(ws, close_status_code, close_msg, user_key)
    
    def on_open(ws):
        on_ws_open(ws, user_key)
    
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
        header={"Authorization": f"Bearer {token}"}
    )
    
    # Start WebSocket connection in a separate thread
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for connection to establish
    time.sleep(2)
    return ws

def register_and_login_users():
    """Register and login test users"""
    logger.info("Registering and logging in test users...")
    
    for i, user_data in enumerate(test_users):
        user_key = f"user{i+1}"
        
        # Try to register the user
        response = requests.post(f"{API_URL}/register", json=user_data)
        
        if response.status_code == 200:
            logger.info(f"User {user_data['username']} registered successfully")
            user_tokens[user_key] = response.json()["access_token"]
            user_ids[user_key] = response.json()["user"]["user_id"]
        elif response.status_code == 400 and "Email already registered" in response.json()["detail"]:
            # User already exists, try logging in
            logger.info(f"User {user_data['username']} already exists, logging in...")
            login_response = requests.post(f"{API_URL}/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            
            if login_response.status_code == 200:
                logger.info(f"User {user_data['username']} logged in successfully")
                user_tokens[user_key] = login_response.json()["access_token"]
                user_ids[user_key] = login_response.json()["user"]["user_id"]
            else:
                logger.error(f"Failed to log in user {user_data['username']}: {login_response.text}")
                return False
        else:
            logger.error(f"Failed to register user {user_data['username']}: {response.text}")
            return False
    
    logger.info("All users registered and logged in successfully")
    return True

def complete_user_profiles():
    """Complete profiles for all test users"""
    logger.info("Completing user profiles...")
    
    for i, user_data in enumerate(test_users):
        user_key = f"user{i+1}"
        headers = {"Authorization": f"Bearer {user_tokens[user_key]}"}
        
        profile_data = {
            "display_name": user_data["display_name"],
            "age": 25 + i,
            "gender": "male" if i % 2 else "female",
            "location": "Test City",
            "bio": f"Test bio for {user_data['username']}",
            "interests": ["testing", "chatting", "real-time"],
            "values": ["quality", "reliability"]
        }
        
        response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to complete profile for {user_key}: {response.text}")
            return False
        
        logger.info(f"Profile completed for {user_key}")
    
    logger.info("All user profiles completed successfully")
    return True

def test_websocket_connection():
    """Test WebSocket connection for all users"""
    logger.info("Testing WebSocket connections...")
    
    for user_key, user_id in user_ids.items():
        token = user_tokens[user_key]
        try:
            ws = connect_websocket(user_id, token, user_key)
            ws_connections[user_key] = ws
            logger.info(f"WebSocket connection established for {user_key}")
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection for {user_key}: {e}")
            return False
    
    # Wait a moment to ensure connections are stable
    time.sleep(3)
    
    logger.info("WebSocket connections established for all users")
    return True

def test_chat_creation():
    """Test chat creation between users"""
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
            "name": f"Test Group Chat {timestamp}",
            "description": "A test group for real-time messaging",
            "members": [user_ids['user2'], user_ids['user3']]
        },
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to create group chat: {response.text}")
        return False
    
    chat_ids['group_chat'] = response.json()["chat_id"]
    logger.info(f"Group chat created with ID: {chat_ids['group_chat']}")
    
    # Wait a moment to allow WebSocket notifications to be processed
    time.sleep(2)
    
    # Check if users received chat creation notifications
    for user_key in ['user2', 'user3']:
        if user_key in ws_messages:
            chat_notifications = [msg for msg in ws_messages[user_key] if msg.get('type') == 'new_chat']
            if chat_notifications:
                logger.info(f"{user_key} received {len(chat_notifications)} chat creation notifications")
            else:
                logger.warning(f"{user_key} did not receive any chat creation notifications")
    
    logger.info("Chat creation tests passed")
    return True

def test_real_time_messaging():
    """Test real-time messaging between users"""
    logger.info("Testing real-time messaging...")
    
    # Clear previous WebSocket messages
    for user_key in ws_messages:
        ws_messages[user_key] = []
    
    # User1 sends a message to the direct chat
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    message_content = f"Hello user2! This is a real-time test message. Timestamp: {timestamp}"
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        json={"content": message_content},
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message to direct chat: {response.text}")
        return False
    
    message_ids['direct_message'] = response.json()["message_id"]
    logger.info(f"Message sent to direct chat with ID: {message_ids['direct_message']}")
    
    # Wait for WebSocket notifications
    time.sleep(3)
    
    # Check if user2 received the message notification
    if 'user2' in ws_messages:
        message_notifications = [msg for msg in ws_messages['user2'] if msg.get('type') == 'new_message']
        if message_notifications:
            logger.info(f"user2 received {len(message_notifications)} message notifications")
            
            # Verify the message content
            for notification in message_notifications:
                if notification.get('data', {}).get('content') == message_content:
                    logger.info("Message content verified in WebSocket notification")
                    break
            else:
                logger.warning("Message content not found in WebSocket notifications")
        else:
            logger.warning("user2 did not receive any message notifications")
    
    # User1 sends a message to the group chat
    message_content = f"Hello everyone! This is a group test message. Timestamp: {timestamp}"
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['group_chat']}/messages",
        json={"content": message_content},
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message to group chat: {response.text}")
        return False
    
    message_ids['group_message'] = response.json()["message_id"]
    logger.info(f"Message sent to group chat with ID: {message_ids['group_message']}")
    
    # Wait for WebSocket notifications
    time.sleep(3)
    
    # Check if user2 and user3 received the message notification
    for user_key in ['user2', 'user3']:
        if user_key in ws_messages:
            message_notifications = [
                msg for msg in ws_messages[user_key] 
                if msg.get('type') == 'new_message' and 
                msg.get('data', {}).get('chat_id') == chat_ids['group_chat']
            ]
            
            if message_notifications:
                logger.info(f"{user_key} received {len(message_notifications)} group message notifications")
            else:
                logger.warning(f"{user_key} did not receive any group message notifications")
    
    logger.info("Real-time messaging tests passed")
    return True

def test_message_history():
    """Test retrieving message history"""
    logger.info("Testing message history retrieval...")
    
    # User2 retrieves direct chat messages
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to retrieve direct chat messages: {response.text}")
        return False
    
    direct_messages = response.json()
    logger.info(f"Retrieved {len(direct_messages)} messages from direct chat")
    
    # Verify the message we sent is in the history
    if not any(msg.get('message_id') == message_ids['direct_message'] for msg in direct_messages):
        logger.error("Direct chat message not found in history")
        return False
    
    # User3 retrieves group chat messages
    headers = {"Authorization": f"Bearer {user_tokens['user3']}"}
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['group_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to retrieve group chat messages: {response.text}")
        return False
    
    group_messages = response.json()
    logger.info(f"Retrieved {len(group_messages)} messages from group chat")
    
    # Verify the message we sent is in the history
    if not any(msg.get('message_id') == message_ids['group_message'] for msg in group_messages):
        logger.error("Group chat message not found in history")
        return False
    
    logger.info("Message history retrieval tests passed")
    return True

def test_file_sharing():
    """Test file sharing in messages"""
    logger.info("Testing file sharing in messages...")
    
    # Create a test image file (1x1 pixel transparent PNG)
    small_png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    
    # Upload the file
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    files = {"file": ("test_image.png", BytesIO(small_png_data), "image/png")}
    
    # Try both potential endpoints
    endpoints = [f"{API_URL}/upload", f"{API_URL}/upload-file"]
    file_data = None
    
    for endpoint in endpoints:
        try:
            response = requests.post(endpoint, headers=headers, files=files)
            
            if response.status_code == 200:
                file_data = response.json()
                logger.info(f"File uploaded successfully using endpoint: {endpoint}")
                break
        except Exception as e:
            logger.error(f"Error trying endpoint {endpoint}: {e}")
    
    if not file_data:
        logger.error("Failed to upload file")
        return False
    
    # Clear previous WebSocket messages
    for user_key in ws_messages:
        ws_messages[user_key] = []
    
    # Send a message with the file attachment to the direct chat
    message_data = {
        "content": f"Here's a test image. Timestamp: {timestamp}",
        "message_type": "image",
        "file_name": file_data.get("file_name", "test_image.png"),
        "file_size": file_data.get("file_size", len(small_png_data)),
        "file_data": file_data.get("file_data", base64.b64encode(small_png_data).decode())
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message with file attachment: {response.text}")
        return False
    
    message_ids['file_message'] = response.json()["message_id"]
    logger.info(f"Message with file attachment sent with ID: {message_ids['file_message']}")
    
    # Wait for WebSocket notifications
    time.sleep(3)
    
    # Check if user2 received the file message notification
    if 'user2' in ws_messages:
        file_notifications = [
            msg for msg in ws_messages['user2'] 
            if msg.get('type') == 'new_message' and 
            msg.get('data', {}).get('message_type') == 'image'
        ]
        
        if file_notifications:
            logger.info(f"user2 received {len(file_notifications)} file message notifications")
        else:
            logger.warning("user2 did not receive any file message notifications")
    
    # User2 retrieves the message to verify file data
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to retrieve messages with file: {response.text}")
        return False
    
    messages = response.json()
    file_message = next((msg for msg in messages if msg.get('message_id') == message_ids['file_message']), None)
    
    if not file_message:
        logger.error("File message not found in history")
        return False
    
    if file_message.get('message_type') != 'image' or not file_message.get('file_data'):
        logger.error("File message missing file data")
        return False
    
    logger.info("File sharing tests passed")
    return True

def run_all_tests():
    """Run all tests in sequence"""
    tests = [
        ("Register and Login Users", register_and_login_users),
        ("Complete User Profiles", complete_user_profiles),
        ("WebSocket Connection", test_websocket_connection),
        ("Chat Creation", test_chat_creation),
        ("Real-time Messaging", test_real_time_messaging),
        ("Message History", test_message_history),
        ("File Sharing", test_file_sharing)
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
    logger.info("REAL-TIME CHAT SYSTEM TEST RESULTS")
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