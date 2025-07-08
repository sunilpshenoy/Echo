import requests
import json
import uuid
import time
from datetime import datetime, timedelta

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"')
            break

API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test users
TEST_USER1 = {
    "username": "map_test_user1",
    "email": "map_test1@example.com",
    "password": "TestPassword123!"
}

TEST_USER2 = {
    "username": "map_test_user2",
    "email": "map_test2@example.com",
    "password": "TestPassword123!"
}

# Global variables to store test data
user1_token = None
user2_token = None
user1_id = None
user2_id = None
test_team_id = None
test_channel_id = None
test_event_id = None

# Helper functions
def register_user(user_data):
    response = requests.post(f"{API_URL}/register", json=user_data)
    if response.status_code == 400 and "Email already registered" in response.text:
        # User already exists, try to login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        response = requests.post(f"{API_URL}/login", json=login_data)
    
    assert response.status_code == 200, f"Failed to register/login user: {response.text}"
    return response.json()

def create_team(token, team_data):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/teams", json=team_data, headers=headers)
    assert response.status_code == 200, f"Failed to create team: {response.text}"
    return response.json()

def setup():
    global user1_token, user2_token, user1_id, user2_id, test_team_id
    
    # Register/login test users
    print("Registering test users...")
    user1_data = register_user(TEST_USER1)
    user2_data = register_user(TEST_USER2)
    
    user1_token = user1_data["access_token"]
    user2_token = user2_data["access_token"]
    user1_id = user1_data["user"]["user_id"]
    user2_id = user2_data["user"]["user_id"]
    
    print(f"User 1 ID: {user1_id}")
    print(f"User 2 ID: {user2_id}")
    
    # Create a test team
    print("Creating test team...")
    team_data = {
        "name": f"Test Team {uuid.uuid4().hex[:8]}",
        "description": "Test team for API testing",
        "members": [user1_id, user2_id]
    }
    
    team_response = create_team(user1_token, team_data)
    test_team_id = team_response["team_id"]
    print(f"Test team ID: {test_team_id}")

