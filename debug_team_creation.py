#!/usr/bin/env python3
"""
Debug Team Creation Issue
"""

import asyncio
import aiohttp
import json
import time

# Backend URL from environment
BACKEND_URL = "https://d2ce893b-8b01-49a3-8aed-a13ce7bbac25.preview.emergentagent.com/api"

async def debug_team_creation():
    """Debug team creation issue"""
    
    async with aiohttp.ClientSession() as session:
        # Register user
        test_email = f"debug_user_{int(time.time())}@test.com"
        register_data = {
            "username": f"debuguser_{int(time.time())}",
            "email": test_email,
            "password": "TestPassword123!",
            "display_name": "Debug User"
        }
        
        async with session.post(f"{BACKEND_URL}/register", json=register_data) as response:
            if response.status == 200:
                data = await response.json()
                auth_token = data['access_token']
                user_id = data['user']['user_id']
                print(f"✅ User registered: {user_id}")
            else:
                print(f"❌ Registration failed: {await response.text()}")
                return
        
        # Create team with minimal data
        headers = {'Authorization': f'Bearer {auth_token}'}
        team_data = {
            "name": f"Debug Team {int(time.time())}"
        }
        
        print(f"📤 Sending team creation request: {team_data}")
        
        async with session.post(f"{BACKEND_URL}/teams", json=team_data, headers=headers) as response:
            print(f"📥 Response status: {response.status}")
            print(f"📥 Response headers: {dict(response.headers)}")
            
            response_text = await response.text()
            print(f"📥 Raw response: {response_text}")
            
            try:
                response_json = json.loads(response_text)
                print(f"📥 Parsed JSON: {response_json}")
            except:
                print(f"❌ Failed to parse JSON")
                
        # Test team retrieval
        async with session.get(f"{BACKEND_URL}/teams", headers=headers) as response:
            print(f"📋 Teams list status: {response.status}")
            teams_data = await response.json()
            print(f"📋 Teams data: {teams_data}")

if __name__ == "__main__":
    asyncio.run(debug_team_creation())