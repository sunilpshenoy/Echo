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
connection_requests = {}

def login_user(email, password):
    """Login a user and return the token and user data"""
    response = requests.post(f"{API_URL}/login", json={"email": email, "password": password})
    
    if response.status_code != 200:
        logger.error(f"Failed to login user {email}: {response.text}")
        return None, None
    
    token = response.json()["access_token"]
    user = response.json()["user"]
    return token, user

def test_detailed_contact_display_names():
    """Test detailed contact display names"""
    logger.info("Testing detailed contact display names...")
    
    # Login as Alice
    alice_token, alice_data = login_user("alice@test.com", "password123")
    if not alice_token:
        return False
    
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    
    # Get Alice's contacts
    response = requests.get(f"{API_URL}/contacts", headers=alice_headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get Alice's contacts: {response.text}")
        return False
    
    alice_contacts = response.json()
    logger.info(f"Alice has {len(alice_contacts)} contacts")
    
    # Check if contacts have proper display names
    for contact in alice_contacts:
        if "contact_user" not in contact:
            logger.error(f"Contact missing contact_user data: {contact}")
            continue
        
        logger.info(f"Contact details: {json.dumps(contact, indent=2)}")
        
        if "display_name" not in contact["contact_user"] or not contact["contact_user"]["display_name"]:
            logger.warning(f"Contact missing display_name: {contact['contact_user']['email']}")
        else:
            logger.info(f"Contact {contact['contact_user']['email']} has display_name: {contact['contact_user']['display_name']}")
    
    # Login as Bob
    bob_token, bob_data = login_user("bob@test.com", "password123")
    if not bob_token:
        return False
    
    bob_headers = {"Authorization": f"Bearer {bob_token}"}
    
    # Get Bob's contacts
    response = requests.get(f"{API_URL}/contacts", headers=bob_headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get Bob's contacts: {response.text}")
        return False
    
    bob_contacts = response.json()
    logger.info(f"Bob has {len(bob_contacts)} contacts")
    
    # Check if contacts have proper display names
    for contact in bob_contacts:
        if "contact_user" not in contact:
            logger.error(f"Contact missing contact_user data: {contact}")
            continue
        
        logger.info(f"Contact details: {json.dumps(contact, indent=2)}")
        
        if "display_name" not in contact["contact_user"] or not contact["contact_user"]["display_name"]:
            logger.warning(f"Contact missing display_name: {contact['contact_user']['email']}")
        else:
            logger.info(f"Contact {contact['contact_user']['email']} has display_name: {contact['contact_user']['display_name']}")
    
    logger.info("Detailed contact display names test completed")
    return True

def test_detailed_pin_connection():
    """Test detailed PIN-based connection"""
    logger.info("Testing detailed PIN-based connection...")
    
    # Login as Alice
    alice_token, alice_data = login_user("alice@test.com", "password123")
    if not alice_token:
        return False
    
    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    
    # Get Alice's QR code and PIN
    response = requests.get(f"{API_URL}/users/qr-code", headers=alice_headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get Alice's QR code: {response.text}")
        return False
    
    alice_qr_data = response.json()
    logger.info(f"Alice's connection PIN: {alice_qr_data.get('connection_pin')}")
    
    # Login as Bob
    bob_token, bob_data = login_user("bob@test.com", "password123")
    if not bob_token:
        return False
    
    bob_headers = {"Authorization": f"Bearer {bob_token}"}
    
    # Get Bob's QR code and PIN
    response = requests.get(f"{API_URL}/users/qr-code", headers=bob_headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get Bob's QR code: {response.text}")
        return False
    
    bob_qr_data = response.json()
    logger.info(f"Bob's connection PIN: {bob_qr_data.get('connection_pin')}")
    
    # Test connection request from Alice to Bob using PIN
    pin_data = {"target_pin": bob_qr_data.get('connection_pin')}
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=pin_data, headers=alice_headers)
    
    if response.status_code == 200:
        logger.info(f"Successfully sent connection request from Alice to Bob using PIN")
        connection_requests["alice_to_bob"] = response.json()
        logger.info(f"Connection request details: {json.dumps(response.json(), indent=2)}")
    elif response.status_code == 400 and "Connection request already sent" in response.json().get("detail", ""):
        logger.info("Connection request from Alice to Bob already exists")
    elif response.status_code == 400 and "Already connected" in response.json().get("detail", ""):
        logger.info("Alice and Bob are already connected")
    else:
        logger.error(f"Failed to send connection request from Alice to Bob: {response.text}")
        return False
    
    # Get pending connection requests for Bob
    response = requests.get(f"{API_URL}/connections/requests", headers=bob_headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get Bob's connection requests: {response.text}")
        return False
    
    bob_requests = response.json()
    logger.info(f"Bob has {len(bob_requests)} connection requests")
    
    # Check if requests have proper sender details
    for request in bob_requests:
        logger.info(f"Connection request details: {json.dumps(request, indent=2)}")
        
        if "sender" not in request:
            logger.error(f"Connection request missing sender data: {request}")
            continue
        
        if "display_name" not in request["sender"] or not request["sender"]["display_name"]:
            logger.warning(f"Connection request sender missing display_name: {request['sender']['email']}")
        else:
            logger.info(f"Connection request from {request['sender']['email']} has display_name: {request['sender']['display_name']}")
    
    logger.info("Detailed PIN-based connection test completed")
    return True

def run_detailed_tests():
    """Run detailed tests"""
    logger.info("Starting detailed tests...")
    
    # Test detailed contact display names
    if not test_detailed_contact_display_names():
        logger.error("Detailed contact display names test failed")
        return False
    
    # Test detailed PIN-based connection
    if not test_detailed_pin_connection():
        logger.error("Detailed PIN-based connection test failed")
        return False
    
    logger.info("All detailed tests completed successfully!")
    return True

if __name__ == "__main__":
    run_detailed_tests()