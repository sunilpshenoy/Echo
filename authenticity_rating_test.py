import requests
import json
import time
import os
import logging
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
timestamp = int(time.time())
test_user = {
    "username": f"auth_test_user_{timestamp}",
    "email": f"auth_test_{timestamp}@example.com",
    "password": "SecureAuth123!",
    "phone": f"+1777{timestamp}"
}

# Global variables to store test data
user_token = None
user_id = None

def test_authenticity_rating_system():
    """Test the authenticity rating system"""
    global user_token, user_id
    
    # Step 1: Register test user
    logger.info("Step 1: Registering test user...")
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
    
    # Step 2: Complete profile with minimal information
    logger.info("Step 2: Completing user profile with minimal information...")
    headers = {"Authorization": f"Bearer {user_token}"}
    minimal_profile_data = {
        "display_name": f"Auth Test User {timestamp}",
        "age": 30,
        "gender": "non-binary",
        "location": "Test City"
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=minimal_profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to complete profile: {response.text}")
        return False
    
    logger.info("Profile completed with minimal information")
    
    # Step 3: Check initial authenticity rating
    logger.info("Step 3: Checking initial authenticity rating...")
    response = requests.get(f"{API_URL}/authenticity/details", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get authenticity details: {response.text}")
        return False
    
    initial_rating = response.json().get("total_rating", 0)
    initial_level = response.json().get("level", "")
    logger.info(f"Initial authenticity rating: {initial_rating}, level: {initial_level}")
    
    # Step 4: Complete profile with more information
    logger.info("Step 4: Updating profile with more information...")
    full_profile_data = {
        "display_name": f"Auth Test User {timestamp}",
        "age": 30,
        "gender": "non-binary",
        "location": "Test City",
        "current_mood": "Curious",
        "mood_reason": "Testing authenticity rating",
        "seeking_type": "Friendship",
        "seeking_age_range": "25-40",
        "seeking_gender": "Any",
        "seeking_location_preference": "Any",
        "connection_purpose": "Testing",
        "additional_requirements": "Interest in technology",
        "bio": "A test user for authenticity rating system",
        "interests": ["technology", "testing", "quality assurance", "software development"],
        "values": ["integrity", "honesty", "reliability", "transparency"]
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=full_profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update profile with more information: {response.text}")
        return False
    
    logger.info("Profile updated with more information")
    
    # Step 5: Check updated authenticity rating
    logger.info("Step 5: Checking updated authenticity rating...")
    response = requests.get(f"{API_URL}/authenticity/details", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get updated authenticity details: {response.text}")
        return False
    
    updated_rating = response.json().get("total_rating", 0)
    updated_level = response.json().get("level", "")
    logger.info(f"Updated authenticity rating: {updated_rating}, level: {updated_level}")
    
    # Verify rating improved
    if updated_rating <= initial_rating:
        logger.error(f"Authenticity rating did not improve after adding more profile information")
        return False
    
    logger.info(f"Authenticity rating improved from {initial_rating} to {updated_rating}")
    
    # Step 6: Check authenticity factors
    logger.info("Step 6: Checking authenticity factors...")
    factors = response.json().get("factors", {})
    
    required_factors = ["profile_completeness", "verification_status", "interaction_quality", 
                        "consistency", "community_feedback"]
    
    for factor in required_factors:
        if factor not in factors:
            logger.error(f"Missing required factor: {factor}")
            return False
        
        factor_data = factors[factor]
        logger.info(f"Factor: {factor}, Score: {factor_data.get('score')}/{factor_data.get('max_score')}")
        
        # Check factor has required fields
        required_fields = ["score", "max_score", "description", "tips"]
        for field in required_fields:
            if field not in factor_data:
                logger.error(f"Factor {factor} missing required field: {field}")
                return False
    
    # Step 7: Test authenticity update endpoint
    logger.info("Step 7: Testing authenticity update endpoint...")
    response = requests.put(f"{API_URL}/authenticity/update", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update authenticity rating: {response.text}")
        return False
    
    update_result = response.json()
    if "new_rating" not in update_result or "level" not in update_result:
        logger.error(f"Authenticity update response missing required fields: {update_result}")
        return False
    
    logger.info(f"Authenticity update successful. New rating: {update_result['new_rating']}, level: {update_result['level']}")
    
    # Step 8: Verify the update is reflected in user profile
    logger.info("Step 8: Verifying authenticity rating in user profile...")
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get user profile: {response.text}")
        return False
    
    user_data = response.json()
    if "authenticity_rating" not in user_data:
        logger.error("User profile missing authenticity_rating field")
        return False
    
    profile_rating = user_data["authenticity_rating"]
    logger.info(f"Authenticity rating in profile: {profile_rating}")
    
    # Verify the rating in profile matches the updated rating
    if abs(profile_rating - update_result["new_rating"]) > 0.1:
        logger.error(f"Authenticity rating mismatch: {profile_rating} vs {update_result['new_rating']}")
        return False
    
    logger.info("Authenticity rating system tests PASSED!")
    return True

if __name__ == "__main__":
    test_authenticity_rating_system()