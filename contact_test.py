import requests
import json
import time
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get backend URL from environment
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"
logger.info(f"Using API URL: {API_URL}")

# Test user credentials
TEST_USER = {
    "username": f"testuser_{int(time.time())}",
    "email": f"testuser_{int(time.time())}@example.com",
    "password": "Password123!"
}

def register_user(user_data):
    """Register a new user and return the token"""
    response = requests.post(f"{API_URL}/register", json=user_data)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Registration failed: {response.status_code} - {response.text}")
        return None

def test_create_test_users(token):
    """Test the create-test-users endpoint"""
    logger.info("\n=== Testing POST /api/contacts/create-test-users ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/contacts/create-test-users", headers=headers)
    
    logger.info(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Message: {result.get('message')}")
        logger.info(f"Created Users: {len(result.get('created_users', []))}")
        for user in result.get('created_users', []):
            logger.info(f"  - {user.get('display_name')} ({user.get('email')}) - PIN: {user.get('connection_pin')}")
        return True, result
    else:
        logger.error(f"Error: {response.text}")
        return False, None

def test_add_contact_by_email(token, email, name=None):
    """Test adding a contact by email"""
    logger.info(f"\n=== Testing POST /api/contacts (Adding contact with email: {email}) ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    data = {"email": email}
    if name:
        data["name"] = name
    
    response = requests.post(f"{API_URL}/contacts", json=data, headers=headers)
    
    logger.info(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        logger.info(f"Contact added: {result.get('contact_name')} (ID: {result.get('contact_user_id')})")
        return True, result
    else:
        logger.error(f"Error: {response.text}")
        return False, None

def test_get_contacts(token):
    """Test getting all contacts"""
    logger.info("\n=== Testing GET /api/contacts ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/contacts", headers=headers)
    
    logger.info(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        contacts = response.json()
        logger.info(f"Total contacts: {len(contacts)}")
        for contact in contacts:
            logger.info(f"  - {contact.get('contact_name')} ({contact.get('contact_user', {}).get('email')})")
        return True, contacts
    else:
        logger.error(f"Error: {response.text}")
        return False, None

def test_error_cases(token):
    """Test error cases for contact endpoints"""
    logger.info("\n=== Testing Error Cases for Contact Endpoints ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test adding non-existent user
    logger.info("\nTesting adding non-existent user:")
    response = requests.post(
        f"{API_URL}/contacts", 
        json={"email": "nonexistent@example.com"}, 
        headers=headers
    )
    logger.info(f"Status Code: {response.status_code}")
    logger.info(f"Response: {response.text}")
    
    # Test adding self as contact
    logger.info("\nTesting adding self as contact:")
    response = requests.post(
        f"{API_URL}/contacts", 
        json={"email": TEST_USER["email"]}, 
        headers=headers
    )
    logger.info(f"Status Code: {response.status_code}")
    logger.info(f"Response: {response.text}")
    
    # Test adding duplicate contact
    logger.info("\nTesting adding duplicate contact:")
    # First, create test users
    success, result = test_create_test_users(token)
    if success and result.get('created_users'):
        test_email = result['created_users'][0]['email']
        # Add the contact first time
        test_add_contact_by_email(token, test_email)
        # Try to add again
        response = requests.post(
            f"{API_URL}/contacts", 
            json={"email": test_email}, 
            headers=headers
        )
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response: {response.text}")

def run_tests():
    """Run all tests"""
    logger.info("=== Starting Contact Management API Tests ===")
    
    # Register a test user
    logger.info("\nRegistering test user...")
    user_data = register_user(TEST_USER)
    if not user_data:
        logger.error("Failed to register test user. Exiting tests.")
        return
    
    token = user_data["access_token"]
    logger.info(f"Test user registered: {TEST_USER['username']} ({TEST_USER['email']})")
    
    # Test creating test users
    success, test_users_result = test_create_test_users(token)
    
    # Test adding contacts
    if success and test_users_result.get('created_users'):
        for user in test_users_result['created_users']:
            test_add_contact_by_email(token, user['email'], f"Custom Name for {user['display_name']}")
    
    # Test getting contacts
    test_get_contacts(token)
    
    # Test error cases
    test_error_cases(token)
    
    logger.info("\n=== Contact Management API Tests Completed ===")

if __name__ == "__main__":
    run_tests()