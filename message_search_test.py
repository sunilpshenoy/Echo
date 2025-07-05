import requests
import json
import time
import uuid
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
test_users = [
    {
        "username": "search_test_alice",
        "email": "search_alice@example.com",
        "password": "SecurePass123!",
        "display_name": "Alice Smith"
    },
    {
        "username": "search_test_bob",
        "email": "search_bob@example.com",
        "password": "StrongPass456!",
        "display_name": "Bob Johnson"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
chat_ids = {}
message_ids = {}

def test_user_registration():
    """Register test users or log them in if they already exist"""
    logger.info("Registering/logging in test users...")
    
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
    
    return True

def test_create_chat():
    """Create a direct chat between the test users"""
    logger.info("Creating direct chat between test users...")
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.post(
        f"{API_URL}/chats",
        json={"chat_type": "direct", "other_user_id": user_ids['user2']},
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to create direct chat: {response.text}")
        return False
    
    chat_ids['direct_chat'] = response.json()["chat_id"]
    logger.info(f"Direct chat created with ID: {chat_ids['direct_chat']}")
    
    # Create a group chat as well
    response = requests.post(
        f"{API_URL}/chats",
        json={
            "chat_type": "group",
            "name": "Search Test Group",
            "members": [user_ids['user2']]
        },
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to create group chat: {response.text}")
        return False
    
    chat_ids['group_chat'] = response.json()["chat_id"]
    logger.info(f"Group chat created with ID: {chat_ids['group_chat']}")
    
    return True

def test_send_test_messages():
    """Send various test messages to test search functionality"""
    logger.info("Sending test messages for search testing...")
    
    # Messages for direct chat
    direct_chat_messages = [
        "Hello, this is a test message for searching",
        "Another message with the word test in it",
        "This message contains the phrase search functionality",
        "Random message without search terms",
        "TEST message with uppercase letters",
        "Message with partial word testing",
        "This is a longer message that talks about how we need to test the search functionality thoroughly to ensure it works correctly with various types of content and edge cases"
    ]
    
    # Messages for group chat
    group_chat_messages = [
        "Group chat test message",
        "Another group message for search testing",
        "This group message has search terms",
        "Random group message",
        "TEST in uppercase in group chat",
        "Group message with testing word"
    ]
    
    # Send direct chat messages
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    for message in direct_chat_messages:
        response = requests.post(
            f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
            json={"content": message},
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to send direct chat message: {response.text}")
            return False
        
        message_ids[message[:20]] = response.json()["message_id"]
        logger.info(f"Sent direct chat message: {message[:30]}...")
    
    # Send group chat messages
    for message in group_chat_messages:
        response = requests.post(
            f"{API_URL}/chats/{chat_ids['group_chat']}/messages",
            json={"content": message},
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to send group chat message: {response.text}")
            return False
        
        message_ids[message[:20]] = response.json()["message_id"]
        logger.info(f"Sent group chat message: {message[:30]}...")
    
    # Send some messages as user2 as well
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    user2_messages = [
        "Hello from Bob, testing search",
        "Another test message from Bob",
        "This is Bob sending a message about search functionality"
    ]
    
    for message in user2_messages:
        response = requests.post(
            f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
            json={"content": message},
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to send user2 message: {response.text}")
            return False
        
        message_ids[message[:20]] = response.json()["message_id"]
        logger.info(f"Sent user2 message: {message[:30]}...")
    
    # Wait a moment for messages to be processed
    time.sleep(1)
    return True

def test_search_single_chat():
    """Test searching messages in a single chat"""
    logger.info("Testing search in a single chat...")
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Test case 1: Basic search with a single word
    search_term = "test"
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/search?q={search_term}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to search for '{search_term}': {response.text}")
        return False
    
    results = response.json()
    logger.info(f"Search for '{search_term}' returned {results['total_results']} results")
    
    if results['total_results'] < 1:
        logger.error(f"Expected at least 1 result for '{search_term}', got {results['total_results']}")
        return False
    
    # Test case 2: Search with a phrase
    search_term = "search functionality"
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/search?q={search_term}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to search for '{search_term}': {response.text}")
        return False
    
    results = response.json()
    logger.info(f"Search for '{search_term}' returned {results['total_results']} results")
    
    if results['total_results'] < 1:
        logger.error(f"Expected at least 1 result for '{search_term}', got {results['total_results']}")
        return False
    
    # Test case 3: Case-insensitive search
    search_term = "TEST"
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/search?q={search_term}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to search for '{search_term}': {response.text}")
        return False
    
    results = response.json()
    logger.info(f"Case-insensitive search for '{search_term}' returned {results['total_results']} results")
    
    if results['total_results'] < 1:
        logger.error(f"Expected at least 1 result for case-insensitive '{search_term}', got {results['total_results']}")
        return False
    
    # Test case 4: Partial word search
    search_term = "test"
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/search?q={search_term}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to search for partial word '{search_term}': {response.text}")
        return False
    
    results = response.json()
    logger.info(f"Partial word search for '{search_term}' returned {results['total_results']} results")
    
    # Check if "testing" messages are found with "test" search
    found_partial = False
    for result in results['results']:
        if "testing" in result['content'].lower():
            found_partial = True
            break
    
    if not found_partial:
        logger.error(f"Partial word search failed to find 'testing' with search term '{search_term}'")
        return False
    
    # Test case 5: Search with no results
    search_term = "nonexistentterm123456789"
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/search?q={search_term}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to search for non-existent term: {response.text}")
        return False
    
    results = response.json()
    logger.info(f"Search for non-existent term returned {results['total_results']} results")
    
    if results['total_results'] != 0:
        logger.error(f"Expected 0 results for non-existent term, got {results['total_results']}")
        return False
    
    # Test case 6: Search with too short query
    search_term = "a"
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/search?q={search_term}",
        headers=headers
    )
    
    if response.status_code != 400:
        logger.error(f"Expected 400 error for too short query, got {response.status_code}")
        return False
    
    logger.info("Successfully tested too short query error handling")
    
    # Test case 7: Search in non-existent chat
    fake_chat_id = str(uuid.uuid4())
    response = requests.get(
        f"{API_URL}/chats/{fake_chat_id}/search?q=test",
        headers=headers
    )
    
    if response.status_code != 404:
        logger.error(f"Expected 404 error for non-existent chat, got {response.status_code}")
        return False
    
    logger.info("Successfully tested non-existent chat error handling")
    
    # Test case 8: Verify message data in search results
    search_term = "Hello"
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/search?q={search_term}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to search for '{search_term}': {response.text}")
        return False
    
    results = response.json()
    
    if results['total_results'] < 1:
        logger.error(f"Expected at least 1 result for '{search_term}', got {results['total_results']}")
        return False
    
    # Check message data structure
    message = results['results'][0]
    required_fields = ['message_id', 'sender_id', 'content', 'timestamp']
    
    for field in required_fields:
        if field not in message:
            logger.error(f"Search result missing required field: {field}")
            return False
    
    logger.info("Search results contain all required message data")
    
    logger.info("Single chat search tests passed")
    return True

def test_search_all_messages():
    """Test searching messages across all chats"""
    logger.info("Testing search across all chats...")
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Test case 1: Basic search across all chats
    search_term = "test"
    response = requests.get(
        f"{API_URL}/search/messages?q={search_term}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to search all chats for '{search_term}': {response.text}")
        return False
    
    results = response.json()
    logger.info(f"Search across all chats for '{search_term}' returned {results['total_results']} results")
    
    if results['total_results'] < 1:
        logger.error(f"Expected at least 1 result for '{search_term}' across all chats, got {results['total_results']}")
        return False
    
    # Verify results are grouped by chat
    if 'results_by_chat' not in results:
        logger.error("All-chats search results not grouped by chat")
        return False
    
    # Check if results include both direct and group chats
    chat_ids_in_results = list(results['results_by_chat'].keys())
    
    if chat_ids['direct_chat'] not in chat_ids_in_results or chat_ids['group_chat'] not in chat_ids_in_results:
        logger.error(f"Search results don't include both chat types. Found chats: {chat_ids_in_results}")
        return False
    
    logger.info("Search results include messages from both direct and group chats")
    
    # Test case 2: Search with a phrase across all chats
    search_term = "search functionality"
    response = requests.get(
        f"{API_URL}/search/messages?q={search_term}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to search all chats for '{search_term}': {response.text}")
        return False
    
    results = response.json()
    logger.info(f"Search across all chats for '{search_term}' returned {results['total_results']} results")
    
    if results['total_results'] < 1:
        logger.error(f"Expected at least 1 result for '{search_term}' across all chats, got {results['total_results']}")
        return False
    
    logger.info("All-chats search tests passed")
    return True

def test_search_access_control():
    """Test that users can only search in chats they have access to"""
    logger.info("Testing search access control...")
    
    # Create a new user who is not in the test chats
    new_user = {
        "username": "search_test_charlie",
        "email": "search_charlie@example.com",
        "password": "SecurePass789!",
        "display_name": "Charlie Davis"
    }
    
    response = requests.post(f"{API_URL}/register", json=new_user)
    
    if response.status_code != 200:
        logger.error(f"Failed to register test user for access control test: {response.text}")
        return False
    
    charlie_token = response.json()["access_token"]
    
    # Charlie tries to search in a chat he's not a member of
    headers = {"Authorization": f"Bearer {charlie_token}"}
    
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/search?q=test",
        headers=headers
    )
    
    if response.status_code != 404:
        logger.error(f"Expected 404 error for unauthorized chat access, got {response.status_code}")
        return False
    
    logger.info("Successfully tested unauthorized chat access error handling")
    
    # Charlie searches across all chats (should return empty results)
    response = requests.get(
        f"{API_URL}/search/messages?q=test",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to search all chats for unauthorized user: {response.text}")
        return False
    
    results = response.json()
    
    if results['total_results'] != 0:
        logger.error(f"Expected 0 results for unauthorized user, got {results['total_results']}")
        return False
    
    logger.info("Successfully verified unauthorized user gets empty search results")
    
    logger.info("Search access control tests passed")
    return True

def run_all_tests():
    """Run all message search tests"""
    logger.info("Starting message search tests...")
    
    if not test_user_registration():
        logger.error("User registration failed")
        return False
    
    if not test_create_chat():
        logger.error("Chat creation failed")
        return False
    
    if not test_send_test_messages():
        logger.error("Sending test messages failed")
        return False
    
    if not test_search_single_chat():
        logger.error("Single chat search tests failed")
        return False
    
    if not test_search_all_messages():
        logger.error("All-chats search tests failed")
        return False
    
    if not test_search_access_control():
        logger.error("Search access control tests failed")
        return False
    
    logger.info("All message search tests passed successfully!")
    return True

if __name__ == "__main__":
    run_all_tests()