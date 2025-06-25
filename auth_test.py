import requests
import json
import os
from dotenv import load_dotenv
import logging
import uuid

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
    "username": f"auth_test_user_{str(uuid.uuid4())[:8]}",
    "email": f"auth_test_{str(uuid.uuid4())[:8]}@example.com",
    "password": "SecureAuthPass123!",
    "phone": f"+1999{str(uuid.uuid4())[:8]}"
}

# Global variables to store test data
user_token = None
user_id = None

def test_register_endpoint():
    """Test user registration endpoint"""
    logger.info("Testing user registration endpoint...")
    
    # Test successful registration
    response = requests.post(f"{API_URL}/register", json=test_user)
    
    if response.status_code == 200:
        logger.info(f"User {test_user['username']} registered successfully")
        global user_token, user_id
        user_token = response.json()["access_token"]
        user_id = response.json()["user"]["user_id"]
        
        # Verify response format
        response_data = response.json()
        required_fields = ["access_token", "token_type", "user"]
        user_fields = ["user_id", "username", "email"]
        
        for field in required_fields:
            if field not in response_data:
                logger.error(f"Missing required field in response: {field}")
                return False
        
        for field in user_fields:
            if field not in response_data["user"]:
                logger.error(f"Missing required user field in response: {field}")
                return False
        
        logger.info("Registration response format is correct")
        return True
    elif response.status_code == 400 and "Email already registered" in response.json().get("detail", ""):
        # User already exists, try a different email
        test_user["email"] = f"auth_test_{str(uuid.uuid4())[:8]}@example.com"
        return test_register_endpoint()  # Retry with new email
    else:
        logger.error(f"Failed to register user: {response.status_code} - {response.text}")
        return False

def test_register_duplicate_email():
    """Test registration with duplicate email"""
    logger.info("Testing registration with duplicate email...")
    
    # Try to register with the same email
    response = requests.post(f"{API_URL}/register", json=test_user)
    
    if response.status_code != 400 or "Email already registered" not in response.json().get("detail", ""):
        logger.error(f"Expected 400 error for duplicate email, got: {response.status_code} - {response.text}")
        return False
    
    logger.info("Registration with duplicate email correctly returns 400 error")
    return True

def test_login_endpoint_valid():
    """Test login endpoint with valid credentials"""
    logger.info("Testing login endpoint with valid credentials...")
    
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    
    response = requests.post(f"{API_URL}/login", json=login_data)
    
    if response.status_code != 200:
        logger.error(f"Failed to login with valid credentials: {response.status_code} - {response.text}")
        return False
    
    # Verify response format
    response_data = response.json()
    required_fields = ["access_token", "token_type", "user"]
    user_fields = ["user_id", "username", "email"]
    
    for field in required_fields:
        if field not in response_data:
            logger.error(f"Missing required field in login response: {field}")
            return False
    
    for field in user_fields:
        if field not in response_data["user"]:
            logger.error(f"Missing required user field in login response: {field}")
            return False
    
    # Update token in case it's different
    global user_token
    user_token = response_data["access_token"]
    
    logger.info("Login with valid credentials successful")
    return True

def test_login_endpoint_invalid():
    """Test login endpoint with invalid credentials"""
    logger.info("Testing login endpoint with invalid credentials...")
    
    # Test with wrong password
    login_data = {
        "email": test_user["email"],
        "password": "WrongPassword123!"
    }
    
    response = requests.post(f"{API_URL}/login", json=login_data)
    
    if response.status_code != 401 or "Invalid credentials" not in response.json().get("detail", ""):
        logger.error(f"Expected 401 error for invalid password, got: {response.status_code} - {response.text}")
        return False
    
    # Test with non-existent email
    login_data = {
        "email": f"nonexistent_{str(uuid.uuid4())[:8]}@example.com",
        "password": test_user["password"]
    }
    
    response = requests.post(f"{API_URL}/login", json=login_data)
    
    if response.status_code != 401 or "Invalid credentials" not in response.json().get("detail", ""):
        logger.error(f"Expected 401 error for non-existent email, got: {response.status_code} - {response.text}")
        return False
    
    logger.info("Login with invalid credentials correctly returns 401 error")
    return True

