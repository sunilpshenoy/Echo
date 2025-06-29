#!/usr/bin/env python3
"""
Script to create test users for contact testing
"""
import requests
import json
import os

# Get backend URL from environment
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1].strip('"\'')
            break

API_URL = f"{BACKEND_URL}/api"

# First, register a temporary user to get a valid token
temp_user = {
    "username": "temp_user_for_creation",
    "email": "temp@example.com", 
    "password": "TempPassword123!",
    "phone": "+1234567999"
}

print("Creating temporary user to get authentication token...")
response = requests.post(f"{API_URL}/register", json=temp_user)

if response.status_code == 200:
    token = response.json()["access_token"]
    print("✅ Got authentication token")
    
    # Now create test users
    print("\nCreating test users...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_URL}/contacts/create-test-users", headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['message']}")
        print("\n🎉 Test users created successfully!")
        print("\n📧 You can now add these contacts by email:")
        for user in result['created_users']:
            print(f"   • {user['display_name']}: {user['email']}")
            print(f"     PIN: {user['connection_pin']}")
        print(f"\n📱 Instructions: {result['instructions']}")
    else:
        print(f"❌ Failed to create test users: {response.text}")
else:
    print(f"❌ Failed to create temp user: {response.text}")