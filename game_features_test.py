import requests
import json
import time
import websocket
import threading
import uuid
import os
import base64
from dotenv import load_dotenv
import logging
from io import BytesIO
from datetime import datetime, timedelta

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
        "username": "alice_smith",
        "email": "alice.smith@example.com",
        "password": "SecurePass123!",
        "phone": "+1234567890"
    },
    {
        "username": "bob_johnson",
        "email": "bob.johnson@example.com",
        "password": "StrongPass456!",
        "phone": "+1987654321"
    },
    {
        "username": "charlie_davis",
        "email": "charlie.davis@example.com",
        "password": "SafePass789!",
        "phone": "+1122334455"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
chat_ids = {}
message_ids = {}
calendar_event_ids = {}
task_ids = {}
document_ids = {}
workspace_profile_ids = {}

def test_user_login():
    """Test user login endpoint"""
    logger.info("Testing user login...")
    
    # Test successful login
    for i, user_data in enumerate(test_users):
        response = requests.post(f"{API_URL}/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        if response.status_code != 200:
            logger.error(f"Failed to log in user {user_data['username']}: {response.text}")
            return False
        
        logger.info(f"User {user_data['username']} logged in successfully")
        user_tokens[f"user{i+1}"] = response.json()["access_token"]
        user_ids[f"user{i+1}"] = response.json()["user"]["user_id"]
    
    logger.info("User login tests passed")
    return True

def test_chat_creation():
    """Test chat creation"""
    logger.info("Testing chat creation...")
    
    # Create direct chat between user1 and user2
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
    
    # Create group chat with all users
    response = requests.post(
        f"{API_URL}/chats",
        json={
            "chat_type": "group",
            "name": "Test Group Chat",
            "members": [user_ids['user2'], user_ids['user3']]
        },
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to create group chat: {response.text}")
        return False
    
    chat_ids['group_chat'] = response.json()["chat_id"]
    logger.info(f"Group chat created with ID: {chat_ids['group_chat']}")
    
    logger.info("Chat creation tests passed")
    return True

def test_calendar_events():
    """Test calendar events endpoints"""
    logger.info("Testing calendar events endpoints...")
    
    # Test POST /api/calendar/events
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Create a calendar event
    event_data = {
        "title": "Team Meeting",
        "description": "Weekly team sync",
        "start_time": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        "end_time": (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat(),
        "event_type": "meeting",
        "location": "Conference Room A",
        "attendees": [user_ids['user2'], user_ids['user3']],
        "reminder_minutes": 15,
        "workspace_mode": "business",
        "priority": "high"
    }
    
    response = requests.post(f"{API_URL}/calendar/events", json=event_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create calendar event: {response.text}")
        return False
    
    event_id = response.json()["event_id"]
    calendar_event_ids['meeting'] = event_id
    logger.info(f"Calendar event created with ID: {event_id}")
    
    # Test GET /api/calendar/events
    response = requests.get(f"{API_URL}/calendar/events", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get calendar events: {response.text}")
        return False
    
    events = response.json()
    if not events or not any(e.get("event_id") == event_id for e in events):
        logger.error(f"Created event not found in events list")
        return False
    
    logger.info(f"Successfully retrieved calendar events: {len(events)} events")
    
    # Test PUT /api/calendar/events/{event_id}
    update_data = {
        "title": "Updated Team Meeting",
        "description": "Updated weekly team sync",
        "priority": "urgent"
    }
    
    response = requests.put(f"{API_URL}/calendar/events/{event_id}", json=update_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update calendar event: {response.text}")
        return False
    
    if response.json().get("title") != update_data["title"]:
        logger.error(f"Event not updated correctly: {response.json()}")
        return False
    
    logger.info("Successfully updated calendar event")
    
    # Test DELETE /api/calendar/events/{event_id}
    response = requests.delete(f"{API_URL}/calendar/events/{event_id}", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to delete calendar event: {response.text}")
        return False
    
    logger.info("Successfully deleted calendar event")
    
    # Verify event was deleted
    response = requests.get(f"{API_URL}/calendar/events", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get calendar events after deletion: {response.text}")
        return False
    
    events = response.json()
    if any(e.get("event_id") == event_id for e in events):
        logger.error(f"Deleted event still found in events list")
        return False
    
    logger.info("Calendar events endpoints tests passed")
    return True

def test_tasks():
    """Test tasks endpoints"""
    logger.info("Testing tasks endpoints...")
    
    # Test POST /api/tasks
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Create a task
    task_data = {
        "title": "Complete Project Proposal",
        "description": "Finish the proposal for the new client project",
        "due_date": (datetime.utcnow() + timedelta(days=3)).isoformat(),
        "priority": "high",
        "workspace_mode": "business",
        "tags": ["proposal", "client", "urgent"],
        "estimated_hours": 4.5
    }
    
    response = requests.post(f"{API_URL}/tasks", json=task_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create task: {response.text}")
        return False
    
    task_id = response.json()["task_id"]
    task_ids['proposal'] = task_id
    logger.info(f"Task created with ID: {task_id}")
    
    # Test GET /api/tasks
    response = requests.get(f"{API_URL}/tasks", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get tasks: {response.text}")
        return False
    
    tasks = response.json()
    if not tasks or not any(t.get("task_id") == task_id for t in tasks):
        logger.error(f"Created task not found in tasks list")
        return False
    
    logger.info(f"Successfully retrieved tasks: {len(tasks)} tasks")
    
    # Test PUT /api/tasks/{task_id}
    update_data = {
        "title": "Updated Project Proposal",
        "status": "in_progress",
        "priority": "urgent"
    }
    
    response = requests.put(f"{API_URL}/tasks/{task_id}", json=update_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update task: {response.text}")
        return False
    
    if response.json().get("title") != update_data["title"] or response.json().get("status") != update_data["status"]:
        logger.error(f"Task not updated correctly: {response.json()}")
        return False
    
    logger.info("Successfully updated task")
    
    logger.info("Tasks endpoints tests passed")
    return True

def test_workspace_profile():
    """Test workspace profile endpoints"""
    logger.info("Testing workspace profile endpoints...")
    
    # Test POST /api/workspace/profile
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Create a workspace profile
    profile_data = {
        "workspace_name": "Tech Solutions Inc.",
        "workspace_type": "business",
        "company_name": "Tech Solutions",
        "department": "Engineering",
        "job_title": "Senior Developer",
        "work_email": "dev@techsolutions.example.com",
        "work_phone": "+1-555-123-4567"
    }
    
    response = requests.post(f"{API_URL}/workspace/profile", json=profile_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create workspace profile: {response.text}")
        return False
    
    profile_id = response.json().get("profile_id")
    if not profile_id:
        logger.error(f"No profile ID returned: {response.json()}")
        return False
    
    workspace_profile_ids['business'] = profile_id
    logger.info(f"Workspace profile created with ID: {profile_id}")
    
    # Test GET /api/workspace/profile
    response = requests.get(f"{API_URL}/workspace/profile", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get workspace profile: {response.text}")
        return False
    
    profile = response.json()
    if not profile or profile.get("workspace_name") != profile_data["workspace_name"]:
        logger.error(f"Retrieved profile doesn't match created profile: {profile}")
        return False
    
    logger.info("Successfully retrieved workspace profile")
    
    logger.info("Workspace profile endpoints tests passed")
    return True

def test_workspace_mode():
    """Test workspace mode endpoint"""
    logger.info("Testing workspace mode endpoint...")
    
    # Test PUT /api/workspace/mode
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Update workspace mode
    mode_data = {
        "mode": "business"
    }
    
    response = requests.put(f"{API_URL}/workspace/mode", json=mode_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update workspace mode: {response.text}")
        return False
    
    if response.json().get("current_mode") != mode_data["mode"]:
        logger.error(f"Workspace mode not updated correctly: {response.json()}")
        return False
    
    logger.info("Successfully updated workspace mode")
    
    # Switch back to personal mode
    mode_data = {
        "mode": "personal"
    }
    
    response = requests.put(f"{API_URL}/workspace/mode", json=mode_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to switch back to personal mode: {response.text}")
        return False
    
    logger.info("Successfully switched back to personal mode")
    
    logger.info("Workspace mode endpoint test passed")
    return True

def test_documents():
    """Test documents endpoints"""
    logger.info("Testing documents endpoints...")
    
    # Test POST /api/documents
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    # Create a document
    document_data = {
        "title": "Project Requirements",
        "content": "# Project Requirements\n\n## Overview\nThis document outlines the requirements for the new project.\n\n## Features\n1. User authentication\n2. Real-time messaging\n3. File sharing\n\n## Timeline\nThe project is expected to be completed within 3 months.",
        "document_type": "markdown",
        "workspace_mode": "business",
        "tags": ["requirements", "project", "documentation"]
    }
    
    response = requests.post(f"{API_URL}/documents", json=document_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to create document: {response.text}")
        return False
    
    document_id = response.json()["document_id"]
    document_ids['requirements'] = document_id
    logger.info(f"Document created with ID: {document_id}")
    
    # Test GET /api/documents
    response = requests.get(f"{API_URL}/documents", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to get documents: {response.text}")
        return False
    
    documents = response.json()
    if not documents or not any(d.get("document_id") == document_id for d in documents):
        logger.error(f"Created document not found in documents list")
        return False
    
    logger.info(f"Successfully retrieved documents: {len(documents)} documents")
    
    # Test PUT /api/documents/{document_id}
    update_data = {
        "title": "Updated Project Requirements",
        "content": "# Updated Project Requirements\n\n## Overview\nThis document outlines the updated requirements for the new project.\n\n## Features\n1. User authentication\n2. Real-time messaging\n3. File sharing\n4. Video calls\n\n## Timeline\nThe project is expected to be completed within 4 months."
    }
    
    response = requests.put(f"{API_URL}/documents/{document_id}", json=update_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to update document: {response.text}")
        return False
    
    if response.json().get("title") != update_data["title"]:
        logger.error(f"Document not updated correctly: {response.json()}")
        return False
    
    logger.info("Successfully updated document")
    
    logger.info("Documents endpoints tests passed")
    return True

def test_game_message_types():
    """Test sending messages with game-related message types"""
    logger.info("Testing game-related message types...")
    
    # Test sending a game_invite message
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    
    game_invite_data = {
        "content": "I'd like to play a game of chess!",
        "message_type": "game_invite",
        "game_type": "chess",
        "game_id": str(uuid.uuid4())
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        json=game_invite_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send game_invite message: {response.text}")
        return False
    
    game_invite_message_id = response.json()["message_id"]
    logger.info(f"Game invite message sent with ID: {game_invite_message_id}")
    
    # Test sending a chess_move message
    chess_move_data = {
        "content": "e2-e4",
        "message_type": "chess_move",
        "game_id": game_invite_data["game_id"],
        "move_notation": "e2-e4"
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        json=chess_move_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send chess_move message: {response.text}")
        return False
    
    chess_move_message_id = response.json()["message_id"]
    logger.info(f"Chess move message sent with ID: {chess_move_message_id}")
    
    # Test sending a tictactoe_move message
    tictactoe_game_id = str(uuid.uuid4())
    
    tictactoe_invite_data = {
        "content": "Let's play Tic-Tac-Toe!",
        "message_type": "game_invite",
        "game_type": "tictactoe",
        "game_id": tictactoe_game_id
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        json=tictactoe_invite_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send tictactoe invite message: {response.text}")
        return False
    
    tictactoe_move_data = {
        "content": "Center square",
        "message_type": "tictactoe_move",
        "game_id": tictactoe_game_id,
        "position": 4  # Center square (0-8)
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        json=tictactoe_move_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send tictactoe_move message: {response.text}")
        return False
    
    tictactoe_move_message_id = response.json()["message_id"]
    logger.info(f"Tic-tac-toe move message sent with ID: {tictactoe_move_message_id}")
    
    # Test sending a wordguess message
    wordguess_game_id = str(uuid.uuid4())
    
    wordguess_invite_data = {
        "content": "Let's play Word Guess!",
        "message_type": "game_invite",
        "game_type": "wordguess",
        "game_id": wordguess_game_id
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        json=wordguess_invite_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send wordguess invite message: {response.text}")
        return False
    
    wordguess_move_data = {
        "content": "HELLO",
        "message_type": "wordguess",
        "game_id": wordguess_game_id,
        "guess": "HELLO",
        "result": "🟩🟨⬛🟨🟩"  # Green, yellow, gray, yellow, green
    }
    
    response = requests.post(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        json=wordguess_move_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send wordguess message: {response.text}")
        return False
    
    wordguess_message_id = response.json()["message_id"]
    logger.info(f"Word guess message sent with ID: {wordguess_message_id}")
    
    # Verify messages were sent correctly
    response = requests.get(
        f"{API_URL}/chats/{chat_ids['direct_chat']}/messages",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get messages to verify game messages: {response.text}")
        return False
    
    messages = response.json()
    
    # Check for game_invite message
    game_invite_message = next((m for m in messages if m.get("message_id") == game_invite_message_id), None)
    if not game_invite_message or game_invite_message.get("message_type") != "game_invite":
        logger.error(f"Game invite message not found or has incorrect type: {game_invite_message}")
        return False
    
    # Check for chess_move message
    chess_move_message = next((m for m in messages if m.get("message_id") == chess_move_message_id), None)
    if not chess_move_message or chess_move_message.get("message_type") != "chess_move":
        logger.error(f"Chess move message not found or has incorrect type: {chess_move_message}")
        return False
    
    logger.info("Game-related message types tests passed")
    return True

def run_tests():
    """Run all tests"""
    logger.info("Starting backend tests for new game features...")
    
    # Basic setup
    if not test_user_login():
        logger.error("User login test failed")
        return False
    
    if not test_chat_creation():
        logger.error("Chat creation test failed")
        return False
    
    # Workspace features tests
    if not test_calendar_events():
        logger.error("Calendar events test failed")
        return False
    
    if not test_tasks():
        logger.error("Tasks test failed")
        return False
    
    if not test_workspace_profile():
        logger.error("Workspace profile test failed")
        return False
    
    if not test_workspace_mode():
        logger.error("Workspace mode test failed")
        return False
    
    if not test_documents():
        logger.error("Documents test failed")
        return False
    
    # Game features tests
    if not test_game_message_types():
        logger.error("Game message types test failed")
        return False
    
    logger.info("All tests passed successfully!")
    return True

if __name__ == "__main__":
    run_tests()