#!/usr/bin/env python3
"""
Debug authentication issue
"""

import requests
import json

BACKEND_URL = "https://9b83238d-a27b-406f-8157-e448fada6ab0.preview.emergentagent.com/api"

# Test login
login_data = {
    "email": "games_backend_test@example.com",
    "password": "TestPassword123!"
}

session = requests.Session()
response = session.post(f"{BACKEND_URL}/login", json=login_data)

print(f"Login Status: {response.status_code}")
print(f"Login Response: {response.text}")

if response.status_code == 200:
    data = response.json()
    print(f"Access Token: {data.get('access_token', 'NOT FOUND')}")
    print(f"User ID: {data.get('user_id', 'NOT FOUND')}")
    
    # Test with token
    token = data.get("access_token")
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Test getting current user
        me_response = session.get(f"{BACKEND_URL}/users/me")
        print(f"\nGet Me Status: {me_response.status_code}")
        print(f"Get Me Response: {me_response.text}")