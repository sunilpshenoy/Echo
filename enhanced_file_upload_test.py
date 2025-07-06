import requests
import json
import base64
import os
import logging
from io import BytesIO
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

# Test user credentials
test_user = {
    "username": "file_upload_test_user",
    "email": "file_upload_test@example.com",
    "password": "FileUploadTest123!"
}

# Global variables
user_token = None
user_id = None

def register_or_login_user():
    """Register a test user or login if already exists"""
    global user_token, user_id
    
    # Try to register the user
    response = requests.post(f"{API_URL}/register", json=test_user)
    
    if response.status_code == 200:
        logger.info(f"User {test_user['username']} registered successfully")
        user_token = response.json()["access_token"]
        user_id = response.json()["user"]["user_id"]
    elif response.status_code == 400 and "Email already registered" in response.json()["detail"]:
        # User already exists, try logging in
        logger.info(f"User {test_user['username']} already exists, logging in...")
        login_response = requests.post(f"{API_URL}/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        
        if login_response.status_code == 200:
            logger.info(f"User {test_user['username']} logged in successfully")
            user_token = login_response.json()["access_token"]
            user_id = login_response.json()["user"]["user_id"]
        else:
            logger.error(f"Failed to log in user {test_user['username']}: {login_response.text}")
            return False
    else:
        logger.error(f"Failed to register user {test_user['username']}: {response.text}")
        return False
    
    return True

def test_file_upload_endpoint():
    """Test the enhanced file upload endpoint with all required fields"""
    logger.info("Testing enhanced file upload endpoint...")
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # Test cases for different file types
    test_cases = [
        {
            "name": "image.png",
            "content": base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="),
            "content_type": "image/png",
            "expected_status": 200,
            "expected_category": "Image",
            "expected_icon": "🖼️"
        },
        {
            "name": "document.pdf",
            "content": b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF",
            "content_type": "application/pdf",
            "expected_status": 200,
            "expected_category": "Document",
            "expected_icon": "📄"
        },
        {
            "name": "audio.mp3",
            "content": b"ID3\x03\x00\x00\x00\x00\x0f\x76TALB\x00\x00\x00\x0f\x00\x00\x03Test Album",
            "content_type": "audio/mpeg",
            "expected_status": 200,
            "expected_category": "Audio",
            "expected_icon": "🎵"
        },
        {
            "name": "video.mp4",
            "content": b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42mp41\x00\x00\x00\x01moov",
            "content_type": "video/mp4",
            "expected_status": 200,
            "expected_category": "Video",
            "expected_icon": "🎬"
        },
        {
            "name": "archive.zip",
            "content": b"PK\x03\x04\x14\x00\x00\x00\x08\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00test.txtPK\x01\x02\x14\x00\x14\x00\x00\x00\x08\x00\x00\x00!\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00test.txtPK\x05\x06\x00\x00\x00\x00\x01\x00\x01\x00.\x00\x00\x00\x1c\x00\x00\x00\x00\x00",
            "content_type": "application/zip",
            "expected_status": 200,
            "expected_category": "Archive",
            "expected_icon": "📦"
        },
        {
            "name": "executable.exe",
            "content": b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00\xb8\x00\x00\x00\x00\x00\x00\x00",
            "content_type": "application/octet-stream",
            "expected_status": 400,
            "expected_error": "File type 'application/octet-stream' not supported"
        }
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        logger.info(f"Testing upload of {test_case['name']} ({test_case['content_type']})")
        
        files = {"file": (test_case["name"], BytesIO(test_case["content"]), test_case["content_type"])}
        
        response = requests.post(f"{API_URL}/upload", headers=headers, files=files)
        
        if response.status_code != test_case["expected_status"]:
            logger.error(f"Unexpected status code: {response.status_code}, expected: {test_case['expected_status']}")
            logger.error(f"Response: {response.text}")
            continue
        
        if test_case["expected_status"] == 200:
            result = response.json()
            
            # Check for required fields
            required_fields = ["file_id", "file_name", "file_size", "file_type", "file_data", "category", "icon"]
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                logger.error(f"Response missing required fields: {missing_fields}")
                logger.error(f"Response: {result}")
                continue
            
            # Check category and icon
            if result["category"] != test_case["expected_category"]:
                logger.error(f"Unexpected category: {result['category']}, expected: {test_case['expected_category']}")
                continue
                
            if result["icon"] != test_case["expected_icon"]:
                logger.error(f"Unexpected icon: {result['icon']}, expected: {test_case['expected_icon']}")
                continue
            
            logger.info(f"Successfully uploaded {test_case['name']} ({result['file_size']} bytes)")
            logger.info(f"Category: {result['category']}, Icon: {result['icon']}")
            success_count += 1
        else:
            # Check error message for rejected files
            if test_case["expected_error"] not in response.json()["detail"]:
                logger.error(f"Unexpected error message: {response.json()['detail']}")
                logger.error(f"Expected to contain: {test_case['expected_error']}")
                continue
            
            logger.info(f"Correctly rejected {test_case['name']} with error: {response.json()['detail']}")
            success_count += 1
    
    logger.info(f"Enhanced file upload endpoint test completed: {success_count}/{len(test_cases)} test cases passed")
    return success_count == len(test_cases)

def run_tests():
    """Run all tests"""
    logger.info("Starting Enhanced File Upload tests...")
    
    # Setup
    if not register_or_login_user():
        logger.error("Failed to setup test user")
        return False
    
    # Run tests
    tests = [
        ("Enhanced File Upload", test_file_upload_endpoint),
    ]
    
    results = {}
    all_passed = True
    
    for test_name, test_func in tests:
        logger.info(f"\n{'=' * 80}\nRunning test: {test_name}\n{'=' * 80}")
        try:
            result = test_func()
            results[test_name] = result
            if not result:
                all_passed = False
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
            all_passed = False
    
    # Print summary
    logger.info("\n\n" + "=" * 80)
    logger.info("ENHANCED FILE UPLOAD TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 80)
    logger.info(f"OVERALL RESULT: {'PASSED' if all_passed else 'FAILED'}")
    logger.info("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    if success:
        logger.info("All Enhanced File Upload tests passed!")
    else:
        logger.error("Some Enhanced File Upload tests failed!")