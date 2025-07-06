import requests
import json
import time
import websocket
import threading
import uuid
import os
import logging
from dotenv import load_dotenv

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
        "username": "caller_user",
        "email": "caller@example.com",
        "password": "SecurePass123!",
        "phone": "+1234567890"
    },
    {
        "username": "callee_user",
        "email": "callee@example.com",
        "password": "StrongPass456!",
        "phone": "+1987654321"
    },
    {
        "username": "unauthorized_user",
        "email": "unauthorized@example.com",
        "password": "SafePass789!",
        "phone": "+1122334455"
    }
]

# Global variables to store test data
user_tokens = {}
user_ids = {}
chat_ids = {}
call_ids = {}
ws_connections = {}
ws_messages = []

def on_ws_message(ws, message):
    """Callback for WebSocket messages"""
    logger.info(f"WebSocket message received: {message}")
    ws_messages.append(json.loads(message))

def on_ws_error(ws, error):
    """Callback for WebSocket errors"""
    logger.error(f"WebSocket error: {error}")

def on_ws_close(ws, close_status_code, close_msg):
    """Callback for WebSocket connection close"""
    logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")

def on_ws_open(ws):
    """Callback for WebSocket connection open"""
    logger.info("WebSocket connection opened")

def connect_websocket(user_id, token):
    """Connect to WebSocket and return the connection"""
    ws_url = f"{BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://')}/api/ws/{user_id}"
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_ws_message,
        on_error=on_ws_error,
        on_close=on_ws_close,
        on_open=on_ws_open,
        header={"Authorization": f"Bearer {token}"}
    )
    
    # Start WebSocket connection in a separate thread
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()
    
    # Wait for connection to establish
    time.sleep(2)
    return ws

def register_or_login_users():
    """Register or login test users"""
    logger.info("Registering or logging in test users...")
    
    for i, user_data in enumerate(test_users):
        # Try to register the user
        response = requests.post(f"{API_URL}/register", json=user_data)
        
        if response.status_code == 200:
            logger.info(f"User {user_data['username']} registered successfully")
            user_tokens[f"user{i+1}"] = response.json()["access_token"]
            user_ids[f"user{i+1}"] = response.json()["user"]["user_id"]
        elif response.status_code == 400 and "Email already registered" in response.json()["detail"]:
            # User already exists, try logging in
            logger.info(f"User {user_data['username']} already exists, logging in...")
            login_response = requests.post(f"{API_URL}/login", json={
                "email": user_data["email"],
                "password": user_data["password"]
            })
            
            if login_response.status_code == 200:
                logger.info(f"User {user_data['username']} logged in successfully")
                user_tokens[f"user{i+1}"] = login_response.json()["access_token"]
                user_ids[f"user{i+1}"] = login_response.json()["user"]["user_id"]
            else:
                logger.error(f"Failed to log in user {user_data['username']}: {login_response.text}")
                return False
        else:
            logger.error(f"Failed to register user {user_data['username']}: {response.text}")
            return False
    
    logger.info("All users registered or logged in successfully")
    return True

def setup_websocket_connections():
    """Set up WebSocket connections for all users"""
    logger.info("Setting up WebSocket connections...")
    
    for user_key, user_id in user_ids.items():
        token = user_tokens[user_key]
        try:
            ws = connect_websocket(user_id, token)
            ws_connections[user_key] = ws
            logger.info(f"WebSocket connection established for {user_key}")
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection for {user_key}: {e}")
            return False
    
    logger.info("WebSocket connections established for all users")
    return True

def create_direct_chat():
    """Create a direct chat between user1 (caller) and user2 (callee)"""
    logger.info("Creating direct chat between caller and callee...")
    
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
    return True

