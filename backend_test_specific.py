import requests
import json
import logging
import os
from dotenv import load_dotenv
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
test_users = [
    {
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",
        "password": "SecurePass123!",
        "display_name": "Test User"
    },
    {
        "username": f"testcontact_{uuid.uuid4().hex[:8]}",
        "email": f"testcontact_{uuid.uuid4().hex[:8]}@example.com",
        "password": "SecurePass456!",
        "display_name": "Test Contact"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}

def test_user_registration():
    """Test user registration endpoint"""
    logger.info("Testing user registration...")
    
    # Test successful registration
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
    
    logger.info("User registration tests passed")
    return True

def test_display_name_update():
    """Test updating user display name"""
    logger.info("Testing display name update...")
    
    if not user_tokens.get("user1"):
        logger.error("No user token available for testing")
        return False
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Test updating display name
    new_display_name = f"Updated Name {uuid.uuid4().hex[:5]}"
    profile_data = {
        "display_name": new_display_name
    }
    
    response = requests.put(f"{API_URL}/profile", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update display name: {response.text}")
        return False
    
    # Verify display name was updated
    if response.json().get("display_name") != new_display_name:
        logger.error(f"Display name not updated correctly: {response.json()}")
        return False
    
    logger.info(f"Successfully updated display name to: {new_display_name}")
    
    # Test getting user profile
    response = requests.get(f"{API_URL}/profile/{user_ids['user1']}", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get user profile: {response.text}")
        return False
    
    if response.json().get("display_name") != new_display_name:
        logger.error(f"Display name not reflected in profile: {response.json()}")
        return False
    
    logger.info("Display name update tests passed")
    return True

def test_add_contacts():
    """Test adding contacts"""
    logger.info("Testing add contacts...")
    
    if len(user_tokens) < 2:
        logger.error("Not enough users registered for contact testing")
        return False
    
    # Add user2 as contact for user1
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.post(
        f"{API_URL}/contacts",
        json={"email": test_users[1]["email"], "contact_name": "Test Contact"},
        headers=headers
    )
    
    # If contact already exists, this is fine
    if response.status_code != 200 and not (response.status_code == 400 and "Already a contact" in response.json().get("detail", "")):
        logger.error(f"Failed to add contact: {response.text}")
        return False
    
    logger.info("Contact added successfully or already exists")
    
    # Test adding self as contact (should fail)
    response = requests.post(
        f"{API_URL}/contacts",
        json={"email": test_users[0]["email"]},
        headers=headers
    )
    
    if response.status_code != 400 or "Cannot add yourself as contact" not in response.json().get("detail", ""):
        logger.error("Adding self as contact should fail with appropriate error")
        return False
    
    logger.info("Successfully verified cannot add self as contact")
    
    # Test adding invalid email (should fail)
    response = requests.post(
        f"{API_URL}/contacts",
        json={"email": "nonexistent@example.com"},
        headers=headers
    )
    
    if response.status_code != 404 or "User not found" not in response.json().get("detail", ""):
        logger.error("Adding nonexistent email should fail with 'User not found'")
        return False
    
    logger.info("Successfully verified cannot add nonexistent user")
    
    # Test getting contacts
    response = requests.get(f"{API_URL}/contacts", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get contacts: {response.text}")
        return False
    
    contacts = response.json()
    logger.info(f"User has {len(contacts)} contacts")
    
    # Verify contact details are included
    for contact in contacts:
        if "contact_user" not in contact:
            logger.error(f"Contact missing user details: {contact}")
            return False
        
        contact_user = contact["contact_user"]
        if not all(key in contact_user for key in ["user_id", "username", "display_name"]):
            logger.error(f"Contact user missing required fields: {contact_user}")
            return False
    
    logger.info("Add contacts tests passed")
    return True

def test_user_profile_management():
    """Test user profile management"""
    logger.info("Testing user profile management...")
    
    if not user_tokens.get("user1"):
        logger.error("No user token available for testing")
        return False
    
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Test getting current user profile
    response = requests.get(f"{API_URL}/profile/{user_ids['user1']}", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get user profile: {response.text}")
        return False
    
    logger.info("Successfully retrieved user profile")
    
    # Test updating multiple profile fields
    profile_data = {
        "status_message": f"Testing profile updates {uuid.uuid4().hex[:5]}",
        "display_name": f"New Display Name {uuid.uuid4().hex[:5]}"
    }
    
    response = requests.put(f"{API_URL}/profile", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update profile: {response.text}")
        return False
    
    # Verify fields were updated
    if (response.json().get("status_message") != profile_data["status_message"] or
        response.json().get("display_name") != profile_data["display_name"]):
        logger.error(f"Profile fields not updated correctly: {response.json()}")
        return False
    
    logger.info("Successfully updated multiple profile fields")
    
    # Test updating extended profile
    extended_profile_data = {
        "bio": "This is a test bio",
        "location": "Test City",
        "website": "https://example.com",
        "interests": ["testing", "coding", "chatting"]
    }
    
    response = requests.put(f"{API_URL}/profile/extended", json=extended_profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update extended profile: {response.text}")
        return False
    
    logger.info("Successfully updated extended profile")
    
    # Get profile again to verify extended profile updates
    response = requests.get(f"{API_URL}/profile/{user_ids['user1']}", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get user profile after extended update: {response.text}")
        return False
    
    # Check if profile contains extended data
    profile = response.json()
    if "profile" not in profile:
        logger.warning("Extended profile data not included in response")
    else:
        extended = profile["profile"]
        if extended.get("bio") != extended_profile_data["bio"]:
            logger.warning(f"Extended profile bio not updated correctly: {extended}")
    
    logger.info("User profile management tests passed")
    return True

def run_specific_tests():
    """Run specific tests for the features mentioned in the review request"""
    test_results = {
        "User Registration": test_user_registration(),
        "Display Name Update": test_display_name_update(),
        "Add Contacts": test_add_contacts(),
        "User Profile Management": test_user_profile_management()
    }
    
    return test_results

if __name__ == "__main__":
    # Run specific tests
    results = run_specific_tests()
    
    # Print summary
    print("\n=== TEST RESULTS SUMMARY ===")
    all_passed = True
    
    for test_name, passed in results.items():
        test_status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {test_status}")
        
        if not passed:
            all_passed = False
    
    print("\nOverall result:", "✅ PASSED" if all_passed else "❌ FAILED")