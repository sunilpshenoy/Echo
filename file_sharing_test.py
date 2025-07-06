import requests
import json
import base64
import os
import logging
from io import BytesIO
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

# Test user credentials
test_user = {
    "username": "file_sharing_test_user",
    "email": "file_sharing_test@example.com",
    "password": "FileSharingTest123!"
}

# Global variables
user_token = None
user_id = None
chat_id = None
uploaded_file = None

def register_or_login_user():
    """Register a test user or login if already exists"""
    global user_token, user_id
    
    # Try to register the user
    response = requests.post(f"{API_URL}/register", json=test_user)
    
    if response.status_code == 200:
        logger.info(f"User {test_user['username']} registered successfully")
        user_token = response.json()["access_token"]
        user_id = response.json()["user"]["user_id"]
    elif response.status_code == 400 and "Email already registered" in response.json()["detail"]:
        # User already exists, try logging in
        logger.info(f"User {test_user['username']} already exists, logging in...")
        login_response = requests.post(f"{API_URL}/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        
        if login_response.status_code == 200:
            logger.info(f"User {test_user['username']} logged in successfully")
            user_token = login_response.json()["access_token"]
            user_id = login_response.json()["user"]["user_id"]
        else:
            logger.error(f"Failed to log in user {test_user['username']}: {login_response.text}")
            return False
    else:
        logger.error(f"Failed to register user {test_user['username']}: {response.text}")
        return False
    
    return True

def create_test_chat():
    """Create a test chat for file sharing"""
    global chat_id
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create a group chat (with just the test user)
    response = requests.post(
        f"{API_URL}/chats",
        json={
            "chat_type": "group",
            "name": "File Sharing Test Chat",
            "members": [user_id]  # Include the current user
        },
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to create test chat: {response.text}")
        return False
    
    chat_id = response.json()["chat_id"]
    logger.info(f"Test chat created with ID: {chat_id}")
    return True

def upload_test_file():
    """Upload a test file for sharing"""
    global uploaded_file
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create a small test image
    small_png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    files = {"file": ("test_image.png", BytesIO(small_png_data), "image/png")}
    
    response = requests.post(f"{API_URL}/upload", headers=headers, files=files)
    
    if response.status_code != 200:
        logger.error(f"Failed to upload test file: {response.text}")
        return False
    
    uploaded_file = response.json()
    
    # Verify all required fields are present
    required_fields = ["file_id", "file_name", "file_size", "file_type", "file_data", "category", "icon"]
    missing_fields = [field for field in required_fields if field not in uploaded_file]
    
    if missing_fields:
        logger.error(f"Upload response missing required fields: {missing_fields}")
        return False
    
    logger.info(f"Successfully uploaded test file: {uploaded_file['file_name']} ({uploaded_file['file_size']} bytes)")
    logger.info(f"Category: {uploaded_file['category']}, Icon: {uploaded_file['icon']}")
    return True

def test_send_file_message():
    """Test sending a message with a file attachment"""
    global uploaded_file
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Prepare message data with all file metadata
    message_data = {
        "content": "Here's an image with enhanced metadata",
        "message_type": "image",
        "file_name": uploaded_file["file_name"],
        "file_size": uploaded_file["file_size"],
        "file_data": uploaded_file["file_data"],
        "file_type": uploaded_file["file_type"],
        "category": uploaded_file["category"],
        "icon": uploaded_file["icon"]
    }
    
    # Send the message
    response = requests.post(
        f"{API_URL}/chats/{chat_id}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message with file attachment: {response.text}")
        return False
    
    message_id = response.json()["message_id"]
    logger.info(f"Message with file attachment sent with ID: {message_id}")
    
    # Retrieve the message to verify it was stored correctly
    response = requests.get(
        f"{API_URL}/chats/{chat_id}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to retrieve messages: {response.text}")
        return False
    
    messages = response.json()
    file_message = next((m for m in messages if m.get("message_id") == message_id), None)
    
    if not file_message:
        logger.error(f"Could not find the sent message in chat history")
        return False
    
    # Log the full message for debugging
    logger.info(f"Retrieved message: {json.dumps(file_message, indent=2)}")
    
    # Check if the message has the file data
    if file_message.get("message_type") != "image":
        logger.error(f"Message has incorrect type: {file_message.get('message_type')}")
        return False
    
    if not file_message.get("file_name"):
        logger.error("Message is missing file_name field")
        return False
    
    if not file_message.get("file_data"):
        logger.error("Message is missing file_data field")
        return False
    
    if not file_message.get("file_size"):
        logger.error("Message is missing file_size field")
        return False
    
    if not file_message.get("file_type"):
        logger.error("Message is missing file_type field")
        return False
    
    # Check for enhanced fields
    if not file_message.get("category"):
        logger.error("Message is missing category field")
        return False
    
    if not file_message.get("icon"):
        logger.error("Message is missing icon field")
        return False
    
    logger.info("Successfully verified file message in chat")
    return True

def run_tests():
    """Run all tests"""
    logger.info("Starting File Sharing tests...")
    
    # Setup
    if not register_or_login_user():
        logger.error("Failed to setup test user")
        return False
    
    if not create_test_chat():
        logger.error("Failed to create test chat")
        return False
    
    if not upload_test_file():
        logger.error("Failed to upload test file")
        return False
    
    # Run tests
    tests = [
        ("Send File Message", test_send_file_message),
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
    logger.info("FILE SHARING TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 80)
    logger.info(f"OVERALL RESULT: {'PASSED' if all_passed else 'FAILED'}")
    logger.info("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    if success:
        logger.info("All File Sharing tests passed!")
    else:
        logger.error("Some File Sharing tests failed!")