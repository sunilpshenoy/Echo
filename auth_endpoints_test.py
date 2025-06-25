import requests
import json
import os
from dotenv import load_dotenv
import logging
import uuid
import time

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

def test_login_valid_credentials():
    """Test POST /api/login with valid credentials"""
    logger.info("Testing login with valid credentials...")
    
    # First register a user if we don't have credentials
    global user_token, user_id
    if not user_token or not user_id:
        response = requests.post(f"{API_URL}/register", json=test_user)
        if response.status_code == 200:
            user_token = response.json()["access_token"]
            user_id = response.json()["user"]["user_id"]
            logger.info(f"Created test user: {test_user['username']}")
        elif response.status_code == 400 and "Email already registered" in response.json().get("detail", ""):
            # Try to login with existing user
            pass
        else:
            logger.error(f"Failed to create test user: {response.status_code} - {response.text}")
            return False
    
    # Test login with valid credentials
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    
    response = requests.post(f"{API_URL}/login", json=login_data)
    
    # Check status code
    if response.status_code != 200:
        logger.error(f"Login failed with status code {response.status_code}: {response.text}")
        return False
    
    # Check response format
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
    
    # Update token
    user_token = response_data["access_token"]
    
    logger.info("Login with valid credentials successful")
    return True

def test_login_invalid_credentials():
    """Test POST /api/login with invalid credentials"""
    logger.info("Testing login with invalid credentials...")
    
    # Test with wrong password
    login_data = {
        "email": test_user["email"],
        "password": "WrongPassword123!"
    }
    
    response = requests.post(f"{API_URL}/login", json=login_data)
    
    # Check status code
    if response.status_code != 401:
        logger.error(f"Expected 401 for invalid password, got {response.status_code}: {response.text}")
        return False
    
    # Check error message
    if "Invalid credentials" not in response.json().get("detail", ""):
        logger.error(f"Expected 'Invalid credentials' error, got: {response.json()}")
        return False
    
    # Test with non-existent email
    login_data = {
        "email": f"nonexistent_{str(uuid.uuid4())[:8]}@example.com",
        "password": test_user["password"]
    }
    
    response = requests.post(f"{API_URL}/login", json=login_data)
    
    # Check status code
    if response.status_code != 401:
        logger.error(f"Expected 401 for non-existent email, got {response.status_code}: {response.text}")
        return False
    
    # Check error message
    if "Invalid credentials" not in response.json().get("detail", ""):
        logger.error(f"Expected 'Invalid credentials' error, got: {response.json()}")
        return False
    
    logger.info("Login with invalid credentials tests passed")
    return True

def test_register_new_user():
    """Test POST /api/register with new user data"""
    logger.info("Testing register with new user data...")
    
    # Create a unique user
    new_user = {
        "username": f"new_user_{str(uuid.uuid4())[:8]}",
        "email": f"new_user_{str(uuid.uuid4())[:8]}@example.com",
        "password": "NewUserPass123!",
        "phone": f"+1888{str(uuid.uuid4())[:8]}"
    }
    
    response = requests.post(f"{API_URL}/register", json=new_user)
    
    # Check status code
    if response.status_code != 200:
        logger.error(f"Registration failed with status code {response.status_code}: {response.text}")
        return False
    
    # Check response format
    response_data = response.json()
    required_fields = ["access_token", "token_type", "user"]
    user_fields = ["user_id", "username", "email"]
    
    for field in required_fields:
        if field not in response_data:
            logger.error(f"Missing required field in registration response: {field}")
            return False
    
    for field in user_fields:
        if field not in response_data["user"]:
            logger.error(f"Missing required user field in registration response: {field}")
            return False
    
    logger.info("Registration with new user data successful")
    return True

def test_register_duplicate_user():
    """Test POST /api/register with duplicate user data"""
    logger.info("Testing register with duplicate user data...")
    
    # Try to register with the same email
    response = requests.post(f"{API_URL}/register", json=test_user)
    
    # Check status code
    if response.status_code != 400:
        logger.error(f"Expected 400 for duplicate email, got {response.status_code}: {response.text}")
        return False
    
    # Check error message
    if "Email already registered" not in response.json().get("detail", ""):
        logger.error(f"Expected 'Email already registered' error, got: {response.json()}")
        return False
    
    logger.info("Registration with duplicate user data correctly returns 400 error")
    return True

def test_user_profile_valid_token():
    """Test GET /api/users/me with valid token"""
    logger.info("Testing user profile with valid token...")
    
    if not user_token or not user_id:
        logger.error("No user token or ID available for profile test")
        return False
    
    # Test with valid token - using /profile/{user_id} endpoint
    headers = {"Authorization": f"Bearer {user_token}"}
    response = requests.get(f"{API_URL}/profile/{user_id}", headers=headers)
    
    # Check status code
    if response.status_code != 200:
        logger.error(f"Profile request failed with status code {response.status_code}: {response.text}")
        return False
    
    # Check response format
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
    
    logger.info("User profile with valid token successful")
    return True