def test_call_initiation():
    """Test call initiation for both voice and video calls"""
    logger.info("Testing call initiation...")
    
    # Test voice call initiation
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    call_data = {
        "chat_id": chat_ids['direct_chat'],
        "call_type": "voice"
    }
    
    response = requests.post(f"{API_URL}/calls/initiate", json=call_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to initiate voice call: {response.text}")
        return False
    
    call_ids['voice_call'] = response.json()["call_id"]
    logger.info(f"Voice call initiated with ID: {call_ids['voice_call']}")
    
    # Verify call data
    if response.json().get("call_type") != "voice" or response.json().get("status") != "ringing":
        logger.error(f"Voice call has incorrect type or status: {response.json()}")
        return False
    
    # Verify participants include both users
    if not all(user_id in response.json().get("participants", []) for user_id in [user_ids['user1'], user_ids['user2']]):
        logger.error(f"Voice call participants incorrect: {response.json().get('participants')}")
        return False
    
    # Wait for WebSocket notifications
    time.sleep(2)
    
    # Check if callee received incoming call notification
    incoming_call_messages = [msg for msg in ws_messages if msg.get("type") == "incoming_call"]
    if not incoming_call_messages:
        logger.warning("No incoming call WebSocket notification received")
    else:
        logger.info(f"Received incoming call notification via WebSocket")
        # Verify notification data
        call_data = incoming_call_messages[0].get("data", {})
        if call_data.get("call_id") != call_ids['voice_call']:
            logger.error(f"Incoming call notification has incorrect call_id: {call_data}")
            return False
    
    # Clear WebSocket messages for next test
    ws_messages.clear()
    
    # Test video call initiation
    call_data = {
        "chat_id": chat_ids['direct_chat'],
        "call_type": "video"
    }
    
    response = requests.post(f"{API_URL}/calls/initiate", json=call_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to initiate video call: {response.text}")
        return False
    
    call_ids['video_call'] = response.json()["call_id"]
    logger.info(f"Video call initiated with ID: {call_ids['video_call']}")
    
    # Verify call data
    if response.json().get("call_type") != "video" or response.json().get("status") != "ringing":
        logger.error(f"Video call has incorrect type or status: {response.json()}")
        return False
    
    # Wait for WebSocket notifications
    time.sleep(2)
    
    # Check if callee received incoming call notification
    incoming_call_messages = [msg for msg in ws_messages if msg.get("type") == "incoming_call"]
    if not incoming_call_messages:
        logger.warning("No incoming call WebSocket notification received for video call")
    else:
        logger.info(f"Received incoming call notification via WebSocket for video call")
    
    logger.info("Call initiation tests passed")
    return True

def test_call_response():
    """Test responding to calls (accept/decline)"""
    logger.info("Testing call response...")
    
    # Test accepting a call
    headers = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response_data = {
        "action": "accept"
    }
    
    response = requests.put(
        f"{API_URL}/calls/{call_ids['voice_call']}/respond",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept call: {response.text}")
        return False
    
    if response.json().get("status") != "accepted":
        logger.error(f"Call accept response has incorrect status: {response.json()}")
        return False
    
    logger.info("Successfully accepted voice call")
    
    # Wait for WebSocket notifications
    time.sleep(2)
    
    # Check if caller received call accepted notification
    call_accepted_messages = [msg for msg in ws_messages if msg.get("type") == "call_accepted"]
    if not call_accepted_messages:
        logger.warning("No call accepted WebSocket notification received")
    else:
        logger.info(f"Received call accepted notification via WebSocket")
    
    # Clear WebSocket messages for next test
    ws_messages.clear()
    
    # Test declining a call
    response_data = {
        "action": "decline"
    }
    
    response = requests.put(
        f"{API_URL}/calls/{call_ids['video_call']}/respond",
        json=response_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to decline call: {response.text}")
        return False
    
    if response.json().get("status") != "declined":
        logger.error(f"Call decline response has incorrect status: {response.json()}")
        return False
    
    logger.info("Successfully declined video call")
    
    # Wait for WebSocket notifications
    time.sleep(2)
    
    # Check if caller received call declined notification
    call_declined_messages = [msg for msg in ws_messages if msg.get("type") == "call_declined"]
    if not call_declined_messages:
        logger.warning("No call declined WebSocket notification received")
    else:
        logger.info(f"Received call declined notification via WebSocket")
    
    logger.info("Call response tests passed")
    return True

def test_call_management():
    """Test call management (ending calls)"""
    logger.info("Testing call management...")
    
    # Initiate a new call for testing end functionality
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    call_data = {
        "chat_id": chat_ids['direct_chat'],
        "call_type": "voice"
    }
    
    response = requests.post(f"{API_URL}/calls/initiate", json=call_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to initiate call for end test: {response.text}")
        return False
    
    test_call_id = response.json()["call_id"]
    logger.info(f"Call initiated for end test with ID: {test_call_id}")
    
    # Accept the call as user2
    headers2 = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.put(
        f"{API_URL}/calls/{test_call_id}/respond",
        json={"action": "accept"},
        headers=headers2
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept call for end test: {response.text}")
        return False
    
    logger.info("Call accepted for end test")
    
    # Wait a moment to simulate call duration
    time.sleep(2)
    
    # End the call
    response = requests.put(f"{API_URL}/calls/{test_call_id}/end", headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to end call: {response.text}")
        return False
    
    if response.json().get("status") != "ended":
        logger.error(f"Call end response has incorrect status: {response.json()}")
        return False
    
    # Verify duration is calculated
    if "duration" not in response.json():
        logger.error(f"Call end response missing duration: {response.json()}")
        return False
    
    logger.info(f"Successfully ended call with duration: {response.json()['duration']} seconds")
    
    # Wait for WebSocket notifications
    time.sleep(2)
    
    # Check if callee received call ended notification
    call_ended_messages = [msg for msg in ws_messages if msg.get("type") == "call_ended"]
    if not call_ended_messages:
        logger.warning("No call ended WebSocket notification received")
    else:
        logger.info(f"Received call ended notification via WebSocket")
    
    logger.info("Call management tests passed")
    return True

def test_webrtc_signaling():
    """Test WebRTC signaling (offer, answer, ICE candidates)"""
    logger.info("Testing WebRTC signaling...")
    
    # Initiate a new call for testing WebRTC
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    call_data = {
        "chat_id": chat_ids['direct_chat'],
        "call_type": "video"
    }
    
    response = requests.post(f"{API_URL}/calls/initiate", json=call_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to initiate call for WebRTC test: {response.text}")
        return False
    
    webrtc_call_id = response.json()["call_id"]
    logger.info(f"Call initiated for WebRTC test with ID: {webrtc_call_id}")
    
    # Accept the call as user2
    headers2 = {"Authorization": f"Bearer {user_tokens['user2']}"}
    response = requests.put(
        f"{API_URL}/calls/{webrtc_call_id}/respond",
        json={"action": "accept"},
        headers=headers2
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to accept call for WebRTC test: {response.text}")
        return False
    
    # Clear WebSocket messages
    ws_messages.clear()
    
    # Test sending WebRTC offer
    offer_data = {
        "offer": {
            "type": "offer",
            "sdp": "v=0\r\no=- 1234567890 1 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=group:BUNDLE 0\r\na=extmap-allow-mixed\r\na=msid-semantic: WMS\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\nc=IN IP4 0.0.0.0\r\na=rtcp:9 IN IP4 0.0.0.0\r\na=ice-ufrag:test\r\na=ice-pwd:test123\r\na=fingerprint:sha-256 00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00\r\na=setup:actpass\r\na=mid:0\r\na=sendrecv\r\na=rtcp-mux\r\na=rtcp-rsize\r\na=rtpmap:96 VP8/90000\r\na=ssrc:1234567890 cname:test\r\n"
        },
        "ice_candidates": [
            {
                "candidate": "candidate:1 1 UDP 2122252543 192.168.1.100 12345 typ host",
                "sdpMid": "0",
                "sdpMLineIndex": 0
            }
        ]
    }
    
    response = requests.post(
        f"{API_URL}/calls/{webrtc_call_id}/webrtc/offer",
        json=offer_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send WebRTC offer: {response.text}")
        return False
    
    logger.info("Successfully sent WebRTC offer")
    
    # Wait for WebSocket notifications
    time.sleep(2)
    
    # Check if callee received WebRTC offer
    webrtc_offer_messages = [msg for msg in ws_messages if msg.get("type") == "webrtc_offer"]
    if not webrtc_offer_messages:
        logger.warning("No WebRTC offer notification received")
    else:
        logger.info(f"Received WebRTC offer notification via WebSocket")
    
    # Clear WebSocket messages
    ws_messages.clear()
    
    # Test sending WebRTC answer
    answer_data = {
        "answer": {
            "type": "answer",
            "sdp": "v=0\r\no=- 9876543210 1 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=group:BUNDLE 0\r\na=extmap-allow-mixed\r\na=msid-semantic: WMS\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\nc=IN IP4 0.0.0.0\r\na=rtcp:9 IN IP4 0.0.0.0\r\na=ice-ufrag:resp\r\na=ice-pwd:resp123\r\na=fingerprint:sha-256 00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00\r\na=setup:active\r\na=mid:0\r\na=sendrecv\r\na=rtcp-mux\r\na=rtcp-rsize\r\na=rtpmap:96 VP8/90000\r\na=ssrc:9876543210 cname:resp\r\n"
        },
        "ice_candidates": [
            {
                "candidate": "candidate:1 1 UDP 2122252543 192.168.1.200 54321 typ host",
                "sdpMid": "0",
                "sdpMLineIndex": 0
            }
        ]
    }
    
    response = requests.post(
        f"{API_URL}/calls/{webrtc_call_id}/webrtc/answer",
        json=answer_data,
        headers=headers2
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send WebRTC answer: {response.text}")
        return False
    
    logger.info("Successfully sent WebRTC answer")
    
    # Wait for WebSocket notifications
    time.sleep(2)
    
    # Check if caller received WebRTC answer
    webrtc_answer_messages = [msg for msg in ws_messages if msg.get("type") == "webrtc_answer"]
    if not webrtc_answer_messages:
        logger.warning("No WebRTC answer notification received")
    else:
        logger.info(f"Received WebRTC answer notification via WebSocket")
    
    # Clear WebSocket messages
    ws_messages.clear()
    
    # Test sending ICE candidate
    ice_data = {
        "candidate": {
            "candidate": "candidate:2 1 UDP 1845501695 203.0.113.100 56789 typ srflx raddr 192.168.1.100 rport 12345",
            "sdpMid": "0",
            "sdpMLineIndex": 0
        }
    }
    
    response = requests.post(
        f"{API_URL}/calls/{webrtc_call_id}/webrtc/ice",
        json=ice_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to send ICE candidate: {response.text}")
        return False
    
    logger.info("Successfully sent ICE candidate")
    
    # Wait for WebSocket notifications
    time.sleep(2)
    
    # Check if callee received ICE candidate
    webrtc_ice_messages = [msg for msg in ws_messages if msg.get("type") == "webrtc_ice"]
    if not webrtc_ice_messages:
        logger.warning("No WebRTC ICE notification received")
    else:
        logger.info(f"Received WebRTC ICE notification via WebSocket")
    
    # End the call
    response = requests.put(f"{API_URL}/calls/{webrtc_call_id}/end", headers=headers)
    
    logger.info("WebRTC signaling tests passed")
    return True

def test_access_control():
    """Test access control for call endpoints"""
    logger.info("Testing access control...")
    
    # Initiate a new call for testing access control
    headers = {"Authorization": f"Bearer {user_tokens['user1']}"}
    call_data = {
        "chat_id": chat_ids['direct_chat'],
        "call_type": "voice"
    }
    
    response = requests.post(f"{API_URL}/calls/initiate", json=call_data, headers=headers)
    
    if response.status_code != 200:
        logger.error(f"Failed to initiate call for access control test: {response.text}")
        return False
    
    access_call_id = response.json()["call_id"]
    logger.info(f"Call initiated for access control test with ID: {access_call_id}")
    
    # Test unauthorized user trying to respond to call
    headers3 = {"Authorization": f"Bearer {user_tokens['user3']}"}
    response = requests.put(
        f"{API_URL}/calls/{access_call_id}/respond",
        json={"action": "accept"},
        headers=headers3
    )
    
    if response.status_code != 403:
        logger.error(f"Unauthorized user was able to respond to call: {response.status_code} - {response.text}")
        return False
    
    logger.info("Successfully prevented unauthorized user from responding to call")
    
    # Test unauthorized user trying to end call
    response = requests.put(f"{API_URL}/calls/{access_call_id}/end", headers=headers3)
    
    if response.status_code != 403:
        logger.error(f"Unauthorized user was able to end call: {response.status_code} - {response.text}")
        return False
    
    logger.info("Successfully prevented unauthorized user from ending call")
    
    # Test unauthorized user trying to send WebRTC offer
    offer_data = {
        "offer": {
            "type": "offer",
            "sdp": "v=0\r\no=- 1234567890 1 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\n"
        }
    }
    
    response = requests.post(
        f"{API_URL}/calls/{access_call_id}/webrtc/offer",
        json=offer_data,
        headers=headers3
    )
    
    if response.status_code != 403:
        logger.error(f"Unauthorized user was able to send WebRTC offer: {response.status_code} - {response.text}")
        return False
    
    logger.info("Successfully prevented unauthorized user from sending WebRTC offer")
    
    # Test with invalid call ID
    invalid_call_id = str(uuid.uuid4())
    response = requests.put(
        f"{API_URL}/calls/{invalid_call_id}/respond",
        json={"action": "accept"},
        headers=headers
    )
    
    if response.status_code != 404:
        logger.error(f"Invalid call ID test failed: {response.status_code} - {response.text}")
        return False
    
    logger.info("Successfully handled invalid call ID")
    
    # End the test call
    response = requests.put(f"{API_URL}/calls/{access_call_id}/end", headers=headers)
    
    logger.info("Access control tests passed")
    return True

def run_tests():
    """Run all tests"""
    logger.info("Starting Voice/Video Call API tests...")
    
    # Setup
    if not register_or_login_users():
        return False
    
    if not setup_websocket_connections():
        return False
    
    if not create_direct_chat():
        return False
    
    # Tests
    test_results = {
        "call_initiation": test_call_initiation(),
        "call_response": test_call_response(),
        "call_management": test_call_management(),
        "webrtc_signaling": test_webrtc_signaling(),
        "access_control": test_access_control()
    }
    
    # Close WebSocket connections
    for user_key, ws in ws_connections.items():
        try:
            ws.close()
            logger.info(f"Closed WebSocket connection for {user_key}")
        except:
            pass
    
    # Print summary
    logger.info("\n=== TEST RESULTS SUMMARY ===")
    all_passed = True
    for test_name, result in test_results.items():
        logger.info(f"{test_name}: {'PASSED' if result else 'FAILED'}")
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n✅ ALL TESTS PASSED")
    else:
        logger.info("\n❌ SOME TESTS FAILED")
    
    return all_passed

if __name__ == "__main__":
    run_tests()