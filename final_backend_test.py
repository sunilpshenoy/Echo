import requests
import json
import time
import os
import logging
import uuid
from dotenv import load_dotenv
from io import BytesIO
from datetime import datetime

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
test_users = [
    {
        "username": f"alice_smith_{timestamp}",
        "email": f"alice.smith_{timestamp}@example.com",
        "password": "SecurePass123!",
        "phone": f"+1234567{timestamp}",
        "display_name": f"Alice Smith {timestamp}"
    },
    {
        "username": f"bob_johnson_{timestamp}",
        "email": f"bob.johnson_{timestamp}@example.com",
        "password": "StrongPass456!",
        "phone": f"+1987654{timestamp}",
        "display_name": f"Bob Johnson {timestamp}"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
user_pins = {}
connection_requests = {}
connections = {}
chat_ids = {}
message_ids = {}

def test_user_registration_and_login():
    """Test user registration and login endpoints"""
    logger.info("Testing user registration and login...")
    
    # Register and login users
    for i, user_data in enumerate(test_users):
        # Try registration
        response = requests.post(f"{API_URL}/register", json=user_data)
        
        if response.status_code == 200:
            logger.info(f"User {user_data['username']} registered successfully")
            user_tokens[f"user{i+1}"] = response.json()["access_token"]
            user_ids[f"user{i+1}"] = response.json()["user"]["user_id"]
        elif response.status_code == 400 and "Email already registered" in response.json()["detail"]:
            # User already exists, try logging in
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
    
    logger.info("User registration and login tests passed")
    return True

def test_get_current_user():
    """Test GET /api/users/me endpoint"""
    logger.info("Testing GET /api/users/me endpoint...")
    
    # Test with valid token
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get current user: {response.text}")
        return False
    
    user_data = response.json()
    required_fields = ["user_id", "username", "email", "profile_completed"]
    for field in required_fields:
        if field not in user_data:
            logger.error(f"User data missing required field: {field}")
            return False
    
    logger.info("Current user data retrieved successfully")
    
    # Test with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{API_URL}/users/me", headers=headers)
    
    if response.status_code != 401:
        logger.error("Invalid token test failed")
        return False
    
    logger.info("GET /api/users/me tests passed")
    return True

def test_profile_completion():
    """Test profile completion endpoint"""
    logger.info("Testing profile completion...")
    
    # Complete profile for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    profile_data = {
        "display_name": test_users[0]["display_name"],
        "age": 28,
        "gender": "female",
        "location": "New York, NY",
        "current_mood": "Excited",
        "mood_reason": "Testing this awesome app",
        "seeking_type": "Friendship",
        "seeking_age_range": "25-35",
        "seeking_gender": "Any",
        "seeking_location_preference": "Nearby",
        "connection_purpose": "Networking",
        "additional_requirements": "Tech enthusiasts preferred",
        "bio": "Software engineer who loves hiking and photography",
        "interests": ["technology", "hiking", "photography", "travel"],
        "values": ["honesty", "creativity", "growth"]
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to complete profile for user1: {response.text}")
        return False
    
    # Check if profile_completed is set to true
    if not response.json().get("profile_completed"):
        logger.error("Profile not marked as completed for user1")
        return False
    
    # Check if connection_pin is generated
    if "connection_pin" in response.json():
        user_pins["user1"] = response.json()["connection_pin"]
        logger.info(f"User1 connection PIN: {user_pins['user1']}")
    else:
        # If connection_pin is not in the response, try to get it from /api/users/me
        me_response = requests.get(f"{API_URL}/users/me", headers=headers)
        if me_response.status_code == 200 and "connection_pin" in me_response.json():
            user_pins["user1"] = me_response.json()["connection_pin"]
            logger.info(f"User1 connection PIN (from /api/users/me): {user_pins['user1']}")
        else:
            # Try to get it from QR code endpoint
            qr_response = requests.get(f"{API_URL}/users/qr-code", headers=headers)
            if qr_response.status_code == 200 and "connection_pin" in qr_response.json():
                user_pins["user1"] = qr_response.json()["connection_pin"]
                logger.info(f"User1 connection PIN (from QR code): {user_pins['user1']}")
            else:
                logger.warning("Could not find connection PIN for user1")
    
    # Complete profile for user2
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    profile_data = {
        "display_name": test_users[1]["display_name"],
        "age": 32,
        "gender": "male",
        "location": "San Francisco, CA",
        "current_mood": "Curious",
        "mood_reason": "Exploring new connections",
        "seeking_type": "Professional",
        "seeking_age_range": "25-40",
        "seeking_gender": "Any",
        "seeking_location_preference": "Any",
        "connection_purpose": "Career growth",
        "additional_requirements": "Tech industry professionals",
        "bio": "Product manager with a passion for AI and machine learning",
        "interests": ["artificial intelligence", "product management", "startups", "hiking"],
        "values": ["innovation", "integrity", "teamwork"]
    }
    
    response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to complete profile for user2: {response.text}")
        return False
    
    # Check if connection_pin is generated
    if "connection_pin" in response.json():
        user_pins["user2"] = response.json()["connection_pin"]
        logger.info(f"User2 connection PIN: {user_pins['user2']}")
    else:
        # If connection_pin is not in the response, try to get it from /api/users/me
        me_response = requests.get(f"{API_URL}/users/me", headers=headers)
        if me_response.status_code == 200 and "connection_pin" in me_response.json():
            user_pins["user2"] = me_response.json()["connection_pin"]
            logger.info(f"User2 connection PIN (from /api/users/me): {user_pins['user2']}")
        else:
            # Try to get it from QR code endpoint
            qr_response = requests.get(f"{API_URL}/users/qr-code", headers=headers)
            if qr_response.status_code == 200 and "connection_pin" in qr_response.json():
                user_pins["user2"] = qr_response.json()["connection_pin"]
                logger.info(f"User2 connection PIN (from QR code): {user_pins['user2']}")
            else:
                logger.warning("Could not find connection PIN for user2")
    
    logger.info("Profile completion tests passed")
    return True

def test_qr_code_generation():
    """Test QR code generation endpoint"""
    logger.info("Testing QR code generation...")
    
    # Get QR code for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/users/qr-code", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get QR code for user1: {response.text}")
        return False
    
    qr_data = response.json()
    if "qr_code" not in qr_data:
        logger.error(f"QR code response missing qr_code field: {qr_data}")
        return False
    
    if "connection_pin" in qr_data and not user_pins.get("user1"):
        user_pins["user1"] = qr_data["connection_pin"]
        logger.info(f"User1 connection PIN (from QR code): {user_pins['user1']}")
    
    # Get QR code for user2
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.get(f"{API_URL}/users/qr-code", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get QR code for user2: {response.text}")
        return False
    
    if "connection_pin" in response.json() and not user_pins.get("user2"):
        user_pins["user2"] = response.json()["connection_pin"]
        logger.info(f"User2 connection PIN (from QR code): {user_pins['user2']}")
    
    logger.info("QR code generation tests passed")
    return True

def test_connection_request_by_pin():
    """Test connection request by PIN endpoint"""
    logger.info("Testing connection request by PIN...")
    
    # Make sure we have PINs for both users
    if not user_pins.get("user1") or not user_pins.get("user2"):
        logger.error("Missing connection PINs for users")
        return False
    
    # User2 requests connection with User1 using PIN
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    
    # Check if the endpoint is /connections/request-by-pin or /connections/request
    endpoints = [
        f"{API_URL}/connections/request-by-pin",
        f"{API_URL}/connections/request"
    ]
    
    request_data = {
        "pin": user_pins["user1"],
        "target_pin": user_pins["user1"],  # Try both field names
        "message": "Hi Alice, I'd like to connect!"
    }
    
    success = False
    for endpoint in endpoints:
        response = requests.post(endpoint, json=request_data, headers=headers)
        if response.status_code == 200:
            success = True
            logger.info(f"Connection request successful using endpoint: {endpoint}")
            
            if "request_id" in response.json():
                connection_requests["user2_to_user1"] = response.json()["request_id"]
                logger.info(f"Connection request ID: {connection_requests['user2_to_user1']}")
            break
    
    if not success:
        # Try with user ID instead of PIN
        request_data = {
            "user_id": user_ids["user1"],
            "message": "Hi Alice, I'd like to connect!"
        }
        
        for endpoint in endpoints:
            response = requests.post(endpoint, json=request_data, headers=headers)
            if response.status_code == 200:
                success = True
                logger.info(f"Connection request successful using user_id and endpoint: {endpoint}")
                
                if "request_id" in response.json():
                    connection_requests["user2_to_user1"] = response.json()["request_id"]
                    logger.info(f"Connection request ID: {connection_requests['user2_to_user1']}")
                break
    
    if not success:
        logger.error("Failed to create connection request using any method")
        return False
    
    logger.info("Connection request by PIN tests passed")
    return True

def test_get_connection_requests():
    """Test getting connection requests endpoint"""
    logger.info("Testing get connection requests...")
    
    # User1 gets their connection requests
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/connections/requests", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connection requests: {response.text}")
        return False
    
    requests_list = response.json()
    logger.info(f"User1 has {len(requests_list)} connection requests")
    
    # If we have requests, store the first one's ID
    if requests_list and not connection_requests.get("user2_to_user1"):
        connection_requests["user2_to_user1"] = requests_list[0].get("request_id")
        logger.info(f"Found connection request ID: {connection_requests['user2_to_user1']}")
    
    logger.info("Get connection requests tests passed")
    return True

def test_respond_to_connection_request():
    """Test responding to connection request endpoint"""
    logger.info("Testing respond to connection request...")
    
    # Make sure we have a request ID
    if not connection_requests.get("user2_to_user1"):
        logger.error("No connection request ID available")
        return False
    
    # User1 accepts connection request from User2
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response_data = {
        "action": "accept"
    }
    
    response = requests.put(
        f"{API_URL}/connections/requests/{connection_requests['user2_to_user1']}",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept connection request: {response.text}")
        return False
    
    logger.info("Connection request accepted successfully")
    
    # Store connection ID if available
    if "connection_id" in response.json():
        connections["user1_user2"] = response.json()["connection_id"]
        logger.info(f"Connection ID: {connections['user1_user2']}")
    
    logger.info("Respond to connection request tests passed")
    return True

def test_get_connections():
    """Test getting connections endpoint"""
    logger.info("Testing get connections...")
    
    # User1 gets their connections
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/connections", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connections: {response.text}")
        return False
    
    connections_list = response.json()
    logger.info(f"User1 has {len(connections_list)} connections")
    
    # If we have connections but no stored ID, store the first one
    if connections_list and not connections.get("user1_user2"):
        connections["user1_user2"] = connections_list[0].get("connection_id")
        logger.info(f"Found connection ID: {connections['user1_user2']}")
    
    logger.info("Get connections tests passed")
    return True

def test_update_trust_level():
    """Test updating trust level endpoint"""
    logger.info("Testing update trust level...")
    
    # Make sure we have a connection ID
    if not connections.get("user1_user2"):
        logger.error("No connection ID available")
        return False
    
    # User1 updates trust level with User2
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    trust_data = {
        "trust_level": 2  # Text Chat level
    }
    
    response = requests.put(
        f"{API_URL}/connections/{connections['user1_user2']}/trust-level",
        json=trust_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update trust level: {response.text}")
        return False
    
    logger.info("Trust level updated successfully")
    
    # Update to higher level
    trust_data = {
        "trust_level": 3  # Voice Call level
    }
    
    response = requests.put(
        f"{API_URL}/connections/{connections['user1_user2']}/trust-level",
        json=trust_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update to higher trust level: {response.text}")
        return False
    
    logger.info("Trust level updated to higher level successfully")
    
    logger.info("Update trust level tests passed")
    return True

def test_get_chats():
    """Test getting chats endpoint"""
    logger.info("Testing get chats...")
    
    # User1 gets their chats
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get chats: {response.text}")
        return False
    
    chats = response.json()
    logger.info(f"User1 has {len(chats)} chats")
    
    # Store chat ID if available
    if chats:
        chat_ids["user1_user2"] = chats[0]["chat_id"]
        logger.info(f"Chat ID: {chat_ids['user1_user2']}")
    
    logger.info("Get chats tests passed")
    return True

def test_send_and_get_messages():
    """Test sending and getting messages endpoints"""
    logger.info("Testing send and get messages...")
    
    # Make sure we have a chat ID
    if not chat_ids.get("user1_user2"):
        # Try to create a chat if we don't have one
        headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
        chat_data = {
            "chat_type": "direct",
            "other_user_id": user_ids["user2"]
        }
        
        response = requests.post(f"{API_URL}/chats", json=chat_data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to create chat: {response.text}")
            return False
        
        chat_ids["user1_user2"] = response.json()["chat_id"]
        logger.info(f"Created chat with ID: {chat_ids['user1_user2']}")
    
    # User1 sends a message to User2
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    message_data = {
        "content": f"Hello Bob! This is a test message from Alice. Timestamp: {timestamp}"
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message: {response.text}")
        return False
    
    message_ids["user1_to_user2"] = response.json()["message_id"]
    logger.info(f"Message sent with ID: {message_ids['user1_to_user2']}")
    
    # User2 sends a message to User1
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    message_data = {
        "content": f"Hi Alice! Thanks for your message. Timestamp: {timestamp}"
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message from user2: {response.text}")
        return False
    
    message_ids["user2_to_user1"] = response.json()["message_id"]
    logger.info(f"Message sent from user2 with ID: {message_ids['user2_to_user1']}")
    
    # User1 gets messages from chat
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['user1_user2']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get chat messages: {response.text}")
        return False
    
    messages = response.json()
    logger.info(f"Retrieved {len(messages)} messages from chat")
    
    logger.info("Send and get messages tests passed")
    return True

def test_authenticity_rating():
    """Test authenticity rating endpoints"""
    logger.info("Testing authenticity rating...")
    
    # User1 gets authenticity details
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/authenticity/details", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get authenticity details: {response.text}")
        return False
    
    details = response.json()
    logger.info(f"User1 authenticity rating: {details.get('total_rating')}, level: {details.get('level')}")
    
    # Check authenticity factors
    factors = details.get("factors", {})
    required_factors = ["profile_completeness", "verification_status", "interaction_quality", 
                        "consistency", "community_feedback"]
    
    for factor in required_factors:
        if factor not in factors:
            logger.error(f"Missing required factor: {factor}")
            return False
        
        factor_data = factors[factor]
        logger.info(f"Factor: {factor}, Score: {factor_data.get('score')}/{factor_data.get('max_score')}")
    
    # User1 updates authenticity rating
    response = requests.put(f"{API_URL}/authenticity/update", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update authenticity rating: {response.text}")
        return False
    
    update_result = response.json()
    logger.info(f"Updated authenticity rating: {update_result.get('new_rating')}, level: {update_result.get('level')}")
    
    # Verify the update is reflected in user profile
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
    
    logger.info("Authenticity rating tests passed")
    return True

def run_all_tests():
    """Run all tests in sequence"""
    tests = [
        ("User Registration and Login", test_user_registration_and_login),
        ("Get Current User", test_get_current_user),
        ("Profile Completion", test_profile_completion),
        ("QR Code Generation", test_qr_code_generation),
        ("Connection Request by PIN", test_connection_request_by_pin),
        ("Get Connection Requests", test_get_connection_requests),
        ("Respond to Connection Request", test_respond_to_connection_request),
        ("Get Connections", test_get_connections),
        ("Update Trust Level", test_update_trust_level),
        ("Get Chats", test_get_chats),
        ("Send and Get Messages", test_send_and_get_messages),
        ("Authenticity Rating", test_authenticity_rating)
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
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 80)
    logger.info(f"OVERALL RESULT: {'PASSED' if all_passed else 'FAILED'}")
    logger.info("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    run_all_tests()