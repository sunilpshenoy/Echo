import requests
import json
import base64
import os
import time
import websocket
import threading
import uuid
from io import BytesIO
from PIL import Image

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"')
            break

API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test users
TEST_USER1 = {
    "username": "emoji_gif_test_user1",
    "email": "emoji_gif_test1@example.com",
    "password": "TestPassword123!"
}

TEST_USER2 = {
    "username": "emoji_gif_test_user2",
    "email": "emoji_gif_test2@example.com",
    "password": "TestPassword123!"
}

# Global variables to store test data
user1_token = None
user2_token = None
user1_id = None
user2_id = None
test_chat_id = None
test_message_id = None
test_gif_message_id = None
test_team_id = None
test_team_chat_id = None

# WebSocket client for real-time notifications
class WSClient:
    def __init__(self, user_id, token):
        self.user_id = user_id
        self.token = token
        self.ws = None
        self.connected = False
        self.messages = []
        self.thread = None

    def on_message(self, ws, message):
        print(f"WebSocket message received: {message}")
        self.messages.append(json.loads(message))

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        self.connected = False

    def on_open(self, ws):
        print(f"WebSocket connection opened for user {self.user_id}")
        self.connected = True

    def connect(self):
        ws_url = f"{BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/api/ws/{self.user_id}"
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
            header=[f"Authorization: Bearer {self.token}"]
        )
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.daemon = True
        self.thread.start()
        time.sleep(1)  # Give time for connection to establish

    def disconnect(self):
        if self.ws:
            self.ws.close()
            self.connected = False

    def wait_for_message(self, message_type, timeout=5):
        start_time = time.time()
        while time.time() - start_time < timeout:
            for msg in self.messages:
                if msg.get("type") == message_type:
                    return msg
            time.sleep(0.1)
        return None

    def clear_messages(self):
        self.messages = []

# Helper functions
def register_user(user_data):
    response = requests.post(f"{API_URL}/register", json=user_data)
    if response.status_code == 400 and "Email already registered" in response.text:
        # User already exists, try to login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        response = requests.post(f"{API_URL}/login", json=login_data)
    
    assert response.status_code == 200, f"Failed to register/login user: {response.text}"
    return response.json()

def create_direct_chat(token, other_user_id):
    headers = {"Authorization": f"Bearer {token}"}
    chat_data = {
        "chat_type": "direct",
        "other_user_id": other_user_id
    }
    response = requests.post(f"{API_URL}/chats", json=chat_data, headers=headers)
    assert response.status_code == 200, f"Failed to create chat: {response.text}"
    return response.json()

def send_message(token, chat_id, content):
    headers = {"Authorization": f"Bearer {token}"}
    message_data = {
        "content": content
    }
    response = requests.post(f"{API_URL}/chats/{chat_id}/messages", json=message_data, headers=headers)
    assert response.status_code == 200, f"Failed to send message: {response.text}"
    return response.json()

def create_test_image(size=(100, 100), color=(255, 0, 0), format='PNG'):
    """Create a test image for upload"""
    image = Image.new('RGB', size, color)
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer

def create_test_gif(size=(100, 100), frames=10):
    """Create a test animated GIF for upload"""
    frames = []
    for i in range(frames):
        # Create frames with different colors
        color = (i * 25 % 255, (i * 50) % 255, (i * 75) % 255)
        frame = Image.new('RGB', size, color)
        frames.append(frame)
    
    buffer = BytesIO()
    # Save as animated GIF
    frames[0].save(
        buffer, 
        format='GIF', 
        save_all=True, 
        append_images=frames[1:], 
        duration=100, 
        loop=0
    )
    buffer.seek(0)
    return buffer

def upload_file(token, file_buffer, filename, content_type):
    headers = {"Authorization": f"Bearer {token}"}
    files = {'file': (filename, file_buffer, content_type)}
    response = requests.post(f"{API_URL}/upload", headers=headers, files=files)
    assert response.status_code == 200, f"Failed to upload file: {response.text}"
    return response.json()

