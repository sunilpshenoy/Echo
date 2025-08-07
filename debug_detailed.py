#!/usr/bin/env python3
"""
Debug games system with detailed error checking
"""

import requests
import json
import traceback

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
    
    # Create a room with just 1 player (should be able to start with AI or fail gracefully)
    room_data = {
        "name": "Single Player Debug Room",
        "gameType": "tic-tac-toe",
        "maxPlayers": 2,
        "isPrivate": False
    }
    
    create_response = session.post(f"{BACKEND_URL}/games/rooms/create", json=room_data)
    print(f"Create Room Status: {create_response.status_code}")
    
    if create_response.status_code == 200:
        room = create_response.json()
        room_id = room.get("room_id")
        print(f"Created room: {room_id}")
        print(f"Room has {len(room.get('players', []))} players")
        
        # Try to start the game with just 1 player
        print("\nTrying to start game with 1 player...")
        start_response = session.post(f"{BACKEND_URL}/games/rooms/{room_id}/start")
        print(f"Start Game Status: {start_response.status_code}")
        print(f"Start Game Response: {start_response.text}")
        
        # Now let's try to create a second user and join the room
        print("\n--- Creating second user ---")
        register_data2 = {
            "username": "games_test_user2",
            "email": "games_test_user2@example.com",
            "password": "TestPassword123!",
            "display_name": "Games Test User 2"
        }
        
        session2 = requests.Session()
        reg_response = session2.post(f"{BACKEND_URL}/register", json=register_data2)
        print(f"Register User 2 Status: {reg_response.status_code}")
        
        if reg_response.status_code in [200, 201] or "already exists" in reg_response.text.lower():
            # Login user 2
            login_data2 = {
                "email": "games_test_user2@example.com",
                "password": "TestPassword123!"
            }
            
            login_response2 = session2.post(f"{BACKEND_URL}/login", json=login_data2)
            if login_response2.status_code == 200:
                data2 = login_response2.json()
                token2 = data2.get("access_token")
                user_data2 = data2.get("user", {})
                user_id2 = user_data2.get("user_id")
                
                session2.headers.update({"Authorization": f"Bearer {token2}"})
                print(f"User 2 logged in as: {user_id2}")
                
                # User 2 joins the room
                join_response = session2.post(f"{BACKEND_URL}/games/rooms/{room_id}/join")
                print(f"User 2 Join Room Status: {join_response.status_code}")
                print(f"User 2 Join Room Response: {join_response.text}")
                
                if join_response.status_code == 200:
                    # Now try to start the game with 2 players
                    print("\nTrying to start game with 2 players...")
                    start_response2 = session.post(f"{BACKEND_URL}/games/rooms/{room_id}/start")
                    print(f"Start Game Status: {start_response2.status_code}")
                    print(f"Start Game Response: {start_response2.text}")
                    
                    # Check final room state
                    rooms_response = session.get(f"{BACKEND_URL}/games/rooms")
                    if rooms_response.status_code == 200:
                        rooms = rooms_response.json()
                        debug_room = next((r for r in rooms if r.get("room_id") == room_id), None)
                        if debug_room:
                            print(f"\nFinal room state:")
                            print(f"  Players: {len(debug_room.get('players', []))}")
                            print(f"  Status: {debug_room.get('status')}")
                            print(f"  Game State: {debug_room.get('game_state', {})}")
else:
    print(f"Login failed: {response.text}")