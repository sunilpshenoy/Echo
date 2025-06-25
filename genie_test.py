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

# Test user for authentication
test_user = {
    "username": "genie_test_user",
    "email": "genie_test@example.com",
    "password": "GenieTest123!",
    "phone": "+1234567890"
}

# Global variables
user_token = None
user_id = None

def register_or_login_user():
    """Register a test user or login if already exists"""
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
    
    return True

def test_genie_process_command(command, expected_intent=None):
    """Test the genie command processing endpoint"""
    if not user_token:
        logger.error("No user token available for testing")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    command_data = {"command": command}
    
    logger.info(f"Testing command: '{command}'")
    logger.info(f"Request data: {command_data}")
    
    try:
        response = requests.post(f"{API_URL}/genie/process", json=command_data, headers=headers)
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response content: {response.text}")
        
        if response.status_code != 200:
            logger.error(f"Failed to process genie command: {response.text}")
            return False
        
        result = response.json()
        logger.info(f"Intent: {result.get('intent')}")
        logger.info(f"Entities: {result.get('entities')}")
        logger.info(f"Action: {result.get('action')}")
        logger.info(f"Response: {result.get('response_text')}")
        
        if expected_intent and result.get('intent') != expected_intent:
            logger.error(f"Expected intent '{expected_intent}' but got '{result.get('intent')}'")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Exception during command processing: {str(e)}")
        return False

def test_genie_undo():
    """Test the genie undo functionality"""
    if not user_token:
        logger.error("No user token available for testing")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # First, create an action to undo (add a contact)
    logger.info("Creating an action to undo (adding a contact)")
    command_data = {"command": "add contact test@example.com"}
    
    try:
        # Process the command first
        process_response = requests.post(f"{API_URL}/genie/process", json=command_data, headers=headers)
        logger.info(f"Process response status: {process_response.status_code}")
        logger.info(f"Process response content: {process_response.text}")
        
        if process_response.status_code != 200:
            logger.error("Failed to create an action to undo")
            return False
        
        # Now try to undo it
        logger.info("Attempting to undo the action")
        undo_response = requests.post(f"{API_URL}/genie/undo", headers=headers)
        
        logger.info(f"Undo response status: {undo_response.status_code}")
        logger.info(f"Undo response content: {undo_response.text}")
        
        if undo_response.status_code != 200:
            logger.error(f"Failed to undo action: {undo_response.text}")
            return False
        
        result = undo_response.json()
        logger.info(f"Undo result: {result}")
        
        if not result.get('success'):
            logger.error(f"Undo operation failed: {result.get('message')}")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Exception during undo test: {str(e)}")
        return False

def run_genie_tests():
    """Run all genie assistant tests"""
    test_results = {}
    
    # Register or login test user
    if not register_or_login_user():
        logger.error("Failed to setup test user")
        return {"setup": False}
    
    # Test various commands
    test_commands = [
        {"command": "create a chat with John", "intent": "create_chat"},
        {"command": "add contact jane@email.com", "intent": "add_contact"},
        {"command": "send message to Sarah saying hello", "intent": "send_message"},
        {"command": "block user Bob", "intent": "block_user"},
        {"command": "show my chats", "intent": "list_chats"},
        {"command": "help me with the app", "intent": "show_help"},
        {"command": "what can you do", "intent": "show_help"}
    ]
    
    for test in test_commands:
        command = test["command"]
        expected_intent = test.get("intent")
        test_results[command] = test_genie_process_command(command, expected_intent)
    
    # Test undo functionality
    test_results["undo_functionality"] = test_genie_undo()
    
    return test_results

if __name__ == "__main__":
    # Run all tests
    results = run_genie_tests()
    
    # Print summary
    print("\n=== GENIE ASSISTANT TEST RESULTS ===")
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        test_status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  - {test_name}: {test_status}")
    
    print("\nOVERALL RESULT:", "✅ PASSED" if all_passed else "❌ FAILED")