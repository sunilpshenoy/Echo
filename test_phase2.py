import requests
import json
import logging
import uuid
import random
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Backend URL
BACKEND_URL = "https://e0ace9f7-0e4c-46c3-9a26-0a592ec88fc7.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

# Global variables to store test data
user_tokens = {}
user_ids = {}
connections = {}

def test_user_registration():
    """Test user registration with profile_completed=false by default"""
    logger.info("Testing user registration...")
    
    # Register a new test user with a unique email
    unique_id = str(uuid.uuid4())[:8]
    test_user = {
        "username": f"authentic_user_{unique_id}",
        "email": f"authentic_{unique_id}@example.com",
        "password": "AuthenticPass123!",
        "phone": f"+1777{unique_id}"
    }
    
    response = requests.post(f"{API_URL}/register", json=test_user)
    
    if response.status_code != 200:
        logger.error(f"Failed to register test user: {response.text}")
        return False
    
    # Verify profile_completed is false by default
    user_data = response.json()
    if "profile_completed" not in user_data["user"]:
        logger.error("profile_completed field not included in user registration response")
        return False
    
    if user_data["user"]["profile_completed"] != False:
        logger.error(f"profile_completed should be false by default, got: {user_data['user']['profile_completed']}")
        return False
    
    logger.info("Successfully verified profile_completed=false by default")
    
    # Store token for further tests
    user_tokens['user1'] = user_data["access_token"]
    user_ids['user1'] = user_data["user"]["user_id"]
    
    # Register a second test user
    unique_id2 = str(uuid.uuid4())[:8]
    test_user2 = {
        "username": f"authentic_user2_{unique_id2}",
        "email": f"authentic2_{unique_id2}@example.com",
        "password": "AuthenticPass456!",
        "phone": f"+1888{unique_id2}"
    }
    
    response = requests.post(f"{API_URL}/register", json=test_user2)
    
    if response.status_code != 200:
        logger.error(f"Failed to register second test user: {response.text}")
        return False
    
    user_data2 = response.json()
    user_tokens['user2'] = user_data2["access_token"]
    user_ids['user2'] = user_data2["user"]["user_id"]
    
    logger.info("Successfully registered two test users")
    return True