def test_user_profile_invalid_token():
    """Test GET /api/users/me with invalid token"""
    logger.info("Testing user profile with invalid token...")
    
    if not user_id:
        logger.error("No user ID available for profile test")
        return False
    
    # Test with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{API_URL}/profile/{user_id}", headers=headers)
    
    # Check status code
    if response.status_code != 401:
        logger.error(f"Expected 401 for invalid token, got {response.status_code}: {response.text}")
        return False
    
    # Check error message
    if "Invalid authentication credentials" not in response.json().get("detail", ""):
        logger.error(f"Expected 'Invalid authentication credentials' error, got: {response.json()}")
        return False
    
    logger.info("User profile with invalid token correctly returns 401 error")
    return True

def test_cors_headers():
    """Verify CORS headers are properly set"""
    logger.info("Testing CORS headers...")
    
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
    
    logger.info("CORS headers are properly set")
    return True

def test_frontend_origin_allowed():
    """Check if frontend origin is allowed"""
    logger.info("Testing if frontend origin is allowed...")
    
    # Test with frontend origin
    headers = {
        "Origin": BACKEND_URL
    }
    
    response = requests.options(f"{API_URL}/login", headers=headers)
    
    # Check if frontend origin is allowed
    allow_origin = response.headers.get("Access-Control-Allow-Origin")
    if allow_origin != "*" and allow_origin != BACKEND_URL:
        logger.error(f"Frontend origin not allowed: {allow_origin}")
        return False
    
    logger.info("Frontend origin is allowed")
    return True

def test_preflight_requests():
    """Test preflight requests"""
    logger.info("Testing preflight requests...")
    
    # Test preflight request for different methods
    methods = ["GET", "POST", "PUT", "DELETE"]
    
    for method in methods:
        headers = {
            "Origin": BACKEND_URL,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "Content-Type, Authorization"
        }
        
        response = requests.options(f"{API_URL}/login", headers=headers)
        
        # Check if method is allowed
        allow_methods = response.headers.get("Access-Control-Allow-Methods", "")
        if method not in allow_methods and "*" not in allow_methods:
            logger.error(f"Method {method} not allowed: {allow_methods}")
            return False
    
    logger.info("Preflight requests are handled correctly")
    return True

def test_server_connectivity():
    """Test basic connectivity to the backend"""
    logger.info("Testing basic connectivity to the backend...")
    
    try:
        response = requests.get(BACKEND_URL)
        
        # Just check if we can connect, don't care about the status code
        logger.info(f"Connected to backend, status code: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to backend: {e}")
        return False

def test_endpoints_accessibility():
    """Verify all endpoints are accessible"""
    logger.info("Testing endpoints accessibility...")
    
    # List of endpoints to test
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
    
    logger.info("All endpoints are accessible")
    return True

def test_server_errors():
    """Check for any server errors"""
    logger.info("Testing for server errors...")
    
    # List of endpoints to test with invalid data to check error handling
    test_cases = [
        {"endpoint": "/login", "method": "post", "data": {}},
        {"endpoint": "/register", "method": "post", "data": {}}
    ]
    
    for test_case in test_cases:
        try:
            if test_case["method"] == "post":
                response = requests.post(f"{API_URL}{test_case['endpoint']}", json=test_case["data"])
            else:
                response = requests.get(f"{API_URL}{test_case['endpoint']}")
            
            # Check if server returns 5xx error
            if 500 <= response.status_code < 600:
                logger.error(f"Server error on {test_case['endpoint']}: {response.status_code} - {response.text}")
                return False
            
            logger.info(f"Endpoint {test_case['endpoint']} handles invalid data correctly")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to test endpoint {test_case['endpoint']}: {e}")
            return False
    
    logger.info("No server errors detected")
    return True

def run_authentication_tests():
    """Run all authentication tests"""
    test_results = {
        "Login Endpoint Testing": {
            "Valid Credentials": test_login_valid_credentials(),
            "Invalid Credentials": test_login_invalid_credentials()
        },
        "Register Endpoint Testing": {
            "New User": test_register_new_user(),
            "Duplicate User": test_register_duplicate_user()
        },
        "User Profile Endpoint Testing": {
            "Valid Token": test_user_profile_valid_token(),
            "Invalid Token": test_user_profile_invalid_token()
        },
        "CORS Configuration Testing": {
            "CORS Headers": test_cors_headers(),
            "Frontend Origin": test_frontend_origin_allowed(),
            "Preflight Requests": test_preflight_requests()
        },
        "Server Health Check": {
            "Connectivity": test_server_connectivity(),
            "Endpoints Accessibility": test_endpoints_accessibility(),
            "Error Handling": test_server_errors()
        }
    }
    
    return test_results

if __name__ == "__main__":
    # Run all tests
    results = run_authentication_tests()
    
    # Print summary
    print("\n=== AUTHENTICATION TESTING RESULTS ===")
    all_passed = True
    
    for category, tests in results.items():
        category_passed = all(tests.values())
        status = "✅ PASSED" if category_passed else "❌ FAILED"
        print(f"\n{category}: {status}")
        
        for test_name, passed in tests.items():
            test_status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  - {test_name}: {test_status}")
        
        if not category_passed:
            all_passed = False
    
    # Print overall status
    print("\n=== SUMMARY ===")
    overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
    print(f"Overall Status: {overall_status}")
    
    # Exit with appropriate code
    exit(0 if all_passed else 1)