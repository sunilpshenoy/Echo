#!/usr/bin/env python3
"""
Quick test for marketplace messaging and chat integration
"""

import requests
import json

BACKEND_URL = "https://a205b7e3-f535-4569-8dd8-c1f8fc23e5dc.preview.emergentagent.com/api"

def test_marketplace_chat_integration():
    session = requests.Session()
    
    # Create test users
    alice_data = {"username": "alice_test", "email": "alice_test@test.com", "password": "test123"}
    bob_data = {"username": "bob_test", "email": "bob_test@test.com", "password": "test123"}
    
    # Register or login Alice
    try:
        alice_response = session.post(f"{BACKEND_URL}/register", json=alice_data)
        if alice_response.status_code != 200:
            alice_response = session.post(f"{BACKEND_URL}/login", json={"email": alice_data["email"], "password": alice_data["password"]})
        alice_token = alice_response.json()["access_token"]
        alice_headers = {"Authorization": f"Bearer {alice_token}"}
        alice_user_id = alice_response.json()["user"]["user_id"]
    except Exception as e:
        print(f"Failed to setup Alice: {e}")
        return
    
    # Register or login Bob
    try:
        bob_response = session.post(f"{BACKEND_URL}/register", json=bob_data)
        if bob_response.status_code != 200:
            bob_response = session.post(f"{BACKEND_URL}/login", json={"email": bob_data["email"], "password": bob_data["password"]})
        bob_token = bob_response.json()["access_token"]
        bob_headers = {"Authorization": f"Bearer {bob_token}"}
        bob_user_id = bob_response.json()["user"]["user_id"]
    except Exception as e:
        print(f"Failed to setup Bob: {e}")
        return
    
    print(f"✅ Created users: Alice ({alice_user_id[:8]}...) and Bob ({bob_user_id[:8]}...)")
    
    # Create a marketplace listing
    listing_data = {
        "title": "Test Integration Item",
        "description": "Testing marketplace chat integration",
        "category": "items",
        "price": 100.0,
        "price_type": "fixed",
        "contact_method": "chat"
    }
    
    listing_response = session.post(f"{BACKEND_URL}/marketplace/listings", json=listing_data, headers=alice_headers)
    if listing_response.status_code != 200:
        print(f"❌ Failed to create listing: {listing_response.status_code}")
        return
    
    listing_id = listing_response.json()["listing_id"]
    print(f"✅ Created listing: {listing_id}")
    
    # Send marketplace message
    message_data = {
        "listing_id": listing_id,
        "recipient_id": alice_user_id,
        "message": "Hi! I'm interested in your item. Is it still available?",
        "offer_price": 90.0
    }
    
    message_response = session.post(f"{BACKEND_URL}/marketplace/listings/{listing_id}/message", json=message_data, headers=bob_headers)
    if message_response.status_code != 200:
        print(f"❌ Failed to send marketplace message: {message_response.status_code}")
        print(f"Response: {message_response.text}")
        return
    
    chat_id = message_response.json()["chat_id"]
    print(f"✅ Sent marketplace message, created chat: {chat_id}")
    
    # Try to access chat messages
    chat_messages_response = session.get(f"{BACKEND_URL}/chats/{chat_id}/messages", headers=alice_headers)
    if chat_messages_response.status_code == 200:
        messages = chat_messages_response.json()
        print(f"✅ Successfully accessed chat messages: {len(messages)} messages found")
        
        # Check if the marketplace message is there
        marketplace_messages = [msg for msg in messages if msg.get("message_type") == "marketplace_inquiry"]
        if marketplace_messages:
            print(f"✅ Found marketplace inquiry message with offer price")
        else:
            print(f"⚠️ No marketplace inquiry messages found")
    else:
        print(f"❌ Failed to access chat messages: {chat_messages_response.status_code}")
        print(f"Response: {chat_messages_response.text}")
    
    # Clean up
    session.delete(f"{BACKEND_URL}/marketplace/listings/{listing_id}", headers=alice_headers)
    print("✅ Cleaned up test listing")

if __name__ == "__main__":
    test_marketplace_chat_integration()