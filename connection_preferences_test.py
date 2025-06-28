import requests
import json
import logging
import os
import uuid
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

def test_connection_preferences_update():
    """
    Test the connection preferences editing functionality
    
    This test will:
    1. Create a test user
    2. Complete initial profile setup
    3. Test updating connection preferences fields:
       - current_mood
       - seeking_type
       - connection_purpose
    4. Verify each field updates correctly
    5. Test edge cases
    """
    logger.info("Testing connection preferences update...")
    
    # Generate unique user for this test
    unique_id = str(uuid.uuid4())[:8]
    test_user = {
        "username": f"conntest_{unique_id}",
        "email": f"conntest_{unique_id}@example.com",
        "password": "TestPass123!",
        "display_name": f"Connection Test User {unique_id}"
    }
    
    # Step 1: Register the test user
    logger.info("Registering test user...")
    response = requests.post(f"{API_URL}/register", json=test_user)
    
    if response.status_code != 200:
        logger.error(f"Failed to register test user: {response.text}")
        return False
    
    user_data = response.json()
    token = user_data["access_token"]
    user_id = user_data["user"]["user_id"]
    
    logger.info(f"Successfully registered user with ID: {user_id}")
    
    # Step 2: Complete initial profile setup
    logger.info("Setting up initial profile...")
    headers = {"Authorization": f"Bearer {token}"}
    
    initial_profile = {
        "age": 30,
        "gender": "non-binary",
        "location": "San Francisco, CA",
        "bio": "Testing connection preferences",
        "interests": ["technology", "testing", "API development"],
        "values": ["quality", "reliability", "thoroughness"],
        "current_mood": "Feeling optimistic and ready to connect",
        "seeking_type": "friendship",
        "connection_purpose": "Looking for meaningful conversations"
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=initial_profile, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to complete initial profile: {response.text}")
        return False
    
    # Verify initial profile was set correctly
    if (response.json().get("current_mood") != initial_profile["current_mood"] or
        response.json().get("seeking_type") != initial_profile["seeking_type"] or
        response.json().get("connection_purpose") != initial_profile["connection_purpose"]):
        logger.error(f"Initial profile not set correctly: {response.json()}")
        return False
    
    logger.info("Initial profile set successfully")
    
    # Step 3: Test updating each connection preference field individually
    
    # Test updating current_mood
    logger.info("Testing current_mood update...")
    update_data = {"current_mood": "Excited about new possibilities"}
    
    response = requests.put(f"{API_URL}/profile/complete", json=update_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update current_mood: {response.text}")
        return False
    
    if response.json().get("current_mood") != update_data["current_mood"]:
        logger.error(f"current_mood not updated correctly: {response.json()}")
        return False
    
    logger.info("current_mood updated successfully")
    
    # Test updating seeking_type
    logger.info("Testing seeking_type update...")
    update_data = {"seeking_type": "romantic"}
    
    response = requests.put(f"{API_URL}/profile/complete", json=update_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update seeking_type: {response.text}")
        return False
    
    if response.json().get("seeking_type") != update_data["seeking_type"]:
        logger.error(f"seeking_type not updated correctly: {response.json()}")
        return False
    
    logger.info("seeking_type updated successfully")
    
    # Test updating connection_purpose
    logger.info("Testing connection_purpose update...")
    update_data = {"connection_purpose": "Building deep, authentic relationships"}
    
    response = requests.put(f"{API_URL}/profile/complete", json=update_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update connection_purpose: {response.text}")
        return False
    
    if response.json().get("connection_purpose") != update_data["connection_purpose"]:
        logger.error(f"connection_purpose not updated correctly: {response.json()}")
        return False
    
    logger.info("connection_purpose updated successfully")
    
    # Step 4: Verify all fields persist with GET /api/users/me
    logger.info("Verifying field persistence with GET /api/users/me...")
    
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get user profile: {response.text}")
        return False
    
    user_profile = response.json()
    
    # Check if all fields are present with correct values
    if (user_profile.get("current_mood") != "Excited about new possibilities" or
        user_profile.get("seeking_type") != "romantic" or
        user_profile.get("connection_purpose") != "Building deep, authentic relationships"):
        logger.error(f"Field persistence verification failed: {user_profile}")
        return False
    
    logger.info("Field persistence verified successfully")
    
    # Step 5: Test updating all connection preferences fields at once
    logger.info("Testing updating all connection preferences fields at once...")
    
    update_data = {
        "current_mood": "Feeling adventurous",
        "seeking_type": "friendship",
        "connection_purpose": "Exploring new ideas and perspectives"
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=update_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update all fields at once: {response.text}")
        return False
    
    if (response.json().get("current_mood") != update_data["current_mood"] or
        response.json().get("seeking_type") != update_data["seeking_type"] or
        response.json().get("connection_purpose") != update_data["connection_purpose"]):
        logger.error(f"Multiple fields not updated correctly: {response.json()}")
        return False
    
    logger.info("Multiple fields updated successfully")
    
    # Step 6: Test edge cases
    
    # Test empty values
    logger.info("Testing empty values...")
    update_data = {
        "current_mood": "",
        "seeking_type": "",
        "connection_purpose": ""
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=update_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update with empty values: {response.text}")
        return False
    
    logger.info("Empty values test passed")
    
    # Test long text values
    logger.info("Testing long text values...")
    long_text = "A" * 1000  # 1000 character string
    update_data = {
        "current_mood": long_text,
        "seeking_type": long_text,
        "connection_purpose": long_text
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=update_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update with long text values: {response.text}")
        return False
    
    logger.info("Long text values test passed")
    
    # Test special characters
    logger.info("Testing special characters...")
    special_text = "!@#$%^&*()_+{}|:<>?~`-=[]\\;',./\"😀🔥💯"
    update_data = {
        "current_mood": special_text,
        "seeking_type": special_text,
        "connection_purpose": special_text
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=update_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update with special characters: {response.text}")
        return False
    
    logger.info("Special characters test passed")
    
    logger.info("All connection preferences update tests passed successfully!")
    return True

if __name__ == "__main__":
    test_connection_preferences_update()