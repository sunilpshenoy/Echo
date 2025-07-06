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
    "username": "emoji_test_user1",
    "email": "emoji_test1@example.com",
    "password": "TestPassword123!"
}

TEST_USER2 = {
    "username": "emoji_test_user2",
    "email": "emoji_test2@example.com",
    "password": "TestPassword123!"
}

# Global variables to store test data
user1_token = None
user2_token = None
user1_id = None
user2_id = None
test_chat_id = None
test_message_id = None
test_custom_emoji_id = None
ws_messages = []

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

def create_test_image(size=(100, 100), color=(255, 0, 0)):
    """Create a test image for custom emoji upload"""
    image = Image.new('RGB', size, color)
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

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

def test_emoji_reactions():
    print("\n=== Testing Emoji Reactions ===")
    
    # Clear WebSocket messages
    ws_client1.clear_messages()
    ws_client2.clear_messages()
    
    # Test 1: Add emoji reaction
    print("Test 1: Adding emoji reaction...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    reaction_data = {"emoji": "👍"}
    
    response = requests.post(
        f"{API_URL}/messages/{test_message_id}/reactions", 
        json=reaction_data, 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to add reaction: {response.text}"
    result = response.json()
    assert result["status"] == "reaction_added", "Reaction was not added"
    assert result["emoji"] == "👍", "Wrong emoji in response"
    
    # Check if WebSocket notification was sent
    ws_message = ws_client2.wait_for_message("reaction_added")
    assert ws_message is not None, "WebSocket notification for reaction_added not received"
    assert ws_message["data"]["emoji"] == "👍", "Wrong emoji in WebSocket notification"
    assert ws_message["data"]["message_id"] == test_message_id, "Wrong message ID in WebSocket notification"
    
    # Test 2: Get message reactions
    print("Test 2: Getting message reactions...")
    response = requests.get(
        f"{API_URL}/messages/{test_message_id}/reactions", 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get reactions: {response.text}"
    result = response.json()
    assert "reactions" in result, "Reactions not found in response"
    assert len(result["reactions"]) > 0, "No reactions returned"
    
    reaction = next((r for r in result["reactions"] if r["emoji"] == "👍"), None)
    assert reaction is not None, "Added reaction not found in results"
    assert reaction["count"] == 1, "Wrong reaction count"
    assert reaction["user_reacted"] == True, "User reaction status incorrect"
    assert len(reaction["users"]) == 1, "Wrong number of users in reaction"
    assert reaction["users"][0]["user_id"] == user1_id, "Wrong user ID in reaction"
    
    # Test 3: Toggle reaction (remove)
    print("Test 3: Toggling reaction (remove)...")
    ws_client1.clear_messages()
    ws_client2.clear_messages()
    
    response = requests.post(
        f"{API_URL}/messages/{test_message_id}/reactions", 
        json=reaction_data, 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to toggle reaction: {response.text}"
    result = response.json()
    assert result["status"] == "reaction_removed", "Reaction was not removed"
    
    # Check if WebSocket notification was sent
    ws_message = ws_client2.wait_for_message("reaction_removed")
    assert ws_message is not None, "WebSocket notification for reaction_removed not received"
    assert ws_message["data"]["emoji"] == "👍", "Wrong emoji in WebSocket notification"
    
    # Test 4: Verify reaction was removed
    print("Test 4: Verifying reaction removal...")
    response = requests.get(
        f"{API_URL}/messages/{test_message_id}/reactions", 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get reactions: {response.text}"
    result = response.json()
    
    reaction = next((r for r in result["reactions"] if r["emoji"] == "👍"), None)
    assert reaction is None, "Reaction was not properly removed"
    
    # Test 5: Add multiple reactions
    print("Test 5: Adding multiple reactions...")
    emojis = ["😀", "❤️", "🎉"]
    
    for emoji in emojis:
        reaction_data = {"emoji": emoji}
        response = requests.post(
            f"{API_URL}/messages/{test_message_id}/reactions", 
            json=reaction_data, 
            headers=headers
        )
        assert response.status_code == 200, f"Failed to add reaction {emoji}: {response.text}"
    
    # Test 6: Verify multiple reactions
    print("Test 6: Verifying multiple reactions...")
    response = requests.get(
        f"{API_URL}/messages/{test_message_id}/reactions", 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get reactions: {response.text}"
    result = response.json()
    
    assert len(result["reactions"]) == len(emojis), f"Expected {len(emojis)} reactions, got {len(result['reactions'])}"
    
    for emoji in emojis:
        reaction = next((r for r in result["reactions"] if r["emoji"] == emoji), None)
        assert reaction is not None, f"Reaction {emoji} not found in results"
        assert reaction["count"] == 1, f"Wrong count for reaction {emoji}"
    
    # Test 7: Second user adds reaction
    print("Test 7: Second user adds reaction...")
    headers2 = {"Authorization": f"Bearer {user2_token}"}
    reaction_data = {"emoji": "❤️"}
    
    response = requests.post(
        f"{API_URL}/messages/{test_message_id}/reactions", 
        json=reaction_data, 
        headers=headers2
    )
    assert response.status_code == 200, f"Failed to add reaction as second user: {response.text}"
    
    # Test 8: Verify reaction counts
    print("Test 8: Verifying reaction counts...")
    response = requests.get(
        f"{API_URL}/messages/{test_message_id}/reactions", 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get reactions: {response.text}"
    result = response.json()
    
    heart_reaction = next((r for r in result["reactions"] if r["emoji"] == "❤️"), None)
    assert heart_reaction is not None, "Heart reaction not found"
    assert heart_reaction["count"] == 2, "Wrong count for heart reaction"
    assert len(heart_reaction["users"]) == 2, "Wrong number of users for heart reaction"
    
    print("All emoji reaction tests passed!")

def test_custom_emojis():
    print("\n=== Testing Custom Emojis ===")
    global test_custom_emoji_id
    
    # Test 1: Upload custom emoji
    print("Test 1: Uploading custom emoji...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    
    # Create test image
    test_image = create_test_image()
    
    files = {
        'file': ('test_emoji.png', test_image, 'image/png')
    }
    data = {
        'name': f'test_emoji_{uuid.uuid4().hex[:8]}',
        'category': 'test'
    }
    
    response = requests.post(
        f"{API_URL}/emojis/custom",
        headers=headers,
        files=files,
        data=data
    )
    assert response.status_code == 200, f"Failed to upload custom emoji: {response.text}"
    result = response.json()
    assert "emoji_id" in result, "Emoji ID not found in response"
    test_custom_emoji_id = result["emoji_id"]
    print(f"Custom emoji ID: {test_custom_emoji_id}")
    
    # Test 2: Get custom emojis
    print("Test 2: Getting custom emojis...")
    response = requests.get(
        f"{API_URL}/emojis/custom",
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get custom emojis: {response.text}"
    result = response.json()
    assert "custom_emojis" in result, "Custom emojis not found in response"
    assert len(result["custom_emojis"]) > 0, "No custom emojis returned"
    
    # Find our test emoji
    test_emoji = next((e for e in result["custom_emojis"] if e["emoji_id"] == test_custom_emoji_id), None)
    assert test_emoji is not None, "Uploaded emoji not found in results"
    assert test_emoji["name"] == data["name"], "Wrong emoji name"
    assert test_emoji["category"] == data["category"], "Wrong emoji category"
    assert "file_data" in test_emoji, "File data not found in emoji"
    
    # Test 3: Upload invalid file type
    print("Test 3: Testing file type validation...")
    invalid_file = BytesIO(b"This is not an image")
    files = {
        'file': ('test.txt', invalid_file, 'text/plain')
    }
    data = {
        'name': f'invalid_emoji_{uuid.uuid4().hex[:8]}',
        'category': 'test'
    }
    
    response = requests.post(
        f"{API_URL}/emojis/custom",
        headers=headers,
        files=files,
        data=data
    )
    assert response.status_code == 400, "Invalid file type was accepted"
    
    # Test 4: Upload with invalid name
    print("Test 4: Testing name validation...")
    test_image = create_test_image()
    files = {
        'file': ('test_emoji.png', test_image, 'image/png')
    }
    data = {
        'name': 'a',  # Too short
        'category': 'test'
    }
    
    response = requests.post(
        f"{API_URL}/emojis/custom",
        headers=headers,
        files=files,
        data=data
    )
    assert response.status_code == 400, "Invalid name (too short) was accepted"
    
    # Test 5: Delete custom emoji
    print("Test 5: Deleting custom emoji...")
    response = requests.delete(
        f"{API_URL}/emojis/custom/{test_custom_emoji_id}",
        headers=headers
    )
    assert response.status_code == 200, f"Failed to delete custom emoji: {response.text}"
    
    # Test 6: Verify emoji was deleted
    print("Test 6: Verifying emoji deletion...")
    response = requests.get(
        f"{API_URL}/emojis/custom",
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get custom emojis: {response.text}"
    result = response.json()
    
    test_emoji = next((e for e in result["custom_emojis"] if e["emoji_id"] == test_custom_emoji_id), None)
    assert test_emoji is None, "Emoji was not properly deleted"
    
    # Test 7: Try to delete non-existent emoji
    print("Test 7: Testing deletion of non-existent emoji...")
    response = requests.delete(
        f"{API_URL}/emojis/custom/{uuid.uuid4()}",
        headers=headers
    )
    assert response.status_code == 404, "Non-existent emoji deletion did not return 404"
    
    # Test 8: Try to delete emoji belonging to another user
    print("Test 8: Testing access control for deletion...")
    # First, upload a new emoji
    test_image = create_test_image()
    files = {
        'file': ('test_emoji.png', test_image, 'image/png')
    }
    data = {
        'name': f'test_emoji_{uuid.uuid4().hex[:8]}',
        'category': 'test'
    }
    
    response = requests.post(
        f"{API_URL}/emojis/custom",
        headers=headers,
        files=files,
        data=data
    )
    assert response.status_code == 200, f"Failed to upload custom emoji: {response.text}"
    result = response.json()
    emoji_id = result["emoji_id"]
    
    # Try to delete with user2
    headers2 = {"Authorization": f"Bearer {user2_token}"}
    response = requests.delete(
        f"{API_URL}/emojis/custom/{emoji_id}",
        headers=headers2
    )
    assert response.status_code == 404, "User was able to delete another user's emoji"
    
    # Clean up - delete the emoji with the correct user
    requests.delete(
        f"{API_URL}/emojis/custom/{emoji_id}",
        headers=headers
    )
    
    print("All custom emoji tests passed!")

def test_emoji_reaction_in_team_chat():
    print("\n=== Testing Emoji Reactions in Team Chat ===")
    
    # Create a team
    print("Creating test team...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    team_data = {
        "name": f"Test Team {uuid.uuid4().hex[:8]}",
        "description": "Test team for emoji reactions",
        "members": [user1_id, user2_id]
    }
    
    response = requests.post(f"{API_URL}/teams", json=team_data, headers=headers)
    assert response.status_code == 200, f"Failed to create team: {response.text}"
    team_result = response.json()
    team_id = team_result["team_id"]
    team_chat_id = team_result.get("chat_id")
    
    # If chat_id is not directly provided, get team details to find it
    if not team_chat_id:
        response = requests.get(f"{API_URL}/teams/{team_id}", headers=headers)
        assert response.status_code == 200, f"Failed to get team details: {response.text}"
        team_details = response.json()
        team_chat_id = team_details.get("chat_id")
    
    assert team_chat_id, "Team chat ID not found"
    print(f"Team ID: {team_id}, Team Chat ID: {team_chat_id}")
    
    # Send a message to the team chat
    message_data = {
        "content": "Test message for team emoji reactions"
    }
    response = requests.post(
        f"{API_URL}/teams/{team_id}/messages", 
        json=message_data, 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to send team message: {response.text}"
    team_message = response.json()
    team_message_id = team_message["message_id"]
    print(f"Team message ID: {team_message_id}")
    
    # Add emoji reaction to team message
    reaction_data = {"emoji": "🚀"}
    response = requests.post(
        f"{API_URL}/messages/{team_message_id}/reactions", 
        json=reaction_data, 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to add reaction to team message: {response.text}"
    result = response.json()
    assert result["status"] == "reaction_added", "Reaction was not added to team message"
    
    # Get reactions for team message
    response = requests.get(
        f"{API_URL}/messages/{team_message_id}/reactions", 
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get team message reactions: {response.text}"
    result = response.json()
    
    reaction = next((r for r in result["reactions"] if r["emoji"] == "🚀"), None)
    assert reaction is not None, "Added reaction not found in team message"
    assert reaction["count"] == 1, "Wrong reaction count for team message"
    
    # Have second user add reaction
    headers2 = {"Authorization": f"Bearer {user2_token}"}
    reaction_data = {"emoji": "🚀"}
    response = requests.post(
        f"{API_URL}/messages/{team_message_id}/reactions", 
        json=reaction_data, 
        headers=headers2
    )
    assert response.status_code == 200, f"Failed to add second user reaction to team message: {response.text}"
    
    # Verify both reactions
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
    
    print("All team chat emoji reaction tests passed!")

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
        test_emoji_reactions()
        test_custom_emojis()
        test_emoji_reaction_in_team_chat()
        print("\n✅ All emoji functionality tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise
    finally:
        cleanup()

if __name__ == "__main__":
    run_tests()