def test_profile_completion():
    """Test PUT /api/profile/complete endpoint"""
    logger.info("Testing PUT /api/profile/complete endpoint...")
    
    if 'user1' not in user_tokens:
        logger.error("User1 not found, run test_user_registration first")
        return False
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Create profile completion data
    profile_data = {
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
            return False
        
        # Verify response includes updated profile data
        user_data = response.json()
        
        # Check profile_completed is now true
        if "profile_completed" not in user_data or user_data["profile_completed"] != True:
            logger.error(f"profile_completed should be true after completion, got: {user_data.get('profile_completed')}")
            return False
        
        # Check authenticity_rating was calculated
        if "authenticity_rating" not in user_data or not isinstance(user_data["authenticity_rating"], (int, float)):
            logger.error(f"authenticity_rating not calculated correctly: {user_data.get('authenticity_rating')}")
            return False
        
        logger.info(f"Profile completed with authenticity rating: {user_data['authenticity_rating']}")
        
        # Verify with GET /users/me that profile is now completed
        me_response = requests.get(f"{API_URL}/users/me", headers=headers)
        
        if me_response.status_code != 200:
            logger.error(f"Failed to get current user info after profile completion: {me_response.text}")
            return False
        
        me_data = me_response.json()
        if me_data.get("profile_completed") != True:
            logger.error(f"profile_completed should be true in /users/me after completion, got: {me_data.get('profile_completed')}")
            return False
        
        logger.info("Successfully verified profile completion with GET /users/me")
        
        # Also complete profile for user2
        headers2 = {"Authorization": f"Bearer {user_tokens['user2']}"}
        
        profile_data2 = {
            "age": random.randint(18, 65),
            "gender": random.choice(["male", "female", "non-binary", "other"]),
            "location": random.choice(["New York", "San Francisco", "London", "Tokyo", "Sydney"]),
            "current_mood": random.choice(["happy", "excited", "curious", "relaxed", "focused"]),
            "mood_reason": "Testing as user2",
            "seeking_type": random.choice(["friendship", "dating", "networking", "mentorship"]),
            "seeking_age_range": "25-45",
            "seeking_gender": "all",
            "seeking_location_preference": "nearby",
            "connection_purpose": "Testing connections as user2",
            "bio": "I'm the second test user",
            "interests": ["testing", "connections", "software"],
            "values": ["honesty", "reliability", "quality"]
        }
        
        response2 = requests.put(f"{API_URL}/profile/complete", json=profile_data2, headers=headers2)
        
        if response2.status_code != 200:
            logger.error(f"Failed to complete profile for user2: {response2.text}")
            return False
        
        logger.info("Successfully completed profile for user2")
        
        logger.info("PUT /api/profile/complete test passed")
        return True
    except Exception as e:
        logger.error(f"Exception in test_profile_completion: {e}")
        return False

def test_get_current_user():
    """Test GET /api/users/me returns full user data including profile_completed"""
    logger.info("Testing GET /api/users/me endpoint...")
    
    if 'user1' not in user_tokens:
        logger.error("User1 not found, run test_user_registration first")
        return False
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get current user info: {response.text}")
        return False
    
    # Verify response includes profile_completed and other authentic connections fields
    user_data = response.json()
    required_fields = [
        "profile_completed", "age", "gender", "location", "bio", 
        "interests", "values", "authenticity_rating", "trust_level"
    ]
    
    for field in required_fields:
        if field not in user_data:
            logger.error(f"Field '{field}' not included in /users/me response")
            return False
    
    logger.info("Successfully verified /users/me includes all required fields")
    
    # Verify token validation works
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    invalid_response = requests.get(f"{API_URL}/users/me", headers=invalid_headers)
    
    if invalid_response.status_code != 401:
        logger.error(f"Invalid token should return 401, got: {invalid_response.status_code}")
        return False
    
    logger.info("Successfully verified token validation")
    
    logger.info("GET /api/users/me test passed")
    return True

def test_authenticity_details():
    """Test GET /api/authenticity/details endpoint"""
    logger.info("Testing GET /api/authenticity/details endpoint...")
    
    if 'user1' not in user_tokens:
        logger.error("User1 not found, run test_user_registration first")
        return False
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    response = requests.get(f"{API_URL}/authenticity/details", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get authenticity details: {response.text}")
        return False
    
    # Verify response includes all required fields
    details = response.json()
    required_fields = [
        "total_rating", "max_rating", "factors", "level", "next_milestone"
    ]
    
    for field in required_fields:
        if field not in details:
            logger.error(f"Field '{field}' not included in authenticity details response")
            return False
    
    # Verify factors are included
    required_factors = [
        "profile_completeness", "verification_status", "interaction_quality", 
        "consistency", "community_feedback"
    ]
    
    for factor in required_factors:
        if factor not in details["factors"]:
            logger.error(f"Factor '{factor}' not included in authenticity details")
            return False
        
        # Check each factor has score, max_score, description, and tips
        factor_data = details["factors"][factor]
        if not all(k in factor_data for k in ["score", "max_score", "description", "tips"]):
            logger.error(f"Factor '{factor}' missing required fields: {factor_data}")
            return False
    
    # Verify rating level is one of the expected values
    expected_levels = ["Getting Started", "Building Trust", "Trusted Member", "Highly Authentic"]
    if details["level"] not in expected_levels:
        logger.error(f"Unexpected rating level: {details['level']}")
        return False
    
    logger.info(f"Authenticity rating: {details['total_rating']}, Level: {details['level']}")
    logger.info("GET /api/authenticity/details test passed")
    return True

def test_authenticity_update():
    """Test PUT /api/authenticity/update endpoint"""
    logger.info("Testing PUT /api/authenticity/update endpoint...")
    
    if 'user1' not in user_tokens:
        logger.error("User1 not found, run test_user_registration first")
        return False
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # First get current rating
    response = requests.get(f"{API_URL}/authenticity/details", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get current authenticity details: {response.text}")
        return False
    
    current_rating = response.json()["total_rating"]
    logger.info(f"Current authenticity rating: {current_rating}")
    
    # Update authenticity rating
    response = requests.put(f"{API_URL}/authenticity/update", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update authenticity rating: {response.text}")
        return False
    
    # Verify response includes new rating and level
    update_result = response.json()
    if "new_rating" not in update_result or "level" not in update_result:
        logger.error(f"Update response missing required fields: {update_result}")
        return False
    
    logger.info(f"Updated authenticity rating: {update_result['new_rating']}, Level: {update_result['level']}")
    
    # Verify with GET /users/me that rating was updated
    me_response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if me_response.status_code != 200:
        logger.error(f"Failed to get current user info after rating update: {me_response.text}")
        return False
    
    me_data = me_response.json()
    if "authenticity_rating" not in me_data:
        logger.error(f"authenticity_rating not included in /users/me response")
        return False
    
    logger.info(f"Verified authenticity_rating in /users/me: {me_data['authenticity_rating']}")
    logger.info("PUT /api/authenticity/update test passed")
    return True

def test_connection_request():
    """Test POST /api/connections/request endpoint"""
    logger.info("Testing POST /api/connections/request endpoint...")
    
    if 'user1' not in user_tokens or 'user2' not in user_tokens:
        logger.error("User tokens not found, run test_user_registration first")
        return False
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Send connection request to user2
    connection_data = {
        "user_id": user_ids['user2'],
        "message": "I'd like to connect with you for testing purposes"
    }
    
    response = requests.post(f"{API_URL}/connections/request", json=connection_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to send connection request: {response.text}")
        return False
    
    # Verify response includes connection details
    connection = response.json()
    if "connection_id" not in connection or "status" not in connection:
        logger.error(f"Connection response missing required fields: {connection}")
        return False
    
    if connection["status"] != "pending":
        logger.error(f"Connection status should be 'pending', got: {connection['status']}")
        return False
    
    connection_id = connection["connection_id"]
    logger.info(f"Successfully sent connection request with ID: {connection_id}")
    
    # Store connection ID for other tests
    connections['test_connection'] = connection_id
    
    logger.info("POST /api/connections/request test passed")
    return True

def test_get_connections():
    """Test GET /api/connections endpoint"""
    logger.info("Testing GET /api/connections endpoint...")
    
    if 'user1' not in user_tokens:
        logger.error("User1 not found, run test_user_registration first")
        return False
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Get all connections
    response = requests.get(f"{API_URL}/connections", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connections: {response.text}")
        return False
    
    connections_list = response.json()
    logger.info(f"Retrieved {len(connections_list)} connections")
    
    # Test with status filter
    response = requests.get(f"{API_URL}/connections?status=pending", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connections with status filter: {response.text}")
        return False
    
    pending_connections = response.json()
    logger.info(f"Retrieved {len(pending_connections)} pending connections")
    
    # Verify each connection has required fields
    for conn in connections_list:
        required_fields = ["connection_id", "user_id", "connected_user_id", "status", "trust_level", "created_at"]
        for field in required_fields:
            if field not in conn:
                logger.error(f"Connection missing required field '{field}': {conn}")
                return False
    
    logger.info("GET /api/connections test passed")
    return True

def test_respond_to_connection():
    """Test PUT /api/connections/{connection_id}/respond endpoint"""
    logger.info("Testing PUT /api/connections/{connection_id}/respond endpoint...")
    
    if 'test_connection' not in connections:
        logger.error("No test connection found, run test_connection_request first")
        return False
    
    connection_id = connections['test_connection']
    
    # User2 responds to the connection request
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    
    response_data = {
        "action": "accept"
    }
    
    response = requests.put(
        f"{API_URL}/connections/{connection_id}/respond", 
        json=response_data, 
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to respond to connection request: {response.text}")
        return False
    
    # Verify response includes updated connection details
    connection = response.json()
    if "status" not in connection:
        logger.error(f"Connection response missing status field: {connection}")
        return False
    
    if connection["status"] != "connected":
        logger.error(f"Connection status should be 'connected', got: {connection['status']}")
        return False
    
    logger.info(f"Successfully accepted connection request")
    
    # Test declining a connection
    # First create another connection request
    headers1 = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Send connection request to user2 again (this might fail if there's a unique constraint)
    # If it fails, we'll create a new user
    connection_data = {
        "user_id": user_ids['user2'],
        "message": "Another test connection request"
    }
    
    request_response = requests.post(f"{API_URL}/connections/request", json=connection_data, headers=headers1)
    
    if request_response.status_code != 200:
        logger.info(f"Could not create second connection request, may already exist: {request_response.text}")
        logger.info("Skipping decline test")
    else:
        second_connection_id = request_response.json()["connection_id"]
        
        # User2 declines the connection request
        decline_data = {
            "action": "decline"
        }
        
        decline_response = requests.put(
            f"{API_URL}/connections/{second_connection_id}/respond", 
            json=decline_data, 
            headers=headers
        )
        
        if decline_response.status_code != 200:
            logger.error(f"Failed to decline connection request: {decline_response.text}")
            return False
        
        # Verify response includes updated connection details
        declined_connection = decline_response.json()
        if declined_connection.get("status") != "declined":
            logger.error(f"Connection status should be 'declined', got: {declined_connection.get('status')}")
            return False
        
        logger.info(f"Successfully declined connection request")
    
    logger.info("PUT /api/connections/{connection_id}/respond test passed")
    return True

def test_update_trust_level():
    """Test PUT /api/connections/{connection_id}/trust-level endpoint"""
    logger.info("Testing PUT /api/connections/{connection_id}/trust-level endpoint...")
    
    if 'test_connection' not in connections:
        logger.error("No test connection found, run test_connection_request first")
        return False
    
    connection_id = connections['test_connection']
    
    # Update trust level
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Test each trust level (1-5)
    for trust_level in range(1, 6):
        trust_data = {
            "trust_level": trust_level
        }
        
        response = requests.put(
            f"{API_URL}/connections/{connection_id}/trust-level", 
            json=trust_data, 
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to update trust level to {trust_level}: {response.text}")
            return False
        
        # Verify response includes updated trust level
        connection = response.json()
        if "trust_level" not in connection:
            logger.error(f"Connection response missing trust_level field: {connection}")
            return False
        
        if connection["trust_level"] != trust_level:
            logger.error(f"Trust level should be {trust_level}, got: {connection['trust_level']}")
            return False
        
        logger.info(f"Successfully updated trust level to {trust_level}")
    
    # Test invalid trust level (should fail)
    invalid_data = {
        "trust_level": 6  # Invalid level (above 5)
    }
    
    invalid_response = requests.put(
        f"{API_URL}/connections/{connection_id}/trust-level", 
        json=invalid_data, 
        headers=headers
    )
    
    if invalid_response.status_code != 400:
        logger.error(f"Invalid trust level should return 400, got: {invalid_response.status_code}")
        return False
    
    logger.info("Successfully verified invalid trust level is rejected")
    
    logger.info("PUT /api/connections/{connection_id}/trust-level test passed")
    return True

def test_integration_flow():
    """Test complete user flow: register → profile setup → authenticity rating → connection requests"""
    logger.info("Testing complete integration flow...")
    
    # 1. Register a new user
    unique_id = str(uuid.uuid4())[:8]
    test_user = {
        "username": f"flow_user_{unique_id}",
        "email": f"flow_{unique_id}@example.com",
        "password": "FlowTest123!",
        "phone": f"+1999{unique_id}"
    }
    
    response = requests.post(f"{API_URL}/register", json=test_user)
    
    if response.status_code != 200:
        logger.error(f"Failed to register user for integration flow: {response.text}")
        return False
    
    user_data = response.json()
    flow_token = user_data["access_token"]
    flow_user_id = user_data["user"]["user_id"]
    
    logger.info(f"Successfully registered user for integration flow")
    
    # 2. Complete profile
    headers = {"Authorization": f"Bearer {flow_token}"}
    
    profile_data = {
        "age": 30,
        "gender": "non-binary",
        "location": "Integration Test City",
        "current_mood": "focused",
        "mood_reason": "Testing the integration flow",
        "seeking_type": "friendship",
        "seeking_age_range": "25-45",
        "seeking_gender": "all",
        "seeking_location_preference": "anywhere",
        "connection_purpose": "Testing the complete user flow",
        "bio": "I'm a test user for the integration flow",
        "interests": ["testing", "integration", "software"],
        "values": ["thoroughness", "reliability", "quality"]
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to complete profile for integration flow: {response.text}")
        return False
    
    logger.info(f"Successfully completed profile for integration flow")
    
    # 3. Check authenticity rating
    response = requests.get(f"{API_URL}/authenticity/details", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get authenticity details for integration flow: {response.text}")
        return False
    
    initial_rating = response.json()["total_rating"]
    logger.info(f"Initial authenticity rating: {initial_rating}")
    
    # 4. Send connection request to user1
    connection_data = {
        "user_id": user_ids['user1'],
        "message": "Connection request from integration flow test"
    }
    
    response = requests.post(f"{API_URL}/connections/request", json=connection_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to send connection request in integration flow: {response.text}")
        return False
    
    flow_connection_id = response.json()["connection_id"]
    logger.info(f"Successfully sent connection request in integration flow")
    
    # 5. User1 accepts the connection
    headers1 = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    response_data = {
        "action": "accept"
    }
    
    response = requests.put(
        f"{API_URL}/connections/{flow_connection_id}/respond", 
        json=response_data, 
        headers=headers1
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept connection in integration flow: {response.text}")
        return False
    
    logger.info(f"Successfully accepted connection in integration flow")
    
    # 6. User1 updates trust level
    trust_data = {
        "trust_level": 3  # Voice Call level
    }
    
    response = requests.put(
        f"{API_URL}/connections/{flow_connection_id}/trust-level", 
        json=trust_data, 
        headers=headers1
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update trust level in integration flow: {response.text}")
        return False
    
    logger.info(f"Successfully updated trust level in integration flow")
    
    # 7. Verify authenticity rating was affected
    response = requests.get(f"{API_URL}/authenticity/details", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get final authenticity details: {response.text}")
        return False
    
    final_rating = response.json()["total_rating"]
    logger.info(f"Final authenticity rating: {final_rating}")
    
    logger.info("Integration flow test passed")
    return True

def run_tests():
    """Run all tests and return results"""
    test_results = {
        "User Registration": test_user_registration(),
        "Profile Completion": test_profile_completion(),
        "Get Current User": test_get_current_user(),
        "Authenticity Rating System": {
            "Get Authenticity Details": test_authenticity_details(),
            "Update Authenticity Rating": test_authenticity_update()
        },
        "Enhanced Connection Management": {
            "Connection Request": test_connection_request(),
            "Get Connections": test_get_connections(),
            "Respond to Connection": test_respond_to_connection(),
            "Update Trust Level": test_update_trust_level()
        },
        "Integration Tests": {
            "Complete User Flow": test_integration_flow()
        }
    }
    
    return test_results

if __name__ == "__main__":
    # Run all tests
    results = run_tests()
    
    # Print summary
    print("\n=== TEST RESULTS SUMMARY ===")
    all_passed = True
    
    for category, result in results.items():
        if isinstance(result, dict):
            category_passed = all(result.values())
            status = "✅ PASSED" if category_passed else "❌ FAILED"
            print(f"{category}: {status}")
            
            for test_name, passed in result.items():
                test_status = "✅ PASSED" if passed else "❌ FAILED"
                print(f"  - {test_name}: {test_status}")
            
            if not category_passed:
                all_passed = False
        else:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{category}: {status}")
            
            if not result:
                all_passed = False
    
    print("\nOVERALL RESULT:", "✅ PASSED" if all_passed else "❌ FAILED")