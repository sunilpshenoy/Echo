import requests
import json
import logging
import os
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
        "email": "alice@test.com",
        "password": "password123"
    },
    {
        "email": "bob@test.com",
        "password": "password123"
    },
    {
        "email": "carol@test.com",
        "password": "password123"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
user_data = {}

def test_login_test_users():
    """Test logging in with the test users"""
    logger.info("Testing login with test users...")
    
    for i, user_data in enumerate(test_users):
        response = requests.post(f"{API_URL}/login", json=user_data)
        
        if response.status_code == 200:
            logger.info(f"User {user_data['email']} logged in successfully")
            user_key = f"user{i+1}"
            user_tokens[user_key] = response.json()["access_token"]
            user_ids[user_key] = response.json()["user"]["user_id"]
            user_data[user_key] = response.json()["user"]
            logger.info(f"User details: {json.dumps(response.json()['user'], indent=2)}")
        else:
            logger.error(f"Failed to log in user {user_data['email']}: {response.text}")
            return False
    
    logger.info("All test users logged in successfully")
    return True

def test_create_test_users():
    """Test creating test users if they don't exist"""
    logger.info("Testing creation of test users...")
    
    # First try to login with one of the test users
    response = requests.post(f"{API_URL}/login", json=test_users[0])
    
    if response.status_code == 200:
        logger.info("Test users already exist, skipping creation")
        return True
    
    # If login fails, try to create the test users
    # First register a temporary user to get a token
    temp_user = {
        "username": "temp_admin",
        "email": "temp_admin@example.com",
        "password": "TempAdmin123!"
    }
    
    response = requests.post(f"{API_URL}/register", json=temp_user)
    
    if response.status_code != 200:
        logger.error(f"Failed to register temporary admin user: {response.text}")
        return False
    
    temp_token = response.json()["access_token"]
    
    # Use the token to create test users
    headers = {"Authorization": f"Bearer {temp_token}"}
    response = requests.post(f"{API_URL}/contacts/create-test-users", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create test users: {response.text}")
        return False
    
    logger.info(f"Test users created: {response.json()}")
    return True

def test_check_test_users_exist():
    """Test if the test users exist in the database"""
    logger.info("Testing if test users exist in the database...")
    
    for user_data in test_users:
        response = requests.post(f"{API_URL}/login", json=user_data)
        
        if response.status_code != 200:
            logger.error(f"User {user_data['email']} does not exist or credentials are incorrect: {response.text}")
            return False
        
        logger.info(f"User {user_data['email']} exists in the database")
    
    logger.info("All test users exist in the database")
    return True

def test_pin_based_connection():
    """Test PIN-based connection lookup"""
    logger.info("Testing PIN-based connection lookup...")
    
    # Login as the first user
    if not user_tokens.get("user1"):
        response = requests.post(f"{API_URL}/login", json=test_users[0])
        if response.status_code == 200:
            user_tokens["user1"] = response.json()["access_token"]
        else:
            logger.error(f"Failed to log in first user: {response.text}")
            return False
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Test PIN-ALI001
    pin_data = {"target_pin": "PIN-ALI001"}
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=pin_data, headers=headers)
    
    if response.status_code == 400 and "Cannot connect to yourself" in response.json().get("detail", ""):
        logger.info("PIN-ALI001 correctly identified as the current user")
    elif response.status_code != 200:
        logger.error(f"Failed to find user with PIN-ALI001: {response.text}")
        return False
    
    # Test PIN-BOB002
    pin_data = {"target_pin": "PIN-BOB002"}
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=pin_data, headers=headers)
    
    if response.status_code == 200:
        logger.info("PIN-BOB002 correctly found and connection request sent")
    elif response.status_code == 400 and "Connection request already sent" in response.json().get("detail", ""):
        logger.info("Connection request to PIN-BOB002 already exists")
    elif response.status_code == 400 and "Already connected" in response.json().get("detail", ""):
        logger.info("Already connected to PIN-BOB002")
    else:
        logger.error(f"Failed to find user with PIN-BOB002: {response.text}")
        return False
    
    # Test PIN-CAR003
    pin_data = {"target_pin": "PIN-CAR003"}
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=pin_data, headers=headers)
    
    if response.status_code == 200:
        logger.info("PIN-CAR003 correctly found and connection request sent")
    elif response.status_code == 400 and "Connection request already sent" in response.json().get("detail", ""):
        logger.info("Connection request to PIN-CAR003 already exists")
    elif response.status_code == 400 and "Already connected" in response.json().get("detail", ""):
        logger.info("Already connected to PIN-CAR003")
    else:
        logger.error(f"Failed to find user with PIN-CAR003: {response.text}")
        return False
    
    # Test invalid PIN
    pin_data = {"target_pin": "PIN-INVALID"}
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=pin_data, headers=headers)
    
    if response.status_code == 404 and "User not found with this PIN" in response.json().get("detail", ""):
        logger.info("Invalid PIN correctly returns 'User not found' error")
    else:
        logger.error(f"Unexpected response for invalid PIN: {response.status_code} - {response.text}")
        return False
    
    logger.info("PIN-based connection lookup tests passed")
    return True

