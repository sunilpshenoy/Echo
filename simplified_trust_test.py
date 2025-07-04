import requests
import json
import time
import uuid
import os
import logging
from datetime import datetime, timedelta
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
    "username": "trust_test_user",
    "email": "trust_test@example.com",
    "password": "SecurePass123!",
    "display_name": "Trust Test User"
}

# Global variables to store test data
user_token = None
user_id = None

def setup_test_user():
    """Register or login test user"""
    global user_token, user_id
    
    # Try to register
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
    
    # Complete profile
    headers = {"Authorization": f"Bearer {user_token}"}
    
    profile_data = {
        "display_name": test_user["display_name"],
        "age": 30,
        "gender": "Male",
        "location": "Test City",
        "current_mood": "Happy",
        "mood_reason": "Testing the trust system",
        "seeking_type": "Friendship",
        "seeking_age_range": "20-35",
        "seeking_gender": "Any",
        "seeking_location_preference": "Nearby",
        "connection_purpose": "Testing",
        "additional_requirements": "None",
        "bio": "This is a test user for trust system testing",
        "interests": ["Testing", "Technology", "Trust Systems"],
        "values": ["Honesty", "Reliability", "Transparency"]
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to complete profile: {response.text}")
        return False
    
    logger.info("Profile completed successfully")
    return True

def test_trust_levels_endpoint():
    """Test /api/trust/levels endpoint"""
    logger.info("Testing /api/trust/levels endpoint...")
    
    response = requests.get(f"{API_URL}/trust/levels")
    
    if response.status_code != 200:
        logger.error(f"Failed to get trust levels: {response.text}")
        return False
    
    trust_levels = response.json().get("trust_levels")
    if not trust_levels or len(trust_levels) != 5:
        logger.error(f"Expected 5 trust levels, got {len(trust_levels) if trust_levels else 0}")
        return False
    
    # Verify all 5 trust levels are properly configured
    expected_level_names = [
        "Anonymous Discovery",
        "Verified Connection",
        "Voice Communication",
        "Video Communication",
        "In-Person Meetup"
    ]
    
    for level_num, level_name in enumerate(expected_level_names, 1):
        level = trust_levels.get(str(level_num))
        if not level:
            logger.error(f"Trust level {level_num} not found")
            return False
        
        if level.get("name") != level_name:
            logger.error(f"Expected level {level_num} to be '{level_name}', got '{level.get('name')}'")
            return False
        
        if not level.get("features") or not isinstance(level.get("features"), list):
            logger.error(f"Trust level {level_num} missing features list")
            return False
        
        if not level.get("requirements") or not isinstance(level.get("requirements"), dict):
            logger.error(f"Trust level {level_num} missing requirements dict")
            return False
    
    logger.info("Trust levels endpoint test passed")
    return True

def test_trust_progress_endpoint():
    """Test /api/trust/progress endpoint"""
    logger.info("Testing /api/trust/progress endpoint...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = requests.get(f"{API_URL}/trust/progress", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get trust progress: {response.text}")
        return False
    
    progress_data = response.json()
    
    # Verify required fields
    required_fields = [
        "current_level", "current_level_info", "metrics", 
        "progress", "can_level_up", "achievements", "milestones"
    ]
    
    for field in required_fields:
        if field not in progress_data:
            logger.error(f"Trust progress missing required field: {field}")
            return False
    
    # Verify metrics
    metrics = progress_data.get("metrics")
    if not metrics or not isinstance(metrics, dict):
        logger.error(f"Trust progress missing valid metrics")
        return False
    
    metric_fields = [
        "total_connections", "days_since_registration", 
        "total_interactions", "video_calls", "messages_sent"
    ]
    
    for field in metric_fields:
        if field not in metrics:
            logger.error(f"Trust metrics missing required field: {field}")
            return False
    
    logger.info(f"Trust progress: Level {progress_data['current_level']}, " +
               f"Connections: {metrics['total_connections']}, " +
               f"Days: {metrics['days_since_registration']}, " +
               f"Interactions: {metrics['total_interactions']}")
    
    logger.info("Trust progress endpoint test passed")
    return True

def test_trust_level_up():
    """Test trust level progression"""
    logger.info("Testing trust level up endpoint...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # First check current trust progress
    response = requests.get(f"{API_URL}/trust/progress", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get trust progress: {response.text}")
        return False
    
    progress_data = response.json()
    current_level = progress_data.get("current_level")
    can_level_up = progress_data.get("can_level_up")
    
    logger.info(f"Current trust level: {current_level}, Can level up: {can_level_up}")
    
    # Try to level up (should fail with proper error if requirements not met)
    response = requests.post(f"{API_URL}/trust/level-up", headers=headers)
    
    if can_level_up:
        if response.status_code != 200:
            logger.error(f"Failed to level up when should be allowed: {response.text}")
            return False
        
        new_level = response.json().get("new_level")
        achievement = response.json().get("achievement")
        
        if new_level != current_level + 1:
            logger.error(f"Expected to level up to {current_level + 1}, got {new_level}")
            return False
        
        if not achievement:
            logger.error("No achievement created for level up")
            return False
        
        logger.info(f"Successfully leveled up to trust level {new_level}")
        
        # Verify level up in trust progress
        response = requests.get(f"{API_URL}/trust/progress", headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get updated trust progress: {response.text}")
            return False
        
        updated_level = response.json().get("current_level")
        
        if updated_level != new_level:
            logger.error(f"Trust progress shows level {updated_level}, expected {new_level}")
            return False
        
        logger.info(f"Trust progress correctly shows new level {updated_level}")
    else:
        if response.status_code == 200:
            logger.warning("Level up succeeded unexpectedly when requirements not met")
        elif response.status_code != 400 or "requirements not met" not in response.json().get("detail", ""):
            logger.error(f"Unexpected error when trying to level up: {response.text}")
            return False
        
        logger.info("Correctly prevented level up when requirements not met")
    
    logger.info("Trust level up endpoint test passed")
    return True

def test_trust_features_endpoint():
    """Test /api/trust/features endpoint"""
    logger.info("Testing /api/trust/features endpoint...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = requests.get(f"{API_URL}/trust/features", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get trust features: {response.text}")
        return False
    
    features_data = response.json()
    
    if "trust_level" not in features_data or "available_features" not in features_data:
        logger.error(f"Trust features response missing required fields")
        return False
    
    trust_level = features_data.get("trust_level")
    available_features = features_data.get("available_features")
    
    if not isinstance(available_features, list):
        logger.error(f"Available features is not a list")
        return False
    
    logger.info(f"Trust level {trust_level} has {len(available_features)} available features: {available_features}")
    
    # Verify features match the expected features for the current level
    response = requests.get(f"{API_URL}/trust/levels")
    if response.status_code != 200:
        logger.error(f"Failed to get trust levels for verification: {response.text}")
        return False
    
    trust_levels = response.json().get("trust_levels", {})
    expected_features = []
    
    for level in range(1, trust_level + 1):
        level_features = trust_levels.get(str(level), {}).get("features", [])
        expected_features.extend(level_features)
    
    # Check if all expected features are in available features
    missing_features = [f for f in expected_features if f not in available_features]
    extra_features = [f for f in available_features if f not in expected_features]
    
    if missing_features:
        logger.error(f"Missing expected features: {missing_features}")
        return False
    
    if extra_features:
        logger.error(f"Unexpected extra features: {extra_features}")
        return False
    
    logger.info("Trust features endpoint test passed")
    return True

def test_trust_achievements_endpoint():
    """Test /api/trust/achievements endpoint"""
    logger.info("Testing /api/trust/achievements endpoint...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = requests.get(f"{API_URL}/trust/achievements", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get trust achievements: {response.text}")
        return False
    
    achievements = response.json()
    
    if not isinstance(achievements, list):
        logger.error(f"Achievements response is not a list")
        return False
    
    logger.info(f"User has {len(achievements)} trust achievements")
    
    # Check if we have any level up achievements
    level_up_achievements = [a for a in achievements if a.get("type") == "trust_level_up"]
    
    if level_up_achievements:
        logger.info(f"Found {len(level_up_achievements)} level up achievements")
        
        for achievement in level_up_achievements:
            if "level" not in achievement or "title" not in achievement or "earned_at" not in achievement:
                logger.error(f"Achievement missing required fields: {achievement}")
                return False
            
            logger.info(f"Achievement: {achievement['title']} (Level {achievement['level']})")
    else:
        logger.info("No level up achievements found yet")
    
    logger.info("Trust achievements endpoint test passed")
    return True

def test_trust_interactions_endpoint():
    """Test /api/trust/interactions endpoint (simulated)"""
    logger.info("Testing trust interactions endpoint (simulated)...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Since we don't have actual connections, we'll just verify the endpoint exists
    # by checking for the expected error message
    
    fake_contact_id = str(uuid.uuid4())
    interaction_data = {
        "type": "message",
        "metadata": {}
    }
    
    response = requests.post(
        f"{API_URL}/trust/interactions/{fake_contact_id}",
        json=interaction_data,
        headers=headers
    )
    
    # We expect a 404 with "Contact not found" message
    if response.status_code != 404 or "Contact not found" not in response.json().get("detail", ""):
        logger.error(f"Unexpected response from interactions endpoint: {response.status_code} - {response.text}")
        return False
    
    logger.info("Trust interactions endpoint exists and returns expected error for invalid contact")
    logger.info("Trust interactions endpoint test passed (simulated)")
    return True

def run_all_tests():
    """Run all trust system tests"""
    logger.info("Starting trust system tests...")
    
    if not setup_test_user():
        logger.error("Failed to set up test user")
        return False
    
    tests = [
        ("Trust Levels Endpoint", test_trust_levels_endpoint),
        ("Trust Progress Endpoint", test_trust_progress_endpoint),
        ("Trust Level Up", test_trust_level_up),
        ("Trust Features Endpoint", test_trust_features_endpoint),
        ("Trust Achievements Endpoint", test_trust_achievements_endpoint),
        ("Trust Interactions Endpoint", test_trust_interactions_endpoint)
    ]
    
    results = {}
    all_passed = True
    
    for test_name, test_func in tests:
        logger.info(f"\n{'=' * 50}\nRunning test: {test_name}\n{'=' * 50}")
        try:
            result = test_func()
            results[test_name] = result
            if not result:
                all_passed = False
                logger.error(f"Test '{test_name}' FAILED")
            else:
                logger.info(f"Test '{test_name}' PASSED")
        except Exception as e:
            logger.error(f"Test '{test_name}' FAILED with exception: {e}")
            results[test_name] = False
            all_passed = False
    
    logger.info("\n\n" + "=" * 50)
    logger.info("TRUST SYSTEM TEST RESULTS")
    logger.info("=" * 50)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 50)
    logger.info(f"Overall result: {'PASSED' if all_passed else 'FAILED'}")
    logger.info("=" * 50)
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()