def send_message_with_file(token, chat_id, content, file_id):
    headers = {"Authorization": f"Bearer {token}"}
    message_data = {
        "content": content,
        "file_id": file_id
    }
    response = requests.post(f"{API_URL}/chats/{chat_id}/messages", json=message_data, headers=headers)
    assert response.status_code == 200, f"Failed to send message with file: {response.text}"
    return response.json()

def create_team(token, name, description, members):
    headers = {"Authorization": f"Bearer {token}"}
    team_data = {
        "name": name,
        "description": description,
        "members": members
    }
    response = requests.post(f"{API_URL}/teams", json=team_data, headers=headers)
    assert response.status_code == 200, f"Failed to create team: {response.text}"
    return response.json()

def send_team_message(token, team_id, content):
    headers = {"Authorization": f"Bearer {token}"}
    message_data = {
        "content": content
    }
    response = requests.post(f"{API_URL}/teams/{team_id}/messages", json=message_data, headers=headers)
    assert response.status_code == 200, f"Failed to send team message: {response.text}"
    return response.json()

def setup():
    global user1_token, user2_token, user1_id, user2_id, test_chat_id, ws_client1, ws_client2
    
    # Register/login test users
    print("Registering test users...")
    user1_data = register_user(TEST_USER1)
    user2_data = register_user(TEST_USER2)
    
    user1_token = user1_data["access_token"]
    user2_token = user2_data["access_token"]
    user1_id = user1_data["user"]["user_id"]
    user2_id = user2_data["user"]["user_id"]
    
    print(f"User 1 ID: {user1_id}")
    print(f"User 2 ID: {user2_id}")
    
    # Create a direct chat between the users
    print("Creating test chat...")
    chat_data = create_direct_chat(user1_token, user2_id)
    test_chat_id = chat_data["chat_id"]
    print(f"Test chat ID: {test_chat_id}")
    
    # Connect WebSocket clients
    print("Connecting WebSocket clients...")
    ws_client1 = WSClient(user1_id, user1_token)
    ws_client2 = WSClient(user2_id, user2_token)
    ws_client1.connect()
    ws_client2.connect()
    
    # Send a test message
    print("Sending test message...")
    message_data = send_message(user1_token, test_chat_id, "Test message for emoji reactions")
    global test_message_id
    test_message_id = message_data["message_id"]
    print(f"Test message ID: {test_message_id}")
    
    # Create a team for team chat testing
    print("Creating test team...")
    team_data = create_team(user1_token, f"Test Team {uuid.uuid4().hex[:8]}", "Test team for emoji and GIF testing", [user1_id, user2_id])
    global test_team_id, test_team_chat_id
    test_team_id = team_data["team_id"]
    test_team_chat_id = team_data.get("chat_id")
    
    # If chat_id is not directly provided, get team details to find it
    if not test_team_chat_id:
        headers = {"Authorization": f"Bearer {user1_token}"}
        response = requests.get(f"{API_URL}/teams/{test_team_id}", headers=headers)
        assert response.status_code == 200, f"Failed to get team details: {response.text}"
        team_details = response.json()
        test_team_chat_id = team_details.get("chat_id")
    
    print(f"Test team ID: {test_team_id}, Team chat ID: {test_team_chat_id}")

