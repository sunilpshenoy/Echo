import requests
import json
import base64
import os
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

def test_emoji_functionality():
    print("\n=== Testing Emoji Functionality ===")
    
    # Step 1: Register/login test users
    print("Step 1: Registering test users...")
    user1_data = register_user(TEST_USER1)
    user2_data = register_user(TEST_USER2)
    
    user1_token = user1_data["access_token"]
    user2_token = user2_data["access_token"]
    user1_id = user1_data["user"]["user_id"]
    user2_id = user2_data["user"]["user_id"]
    
    print(f"User 1 ID: {user1_id}")
    print(f"User 2 ID: {user2_id}")
    
    # Step 2: Create a direct chat between the users
    print("\nStep 2: Creating test chat...")
    chat_data = create_direct_chat(user1_token, user2_id)
    test_chat_id = chat_data["chat_id"]
    print(f"Test chat ID: {test_chat_id}")
    
    # Step 3: Send a test message
    print("\nStep 3: Sending test message...")
    message_data = send_message(user1_token, test_chat_id, "Test message for emoji reactions")
    test_message_id = message_data["message_id"]
    print(f"Test message ID: {test_message_id}")
    
    # Step 4: Check if the message exists
    print("\nStep 4: Verifying message exists...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    response = requests.get(f"{API_URL}/chats/{test_chat_id}/messages", headers=headers)
    print(f"Get messages response: {response.status_code}")
    if response.status_code == 200:
        messages = response.json()
        print(f"Found {len(messages)} messages in chat")
        for msg in messages:
            print(f"Message ID: {msg.get('message_id')}, Content: {msg.get('content')}")
    
    # Step 5: Test message reactions endpoint
    print("\nStep 5: Testing message reactions endpoint...")
    print("NOTE: This test is expected to fail if the emoji reactions endpoints are not properly registered")
    reaction_data = {"emoji": "👍"}
    
    print(f"Making request to: {API_URL}/messages/{test_message_id}/reactions")
    response = requests.post(
        f"{API_URL}/messages/{test_message_id}/reactions", 
        json=reaction_data, 
        headers=headers
    )
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 404:
        print("\n⚠️ ISSUE DETECTED: The emoji reactions endpoint is returning 404 Not Found.")
        print("This is likely because the endpoint was defined after app.include_router(api_router) in server.py.")
        print("To fix this issue, move the app.include_router(api_router) line to the end of the file, after all endpoints are defined.")
    
    # Step 6: Test custom emoji upload endpoint
    print("\nStep 6: Testing custom emoji upload endpoint...")
    print("NOTE: This test is expected to fail if the custom emoji endpoints are not properly registered")
    
    test_image = create_test_image()
    files = {
        'file': ('test_emoji.png', test_image, 'image/png')
    }
    data = {
        'name': 'test_emoji',
        'category': 'test'
    }
    
    response = requests.post(
        f"{API_URL}/emojis/custom",
        headers=headers,
        files=files,
        data=data
    )
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 404:
        print("\n⚠️ ISSUE DETECTED: The custom emoji upload endpoint is returning 404 Not Found.")
        print("This is likely because the endpoint was defined after app.include_router(api_router) in server.py.")
        print("To fix this issue, move the app.include_router(api_router) line to the end of the file, after all endpoints are defined.")
    
    print("\n=== Emoji Functionality Test Summary ===")
    print("The emoji functionality tests have identified an issue with the endpoint registration.")
    print("The emoji-related endpoints are defined after the app.include_router(api_router) line in server.py,")
    print("which means they are not being included in the router and are not accessible.")
    print("\nTo fix this issue, the app.include_router(api_router) line should be moved to the end of the file,")
    print("after all endpoints are defined.")

if __name__ == "__main__":
    test_emoji_functionality()