def test_user_profile_endpoint():
    """Test user profile endpoint"""
    logger.info("Testing user profile endpoint...")
    
    if not user_token or not user_id:
        logger.error("No user token or ID available for profile test")
        return False
    
    # Test with valid token - using /profile/{user_id} endpoint
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{API_URL}/profile/{user_id}", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get user profile: {response.status_code} - {response.text}")
        return False
    
    # Verify response format
    response_data = response.json()
    required_fields = ["user_id", "username"]
    
    for field in required_fields:
        if field not in response_data:
            logger.error(f"Missing required field in profile response: {field}")
            return False
    
    # Verify user_id matches
    if response_data["user_id"] != user_id:
        logger.error(f"User ID mismatch: expected {user_id}, got {response_data['user_id']}")
        return False
    
    logger.info("User profile endpoint with valid token successful")
    
    # Test with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{API_URL}/profile/{user_id}", headers=headers)
    
    if response.status_code != 401:
        logger.error(f"Expected 401 error for invalid token, got: {response.status_code} - {response.text}")
        return False
    
    logger.info("User profile endpoint with invalid token correctly returns 401 error")
    return True

def test_cors_configuration():
    """Test CORS configuration"""
    logger.info("Testing CORS configuration...")
    
    # Test preflight request
    headers = {
        "Origin": BACKEND_URL,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, Authorization"
    }
    
    response = requests.options(f"{API_URL}/login", headers=headers)
    
    # Check if CORS headers are present
    cors_headers = [
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Methods",
        "Access-Control-Allow-Headers"
    ]
    
    for header in cors_headers:
        if header not in response.headers:
            logger.error(f"Missing CORS header: {header}")
            return False
    
    # Check if frontend origin is allowed
    if response.headers.get("Access-Control-Allow-Origin") != "*" and response.headers.get("Access-Control-Allow-Origin") != BACKEND_URL:
        logger.error(f"Frontend origin not allowed: {response.headers.get('Access-Control-Allow-Origin')}")
        return False
    
    logger.info("CORS configuration is correct")
    return True

def test_server_health():
    """Test server health and connectivity"""
    logger.info("Testing server health and connectivity...")
    
    # Test basic connectivity
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            logger.info("Health endpoint is available")
        else:
            # Some servers might not have a dedicated health endpoint
            # Try a different endpoint
            response = requests.get(BACKEND_URL)
            if response.status_code < 500:
                logger.info(f"Server is reachable, status code: {response.status_code}")
            else:
                logger.error(f"Server returned error: {response.status_code}")
                return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to server: {e}")
        return False
    
    # Test API endpoint accessibility
    endpoints = [
        "/login",
        "/register"
    ]
    
    for endpoint in endpoints:
        try:
            # Just check if the endpoint is reachable, don't care about the response code
            response = requests.options(f"{API_URL}{endpoint}")
            logger.info(f"Endpoint {endpoint} is accessible")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to access endpoint {endpoint}: {e}")
            return False
    
    logger.info("Server health check passed")
    return True

def run_auth_tests():
    """Run all authentication tests"""
    test_results = {
        "register_endpoint": test_register_endpoint(),
        "register_duplicate_email": test_register_duplicate_email(),
        "login_endpoint_valid": test_login_endpoint_valid(),
        "login_endpoint_invalid": test_login_endpoint_invalid(),
        "user_profile_endpoint": test_user_profile_endpoint(),
        "cors_configuration": test_cors_configuration(),
        "server_health": test_server_health()
    }
    
    return test_results

if __name__ == "__main__":
    # Run all tests
    results = run_auth_tests()
    
    # Print summary
    print("\n=== AUTHENTICATION TEST RESULTS SUMMARY ===")
    all_passed = True
    
    for test_name, passed in results.items():
        test_status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  - {test_name}: {test_status}")
        
        if not passed:
            all_passed = False
    
    # Print overall status
    overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
    print(f"\nOverall Status: {overall_status}")
    
    # Exit with appropriate code
    exit(0 if all_passed else 1)