def test_emoji_reactions_websocket():
    print("\n=== Testing Emoji Reactions WebSocket Notifications ===")
    
    # Clear WebSocket messages
    ws_client1.clear_messages()
    ws_client2.clear_messages()
    
    # Test 1: Add emoji reaction and verify WebSocket notification
    print("Test 1: Adding emoji reaction and verifying WebSocket notification...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    reaction_data = {"emoji": "🎉"}
    
    response = requests.post(
        f"{API_URL}/messages/{test_message_id}/reactions", 
        json=reaction_data, 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to add reaction: {response.text}"
    
    # Check if WebSocket notification was sent to the other user
    ws_message = ws_client2.wait_for_message("reaction_added")
    assert ws_message is not None, "WebSocket notification for reaction_added not received"
    assert ws_message["data"]["emoji"] == "🎉", "Wrong emoji in WebSocket notification"
    assert ws_message["data"]["message_id"] == test_message_id, "Wrong message ID in WebSocket notification"
    
    # Test 2: Remove emoji reaction and verify WebSocket notification
    print("Test 2: Removing emoji reaction and verifying WebSocket notification...")
    ws_client2.clear_messages()
    
    response = requests.post(
        f"{API_URL}/messages/{test_message_id}/reactions", 
        json=reaction_data, 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to remove reaction: {response.text}"
    
    # Check if WebSocket notification was sent to the other user
    ws_message = ws_client2.wait_for_message("reaction_removed")
    assert ws_message is not None, "WebSocket notification for reaction_removed not received"
    assert ws_message["data"]["emoji"] == "🎉", "Wrong emoji in WebSocket notification"
    assert ws_message["data"]["message_id"] == test_message_id, "Wrong message ID in WebSocket notification"
    
    print("All emoji reaction WebSocket notification tests passed!")

def test_gif_upload_and_messaging():
    print("\n=== Testing GIF Upload and Messaging ===")
    global test_gif_message_id
    
    # Test 1: Upload a GIF file
    print("Test 1: Uploading a GIF file...")
    gif_buffer = create_test_gif()
    gif_filename = f"test_gif_{uuid.uuid4().hex[:8]}.gif"
    
    file_data = upload_file(user1_token, gif_buffer, gif_filename, "image/gif")
    assert "file_id" in file_data, "File ID not found in response"
    assert file_data["file_type"] == "image/gif", "Wrong file type in response"
    assert file_data["category"] == "Image", "Wrong category in response"
    
    # Test 2: Send a message with the GIF
    print("Test 2: Sending a message with the GIF...")
    message_data = send_message_with_file(user1_token, test_chat_id, "Check out this GIF!", file_data["file_id"])
    test_gif_message_id = message_data["message_id"]
    
    assert message_data["file_name"] == gif_filename, "Wrong file name in message"
    assert message_data["file_type"] == "image/gif", "Wrong file type in message"
    assert "file_data" in message_data, "File data not found in message"
    
    # Test 3: Retrieve the message and verify GIF data
    print("Test 3: Retrieving the message and verifying GIF data...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    response = requests.get(f"{API_URL}/chats/{test_chat_id}/messages", headers=headers)
    assert response.status_code == 200, f"Failed to get messages: {response.text}"
    
    messages = response.json()
    gif_message = next((m for m in messages if m.get("message_id") == test_gif_message_id), None)
    assert gif_message is not None, "GIF message not found in chat messages"
    assert gif_message["file_type"] == "image/gif", "Wrong file type in retrieved message"
    assert gif_message["file_name"] == gif_filename, "Wrong file name in retrieved message"
    
    # Test 4: Add emoji reaction to GIF message
    print("Test 4: Adding emoji reaction to GIF message...")
    reaction_data = {"emoji": "👍"}
    response = requests.post(
        f"{API_URL}/messages/{test_gif_message_id}/reactions", 
        json=reaction_data, 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to add reaction to GIF message: {response.text}"
    
    # Test 5: Get reactions for GIF message
    print("Test 5: Getting reactions for GIF message...")
    response = requests.get(
        f"{API_URL}/messages/{test_gif_message_id}/reactions", 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get reactions for GIF message: {response.text}"
    
    result = response.json()
    reaction = next((r for r in result["reactions"] if r["emoji"] == "👍"), None)
    assert reaction is not None, "Added reaction not found in GIF message"
    
    print("All GIF upload and messaging tests passed!")

def test_emoji_reactions_in_team_chat():
    print("\n=== Testing Emoji Reactions in Team Chat ===")
    
    # Test 1: Send a message to the team chat
    print("Test 1: Sending a message to the team chat...")
    message_data = send_team_message(user1_token, test_team_id, "Test message for team emoji reactions")
    team_message_id = message_data["message_id"]
    print(f"Team message ID: {team_message_id}")
    
    # Test 2: Add emoji reaction to team message
    print("Test 2: Adding emoji reaction to team message...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    reaction_data = {"emoji": "🚀"}
    
    response = requests.post(
        f"{API_URL}/messages/{team_message_id}/reactions", 
        json=reaction_data, 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to add reaction to team message: {response.text}"
    result = response.json()
    assert result["status"] == "reaction_added", "Reaction was not added to team message"
    
    # Test 3: Get reactions for team message
    print("Test 3: Getting reactions for team message...")
    response = requests.get(
        f"{API_URL}/messages/{team_message_id}/reactions", 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get team message reactions: {response.text}"
    result = response.json()
    
    reaction = next((r for r in result["reactions"] if r["emoji"] == "🚀"), None)
    assert reaction is not None, "Added reaction not found in team message"
    assert reaction["count"] == 1, "Wrong reaction count for team message"
    
    # Test 4: Have second user add reaction
    print("Test 4: Having second user add reaction...")
    headers2 = {"Authorization": f"Bearer {user2_token}"}
    reaction_data = {"emoji": "🚀"}
    
    response = requests.post(
        f"{API_URL}/messages/{team_message_id}/reactions", 
        json=reaction_data, 
        headers=headers2
    )
    assert response.status_code == 200, f"Failed to add second user reaction to team message: {response.text}"
    
    # Test 5: Verify both reactions
    print("Test 5: Verifying both reactions...")
    response = requests.get(
        f"{API_URL}/messages/{team_message_id}/reactions", 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get team message reactions: {response.text}"
    result = response.json()
    
    reaction = next((r for r in result["reactions"] if r["emoji"] == "🚀"), None)
    assert reaction is not None, "Reaction not found in team message"
    assert reaction["count"] == 2, "Wrong reaction count for team message"
    assert len(reaction["users"]) == 2, "Wrong number of users in team message reaction"
    
    # Test 6: Upload and send GIF in team chat
    print("Test 6: Uploading and sending GIF in team chat...")
    gif_buffer = create_test_gif()
    gif_filename = f"team_gif_{uuid.uuid4().hex[:8]}.gif"
    
    file_data = upload_file(user1_token, gif_buffer, gif_filename, "image/gif")
    
    # Send message with GIF to team chat
    headers = {"Authorization": f"Bearer {user1_token}"}
    message_data = {
        "content": "Team GIF message!",
        "file_id": file_data["file_id"]
    }
    
    response = requests.post(f"{API_URL}/teams/{test_team_id}/messages", json=message_data, headers=headers)
    assert response.status_code == 200, f"Failed to send GIF to team chat: {response.text}"
    team_gif_message = response.json()
    
    assert team_gif_message["file_name"] == gif_filename, "Wrong file name in team GIF message"
    assert team_gif_message["file_type"] == "image/gif", "Wrong file type in team GIF message"
    
    print("All team chat emoji reaction and GIF tests passed!")

def cleanup():
    print("\n=== Cleaning up ===")
    # Disconnect WebSocket clients
    if 'ws_client1' in globals():
        ws_client1.disconnect()
    if 'ws_client2' in globals():
        ws_client2.disconnect()

def run_tests():
    try:
        setup()
        test_emoji_reactions_websocket()
        test_gif_upload_and_messaging()
        test_emoji_reactions_in_team_chat()
        print("\n✅ All emoji, GIF, and customization functionality tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise
    finally:
        cleanup()

if __name__ == "__main__":
    run_tests()