def test_contact_addition_by_email():
    """Test adding contacts by email"""
    logger.info("Testing contact addition by email...")
    
    # Login as the first user if not already logged in
    if not user_tokens.get("user1"):
        response = requests.post(f"{API_URL}/login", json=test_users[0])
        if response.status_code == 200:
            user_tokens["user1"] = response.json()["access_token"]
        else:
            logger.error(f"Failed to log in first user: {response.text}")
            return False
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Add bob@test.com as contact
    contact_data = {"email": "bob@test.com", "name": "Bob Custom Name"}
    response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)
    
    if response.status_code == 200:
        logger.info("Successfully added bob@test.com as contact")
    elif response.status_code == 400 and "Contact already exists" in response.json().get("detail", ""):
        logger.info("bob@test.com is already a contact")
    else:
        logger.error(f"Failed to add bob@test.com as contact: {response.text}")
        return False
    
    # Add carol@test.com as contact
    contact_data = {"email": "carol@test.com", "name": "Carol Custom Name"}
    response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)
    
    if response.status_code == 200:
        logger.info("Successfully added carol@test.com as contact")
    elif response.status_code == 400 and "Contact already exists" in response.json().get("detail", ""):
        logger.info("carol@test.com is already a contact")
    else:
        logger.error(f"Failed to add carol@test.com as contact: {response.text}")
        return False
    
    # Get contacts and check if they have proper display names
    response = requests.get(f"{API_URL}/contacts", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get contacts: {response.text}")
        return False
    
    contacts = response.json()
    logger.info(f"Retrieved {len(contacts)} contacts")
    
    # Check if contacts have proper display names
    for contact in contacts:
        if "contact_user" not in contact:
            logger.error(f"Contact missing contact_user data: {contact}")
            return False
        
        if "display_name" not in contact["contact_user"] or not contact["contact_user"]["display_name"]:
            logger.error(f"Contact missing display_name: {contact}")
            return False
        
        logger.info(f"Contact {contact['contact_user']['email']} has display_name: {contact['contact_user']['display_name']}")
    
    logger.info("Contact addition by email tests passed")
    return True

def run_all_tests():
    """Run all tests"""
    logger.info("Starting tests...")
    
    # First ensure test users exist
    if not test_create_test_users():
        logger.error("Failed to create test users")
        return False
    
    # Check if test users exist
    if not test_check_test_users_exist():
        logger.error("Test users do not exist in the database")
        return False
    
    # Login with test users
    if not test_login_test_users():
        logger.error("Failed to login with test users")
        return False
    
    # Test PIN-based connection
    if not test_pin_based_connection():
        logger.error("PIN-based connection tests failed")
        return False
    
    # Test contact addition by email
    if not test_contact_addition_by_email():
        logger.error("Contact addition by email tests failed")
        return False
    
    logger.info("All tests completed successfully!")
    return True

if __name__ == "__main__":
    run_all_tests()