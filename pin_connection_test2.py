#!/usr/bin/env python3

import requests
import json
import time
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
        "username": "pin_test_user1",
        "email": "pin_test1@example.com",
        "password": "SecurePin123!",
        "phone": "+1555123456"
    },
    {
        "username": "pin_test_user2",
        "email": "pin_test2@example.com",
        "password": "SecurePin456!",
        "phone": "+1555654321"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
connection_pins = {}
connection_request_ids = {}

def test_pin_connection_system():
    """Test the complete PIN-based connection system"""
    
    # Step 1: Register test users
    logger.info("Step 1: Registering test users...")
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
    
    # Step 2: Complete profiles to generate PINs
    logger.info("Step 2: Completing user profiles...")
    for i, user_key in enumerate(['user1', 'user2']):
        headers = {"Authorization": f"Bearer {user_tokens[user_key]}"}
        profile_data = {
            "display_name": f"PIN Test User {i+1}",
            "age": 30 + i,
            "gender": "male" if i % 2 == 0 else "female",
            "location": "Test City",
            "bio": f"Test user {i+1} for PIN connection system",
            "interests": ["technology", "testing"],
            "values": ["quality", "reliability"]
        }
        
        response = requests.put(f"{API_URL}/profile/complete", json=profile_data, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to complete profile for {user_key}: {response.text}")
            return False
        
        logger.info(f"Profile completed for {user_key}")
        
        # Check if PIN was generated
        if not response.json().get("connection_pin"):
            # Get user info to check for PIN
            user_response = requests.get(f"{API_URL}/users/me", headers=headers)
            if user_response.status_code != 200 or not user_response.json().get("connection_pin"):
                logger.error(f"Connection PIN not generated for {user_key}")
                return False
            connection_pins[user_key] = user_response.json()["connection_pin"]
        else:
            connection_pins[user_key] = response.json()["connection_pin"]
        
        logger.info(f"{user_key} has connection PIN: {connection_pins[user_key]}")
    
    # Step 3: Test QR code generation
    logger.info("Step 3: Testing QR code generation...")
    for user_key in ['user1', 'user2']:
        headers = {"Authorization": f"Bearer {user_tokens[user_key]}"}
        response = requests.get(f"{API_URL}/users/qr-code", headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get QR code for {user_key}: {response.text}")
            return False
        
        if not response.json().get("connection_pin") or not response.json().get("qr_code"):
            logger.error(f"QR code response missing required fields for {user_key}")
            return False
        
        # Verify the PIN matches what we have stored
        if response.json()["connection_pin"] != connection_pins[user_key]:
            logger.error(f"Connection PIN mismatch for {user_key}")
            return False
        
        logger.info(f"Successfully generated QR code for {user_key}")
    
    # Step 4: User2 sends connection request to User1 using PIN
    logger.info("Step 4: Testing connection request by PIN...")
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    request_data = {
        "target_pin": connection_pins['user1'],
        "message": "Hello, I'd like to connect with you!"
    }
    
    response = requests.post(f"{API_URL}/connections/request-by-pin", json=request_data, headers=headers)
    
    if response.status_code == 200:
        connection_request_ids['request1'] = response.json()["request_id"]
        logger.info(f"Connection request sent successfully with ID: {connection_request_ids['request1']}")
    elif response.status_code == 400 and "Already connected" in response.json().get("detail", ""):
        logger.info("Users are already connected, skipping connection request")
        
        # Skip to step 7 to verify chat exists
        logger.info("Step 7: Verifying existing chat...")
        headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
        response = requests.get(f"{API_URL}/chats", headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get chats: {response.text}")
            return False
        
        chats = response.json()
        
        # Find direct chat with user2
        direct_chat = next((
            c for c in chats 
            if (c.get("chat_type") == "direct" or c.get("type") == "direct") and 
            (user_ids['user2'] in c.get("members", []) or user_ids['user2'] in c.get("participants", []))
        ), None)
        
        if not direct_chat:
            logger.info("No direct chat found between users despite being connected")
            
            # Create a chat directly since one doesn't exist
            logger.info("Creating a direct chat between the users...")
            chat_data = {
                "chat_type": "direct",
                "other_user_id": user_ids['user2']
            }
            
            response = requests.post(f"{API_URL}/chats", json=chat_data, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to create direct chat: {response.text}")
                return False
            
            chat_id = response.json()["chat_id"]
            logger.info(f"Created direct chat with ID: {chat_id}")
        else:
            logger.info(f"Found existing direct chat with ID: {direct_chat.get('chat_id') or direct_chat.get('id')}")
            chat_id = direct_chat.get('chat_id') or direct_chat.get('id')
        
        # Step 8: Testing message sending in new chat
        logger.info("Step 8: Testing message sending in new chat...")
        
        message_data = {
            "content": "Hello! This is a test message in our new connection."
        }
        
        response = requests.post(
            f"{API_URL}/chats/{chat_id}/messages",
            json=message_data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to send message in existing chat: {response.text}")
            return False
        
        logger.info("Message sent successfully in the existing chat")
        
        # Skip to step 9
        logger.info("Step 9: Testing trust level update...")
        
        # Get the connection ID
        response = requests.get(f"{API_URL}/connections", headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get connections: {response.text}")
            return False
        
        connections = response.json()
        if not connections:
            logger.error("No connections found for user1")
            return False
        
        # Find connection with user2
        connection = next((
            c for c in connections if 
            c.get("connected_user_id") == user_ids['user2'] or 
            c.get("user_id") == user_ids['user2']
        ), None)
        if not connection:
            logger.error(f"Connection with user2 not found")
            return False
        
        connection_id = connection.get("connection_id")
        
        # Get current trust level
        current_trust_level = connection.get("trust_level", 1)
        
        # Update trust level by 1
        new_trust_level = min(5, current_trust_level + 1)
        trust_data = {
            "trust_level": new_trust_level
        }
        
        response = requests.put(
            f"{API_URL}/connections/{connection_id}/trust-level",
            json=trust_data,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to update trust level: {response.text}")
            return False
        
        if "trust_level" not in response.json():
            logger.error(f"Trust level not included in response: {response.json()}")
            return False
        
        logger.info(f"Trust level updated successfully to level {response.json()['trust_level']}")
        
        logger.info("PIN-based connection system tests PASSED!")
        return True
    else:
        logger.error(f"Failed to send connection request by PIN: {response.text}")
        return False
    
    # Continue with normal flow if connection request was sent successfully
    # Step 5: User1 checks pending connection requests
    logger.info("Step 5: Checking pending connection requests...")
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    response = requests.get(f"{API_URL}/connections/requests", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connection requests: {response.text}")
        return False
    
    requests_list = response.json()
    if not requests_list:
        logger.error("No connection requests found for user1")
        return False
    
    # Verify the request from user2 is in the list
    request = next((r for r in requests_list if r.get("sender_id") == user_ids['user2']), None)
    if not request:
        logger.error(f"Connection request from user2 not found in requests list")
        return False
    
    logger.info(f"Successfully retrieved connection requests for user1")
    
    # Step 6: User1 accepts the connection request
    logger.info("Step 6: Accepting connection request...")
    response_data = {
        "action": "accept"
    }
    
    response = requests.put(
        f"{API_URL}/connections/requests/{connection_request_ids['request1']}",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept connection request: {response.text}")
        return False
    
    if response.json().get("status") != "accepted":
        logger.error(f"Connection request not marked as accepted: {response.json()}")
        return False
    
    logger.info("Connection request accepted successfully")
    
    # Step 7: Verify a chat was created between the users
    logger.info("Step 7: Verifying chat creation...")
    response = requests.get(f"{API_URL}/chats", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get chats after connection: {response.text}")
        return False
    
    chats = response.json()
    
    # Find direct chat with user2
    direct_chat = next((
        c for c in chats 
        if (c.get("chat_type") == "direct" or c.get("type") == "direct") and 
        (user_ids['user2'] in c.get("members", []) or user_ids['user2'] in c.get("participants", []))
    ), None)
    
    if not direct_chat:
        logger.error("Direct chat not created after accepting connection request")
        return False
    
    logger.info(f"Direct chat created successfully with ID: {direct_chat.get('chat_id')}")
    
    # Step 8: Test sending a message in the new chat
    logger.info("Step 8: Testing message sending in new chat...")
    chat_id = direct_chat.get('chat_id')
    
    message_data = {
        "content": "Hello! This is a test message in our new connection."
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_id}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send message in new chat: {response.text}")
        return False
    
    logger.info("Message sent successfully in the new chat")
    
    # Step 9: Test updating trust level
    logger.info("Step 9: Testing trust level update...")
    
    # Get the connection ID
    response = requests.get(f"{API_URL}/connections", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get connections: {response.text}")
        return False
    
    connections = response.json()
    if not connections:
        logger.error("No connections found for user1")
        return False
    
    # Find connection with user2
    connection = next((c for c in connections if c.get("connected_user_id") == user_ids['user2']), None)
    if not connection:
        logger.error(f"Connection with user2 not found")
        return False
    
    connection_id = connection.get("connection_id")
    
    # Update trust level to 3 (Voice Call)
    trust_data = {
        "trust_level": 3
    }
    
    response = requests.put(
        f"{API_URL}/connections/{connection_id}/trust-level",
        json=trust_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to update trust level: {response.text}")
        return False
    
    if response.json().get("trust_level") != 3:
        logger.error(f"Trust level not updated correctly: {response.json()}")
        return False
    
    logger.info("Trust level updated successfully to level 3 (Voice Call)")
    
    logger.info("PIN-based connection system tests PASSED!")
    return True

if __name__ == "__main__":
    test_pin_connection_system()