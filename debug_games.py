#!/usr/bin/env python3
"""
Debug games system issues
"""

import requests
import json

BACKEND_URL = "https://9b83238d-a27b-406f-8157-e448fada6ab0.preview.emergentagent.com/api"

# Login first
login_data = {
    "email": "games_backend_test@example.com",
    "password": "TestPassword123!"
}

session = requests.Session()
response = session.post(f"{BACKEND_URL}/login", json=login_data)

if response.status_code == 200:
    data = response.json()
    token = data.get("access_token")
    user_data = data.get("user", {})
    user_id = user_data.get("user_id")
    
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    print(f"Logged in as: {user_id}")
    
    # Create a room
    room_data = {
        "name": "Debug Room",
        "gameType": "tic-tac-toe",
        "maxPlayers": 2,
        "isPrivate": False
    }
    
    create_response = session.post(f"{BACKEND_URL}/games/rooms/create", json=room_data)
    print(f"Create Room Status: {create_response.status_code}")
    print(f"Create Room Response: {create_response.text}")
    
    if create_response.status_code == 200:
        room = create_response.json()
        room_id = room.get("room_id")
        print(f"Created room: {room_id}")
        
        # Try to join the room (should fail)
        join_response = session.post(f"{BACKEND_URL}/games/rooms/{room_id}/join")
        print(f"Join Room Status: {join_response.status_code}")
        print(f"Join Room Response: {join_response.text}")
        
        # Try to start the game
        start_response = session.post(f"{BACKEND_URL}/games/rooms/{room_id}/start")
        print(f"Start Game Status: {start_response.status_code}")
        print(f"Start Game Response: {start_response.text}")
        
        # Check room details
        rooms_response = session.get(f"{BACKEND_URL}/games/rooms")
        if rooms_response.status_code == 200:
            rooms = rooms_response.json()
            debug_room = next((r for r in rooms if r.get("room_id") == room_id), None)
            if debug_room:
                print(f"Room details: {json.dumps(debug_room, indent=2)}")
else:
    print(f"Login failed: {response.text}")