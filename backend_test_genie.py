import requests
import json
import os
import logging
import sys
from dotenv import load_dotenv

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
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
    "username": "backend_test_user",
    "email": "backend_test@example.com",
    "password": "BackendTest123!",
    "phone": "+1234567890"
}

# Global variables
user_token = None
user_id = None

def register_or_login_user():
    """Register a test user or login if already exists"""
    global user_token, user_id
    
    # Try to register
    logger.info(f"Attempting to register user: {test_user['username']}")
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
    
    logger.info(f"User ID: {user_id}")
    logger.info(f"Token: {user_token[:10]}...")
    return True

def test_genie_command_processing():
    """Test the Genie Command Processing endpoint with various commands"""
    if not user_token:
        logger.error("No user token available for testing")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Test commands and their expected intents
    test_commands = [
        {"command": "create a chat with John", "expected_intent": "create_chat"},
        {"command": "add contact jane@email.com", "expected_intent": "add_contact"},
        {"command": "send message to Sarah saying hello", "expected_intent": "send_message"},
        {"command": "block user Bob", "expected_intent": "block_user"},
        {"command": "show my chats", "expected_intent": "list_chats"},
        {"command": "help me with the app", "expected_intent": "show_help"},
        {"command": "what can you do", "expected_intent": "show_help"}
    ]
    
    results = {}
    
    for test in test_commands:
        command = test["command"]
        expected_intent = test["expected_intent"]
        command_data = {"command": command}
        
        logger.info(f"Testing command: '{command}'")
        logger.info(f"Expected intent: '{expected_intent}'")
        
        try:
            response = requests.post(f"{API_URL}/genie/process", json=command_data, headers=headers)
            
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Failed to process genie command: {response.text}")
                results[command] = False
                continue
            
            result = response.json()
            actual_intent = result.get("intent")
            logger.info(f"Actual intent: '{actual_intent}'")
            logger.info(f"Entities: {result.get('entities')}")
            logger.info(f"Action: {result.get('action')}")
            logger.info(f"Response: {result.get('response_text')}")
            
            if actual_intent != expected_intent:
                logger.error(f"Intent mismatch: expected '{expected_intent}' but got '{actual_intent}'")
                results[command] = False
            else:
                logger.info(f"Intent matched correctly: '{actual_intent}'")
                results[command] = True
                
        except Exception as e:
            logger.error(f"Exception during command processing: {str(e)}")
            results[command] = False
    
    # Check overall results
    all_passed = all(results.values())
    if all_passed:
        logger.info("All genie commands were processed correctly")
    else:
        failed_commands = [cmd for cmd, passed in results.items() if not passed]
        logger.error(f"The following commands failed: {failed_commands}")
    
    return results

def test_genie_undo_functionality():
    """Test the Genie Undo functionality"""
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
        
        if process_response.status_code != 200:
            logger.error("Failed to create an action to undo")
            return False
        
        # Now try to undo it
        logger.info("Attempting to undo the action")
        undo_response = requests.post(f"{API_URL}/genie/undo", headers=headers)
        
        logger.info(f"Undo response status: {undo_response.status_code}")
        
        if undo_response.status_code != 200:
            logger.error(f"Failed to undo action: {undo_response.text}")
            return False
        
        result = undo_response.json()
        logger.info(f"Undo result: {result}")
        
        if not result.get('success'):
            logger.error(f"Undo operation failed: {result.get('message')}")
            return False
        
        logger.info("Undo operation succeeded")
        return True
    except Exception as e:
        logger.error(f"Exception during undo test: {str(e)}")
        return False

