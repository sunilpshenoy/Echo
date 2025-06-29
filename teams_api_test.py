import requests
import json
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
test_user = {
    "username": "teams_test_user",
    "email": "teams_test@example.com",
    "password": "TeamsTest123!",
    "phone": "+1234567890"
}

# Global variables to store test data
user_token = None
user_id = None

def test_user_registration():
    """Register a test user or login if already exists"""
    global user_token, user_id
    
    logger.info("Registering test user or logging in if already exists...")
    
    # Try to register
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

def test_get_teams():
    """Test GET /api/teams endpoint"""
    logger.info("Testing GET /api/teams endpoint...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{API_URL}/teams", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"GET /api/teams failed with status code {response.status_code}: {response.text}")
        return False
    
    teams = response.json()
    logger.info(f"GET /api/teams returned: {teams}")
    
    # Verify the response is an empty array (as per the placeholder implementation)
    if not isinstance(teams, list):
        logger.error(f"Expected an array response, got: {type(teams)}")
        return False
    
    logger.info("GET /api/teams test passed")
    return True

def test_create_team():
    """Test POST /api/teams endpoint"""
    logger.info("Testing POST /api/teams endpoint...")
    
    team_data = {
        "name": "Test Team",
        "description": "A team for testing the API"
    }
    
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.post(f"{API_URL}/teams", json=team_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"POST /api/teams failed with status code {response.status_code}: {response.text}")
        return False
    
    result = response.json()
    logger.info(f"POST /api/teams returned: {result}")
    
    # Verify the response contains the expected placeholder message
    if "message" not in result or "Team creation will be implemented soon" not in result["message"]:
        logger.error(f"Expected placeholder message not found in response: {result}")
        return False
    
    # Verify the team_data was echoed back
    if "team_data" not in result:
        logger.error(f"Expected team_data in response: {result}")
        return False
    
    # Verify the status is "placeholder"
    if "status" not in result or result["status"] != "placeholder":
        logger.error(f"Expected status 'placeholder' in response: {result}")
        return False
    
    logger.info("POST /api/teams test passed")
    return True

def test_unauthorized_access():
    """Test that the endpoints require authentication"""
    logger.info("Testing unauthorized access to Teams API endpoints...")
    
    # Test GET /api/teams without authentication
    response = requests.get(f"{API_URL}/teams")
    if response.status_code != 401:
        logger.error(f"GET /api/teams without auth should return 401, got: {response.status_code}")
        return False
    
    # Test POST /api/teams without authentication
    team_data = {"name": "Unauthorized Team"}
    response = requests.post(f"{API_URL}/teams", json=team_data)
    if response.status_code != 401:
        logger.error(f"POST /api/teams without auth should return 401, got: {response.status_code}")
        return False
    
    logger.info("Unauthorized access tests passed")
    return True

def run_tests():
    """Run all tests"""
    logger.info("Starting Teams API endpoint tests...")
    
    # Register/login test user
    if not test_user_registration():
        logger.error("Failed to register/login test user. Aborting tests.")
        return False
    
    # Run tests
    tests = [
        test_get_teams,
        test_create_team,
        test_unauthorized_access
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    if all_passed:
        logger.info("All Teams API endpoint tests passed!")
    else:
        logger.error("Some Teams API endpoint tests failed.")
    
    return all_passed

if __name__ == "__main__":
    run_tests()