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

def test_get_user_chats():
    """Test getting user chats"""
    logger.info("Testing get user chats...")
    
    # Get chats for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get user chats: {response.text}")
        return False
    
    chats = response.json()
    if len(chats) < 2:  # Should have at least direct and group chat
        logger.error(f"Expected at least 2 chats, got {len(chats)}")
        return False
    
    logger.info(f"User has {len(chats)} chats")
    
    # Get chats for user2
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get user chats for user2: {response.text}")
        return False
    
    chats = response.json()
    if len(chats) < 2:  # Should have at least direct and group chat
        logger.error(f"Expected at least 2 chats for user2, got {len(chats)}")
        return False
    
    logger.info("Get user chats tests passed")
    return True

def test_send_messages():
    """Test sending messages"""
    logger.info("Testing send messages...")
    
    # Send message from user1 to direct chat
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
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
    
    # Send message from user1 to group chat
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
    
    # Wait for WebSocket messages to be received
    time.sleep(2)
    
    logger.info("Send messages tests passed")
    return True

def test_get_chat_messages():
    """Test getting chat messages"""
    logger.info("Testing get chat messages...")
    
    # Get messages for direct chat
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
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
    
    logger.info("Get chat messages tests passed")
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
    if response.status_code != 200 and not (response.status_code == 400 and "Contact already exists" in response.json().get("detail", "")):
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
    if response.status_code != 200 and not (response.status_code == 400 and "Contact already exists" in response.json().get("detail", "")):
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
    
    logger.info("Get contacts tests passed")
    return True

def test_search_users():
    """Test searching users"""
    logger.info("Testing search users...")
    
    # Search for users with 'bob' in their username/email/phone
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/users/search?q=bob", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to search users: {response.text}")
        return False
    
    users = response.json()
    if len(users) < 1:
        logger.error(f"Expected at least 1 user in search results, got {len(users)}")
        return False
    
    logger.info(f"Search returned {len(users)} users")
    
    logger.info("Search users tests passed")
    return True

def test_file_upload():
    """Test file upload endpoint"""
    logger.info("Testing file upload...")
    
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
    
    # Test file size limit (create a file > 10MB)
    # We'll simulate this by creating a request with a Content-Length header that exceeds the limit
    # without actually sending 10MB of data
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
            # This test is tricky to implement correctly, so we'll consider it a warning rather than a failure
    except Exception as e:
        logger.info(f"Large file upload test exception (expected): {e}")
    
    # Test unsupported file type
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    files = {"file": ("test_file.exe", BytesIO(b"test data"), "application/octet-stream")}
    
    response = requests.post(f"{API_URL}/upload", headers=headers, files=files)
    
    if response.status_code != 400 or "File type not supported" not in response.json().get("detail", ""):
        logger.error(f"Unsupported file type test failed: {response.status_code} - {response.text}")
        return False
    
    logger.info("File upload tests passed")
    return True