def test_map_view_api():
    print("\n=== Testing Map View API ===")
    
    # Test 1: Get groups on map
    print("Test 1: Getting groups on map...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    
    # Test with default parameters
    response = requests.get(
        f"{API_URL}/map/groups",
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get groups on map: {response.text}"
    result = response.json()
    print(f"Found {len(result)} groups on map")
    
    # Test with specific location and radius
    params = {
        "lat": 37.7749,
        "lng": -122.4194,
        "radius": 10
    }
    response = requests.get(
        f"{API_URL}/map/groups",
        params=params,
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get groups on map with location: {response.text}"
    result = response.json()
    print(f"Found {len(result)} groups on map within radius")
    
    # Verify response format
    if len(result) > 0:
        group = result[0]
        assert "group_id" in group, "Group ID missing in response"
        assert "name" in group, "Group name missing in response"
        assert "location" in group, "Location missing in response"
        assert "lat" in group["location"], "Latitude missing in location"
        assert "lng" in group["location"], "Longitude missing in location"
    
    # Test 2: Get activities on map
    print("Test 2: Getting activities on map...")
    
    # Test with default parameters
    response = requests.get(
        f"{API_URL}/map/activities",
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get activities on map: {response.text}"
    result = response.json()
    print(f"Found {len(result)} activities on map")
    
    # Test with specific location, radius, and date range
    today = datetime.now()
    one_week_later = today + timedelta(days=7)
    
    params = {
        "lat": 37.7749,
        "lng": -122.4194,
        "radius": 10,
        "start_date": today.isoformat(),
        "end_date": one_week_later.isoformat()
    }
    response = requests.get(
        f"{API_URL}/map/activities",
        params=params,
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get activities on map with parameters: {response.text}"
    result = response.json()
    print(f"Found {len(result)} activities on map within radius and date range")
    
    # Verify response format
    if len(result) > 0:
        activity = result[0]
        assert "activity_id" in activity, "Activity ID missing in response"
        assert "title" in activity, "Title missing in response"
        assert "location" in activity, "Location missing in response"
        assert "lat" in activity["location"], "Latitude missing in location"
        assert "lng" in activity["location"], "Longitude missing in location"
        assert "start_time" in activity, "Start time missing in response"
    
    print("Map View API tests passed!")

def test_channels_api():
    print("\n=== Testing Channels API ===")
    global test_channel_id
    
    # Test 1: Get team channels
    print("Test 1: Getting team channels...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    
    response = requests.get(
        f"{API_URL}/teams/{test_team_id}/channels",
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get team channels: {response.text}"
    channels = response.json()
    print(f"Found {len(channels)} channels in team")
    
    # Test 2: Create a channel
    print("Test 2: Creating a channel...")
    channel_data = {
        "name": f"Test Channel {uuid.uuid4().hex[:8]}",
        "description": "Test channel for API testing",
        "channel_type": "general"
    }
    
    response = requests.post(
        f"{API_URL}/teams/{test_team_id}/channels",
        json=channel_data,
        headers=headers
    )
    assert response.status_code == 200, f"Failed to create channel: {response.text}"
    channel = response.json()
    test_channel_id = channel["channel_id"]
    print(f"Created channel with ID: {test_channel_id}")
    
    # Test 3: Get channel messages
    print("Test 3: Getting channel messages...")
    response = requests.get(
        f"{API_URL}/channels/{test_channel_id}/messages",
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get channel messages: {response.text}"
    messages = response.json()
    print(f"Found {len(messages)} messages in channel")
    
    # Test 4: Send a message to the channel
    print("Test 4: Sending a message to the channel...")
    message_data = {
        "content": "Test message for channel API testing"
    }
    
    response = requests.post(
        f"{API_URL}/channels/{test_channel_id}/messages",
        json=message_data,
        headers=headers
    )
    assert response.status_code == 200, f"Failed to send message to channel: {response.text}"
    message = response.json()
    assert "message_id" in message, "Message ID missing in response"
    print(f"Sent message with ID: {message['message_id']}")
    
    # Test 5: Verify message was added
    print("Test 5: Verifying message was added...")
    response = requests.get(
        f"{API_URL}/channels/{test_channel_id}/messages",
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get channel messages: {response.text}"
    messages = response.json()
    assert len(messages) > 0, "No messages found in channel after sending"
    
    # Test 6: Test access control - user not in team
    print("Test 6: Testing access control...")
    # Create a new user not in the team
    new_user = {
        "username": "map_test_user3",
        "email": "map_test3@example.com",
        "password": "TestPassword123!"
    }
    new_user_data = register_user(new_user)
    new_user_token = new_user_data["access_token"]
    
    # Try to access channel messages
    headers_new = {"Authorization": f"Bearer {new_user_token}"}
    response = requests.get(
        f"{API_URL}/channels/{test_channel_id}/messages",
        headers=headers_new
    )
    assert response.status_code in [403, 404], "User not in team should not be able to access channel messages"
    
    print("Channels API tests passed!")

def test_calendar_api():
    print("\n=== Testing Calendar API ===")
    global test_event_id
    
    # Test 1: Get calendar events
    print("Test 1: Getting calendar events...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    
    # Test with default parameters
    response = requests.get(
        f"{API_URL}/calendar/events",
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get calendar events: {response.text}"
    events = response.json()
    print(f"Found {len(events)} calendar events")
    
    # Test with date range
    today = datetime.now()
    one_month_later = today + timedelta(days=30)
    
    params = {
        "start_date": today.isoformat(),
        "end_date": one_month_later.isoformat()
    }
    response = requests.get(
        f"{API_URL}/calendar/events",
        params=params,
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get calendar events with date range: {response.text}"
    events = response.json()
    print(f"Found {len(events)} calendar events within date range")
    
    # Test 2: Create a calendar event
    print("Test 2: Creating a calendar event...")
    tomorrow = today + timedelta(days=1)
    tomorrow_end = tomorrow + timedelta(hours=1)
    
    event_data = {
        "title": f"Test Event {uuid.uuid4().hex[:8]}",
        "description": "Test event for API testing",
        "start_time": tomorrow.isoformat(),
        "end_time": tomorrow_end.isoformat(),
        "event_type": "meeting",
        "location": "Virtual",
        "attendees": [user2_id]
    }
    
    response = requests.post(
        f"{API_URL}/calendar/events",
        json=event_data,
        headers=headers
    )
    assert response.status_code == 200, f"Failed to create calendar event: {response.text}"
    event = response.json()
    test_event_id = event["event_id"]
    print(f"Created event with ID: {test_event_id}")
    
    # Test 3: Verify event was created
    print("Test 3: Verifying event was created...")
    response = requests.get(
        f"{API_URL}/calendar/events",
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get calendar events: {response.text}"
    events = response.json()
    
    found_event = False
    for event in events:
        if event.get("event_id") == test_event_id:
            found_event = True
            assert event["title"] == event_data["title"], "Event title doesn't match"
            assert event["description"] == event_data["description"], "Event description doesn't match"
            assert event["event_type"] == event_data["event_type"], "Event type doesn't match"
            break
    
    assert found_event, "Created event not found in calendar events"
    
    # Test 4: Test validation - invalid date range
    print("Test 4: Testing validation - invalid date range...")
    invalid_event_data = {
        "title": "Invalid Event",
        "description": "Event with end time before start time",
        "start_time": tomorrow_end.isoformat(),  # End time
        "end_time": tomorrow.isoformat(),        # Start time (earlier)
        "event_type": "meeting"
    }
    
    response = requests.post(
        f"{API_URL}/calendar/events",
        json=invalid_event_data,
        headers=headers
    )
    assert response.status_code == 400, "Should reject event with end time before start time"
    
    print("Calendar API tests passed!")

def run_tests():
    try:
        setup()
        test_map_view_api()
        test_channels_api()
        test_calendar_api()
        print("\n✅ All API tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_tests()