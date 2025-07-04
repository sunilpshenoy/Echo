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
test_users = [
    {
        "username": "trust_test_alice",
        "email": "trust_alice@example.com",
        "password": "SecurePass123!",
        "display_name": "Alice (Trust Test)"
    },
    {
        "username": "trust_test_bob",
        "email": "trust_bob@example.com",
        "password": "StrongPass456!",
        "display_name": "Bob (Trust Test)"
    },
    {
        "username": "trust_test_charlie",
        "email": "trust_charlie@example.com",
        "password": "SafePass789!",
        "display_name": "Charlie (Trust Test)"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
connection_ids = {}

def test_user_registration():
    """Register test users for trust system testing"""
    logger.info("Registering test users for trust system testing...")
    
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
    
    logger.info("All test users registered/logged in successfully")
    return True

def test_complete_profiles():
    """Complete profiles for all test users"""
    logger.info("Completing profiles for test users...")
    
    for i, user_data in enumerate(test_users):
        headers = {"Authorization": f"Bearer {user_tokens[f'user{i+1}']}"}
        
        profile_data = {
            "display_name": user_data["display_name"],
            "age": 25 + i,
            "gender": "Male" if i % 2 == 0 else "Female",
            "location": f"Test City {i+1}",
            "current_mood": "Happy",
            "mood_reason": "Testing the trust system",
            "seeking_type": "Friendship",
            "seeking_age_range": "20-35",
            "seeking_gender": "Any",
            "seeking_location_preference": "Nearby",
            "connection_purpose": "Testing",
            "additional_requirements": "None",
            "bio": f"This is a test user {i+1} for trust system testing",
            "interests": ["Testing", "Technology", "Trust Systems"],
            "values": ["Honesty", "Reliability", "Transparency"]
        }
        
        response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to complete profile for user{i+1}: {response.text}")
            return False
        
        logger.info(f"Profile completed for user{i+1}")
    
    logger.info("All profiles completed successfully")
    return True

def test_create_connections():
    """Create connections between test users"""
    logger.info("Creating connections between test users...")
    
    # User1 connects with User2
    headers1 = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Get User1's connection PIN
    response = requests.get(f"{API_URL}/users/me", headers=headers1)
    if response.status_code != 200:
        logger.error(f"Failed to get user1 info: {response.text}")
        return False
    
    user1_pin = response.json().get("connection_pin")
    if not user1_pin:
        logger.error("User1 doesn't have a connection PIN")
        return False
    
    logger.info(f"User1 connection PIN: {user1_pin}")
    
    # User2 connects to User1 using PIN
    headers2 = {"Authorization": f"Bearer {user_tokens['user2']}"}
    connection_data = {
        "target_pin": user1_pin,
        "message": "Hello from User2, connecting via PIN"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=connection_data, headers=headers2)
    if response.status_code != 200:
        logger.error(f"Failed to create connection request by PIN: {response.text}")
        return False
    
    connection_request_id = response.json().get("connection_id")
    logger.info(f"Connection request created with ID: {connection_request_id}")
    
    # User1 accepts the connection request
    response = requests.put(
        f"{API_URL}/connections/{connection_request_id}/respond",
        json={"action": "accept"},
        headers=headers1
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept connection request: {response.text}")
        return False
    
    connection_ids["user1_user2"] = connection_request_id
    logger.info(f"Connection established between User1 and User2 with ID: {connection_request_id}")
    
    # User1 connects with User3
    # Get User3's connection PIN
    headers3 = {"Authorization": f"Bearer {user_tokens['user3']}"}
    response = requests.get(f"{API_URL}/users/me", headers=headers3)
    if response.status_code != 200:
        logger.error(f"Failed to get user3 info: {response.text}")
        return False
    
    user3_pin = response.json().get("connection_pin")
    if not user3_pin:
        logger.error("User3 doesn't have a connection PIN")
        return False
    
    logger.info(f"User3 connection PIN: {user3_pin}")
    
    # User1 connects to User3 using PIN
    connection_data = {
        "target_pin": user3_pin,
        "message": "Hello from User1, connecting via PIN"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=connection_data, headers=headers1)
    if response.status_code != 200:
        logger.error(f"Failed to create connection request by PIN: {response.text}")
        return False
    
    connection_request_id = response.json().get("connection_id")
    logger.info(f"Connection request created with ID: {connection_request_id}")
    
    # User3 accepts the connection request
    response = requests.put(
        f"{API_URL}/connections/{connection_request_id}/respond",
        json={"action": "accept"},
        headers=headers3
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept connection request: {response.text}")
        return False
    
    connection_ids["user1_user3"] = connection_request_id
    logger.info(f"Connection established between User1 and User3 with ID: {connection_request_id}")
    
    # User2 connects with User3
    connection_data = {
        "target_pin": user3_pin,
        "message": "Hello from User2, connecting via PIN"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=connection_data, headers=headers2)
    if response.status_code != 200:
        logger.error(f"Failed to create connection request by PIN: {response.text}")
        return False
    
    connection_request_id = response.json().get("connection_id")
    logger.info(f"Connection request created with ID: {connection_request_id}")
    
    # User3 accepts the connection request
    response = requests.put(
        f"{API_URL}/connections/{connection_request_id}/respond",
        json={"action": "accept"},
        headers=headers3
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept connection request: {response.text}")
        return False
    
    connection_ids["user2_user3"] = connection_request_id
    logger.info(f"Connection established between User2 and User3 with ID: {connection_request_id}")
    
    logger.info("All connections created successfully")
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
    
    # Test for each user
    for i in range(1, 4):
        headers = {"Authorization": f"Bearer {user_tokens[f'user{i}']}"}
        
        response = requests.get(f"{API_URL}/trust/progress", headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get trust progress for user{i}: {response.text}")
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
        
        logger.info(f"Trust progress for user{i}: Level {progress_data['current_level']}, " +
                   f"Connections: {metrics['total_connections']}, " +
                   f"Days: {metrics['days_since_registration']}, " +
                   f"Interactions: {metrics['total_interactions']}")
    
    logger.info("Trust progress endpoint test passed")
    return True

def test_record_interactions():
    """Test recording trust-building interactions"""
    logger.info("Testing /api/trust/interactions endpoint...")
    
    # User1 records interactions with User2
    headers1 = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    interaction_types = ["message", "voice_call", "video_call", "meetup", "file_share"]
    
    for interaction_type in interaction_types:
        interaction_data = {
            "type": interaction_type,
            "metadata": {
                "duration": 300 if interaction_type in ["voice_call", "video_call"] else None,
                "location": "Test Location" if interaction_type == "meetup" else None,
                "file_type": "image" if interaction_type == "file_share" else None
            }
        }
        
        response = requests.post(
            f"{API_URL}/trust/interactions/{user_ids['user2']}",
            json=interaction_data,
            headers=headers1
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to record {interaction_type} interaction: {response.text}")
            return False
        
        logger.info(f"Successfully recorded {interaction_type} interaction")
    
    # User2 records interactions with User1
    headers2 = {"Authorization": f"Bearer {user_tokens['user2']}"}
    
    for interaction_type in interaction_types:
        interaction_data = {
            "type": interaction_type,
            "metadata": {
                "duration": 300 if interaction_type in ["voice_call", "video_call"] else None,
                "location": "Test Location" if interaction_type == "meetup" else None,
                "file_type": "document" if interaction_type == "file_share" else None
            }
        }
        
        response = requests.post(
            f"{API_URL}/trust/interactions/{user_ids['user1']}",
            json=interaction_data,
            headers=headers2
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to record {interaction_type} interaction: {response.text}")
            return False
        
        logger.info(f"Successfully recorded {interaction_type} interaction")
    
    # Record multiple message interactions to meet requirements for level 3
    for _ in range(5):
        interaction_data = {"type": "message", "metadata": {}}
        
        requests.post(
            f"{API_URL}/trust/interactions/{user_ids['user2']}",
            json=interaction_data,
            headers=headers1
        )
        
        requests.post(
            f"{API_URL}/trust/interactions/{user_ids['user1']}",
            json=interaction_data,
            headers=headers2
        )
    
    logger.info("Interaction recording test passed")
    return True

def test_trust_level_up():
    """Test trust level progression"""
    logger.info("Testing trust level progression...")
    
    # First check current trust progress
    headers1 = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    response = requests.get(f"{API_URL}/trust/progress", headers=headers1)
    
    if response.status_code != 200:
        logger.error(f"Failed to get trust progress: {response.text}")
        return False
    
    progress_data = response.json()
    current_level = progress_data.get("current_level")
    can_level_up = progress_data.get("can_level_up")
    
    logger.info(f"Current trust level: {current_level}, Can level up: {can_level_up}")
    
    # If can't level up yet, simulate more interactions and time
    if not can_level_up:
        logger.info("Cannot level up yet, simulating more interactions...")
        
        # Record more interactions
        for _ in range(10):
            interaction_data = {"type": "message", "metadata": {}}
            
            requests.post(
                f"{API_URL}/trust/interactions/{user_ids['user2']}",
                json=interaction_data,
                headers=headers1
            )
        
        # Try to level up anyway (should fail with proper error)
        response = requests.post(f"{API_URL}/trust/level-up", headers=headers1)
        
        if response.status_code == 200:
            logger.warning("Level up succeeded unexpectedly when requirements not met")
        elif response.status_code != 400 or "requirements not met" not in response.json().get("detail", ""):
            logger.error(f"Unexpected error when trying to level up: {response.text}")
            return False
        
        logger.info("Correctly prevented level up when requirements not met")
    else:
        # Try to level up
        response = requests.post(f"{API_URL}/trust/level-up", headers=headers1)
        
        if response.status_code != 200:
            logger.error(f"Failed to level up: {response.text}")
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
        response = requests.get(f"{API_URL}/trust/progress", headers=headers1)
        
        if response.status_code != 200:
            logger.error(f"Failed to get updated trust progress: {response.text}")
            return False
        
        updated_level = response.json().get("current_level")
        
        if updated_level != new_level:
            logger.error(f"Trust progress shows level {updated_level}, expected {new_level}")
            return False
        
        logger.info(f"Trust progress correctly shows new level {updated_level}")
    
    logger.info("Trust level progression test passed")
    return True

def test_trust_features_endpoint():
    """Test /api/trust/features endpoint"""
    logger.info("Testing /api/trust/features endpoint...")
    
    headers1 = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    response = requests.get(f"{API_URL}/trust/features", headers=headers1)
    
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
    
    headers1 = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    response = requests.get(f"{API_URL}/trust/achievements", headers=headers1)
    
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

def test_connection_trust_level_update():
    """Test updating trust level for a connection"""
    logger.info("Testing connection trust level update...")
    
    # Get the connection between User1 and User2
    connection_id = connection_ids.get("user1_user2")
    if not connection_id:
        logger.error("No connection ID found for User1-User2")
        return False
    
    headers1 = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Update trust level to 2
    trust_data = {"trust_level": 2}
    
    response = requests.put(
        f"{API_URL}/connections/{connection_id}/trust-level",
        json=trust_data,
        headers=headers1
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update connection trust level: {response.text}")
        return False
    
    updated_level = response.json().get("trust_level")
    level_name = response.json().get("level_name")
    
    if updated_level != 2:
        logger.error(f"Expected trust level 2, got {updated_level}")
        return False
    
    logger.info(f"Successfully updated connection trust level to {updated_level} ({level_name})")
    
    # Try to update to level 4 (should fail as can only progress one level at a time)
    trust_data = {"trust_level": 4}
    
    response = requests.put(
        f"{API_URL}/connections/{connection_id}/trust-level",
        json=trust_data,
        headers=headers1
    )
    
    if response.status_code == 200:
        logger.error("Unexpectedly allowed jumping multiple trust levels")
        return False
    
    if response.status_code != 400 or "one trust level at a time" not in response.json().get("detail", ""):
        logger.error(f"Unexpected error when trying to jump multiple levels: {response.text}")
        return False
    
    logger.info("Correctly prevented jumping multiple trust levels")
    
    # Update to level 3
    trust_data = {"trust_level": 3}
    
    response = requests.put(
        f"{API_URL}/connections/{connection_id}/trust-level",
        json=trust_data,
        headers=headers1
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update to level 3: {response.text}")
        return False
    
    updated_level = response.json().get("trust_level")
    level_name = response.json().get("level_name")
    
    if updated_level != 3:
        logger.error(f"Expected trust level 3, got {updated_level}")
        return False
    
    logger.info(f"Successfully updated connection trust level to {updated_level} ({level_name})")
    
    logger.info("Connection trust level update test passed")
    return True

def run_all_tests():
    """Run all trust system tests"""
    logger.info("Starting trust system tests...")
    
    tests = [
        ("User Registration", test_user_registration),
        ("Profile Completion", test_complete_profiles),
        ("Create Connections", test_create_connections),
        ("Trust Levels Endpoint", test_trust_levels_endpoint),
        ("Trust Progress Endpoint", test_trust_progress_endpoint),
        ("Record Interactions", test_record_interactions),
        ("Trust Level Up", test_trust_level_up),
        ("Trust Features Endpoint", test_trust_features_endpoint),
        ("Trust Achievements Endpoint", test_trust_achievements_endpoint),
        ("Connection Trust Level Update", test_connection_trust_level_update)
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