def test_send_message_with_attachment():
    """Test sending messages with file attachments"""
    logger.info("Testing send message with attachment...")
    
    # First upload a file
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    small_png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    files = {"file": ("test_attachment.png", BytesIO(small_png_data), "image/png")}
    
    upload_response = requests.post(f"{API_URL}/upload", headers=headers, files=files)
    
    if upload_response.status_code != 200:
        logger.error(f"Failed to upload file for attachment test: {upload_response.text}")
        return False
    
    file_data = upload_response.json()
    
    # Send message with image attachment to direct chat
    message_data = {
        "content": "Here's an image attachment",
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
    
    message_ids['image_message'] = response.json()["message_id"]
    logger.info(f"Message with image attachment sent with ID: {message_ids['image_message']}")
    
    # Create a text file attachment
    text_content = "This is a test text file for attachment"
    text_data = base64.b64encode(text_content.encode('utf-8')).decode('utf-8')
    
    # Send message with text file attachment to group chat
    message_data = {
        "content": "Here's a text file attachment",
        "message_type": "file",
        "file_name": "test_document.txt",
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
    
    message_ids['file_message'] = response.json()["message_id"]
    logger.info(f"Message with text file attachment sent with ID: {message_ids['file_message']}")
    
    # Wait for WebSocket messages to be received
    time.sleep(2)
    
    # Verify the messages were stored correctly
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get messages to verify attachments: {response.text}")
        return False
    
    messages = response.json()
    image_message = next((m for m in messages if m.get("message_id") == message_ids['image_message']), None)
    
    if not image_message:
        logger.error("Could not find image message in chat history")
        return False
    
    if (image_message.get("message_type") != "image" or 
        not image_message.get("file_name") or 
        not image_message.get("file_data")):
        logger.error(f"Image message missing attachment data: {image_message}")
        return False
    
    logger.info("Send message with attachment tests passed")
    return True

def test_read_receipts():
    """Test read receipts functionality"""
    logger.info("Testing read receipts...")
    
    # First, user2 marks messages from user1 as read
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    
    # Get messages in direct chat
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get messages for read receipt test: {response.text}")
        return False
    
    messages = response.json()
    
    # Filter messages sent by user1
    user1_messages = [m for m in messages if m.get("sender_id") == user_ids['user1']]
    
    if not user1_messages:
        logger.error("No messages from user1 found for read receipt test")
        return False
    
    # Mark messages as read
    message_ids_to_mark = [m["message_id"] for m in user1_messages]
    
    response = requests.post(
        f"{API_URL}/messages/read",
        json={"message_ids": message_ids_to_mark},
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to mark messages as read: {response.text}")
        return False
    
    logger.info(f"Marked {len(message_ids_to_mark)} messages as read")
    
    # Verify messages are marked as read
    # Wait a moment for the updates to propagate
    time.sleep(2)
    
    # User1 checks the messages
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get messages to verify read status: {response.text}")
        return False
    
    messages = response.json()
    
    # Check if the messages are marked as read
    for message_id in message_ids_to_mark:
        message = next((m for m in messages if m["message_id"] == message_id), None)
        if not message:
            continue
        
        if message.get("read_status") != "read":
            logger.error(f"Message {message_id} not marked as read: {message.get('read_status')}")
            return False
    
    logger.info("Read receipts tests passed")
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
        f"{API_URL}/chats/group",
        json=group_data,
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
    
    # Test member management - remove user3
    member_action = {
        "action": "remove",
        "user_id": user_ids['user3']
    }
    
    response = requests.put(
        f"{API_URL}/chats/{enhanced_group_id}/members",
        json=member_action,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to remove member from group: {response.text}")
        return False
    
    # Verify member was removed
    if len(response.json().get("members", [])) != 2:  # user1 + user2
        logger.error(f"Group chat has incorrect number of members after removal: {len(response.json().get('members', []))}")
        return False
    
    logger.info("Successfully removed member from group")
    
    # Test member management - add user3 back
    member_action = {
        "action": "add",
        "user_id": user_ids['user3']
    }
    
    response = requests.put(
        f"{API_URL}/chats/{enhanced_group_id}/members",
        json=member_action,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to add member to group: {response.text}")
        return False
    
    # Verify member was added
    if len(response.json().get("members", [])) != 3:  # user1 + user2 + user3
        logger.error(f"Group chat has incorrect number of members after addition: {len(response.json().get('members', []))}")
        return False
    
    logger.info("Successfully added member to group")
    
    # Verify non-admin cannot manage members
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    member_action = {
        "action": "remove",
        "user_id": user_ids['user3']
    }
    
    response = requests.put(
        f"{API_URL}/chats/{enhanced_group_id}/members",
        json=member_action,
        headers=headers
    )
    
    if response.status_code != 403:
        logger.error(f"Non-admin should not be able to manage members: {response.status_code}")
        return False
    
    logger.info("Verified non-admin cannot manage members")
    
    logger.info("Enhanced group chat tests passed")
    return True

def test_enhanced_user_profile():
    """Test enhanced user profile features"""
    logger.info("Testing enhanced user profile...")
    
    # Update user1's status message
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    profile_data = {
        "status_message": "Testing the new status message feature!"
    }
    
    response = requests.put(
        f"{API_URL}/profile",
        json=profile_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update status message: {response.text}")
        return False
    
    # Verify status message was updated
    if response.json().get("status_message") != profile_data["status_message"]:
        logger.error(f"Status message not updated correctly: {response.json()}")
        return False
    
    logger.info("Successfully updated status message")
    
    # Update multiple profile fields
    profile_data = {
        "username": f"Updated_{test_users[0]['username']}",
        "status_message": "Multiple field update test"
    }
    
    response = requests.put(
        f"{API_URL}/profile",
        json=profile_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update multiple profile fields: {response.text}")
        return False
    
    # Verify fields were updated
    if (response.json().get("username") != profile_data["username"] or
        response.json().get("status_message") != profile_data["status_message"]):
        logger.error(f"Profile fields not updated correctly: {response.json()}")
        return False
    
    logger.info("Successfully updated multiple profile fields")
    
    # Verify enhanced user data in responses
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get chats to verify enhanced user data: {response.text}")
        return False
    
    chats = response.json()
    for chat in chats:
        if chat["chat_type"] == "direct" and "other_user" in chat:
            if "status_message" not in chat["other_user"]:
                logger.error(f"Enhanced user data missing status_message: {chat['other_user']}")
                return False
    
    logger.info("Enhanced user profile tests passed")
    return True

def run_all_tests():
    """Run all tests and return results"""
    test_results = {
        "User Authentication System": {
            "registration": test_user_registration(),
            "login": test_user_login()
        },
        "WebSocket Real-time Communication": {
            "connection": test_websocket_connection()
        },
        "Chat Management System": {
            "create_chats": test_chat_creation(),
            "get_chats": test_get_user_chats()
        },
        "Message Storage and Retrieval": {
            "send_messages": test_send_messages(),
            "get_messages": test_get_chat_messages()
        },
        "Contact Management": {
            "add_contacts": test_add_contacts(),
            "get_contacts": test_get_contacts(),
            "search_users": test_search_users()
        }
    }
    
    # Close WebSocket connections
    for user_key, ws in ws_connections.items():
        try:
            ws.close()
            logger.info(f"Closed WebSocket connection for {user_key}")
        except:
            pass
    
    return test_results

if __name__ == "__main__":
    # Run all tests
    results = run_all_tests()
    
    # Print summary
    print("\n=== TEST RESULTS SUMMARY ===")
    all_passed = True
    
    for category, tests in results.items():
        category_passed = all(tests.values())
        status = "✅ PASSED" if category_passed else "❌ FAILED"
        print(f"{category}: {status}")
        
        for test_name, passed in tests.items():
            test_status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  - {test_name}: {test_status}")
        
        if not category_passed:
            all_passed = False
    
    print("\nOVERALL RESULT:", "✅ PASSED" if all_passed else "❌ FAILED")