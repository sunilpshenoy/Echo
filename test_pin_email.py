#!/usr/bin/env python3
"""
Quick test to verify PIN and email contact issues
"""
import requests
import json

# Backend URL
API_URL = "http://localhost:8001/api"

# Test user credentials
test_user = {
    "username": "pin_test_user",
    "email": "pin_test@example.com", 
    "password": "TestPassword123!",
    "phone": "+1234567000"
}

print("1. Registering test user...")
response = requests.post(f"{API_URL}/register", json=test_user)

if response.status_code == 200:
    token = response.json()["access_token"]
    print("✅ Test user registered successfully")
else:
    # Try to login if user already exists
    response = requests.post(f"{API_URL}/login", json={
        "email": test_user["email"],
        "password": test_user["password"]
    })
    if response.status_code == 200:
        token = response.json()["access_token"]
        print("✅ Test user logged in successfully")
    else:
        print(f"❌ Failed to register/login: {response.text}")
        exit(1)

headers = {"Authorization": f"Bearer {token}"}

print("\n2. Testing PIN connection with PIN-ALI001...")
pin_data = {"target_pin": "PIN-ALI001", "message": "Test connection request"}
response = requests.post(f"{API_URL}/connections/request-by-pin", json=pin_data, headers=headers)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("✅ PIN-ALI001 connection request sent successfully")
elif response.status_code == 400 and "already" in response.text.lower():
    print("✅ PIN-ALI001 found (already connected/requested)")
elif response.status_code == 404:
    print("❌ PIN-ALI001 not found - test user doesn't exist")
else:
    print(f"❌ Unexpected response: {response.status_code}")

print("\n3. Testing email contact addition with alice@test.com...")
contact_data = {"email": "alice@test.com"}
response = requests.post(f"{API_URL}/contacts", json=contact_data, headers=headers)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("✅ alice@test.com added as contact successfully")
elif response.status_code == 400 and "already exists" in response.text.lower():
    print("✅ alice@test.com already exists as contact")
elif response.status_code == 404:
    print("❌ alice@test.com not found - test user doesn't exist")
else:
    print(f"❌ Unexpected response: {response.status_code}")

print("\n4. Testing chat list to check display names...")
response = requests.get(f"{API_URL}/chats", headers=headers)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    chats = response.json()
    print(f"Found {len(chats)} chats:")
    for chat in chats:
        if chat.get("other_user"):
            print(f"  • {chat['other_user'].get('display_name', 'NO DISPLAY NAME')} ({chat['other_user'].get('email', 'NO EMAIL')})")
        else:
            print(f"  • NO OTHER_USER DATA: {chat}")
else:
    print(f"Failed to get chats: {response.text}")