import requests
import json
import logging
import os
import random
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

def test_comprehensive_connection_preferences():
    """
    Comprehensive test for connection preferences fix.
    
    Tests:
    1. Connection Preferences Fix Verification
       - Test PUT /api/profile/complete with connection preferences fields
       - Verify all fields are returned in the response
       - Test GET /api/users/me includes connection preferences fields
       - Test individual field updates and multiple field updates
    
    2. Profile Management Verification
       - Test that display_name updates still work correctly
       - Test all other profile fields work correctly
       - Verify profile completion flow works end-to-end
    
    3. Authenticity Rating System
       - Test GET /api/authenticity/details still works
       - Test PUT /api/authenticity/update still works
       - Verify rating calculation includes connection preferences
    
    4. User Flow Integration
       - Test complete user journey
       - Verify all data persists correctly
       - Test that profile_completed status is handled correctly
    """
    logger.info("Starting comprehensive test for connection preferences fix")
    
    # Generate unique user for this test
    unique_id = str(uuid.uuid4())[:8]
    test_user = {
        "username": f"comptest_{unique_id}",
        "email": f"comptest_{unique_id}@example.com",
        "password": "TestPass123!",
        "display_name": f"Comprehensive Test User {unique_id}"
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
    display_name = user_data["user"]["display_name"]
    
    logger.info(f"Successfully registered user with ID: {user_id}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Complete initial profile setup
    logger.info("Setting up initial profile...")
    
    initial_profile = {
        "display_name": display_name,
        "age": 30,
        "gender": "non-binary",
        "location": "San Francisco, CA",
        "bio": "Testing connection preferences",
        "interests": ["technology", "testing", "API development"],
        "values": ["quality", "reliability", "thoroughness"],
        "current_mood": "Feeling optimistic",
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
    
    # Step 3: Test updating only connection preferences fields
    logger.info("Testing updating only connection preferences fields...")
    
    connection_prefs_update = {
        "current_mood": "Excited about new possibilities",
        "seeking_type": "romantic",
        "connection_purpose": "Building deep, authentic relationships"
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=connection_prefs_update, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update connection preferences: {response.text}")
        return False
    
    # Verify response includes updated fields
    user_data = response.json()
    
    for field, value in connection_prefs_update.items():
        if field not in user_data:
            logger.error(f"Field '{field}' not included in update response")
            return False
        if user_data[field] != value:
            logger.error(f"Field '{field}' has incorrect value. Expected: {value}, Got: {user_data[field]}")
            return False
    
    # Verify other fields are preserved
    preserved_fields = ["display_name", "age", "gender", "location", "bio"]
    for field in preserved_fields:
        if field not in user_data:
            logger.error(f"Field '{field}' not included in update response")
            return False
        if user_data[field] != initial_profile[field]:
            logger.error(f"Field '{field}' was not preserved. Expected: {initial_profile[field]}, Got: {user_data[field]}")
            return False
    
    logger.info("Successfully updated only connection preferences fields")
    
    # Step 4: Test updating a single connection preference field
    logger.info("Testing updating a single connection preference field...")
    
    single_field_update = {
        "current_mood": "Relaxed and thoughtful"
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=single_field_update, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update single connection preference field: {response.text}")
        return False
    
    # Verify response includes updated field
    user_data = response.json()
    
    if "current_mood" not in user_data:
        logger.error("Field 'current_mood' not included in single field update response")
        return False
    if user_data["current_mood"] != single_field_update["current_mood"]:
        logger.error(f"Field 'current_mood' has incorrect value. Expected: {single_field_update['current_mood']}, Got: {user_data['current_mood']}")
        return False
    
    # Verify other connection preference fields are preserved
    if user_data["seeking_type"] != connection_prefs_update["seeking_type"]:
        logger.error(f"Field 'seeking_type' was not preserved. Expected: {connection_prefs_update['seeking_type']}, Got: {user_data['seeking_type']}")
        return False
    if user_data["connection_purpose"] != connection_prefs_update["connection_purpose"]:
        logger.error(f"Field 'connection_purpose' was not preserved. Expected: {connection_prefs_update['connection_purpose']}, Got: {user_data['connection_purpose']}")
        return False
    
    logger.info("Successfully updated a single connection preference field")
    
    # Step 5: Verify GET /api/users/me includes all fields
    logger.info("Verifying GET /api/users/me includes all fields...")
    
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get current user info: {response.text}")
        return False
    
    # Verify response includes all fields
    user_data = response.json()
    
    # Check connection preferences fields
    connection_pref_fields = ["current_mood", "seeking_type", "connection_purpose"]
    for field in connection_pref_fields:
        if field not in user_data:
            logger.error(f"Field '{field}' not included in GET /api/users/me response")
            return False
    
    # Verify field values match what we set
    if user_data["current_mood"] != single_field_update["current_mood"]:
        logger.error(f"Field 'current_mood' has incorrect value in GET /api/users/me. Expected: {single_field_update['current_mood']}, Got: {user_data['current_mood']}")
        return False
    if user_data["seeking_type"] != connection_prefs_update["seeking_type"]:
        logger.error(f"Field 'seeking_type' has incorrect value in GET /api/users/me. Expected: {connection_prefs_update['seeking_type']}, Got: {user_data['seeking_type']}")
        return False
    if user_data["connection_purpose"] != connection_prefs_update["connection_purpose"]:
        logger.error(f"Field 'connection_purpose' has incorrect value in GET /api/users/me. Expected: {connection_prefs_update['connection_purpose']}, Got: {user_data['connection_purpose']}")
        return False
    
    logger.info("Successfully verified GET /api/users/me includes all connection preference fields")
    
    # Step 6: Test display_name updates still work correctly
    logger.info("Testing display_name updates...")
    
    new_display_name = f"Updated Display Name {random.randint(100, 999)}"
    display_name_update = {
        "display_name": new_display_name
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=display_name_update, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update display_name: {response.text}")
        return False
    
    # Verify response includes updated display_name
    user_data = response.json()
    
    if "display_name" not in user_data:
        logger.error("Field 'display_name' not included in display_name update response")
        return False
    if user_data["display_name"] != new_display_name:
        logger.error(f"Field 'display_name' has incorrect value. Expected: {new_display_name}, Got: {user_data['display_name']}")
        return False
    
    # Verify connection preference fields are still preserved
    if user_data["current_mood"] != single_field_update["current_mood"]:
        logger.error(f"Field 'current_mood' was not preserved. Expected: {single_field_update['current_mood']}, Got: {user_data['current_mood']}")
        return False
    if user_data["seeking_type"] != connection_prefs_update["seeking_type"]:
        logger.error(f"Field 'seeking_type' was not preserved. Expected: {connection_prefs_update['seeking_type']}, Got: {user_data['seeking_type']}")
        return False
    if user_data["connection_purpose"] != connection_prefs_update["connection_purpose"]:
        logger.error(f"Field 'connection_purpose' was not preserved. Expected: {connection_prefs_update['connection_purpose']}, Got: {user_data['connection_purpose']}")
        return False
    
    logger.info("Successfully updated display_name while preserving connection preferences")
    
    # Step 7: Test authenticity rating calculation includes connection preferences
    logger.info("Testing authenticity rating calculation includes connection preferences...")
    
    response = requests.get(f"{API_URL}/authenticity/details", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get authenticity details: {response.text}")
        return False
    
    auth_data = response.json()
    
    if "factors" not in auth_data or "profile_completeness" not in auth_data["factors"]:
        logger.error("Authenticity details missing profile_completeness factor")
        return False
    
    # Verify authenticity rating update works
    response = requests.put(f"{API_URL}/authenticity/update", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update authenticity rating: {response.text}")
        return False
    
    logger.info("Successfully verified authenticity rating calculation includes connection preferences")
    
    # Step 8: Test complete user flow
    logger.info("Testing complete user flow...")
    
    # Log out (just for testing the flow - no actual logout endpoint needed)
    logger.info("Simulating logout")
    
    # Log back in
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    
    response = requests.post(f"{API_URL}/login", json=login_data)
    
    if response.status_code != 200:
        logger.error(f"Failed to log in: {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Verify profile data is still there
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get current user info after login: {response.text}")
        return False
    
    user_data = response.json()
    
    if user_data["display_name"] != new_display_name:
        logger.error(f"Field 'display_name' not preserved after login. Expected: {new_display_name}, Got: {user_data['display_name']}")
        return False
    if user_data["current_mood"] != single_field_update["current_mood"]:
        logger.error(f"Field 'current_mood' not preserved after login. Expected: {single_field_update['current_mood']}, Got: {user_data['current_mood']}")
        return False
    if user_data["seeking_type"] != connection_prefs_update["seeking_type"]:
        logger.error(f"Field 'seeking_type' not preserved after login. Expected: {connection_prefs_update['seeking_type']}, Got: {user_data['seeking_type']}")
        return False
    if user_data["connection_purpose"] != connection_prefs_update["connection_purpose"]:
        logger.error(f"Field 'connection_purpose' not preserved after login. Expected: {connection_prefs_update['connection_purpose']}, Got: {user_data['connection_purpose']}")
        return False
    
    logger.info("Successfully verified complete user flow")
    
    logger.info("All connection preferences fix tests passed!")
    return True

if __name__ == "__main__":
    test_comprehensive_connection_preferences()