def test_nlp_intent_recognition():
    """Test NLP intent recognition with various phrasings"""
    if not user_token:
        logger.error("No user token available for testing")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Test different phrasings for the same intents
    test_phrasings = [
        # Chat creation variations
        {"command": "create a chat with John", "expected_intent": "create_chat"},
        {"command": "start a conversation with John", "expected_intent": "create_chat"},
        {"command": "new chat with John", "expected_intent": "create_chat"},
        {"command": "message John", "expected_intent": "create_chat"},
        {"command": "talk to John", "expected_intent": "create_chat"},
        
        # Contact management variations
        {"command": "add contact jane@email.com", "expected_intent": "add_contact"},
        {"command": "add jane@email.com as contact", "expected_intent": "add_contact"},
        {"command": "save contact jane@email.com", "expected_intent": "add_contact"},
        {"command": "new contact jane@email.com", "expected_intent": "add_contact"},
        
        # Message sending variations
        {"command": "send message to Sarah saying hello", "expected_intent": "send_message"},
        {"command": "tell Sarah that hello", "expected_intent": "send_message"},
        {"command": "message Sarah hello", "expected_intent": "send_message"},
        
        # User blocking variations
        {"command": "block user Bob", "expected_intent": "block_user"},
        {"command": "block Bob", "expected_intent": "block_user"},
        {"command": "stop Bob from messaging", "expected_intent": "block_user"},
        
        # Help variations
        {"command": "help", "expected_intent": "show_help"},
        {"command": "what can you do", "expected_intent": "show_help"},
        {"command": "show features", "expected_intent": "show_help"},
        {"command": "how to use", "expected_intent": "show_help"}
    ]
    
    results = {}
    
    for test in test_phrasings:
        command = test["command"]
        expected_intent = test["expected_intent"]
        command_data = {"command": command}
        
        logger.info(f"Testing phrasing: '{command}'")
        logger.info(f"Expected intent: '{expected_intent}'")
        
        try:
            response = requests.post(f"{API_URL}/genie/process", json=command_data, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to process genie command: {response.text}")
                results[command] = False
                continue
            
            result = response.json()
            actual_intent = result.get("intent")
            logger.info(f"Actual intent: '{actual_intent}'")
            
            if actual_intent != expected_intent:
                logger.error(f"Intent mismatch: expected '{expected_intent}' but got '{actual_intent}'")
                results[command] = False
            else:
                logger.info(f"Intent matched correctly: '{actual_intent}'")
                results[command] = True
                
        except Exception as e:
            logger.error(f"Exception during intent recognition: {str(e)}")
            results[command] = False
    
    # Check overall results
    all_passed = all(results.values())
    if all_passed:
        logger.info("All phrasings were recognized correctly")
    else:
        failed_phrasings = [cmd for cmd, passed in results.items() if not passed]
        logger.error(f"The following phrasings failed: {failed_phrasings}")
    
    return results

def test_integration_with_existing_features():
    """Test integration of genie commands with existing features"""
    if not user_token:
        logger.error("No user token available for testing")
        return False
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Test integration with chat creation
    logger.info("Testing integration with chat creation")
    command_data = {"command": "create a chat with TestUser"}
    
    try:
        response = requests.post(f"{API_URL}/genie/process", json=command_data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to process chat creation command: {response.text}")
            return False
        
        # Verify that the action is correct
        result = response.json()
        action = result.get("action")
        
        if not action or action.get("type") != "create_chat":
            logger.error(f"Incorrect action type: {action}")
            return False
        
        logger.info("Chat creation integration test passed")
        
        # Test integration with contact management
        logger.info("Testing integration with contact management")
        command_data = {"command": "add contact test_contact@example.com"}
        
        response = requests.post(f"{API_URL}/genie/process", json=command_data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to process contact addition command: {response.text}")
            return False
        
        # Verify that the action is correct
        result = response.json()
        action = result.get("action")
        
        if not action or action.get("type") != "add_contact":
            logger.error(f"Incorrect action type: {action}")
            return False
        
        logger.info("Contact management integration test passed")
        
        # Test integration with user blocking
        logger.info("Testing integration with user blocking")
        command_data = {"command": "block user BlockedUser"}
        
        response = requests.post(f"{API_URL}/genie/process", json=command_data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to process user blocking command: {response.text}")
            return False
        
        # Verify that the action is correct
        result = response.json()
        action = result.get("action")
        
        if not action or action.get("type") != "block_user":
            logger.error(f"Incorrect action type: {action}")
            return False
        
        logger.info("User blocking integration test passed")
        
        return True
    except Exception as e:
        logger.error(f"Exception during integration testing: {str(e)}")
        return False

def run_all_tests():
    """Run all genie assistant tests"""
    # Register or login test user
    if not register_or_login_user():
        logger.error("Failed to setup test user")
        return {
            "setup": False
        }
    
    # Run all tests
    results = {
        "genie_command_processing": test_genie_command_processing(),
        "genie_undo_functionality": test_genie_undo_functionality(),
        "nlp_intent_recognition": test_nlp_intent_recognition(),
        "integration_with_existing_features": test_integration_with_existing_features()
    }
    
    return results

if __name__ == "__main__":
    # Run all tests
    test_results = run_all_tests()
    
    # Print summary
    print("\n=== GENIE ASSISTANT TEST RESULTS ===")
    
    for test_name, result in test_results.items():
        if isinstance(result, dict):
            # For tests that return detailed results for each command
            all_passed = all(result.values())
            test_status = "✅ PASSED" if all_passed else "❌ FAILED"
            print(f"{test_name}: {test_status}")
            
            # Print details for failed commands
            if not all_passed:
                failed_items = [item for item, passed in result.items() if not passed]
                print(f"  Failed items: {failed_items}")
        else:
            # For tests that return a simple boolean
            test_status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {test_status}")
    
    # Overall result
    all_passed = all(
        result if isinstance(result, bool) else all(result.values())
        for result in test_results.values()
    )
    
    print("\nOVERALL RESULT:", "✅ PASSED" if all_passed else "❌ FAILED")
    
    # Detailed analysis of issues
    if not all_passed:
        print("\n=== DETAILED ANALYSIS ===")
        
        # Check command processing issues
        if "genie_command_processing" in test_results:
            cmd_results = test_results["genie_command_processing"]
            if isinstance(cmd_results, dict) and not all(cmd_results.values()):
                failed_commands = [cmd for cmd, passed in cmd_results.items() if not passed]
                print(f"Command Processing Issues: {failed_commands}")
                
                # Special check for send_message intent
                if "send message to Sarah saying hello" in failed_commands:
                    print("The 'send_message' intent recognition is not working correctly.")
                    print("The regex pattern for send_message needs to be fixed to properly extract recipient and message content.")
        
        # Check undo functionality issues
        if "genie_undo_functionality" in test_results and not test_results["genie_undo_functionality"]:
            print("Undo Functionality Issues:")
            print("The undo operation is failing. This could be due to:")
            print("1. Actions not being properly logged in the database")
            print("2. The perform_undo function not finding the correct action to undo")
            print("3. Implementation issues in the undo logic")