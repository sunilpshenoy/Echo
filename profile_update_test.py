import requests
import json
import time
import os
import logging
import random
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

# Test data
test_user = {
    "username": f"testuser_{int(time.time())}",
    "email": f"testuser_{int(time.time())}@example.com",
    "password": "SecurePass123!",
    "phone": f"+1{int(time.time())}"
}

# Global variables to store test data
user_token = None
user_id = None

def test_user_registration():
    """Test user registration endpoint"""
    global user_token, user_id
    
    logger.info("Testing user registration...")
    logger.info(f"Registering user: {test_user['username']}")
    
    response = requests.post(f"{API_URL}/register", json=test_user)
    
    if response.status_code == 200:
        logger.info(f"User {test_user['username']} registered successfully")
        user_token = response.json()["access_token"]
        user_id = response.json()["user"]["user_id"]
        return True
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
            return True
        else:
            logger.error(f"Failed to log in user {test_user['username']}: {login_response.text}")
            return False
    else:
        logger.error(f"Failed to register user {test_user['username']}: {response.text}")
        return False

def test_complete_profile():
    """Test PUT /api/profile/complete endpoint"""
    global user_token, user_id
    
    logger.info("Testing PUT /api/profile/complete endpoint...")
    
    if not user_token:
        logger.error("User token not found, run test_user_registration first")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Create profile completion data with display_name
    profile_data = {
        "display_name": "John Doe",
        "age": random.randint(18, 65),
        "gender": random.choice(["male", "female", "non-binary", "other"]),
        "location": random.choice(["New York", "San Francisco", "London", "Tokyo", "Sydney"]),
        "current_mood": random.choice(["happy", "excited", "curious", "relaxed", "focused"]),
        "mood_reason": "Testing the authentic connections app",
        "seeking_type": random.choice(["friendship", "dating", "networking", "mentorship"]),
        "seeking_age_range": "25-45",
        "seeking_gender": "all",
        "seeking_location_preference": "nearby",
        "connection_purpose": "Finding authentic connections through testing",
        "additional_requirements": "Must enjoy software testing",
        "bio": "I'm a test user exploring the authentic connections platform",
        "interests": ["technology", "testing", "software development", "AI"],
        "values": ["honesty", "authenticity", "curiosity", "reliability"]
    }
    
    try:
        logger.info(f"Sending profile completion request to {API_URL}/profile/complete")
        
        response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
        
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Failed to complete profile: {response.text}")
            logger.error(f"Status code: {response.status_code}")
            return False
        
        # Verify response includes updated profile data
        user_data = response.json()
        
        # Check profile_completed is now true
        if "profile_completed" not in user_data or user_data["profile_completed"] != True:
            logger.error(f"profile_completed should be true after completion, got: {user_data.get('profile_completed')}")
            return False
        
        # Check display_name was saved correctly
        if "display_name" not in user_data or user_data["display_name"] != profile_data["display_name"]:
            logger.error(f"display_name not saved correctly. Expected: {profile_data['display_name']}, Got: {user_data.get('display_name')}")
            return False
        
        logger.info(f"Profile completed with display_name: {user_data['display_name']}")
        
        # Verify with GET /users/me that profile is now completed and display_name is correct
        me_response = requests.get(f"{API_URL}/users/me", headers=headers)
        
        if me_response.status_code != 200:
            logger.error(f"Failed to get current user info after profile completion: {me_response.text}")
            return False
        
        me_data = me_response.json()
        if me_data.get("profile_completed") != True:
            logger.error(f"profile_completed should be true in /users/me after completion, got: {me_data.get('profile_completed')}")
            return False
        
        if me_data.get("display_name") != profile_data["display_name"]:
            logger.error(f"display_name incorrect in /users/me. Expected: {profile_data['display_name']}, Got: {me_data.get('display_name')}")
            return False
        
        logger.info("Successfully verified profile completion with GET /users/me")
        
        logger.info("PUT /api/profile/complete test passed")
        return True
    except Exception as e:
        logger.error(f"Exception in test_complete_profile: {e}")
        return False

def test_update_display_name():
    """Test updating display_name via PUT /api/profile/complete endpoint"""
    global user_token, user_id
    
    logger.info("Testing display_name update via PUT /api/profile/complete endpoint...")
    
    if not user_token:
        logger.error("User token not found, run test_user_registration first")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Get current user data
    me_response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if me_response.status_code != 200:
        logger.error(f"Failed to get current user info: {me_response.text}")
        return False
    
    current_user = me_response.json()
    logger.info(f"Current display_name: {current_user.get('display_name')}")
    
    # Update only the display_name
    new_display_name = "John Smith"
    profile_data = {
        "display_name": new_display_name
    }
    
    logger.info(f"Updating display_name to: {new_display_name}")
    
    response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update display_name: {response.text}")
        return False
    
    # Verify response includes updated display_name
    user_data = response.json()
    
    if "display_name" not in user_data or user_data["display_name"] != new_display_name:
        logger.error(f"display_name not updated correctly. Expected: {new_display_name}, Got: {user_data.get('display_name')}")
        return False
    
    logger.info(f"display_name updated to: {user_data['display_name']}")
    
    # Verify with GET /users/me that display_name is updated
    me_response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if me_response.status_code != 200:
        logger.error(f"Failed to get current user info after display_name update: {me_response.text}")
        return False
    
    me_data = me_response.json()
    
    if me_data.get("display_name") != new_display_name:
        logger.error(f"display_name incorrect in /users/me. Expected: {new_display_name}, Got: {me_data.get('display_name')}")
        return False
    
    logger.info("Successfully verified display_name update with GET /users/me")
    
    logger.info("Display name update test passed")
    return True

