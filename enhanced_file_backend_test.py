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
    "username": "enhanced_file_backend_test_user",
    "email": "enhanced_file_backend_test@example.com",
    "password": "EnhancedFileBackendTest123!"
}

# Global variables
user_token = None
user_id = None
chat_id = None
team_id = None
team_chat_id = None
uploaded_files = {}

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
            "name": "Enhanced File Backend Test Chat",
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

def create_test_team():
    """Create a test team for file sharing"""
    global team_id, team_chat_id
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create a team
    response = requests.post(
        f"{API_URL}/teams",
        json={
            "name": "Enhanced File Backend Test Team",
            "description": "A team for testing enhanced file sharing backend functionality"
        },
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to create test team: {response.text}")
        return False
    
    team_id = response.json()["team_id"]
    
    # Get the team chat ID
    if "team_chat_id" in response.json():
        team_chat_id = response.json()["team_chat_id"]
        logger.info(f"Test team created with ID: {team_id}, chat ID: {team_chat_id}")
        return True
    
    # If team_chat_id not directly provided, try to find it
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get chats: {response.text}")
        return False
    
    chats = response.json()
    for chat in chats:
        if chat.get("team_id") == team_id:
            team_chat_id = chat["chat_id"]
            logger.info(f"Test team created with ID: {team_id}, chat ID: {team_chat_id}")
            return True
    
    logger.error(f"Failed to find team chat ID for team: {team_id}")
    return False

def test_file_upload_endpoint():
    """Test the enhanced file upload endpoint with all required fields"""
    global uploaded_files
    
    logger.info("Testing enhanced file upload endpoint...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Test cases for different file types
    test_cases = [
        {
            "name": "image.png",
            "content": base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="),
            "content_type": "image/png",
            "expected_status": 200,
            "expected_category": "Image",
            "expected_icon": "🖼️"
        },
        {
            "name": "document.pdf",
            "content": b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF",
            "content_type": "application/pdf",
            "expected_status": 200,
            "expected_category": "Document",
            "expected_icon": "📄"
        },
        {
            "name": "audio.mp3",
            "content": b"ID3\x03\x00\x00\x00\x00\x0f\x76TALB\x00\x00\x00\x0f\x00\x00\x03Test Album",
            "content_type": "audio/mpeg",
            "expected_status": 200,
            "expected_category": "Audio",
            "expected_icon": "🎵"
        },
        {
            "name": "video.mp4",
            "content": b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41\x00\x00\x00\x01moov",
            "content_type": "video/mp4",
            "expected_status": 200,
            "expected_category": "Video",
            "expected_icon": "🎬"
        },
        {
            "name": "archive.zip",
            "content": b"PK\x03\x04\x14\x00\x00\x00\x08\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00test.txtPK\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00test.txtPK\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00.\x00\x00\x00\x1c\x00\x00\x00\x00\x00",
            "content_type": "application/zip",
            "expected_status": 200,
            "expected_category": "Archive",
            "expected_icon": "📦"
        },
        {
            "name": "executable.exe",
            "content": b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00\xb8\x00\x00\x00\x00\x00\x00\x00",
            "content_type": "application/octet-stream",
            "expected_status": 400,
            "expected_error": "File type 'application/octet-stream' not supported"
        }
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        logger.info(f"Testing upload of {test_case['name']} ({test_case['content_type']})")
        
        files = {"file": (test_case["name"], BytesIO(test_case["content"]), test_case["content_type"])}
        
        response = requests.post(f"{API_URL}/upload", headers=headers, files=files)
        
        if response.status_code != test_case["expected_status"]:
            logger.error(f"Unexpected status code: {response.status_code}, expected: {test_case['expected_status']}")
            logger.error(f"Response: {response.text}")
            continue
        
        if test_case["expected_status"] == 200:
            result = response.json()
            
            # Check for required fields
            required_fields = ["file_id", "file_name", "file_size", "file_type", "file_data", "category", "icon"]
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                logger.error(f"Response missing required fields: {missing_fields}")
                logger.error(f"Response: {result}")
                continue
            
            # Check category and icon
            if result["category"] != test_case["expected_category"]:
                logger.error(f"Unexpected category: {result['category']}, expected: {test_case['expected_category']}")
                continue
                
            if result["icon"] != test_case["expected_icon"]:
                logger.error(f"Unexpected icon: {result['icon']}, expected: {test_case['expected_icon']}")
                continue
            
            logger.info(f"Successfully uploaded {test_case['name']} ({result['file_size']} bytes)")
            logger.info(f"Category: {result['category']}, Icon: {result['icon']}")
            
            # Store the uploaded file data for later tests
            if test_case["expected_status"] == 200:
                uploaded_files[test_case["name"]] = result
            
            success_count += 1
        else:
            # Check error message for rejected files
            if test_case["expected_error"] not in response.json()["detail"]:
                logger.error(f"Unexpected error message: {response.json()['detail']}")
                logger.error(f"Expected to contain: {test_case['expected_error']}")
                continue
            
            logger.info(f"Correctly rejected {test_case['name']} with error: {response.json()['detail']}")
            success_count += 1
    
    logger.info(f"Enhanced file upload endpoint test completed: {success_count}/{len(test_cases)} test cases passed")
    return success_count == len(test_cases)

def test_file_sharing_in_chat():
    """Test sharing files in chat messages"""
    logger.info("Testing file sharing in chat messages...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Use the image file we uploaded earlier
    file_data = uploaded_files.get("image.png")
    if not file_data:
        logger.error("No image file available for testing")
        return False
    
    # Send message with image attachment to chat
    message_data = {
        "content": "Here's an image attachment",
        "message_type": "image",
        "file_name": file_data["file_name"],
        "file_size": file_data["file_size"],
        "file_data": file_data["file_data"],
        "file_type": file_data["file_type"]
    }
    
    # Add enhanced fields if they exist
    if "category" in file_data:
        message_data["category"] = file_data["category"]
    
    if "icon" in file_data:
        message_data["icon"] = file_data["icon"]
    
    response = requests.post(
        f"{API_URL}/chats/{chat_id}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message with image attachment: {response.text}")
        return False
    
    message_id = response.json()["message_id"]
    logger.info(f"Message with image attachment sent with ID: {message_id}")
    
    # Verify the message was stored correctly
    response = requests.get(
        f"{API_URL}/chats/{chat_id}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get messages to verify attachment: {response.text}")
        return False
    
    messages = response.json()
    image_message = next((m for m in messages if m.get("message_id") == message_id), None)
    
    if not image_message:
        logger.error("Could not find image message in chat history")
        return False
    
    # Log the full message for debugging
    logger.info(f"Retrieved message: {json.dumps(image_message, indent=2)}")
    
    # Check that all file metadata was stored correctly
    if (image_message.get("message_type") != "image" or 
        not image_message.get("file_name") or 
        not image_message.get("file_data")):
        logger.error(f"Image message missing basic attachment data")
        return False
    
    logger.info("File sharing in chat messages test passed")
    return True

def test_file_sharing_in_team_chat():
    """Test sharing files in team chats"""
    logger.info("Testing file sharing in team chats...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Use the document file we uploaded earlier
    file_data = uploaded_files.get("document.pdf")
    if not file_data:
        logger.error("No document file available for testing")
        return False
    
    # Send message with document attachment to team chat
    message_data = {
        "content": "Here's a document for the team",
        "message_type": "file",
        "file_name": file_data["file_name"],
        "file_size": file_data["file_size"],
        "file_data": file_data["file_data"],
        "file_type": file_data["file_type"]
    }
    
    # Add enhanced fields if they exist
    if "category" in file_data:
        message_data["category"] = file_data["category"]
    
    if "icon" in file_data:
        message_data["icon"] = file_data["icon"]
    
    # Try both team-specific endpoint and regular chat endpoint
    endpoints_to_try = [
        f"{API_URL}/teams/{team_id}/messages",
        f"{API_URL}/chats/{team_chat_id}/messages"
    ]
    
    success = False
    message_id = None
    
    for endpoint in endpoints_to_try:
        response = requests.post(endpoint, json=message_data, headers=headers)
        
        if response.status_code == 200:
            message_id = response.json()["message_id"]
            logger.info(f"Message with document attachment sent to team chat with ID: {message_id} via {endpoint}")
            success = True
            break
        else:
            logger.warning(f"Failed to send message via {endpoint}: {response.text}")
    
    if not success:
        logger.error("Failed to send file message to team chat via any endpoint")
        return False
    
    # Verify the message was stored correctly
    endpoints_to_check = [
        f"{API_URL}/teams/{team_id}/messages",
        f"{API_URL}/chats/{team_chat_id}/messages"
    ]
    
    for endpoint in endpoints_to_check:
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            messages = response.json()
            if not messages:
                logger.warning(f"No messages found via {endpoint}")
                continue
                
            document_message = next((m for m in messages if m.get("message_id") == message_id), None)
            
            if not document_message:
                logger.warning(f"Could not find document message via {endpoint}")
                continue
            
            # Log the full message for debugging
            logger.info(f"Retrieved team message: {json.dumps(document_message, indent=2)}")
            
            # Check that all file metadata was stored correctly
            if (document_message.get("message_type") != "file" or 
                not document_message.get("file_name") or 
                not document_message.get("file_data")):
                logger.error(f"Document message missing basic attachment data")
                continue
            
            logger.info(f"Successfully verified document message via {endpoint}")
            return True
    
    logger.error("Failed to verify file message in team chat via any endpoint")
    return False

def test_various_file_types():
    """Test sharing various file types in chat messages"""
    logger.info("Testing sharing various file types in chat messages...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Test cases for different file types
    test_cases = [
        {
            "file_key": "audio.mp3",
            "message_type": "audio",
            "content": "Here's an audio file"
        },
        {
            "file_key": "video.mp4",
            "message_type": "video",
            "content": "Here's a video file"
        },
        {
            "file_key": "archive.zip",
            "message_type": "file",
            "content": "Here's an archive file"
        }
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        file_data = uploaded_files.get(test_case["file_key"])
        if not file_data:
            logger.error(f"No {test_case['file_key']} file available for testing")
            continue
        
        # Send message with file attachment to chat
        message_data = {
            "content": test_case["content"],
            "message_type": test_case["message_type"],
            "file_name": file_data["file_name"],
            "file_size": file_data["file_size"],
            "file_data": file_data["file_data"],
            "file_type": file_data["file_type"]
        }
        
        # Add enhanced fields if they exist
        if "category" in file_data:
            message_data["category"] = file_data["category"]
        
        if "icon" in file_data:
            message_data["icon"] = file_data["icon"]
        
        response = requests.post(
            f"{API_URL}/chats/{chat_id}/messages",
            json=message_data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to send message with {test_case['file_key']} attachment: {response.text}")
            continue
        
        message_id = response.json()["message_id"]
        logger.info(f"Message with {test_case['file_key']} attachment sent with ID: {message_id}")
        
        # Verify the message was stored correctly
        response = requests.get(
            f"{API_URL}/chats/{chat_id}/messages",
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get messages to verify {test_case['file_key']} attachment: {response.text}")
            continue
        
        messages = response.json()
        file_message = next((m for m in messages if m.get("message_id") == message_id), None)
        
        if not file_message:
            logger.error(f"Could not find {test_case['file_key']} message in chat history")
            continue
        
        # Check that all file metadata was stored correctly
        if (file_message.get("message_type") != test_case["message_type"] or 
            not file_message.get("file_name") or 
            not file_message.get("file_data")):
            logger.error(f"{test_case['file_key']} message missing basic attachment data")
            continue
        
        logger.info(f"Successfully verified {test_case['file_key']} message")
        success_count += 1
    
    logger.info(f"Various file types test completed: {success_count}/{len(test_cases)} test cases passed")
    return success_count == len(test_cases)

def run_tests():
    """Run all tests"""
    logger.info("Starting Enhanced File Sharing Backend Tests...")
    
    # Setup
    if not register_or_login_user():
        logger.error("Failed to setup test user")
        return False
    
    if not create_test_chat():
        logger.error("Failed to create test chat")
        return False
    
    if not create_test_team():
        logger.error("Failed to create test team")
        return False
    
    # Run tests
    tests = [
        ("Enhanced File Upload", test_file_upload_endpoint),
        ("File Sharing in Chat", test_file_sharing_in_chat),
        ("File Sharing in Team Chat", test_file_sharing_in_team_chat),
        ("Various File Types", test_various_file_types)
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
    logger.info("ENHANCED FILE SHARING BACKEND TEST RESULTS SUMMARY")
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
        logger.info("All Enhanced File Sharing Backend Tests passed!")
    else:
        logger.error("Some Enhanced File Sharing Backend Tests failed!")