import requests
import json
import time
import uuid
import os
import base64
from dotenv import load_dotenv
import logging
from io import BytesIO
from datetime import datetime, timedelta
import random

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
        "username": "alice_test",
        "email": "alice.test@example.com",
        "password": "SecurePass123!",
        "phone": "+1234567890"
    },
    {
        "username": "bob_test",
        "email": "bob.test@example.com",
        "password": "StrongPass456!",
        "phone": "+1987654321"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
chat_ids = {}

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
    
    logger.info("Chat creation tests passed")
    return True

def test_voice_video_calls():
    """Test voice/video call initiation"""
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
    
    logger.info("Voice/video calls tests passed")
    return True

def test_file_sharing():
    """Test file sharing in chat"""
    logger.info("Testing file sharing...")
    
    # Create a test image file (1x1 pixel transparent PNG)
    small_png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    
    # Test file upload to chat
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Create file data
    file_data = {
        "filename": "test_image.png",
        "file_type": "image/png",
        "file_data": base64.b64encode(small_png_data).decode('utf-8')
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/files",
        json=file_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to upload file to chat: {response.text}")
        return False
    
    logger.info(f"Successfully uploaded file to chat")
    
    # Verify file data in response
    if "file_id" not in response.json():
        logger.error(f"File upload response missing file_id: {response.json()}")
        return False
    
    logger.info("File sharing tests passed")
    return True

def test_teams_api():
    """Test teams API endpoints"""
    logger.info("Testing teams API...")
    
    # Test GET /api/teams
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/teams", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get teams: {response.text}")
        return False
    
    logger.info(f"Successfully retrieved teams")
    
    # Test POST /api/teams
    team_data = {
        "name": f"Test Team {uuid.uuid4().hex[:8]}",
        "description": "A test team for API testing",
        "members": [user_ids['user2']]
    }
    
    response = requests.post(f"{API_URL}/teams", json=team_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create team: {response.text}")
        return False
    
    team_id = response.json().get("team_id")
    if not team_id:
        logger.error(f"Team creation response missing team_id: {response.json()}")
        return False
    
    logger.info(f"Successfully created team with ID: {team_id}")
    
    # Verify team was created by getting teams again
    response = requests.get(f"{API_URL}/teams", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get teams after creation: {response.text}")
        return False
    
    teams = response.json()
    if not any(team.get("team_id") == team_id for team in teams):
        logger.error(f"Created team not found in teams list")
        return False
    
    logger.info("Teams API tests passed")
    return True

def run_tests():
    """Run all tests"""
    logger.info("Starting Free Tier Feature Tests...")
    
    # Setup tests
    if not test_user_registration():
        logger.error("User registration tests failed")
        return False
    
    if not test_chat_creation():
        logger.error("Chat creation tests failed")
        return False
    
    # Feature tests
    voice_video_result = test_voice_video_calls()
    file_sharing_result = test_file_sharing()
    teams_result = test_teams_api()
    
    # Print summary
    logger.info("\n=== TEST RESULTS ===")
    logger.info(f"Voice/Video Calls: {'PASSED' if voice_video_result else 'FAILED'}")
    logger.info(f"File Sharing: {'PASSED' if file_sharing_result else 'FAILED'}")
    logger.info(f"Teams API: {'PASSED' if teams_result else 'FAILED'}")
    
    return voice_video_result and file_sharing_result and teams_result

if __name__ == "__main__":
    run_tests()