def test_multiple_profile_updates():
    """Test multiple profile updates to ensure data persistence"""
    global user_token, user_id
    
    logger.info("Testing multiple profile updates...")
    
    if not user_token:
        logger.error("User token not found, run test_user_registration first")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Get current user data
    me_response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if me_response.status_code != 200:
        logger.error(f"Failed to get current user info: {me_response.text}")
        return False
    
    current_user = me_response.json()
    current_display_name = current_user.get('display_name')
    logger.info(f"Current display_name: {current_display_name}")
    
    # Update multiple fields but keep display_name the same
    profile_data = {
        "age": 30,
        "gender": "male",
        "location": "Chicago",
        "bio": "Updated bio for testing multiple updates",
        "interests": ["music", "travel", "food"],
        "values": ["integrity", "growth", "balance"]
    }
    
    logger.info(f"Updating multiple profile fields while keeping display_name: {current_display_name}")
    
    response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update profile: {response.text}")
        return False
    
    # Verify response includes updated fields and unchanged display_name
    user_data = response.json()
    
    if "display_name" not in user_data or user_data["display_name"] != current_display_name:
        logger.error(f"display_name changed unexpectedly. Expected: {current_display_name}, Got: {user_data.get('display_name')}")
        return False
    
    # Verify updated fields
    for key, value in profile_data.items():
        if key not in user_data or user_data[key] != value:
            logger.error(f"Field '{key}' not updated correctly. Expected: {value}, Got: {user_data.get(key)}")
            return False
    
    logger.info("Successfully updated multiple profile fields while preserving display_name")
    
    # Verify with GET /users/me that all fields are updated correctly
    me_response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if me_response.status_code != 200:
        logger.error(f"Failed to get current user info after multiple updates: {me_response.text}")
        return False
    
    me_data = me_response.json()
    
    if me_data.get("display_name") != current_display_name:
        logger.error(f"display_name changed unexpectedly in /users/me. Expected: {current_display_name}, Got: {me_data.get('display_name')}")
        return False
    
    # Verify updated fields in /users/me
    for key, value in profile_data.items():
        if key not in me_data or me_data[key] != value:
            logger.error(f"Field '{key}' not updated correctly in /users/me. Expected: {value}, Got: {me_data.get(key)}")
            return False
    
    logger.info("Successfully verified multiple profile updates with GET /users/me")
    
    logger.info("Multiple profile updates test passed")
    return True

def test_all_profile_fields_update():
    """Test updating all profile fields to ensure complete functionality"""
    global user_token, user_id
    
    logger.info("Testing update of all profile fields...")
    
    if not user_token:
        logger.error("User token not found, run test_user_registration first")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Update all profile fields
    profile_data = {
        "display_name": "Complete Test User",
        "age": 35,
        "gender": "non-binary",
        "location": "Seattle",
        "current_mood": "inspired",
        "mood_reason": "Testing all profile fields",
        "seeking_type": "friendship",
        "seeking_age_range": "30-50",
        "seeking_gender": "all",
        "seeking_location_preference": "anywhere",
        "connection_purpose": "Testing comprehensive profile updates",
        "additional_requirements": "Must be detail-oriented",
        "bio": "This is a comprehensive test of all profile fields",
        "interests": ["testing", "quality assurance", "software", "debugging"],
        "values": ["thoroughness", "precision", "reliability"]
    }
    
    logger.info(f"Updating all profile fields")
    
    response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update all profile fields: {response.text}")
        return False
    
    # Verify response includes all updated fields
    user_data = response.json()
    
    for key, value in profile_data.items():
        if key not in user_data or user_data[key] != value:
            logger.error(f"Field '{key}' not updated correctly. Expected: {value}, Got: {user_data.get(key)}")
            return False
    
    logger.info("Successfully updated all profile fields")
    
    # Verify with GET /users/me that all fields are updated correctly
    me_response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if me_response.status_code != 200:
        logger.error(f"Failed to get current user info after updating all fields: {me_response.text}")
        return False
    
    me_data = me_response.json()
    
    for key, value in profile_data.items():
        if key not in me_data or me_data[key] != value:
            logger.error(f"Field '{key}' not updated correctly in /users/me. Expected: {value}, Got: {me_data.get(key)}")
            return False
    
    logger.info("Successfully verified all profile fields update with GET /users/me")
    
    logger.info("All profile fields update test passed")
    return True

def run_tests():
    """Run all tests"""
    logger.info("Starting profile update tests...")
    
    # Test user registration
    if not test_user_registration():
        logger.error("User registration test failed")
        return False
    
    # Test initial profile completion with display_name
    if not test_complete_profile():
        logger.error("Profile completion test failed")
        return False
    
    # Test updating display_name
    if not test_update_display_name():
        logger.error("Display name update test failed")
        return False
    
    # Test multiple profile updates
    if not test_multiple_profile_updates():
        logger.error("Multiple profile updates test failed")
        return False
    
    # Test updating all profile fields
    if not test_all_profile_fields_update():
        logger.error("All profile fields update test failed")
        return False
    
    logger.info("All profile update tests passed successfully!")
    return True

if __name__ == "__main__":
    run_tests()