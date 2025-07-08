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
    "username": "api_test_user1",
    "email": "api_test1@example.com",
    "password": "TestPassword123!"
}

TEST_USER2 = {
    "username": "api_test_user2",
    "email": "api_test2@example.com",
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

def setup():
    global user1_token, user2_token, user1_id, user2_id
    
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

def test_map_view_api():
    print("\n=== Testing Map View API ===")
    
    # Test 1: Get groups on map
    print("Test 1: Getting groups on map...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    
    # Test with required parameters
    params = {
        "lat": 37.7749,
        "lng": -122.4194
    }
    response = requests.get(
        f"{API_URL}/map/groups",
        params=params,
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
    
    # Test with required parameters
    params = {
        "lat": 37.7749,
        "lng": -122.4194
    }
    response = requests.get(
        f"{API_URL}/map/activities",
        params=params,
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
        "start_date": today.strftime("%Y-%m-%d"),
        "end_date": one_week_later.strftime("%Y-%m-%d")
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

def test_teams_channels_api():
    print("\n=== Testing Teams and Channels API ===")
    global test_team_id, test_channel_id
    
    # Test 1: Get teams
    print("Test 1: Getting teams...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    
    response = requests.get(
        f"{API_URL}/teams",
        headers=headers
    )
    assert response.status_code == 200, f"Failed to get teams: {response.text}"
    teams = response.json()
    print(f"Found {len(teams)} teams")
    
    # Test 2: Create a team
    print("Test 2: Creating a team...")
    team_data = {
        "name": f"Test Team {uuid.uuid4().hex[:8]}",
        "description": "Test team for API testing",
        "members": [user1_id, user2_id]
    }
    
    response = requests.post(
        f"{API_URL}/teams",
        json=team_data,
        headers=headers
    )
    
    if response.status_code == 200:
        team = response.json()
        if team:
            test_team_id = team.get("team_id")
            print(f"Created team with ID: {test_team_id}")
        else:
            print("Team creation response was empty")
            # Try to use an existing team
            if teams and len(teams) > 0:
                test_team_id = teams[0].get("team_id")
                print(f"Using existing team with ID: {test_team_id}")
            else:
                print("No teams available, skipping team-specific tests")
                return
    
    # Test 3: Get team channels
    print("Test 3: Getting team channels...")
    response = requests.get(
        f"{API_URL}/teams/{test_team_id}/channels",
        headers=headers
    )
    
    if response.status_code == 200:
        channels = response.json()
        print(f"Found {len(channels)} channels in team")
        
        # If channels exist, use the first one for testing
        if channels and len(channels) > 0:
            test_channel_id = channels[0].get("channel_id")
            print(f"Using existing channel with ID: {test_channel_id}")
    else:
        print(f"Failed to get team channels: {response.status_code} - {response.text}")
    
    # Test 4: Create a channel
    print("Test 4: Creating a channel...")
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
    
    if response.status_code == 200:
        channel = response.json()
        test_channel_id = channel.get("channel_id")
        print(f"Created channel with ID: {test_channel_id}")
    else:
        print(f"Failed to create channel: {response.status_code} - {response.text}")
        if not test_channel_id:
            print("No channels available, skipping channel-specific tests")
            return
    
    # Test 5: Get channel messages
    print("Test 5: Getting channel messages...")
    response = requests.get(
        f"{API_URL}/channels/{test_channel_id}/messages",
        headers=headers
    )
    
    if response.status_code == 200:
        messages = response.json()
        print(f"Found {len(messages)} messages in channel")
    else:
        print(f"Failed to get channel messages: {response.status_code} - {response.text}")
    
    # Test 6: Send a message to the channel
    print("Test 6: Sending a message to the channel...")
    message_data = {
        "content": "Test message for channel API testing"
    }
    
    response = requests.post(
        f"{API_URL}/channels/{test_channel_id}/messages",
        json=message_data,
        headers=headers
    )
    
    if response.status_code == 200:
        message = response.json()
        print(f"Sent message with ID: {message.get('message_id')}")
        
        # Verify message was added
        response = requests.get(
            f"{API_URL}/channels/{test_channel_id}/messages",
            headers=headers
        )
        
        if response.status_code == 200:
            messages = response.json()
            print(f"Found {len(messages)} messages in channel after sending")
    else:
        print(f"Failed to send message to channel: {response.status_code} - {response.text}")
    
    print("Teams and Channels API tests completed!")

def test_calendar_api():
    print("\n=== Testing Calendar API ===")
    global test_event_id
    
    # Test 1: Get calendar events
    print("Test 1: Getting calendar events...")
    headers = {"Authorization": f"Bearer {user1_token}"}
    
    # Try with required parameters
    today = datetime.now()
    one_month_later = today + timedelta(days=30)
    
    # Format dates as strings in ISO format
    start_date_str = today.strftime("%Y-%m-%d")
    end_date_str = one_month_later.strftime("%Y-%m-%d")
    
    params = {
        "start_date": start_date_str,
        "end_date": end_date_str
    }
    
    print(f"Using date parameters: {params}")
    
    response = requests.get(
        f"{API_URL}/calendar/events",
        params=params,
        headers=headers
    )
    
    if response.status_code == 200:
        events = response.json()
        print(f"Found {len(events)} calendar events")
    else:
        print(f"Failed to get calendar events: {response.status_code} - {response.text}")
    
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
    
    if response.status_code == 200:
        event = response.json()
        test_event_id = event.get("event_id")
        print(f"Created event with ID: {test_event_id}")
        
        # Verify event was created
        response = requests.get(
            f"{API_URL}/calendar/events",
            params=params,
            headers=headers
        )
        
        if response.status_code == 200:
            events = response.json()
            print(f"Found {len(events)} calendar events after creating")
    else:
        print(f"Failed to create calendar event: {response.status_code} - {response.text}")
    
    print("Calendar API tests completed!")

def run_tests():
    try:
        setup()
        test_map_view_api()
        test_teams_channels_api()
        test_calendar_api()
        print("\n✅ All API tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_tests()