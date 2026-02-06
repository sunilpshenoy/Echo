"""
Pulse Backend - Photo System Tests
Comprehensive tests for photo upload, moderation, storage, and avatars
"""

import pytest
import asyncio
import os
from io import BytesIO
from PIL import Image
from unittest.mock import Mock, patch, MagicMock

from services.photo_service import PhotoService, PhotoType, ModerationStatus


# ==========================================
# TEST FIXTURES
# ==========================================

@pytest.fixture
def photo_service():
    """Initialize photo service for testing"""
    with patch('boto3.client'):
        with patch('google.cloud.vision.ImageAnnotatorClient'):
            service = PhotoService()
            service.ENABLE_MODERATION = False  # Disable for faster tests
            return service


@pytest.fixture
def sample_image():
    """Create a sample test image (200x200 white square)"""
    img = Image.new('RGB', (200, 200), color='white')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()


@pytest.fixture
def large_image():
    """Create a large test image (2000x2000)"""
    img = Image.new('RGB', (2000, 2000), color='blue')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG', quality=95)
    return img_bytes.getvalue()


@pytest.fixture
def small_image():
    """Create a too-small image (100x100)"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    return img_bytes.getvalue()


# ==========================================
# PHOTO VALIDATION TESTS
# ==========================================

def test_validate_photo_valid(photo_service, sample_image):
    """Test validation of valid photo"""
    result = photo_service._validate_photo(sample_image, "test.jpg")
    assert result['valid'] == True


def test_validate_photo_too_small(photo_service, small_image):
    """Test rejection of too-small photo"""
    result = photo_service._validate_photo(small_image, "small.jpg")
    assert result['valid'] == False
    assert 'too small' in result['error'].lower()


def test_validate_photo_too_large(photo_service):
    """Test rejection of too-large photo"""
    # Create 15 MB image (exceeds 10 MB limit)
    large_data = b'0' * (15 * 1024 * 1024)
    result = photo_service._validate_photo(large_data, "huge.jpg")
    assert result['valid'] == False
    assert 'too large' in result['error'].lower()


def test_validate_photo_invalid_format(photo_service):
    """Test rejection of invalid format"""
    # Not a valid image
    invalid_data = b'not an image'
    result = photo_service._validate_photo(invalid_data, "invalid.jpg")
    assert result['valid'] == False


# ==========================================
# IMAGE PROCESSING TESTS
# ==========================================

def test_process_image_creates_thumbnail(photo_service, large_image):
    """Test that image processing creates thumbnail"""
    result = photo_service._process_image(large_image)
    
    assert 'original' in result
    assert 'thumbnail' in result
    
    # Check thumbnail size
    thumb_img = Image.open(BytesIO(result['thumbnail']))
    assert thumb_img.size == (200, 200)


def test_process_image_crops_to_square(photo_service):
    """Test that non-square images are cropped to square"""
    # Create 300x200 image (3:2 aspect ratio)
    img = Image.new('RGB', (300, 200), color='green')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    
    result = photo_service._process_image(img_bytes.getvalue())
    
    # Check original is square
    original_img = Image.open(BytesIO(result['original']))
    assert original_img.size == (1024, 1024)


def test_process_image_converts_rgba_to_rgb(photo_service):
    """Test that RGBA images are converted to RGB"""
    # Create RGBA image (PNG with transparency)
    img = Image.new('RGBA', (300, 300), color=(255, 0, 0, 128))
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    
    result = photo_service._process_image(img_bytes.getvalue())
    
    # Should be converted to JPEG (RGB)
    original_img = Image.open(BytesIO(result['original']))
    assert original_img.mode == 'RGB'


# ==========================================
# AI MODERATION TESTS (MOCKED)
# ==========================================

@pytest.mark.asyncio
async def test_moderate_photo_safe_content(photo_service, sample_image):
    """Test moderation of safe content"""
    # Mock Google Vision API response
    mock_response = MagicMock()
    mock_response.safe_search_annotation.adult = 1
    mock_response.safe_search_annotation.violence = 1
    mock_response.safe_search_annotation.racy = 1
    mock_response.safe_search_annotation.medical = 1
    
    mock_faces = MagicMock()
    mock_faces.face_annotations = [MagicMock(detection_confidence=0.95)]
    
    mock_labels = MagicMock()
    mock_labels.label_annotations = []
    
    photo_service.VISION_CLIENT = MagicMock()
    photo_service.VISION_CLIENT.safe_search_detection.return_value = mock_response
    photo_service.VISION_CLIENT.face_detection.return_value = mock_faces
    photo_service.VISION_CLIENT.label_detection.return_value = mock_labels
    photo_service.VISION_CLIENT.image_properties.return_value = MagicMock()
    photo_service.ENABLE_MODERATION = True
    
    result = await photo_service._moderate_photo(sample_image)
    
    assert result['safe'] == True
    assert result['face_count'] == 1


@pytest.mark.asyncio
async def test_moderate_photo_adult_content(photo_service, sample_image):
    """Test rejection of adult content"""
    # Mock adult content detection
    mock_response = MagicMock()
    mock_response.safe_search_annotation.adult = 4  # LIKELY
    mock_response.safe_search_annotation.violence = 1
    mock_response.safe_search_annotation.racy = 1
    mock_response.safe_search_annotation.medical = 1
    
    photo_service.VISION_CLIENT = MagicMock()
    photo_service.VISION_CLIENT.safe_search_detection.return_value = mock_response
    photo_service.ENABLE_MODERATION = True
    
    result = await photo_service._moderate_photo(sample_image)
    
    assert result['safe'] == False
    assert 'adult' in result['reason'].lower()


@pytest.mark.asyncio
async def test_moderate_photo_multiple_faces(photo_service, sample_image):
    """Test rejection of photos with multiple faces"""
    # Mock multiple face detection
    mock_response = MagicMock()
    mock_response.safe_search_annotation.adult = 1
    mock_response.safe_search_annotation.violence = 1
    mock_response.safe_search_annotation.racy = 1
    mock_response.safe_search_annotation.medical = 1
    
    mock_faces = MagicMock()
    # 3 faces detected
    mock_faces.face_annotations = [MagicMock(), MagicMock(), MagicMock()]
    
    photo_service.VISION_CLIENT = MagicMock()
    photo_service.VISION_CLIENT.safe_search_detection.return_value = mock_response
    photo_service.VISION_CLIENT.face_detection.return_value = mock_faces
    photo_service.ENABLE_MODERATION = True
    
    result = await photo_service._moderate_photo(sample_image)
    
    assert result['safe'] == False
    assert result['face_count'] == 3
    assert 'multiple faces' in result['reason'].lower()


# ==========================================
# S3 STORAGE TESTS (MOCKED)
# ==========================================

def test_get_s3_keys(photo_service):
    """Test S3 key generation"""
    user_id = "user123"
    keys = photo_service._get_s3_keys(user_id)
    
    assert keys['original'] == f"users/{user_id}/profile.jpg"
    assert keys['thumbnail'] == f"users/{user_id}/profile_thumb.jpg"


def test_upload_to_s3(photo_service, sample_image):
    """Test S3 upload"""
    # Mock S3 client
    photo_service.s3_client = MagicMock()
    
    key = "test/photo.jpg"
    result = photo_service._upload_to_s3(sample_image, key, 'image/jpeg')
    
    # Should call put_object
    photo_service.s3_client.put_object.assert_called_once()
    
    # Should return key
    assert result == key


def test_generate_signed_url(photo_service):
    """Test signed URL generation"""
    # Mock S3 client
    photo_service.s3_client = MagicMock()
    photo_service.s3_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/..."
    
    url = photo_service.generate_signed_url("test/photo.jpg", 3600)
    
    # Should call generate_presigned_url
    photo_service.s3_client.generate_presigned_url.assert_called_once()
    
    assert url.startswith("https://")


# ==========================================
# AVATAR GENERATION TESTS
# ==========================================

def test_generate_avatar_url(photo_service):
    """Test DiceBear avatar URL generation"""
    user_id = "user123"
    url = photo_service.generate_avatar_url(user_id)
    
    assert "dicebear.com" in url
    assert "avataaars" in url
    assert "seed=" in url
    assert "backgroundColor=4A1A5C" in url


def test_generate_initials_avatar(photo_service):
    """Test initials avatar URL generation"""
    initials = "PK"
    url = photo_service.generate_initials_avatar(initials)
    
    assert "dicebear.com" in url
    assert "initials" in url
    assert "seed=PK" in url
    assert "backgroundColor=4A1A5C" in url


def test_get_emoji_avatar_url(photo_service):
    """Test emoji avatar URL generation"""
    emoji = "😊"
    url = photo_service.get_emoji_avatar_url(emoji)
    
    assert "twemoji" in url or "jsdelivr" in url
    assert ".png" in url


# ==========================================
# PRIVACY CONTROL TESTS
# ==========================================

@pytest.mark.asyncio
async def test_get_photo_urls_level_1(photo_service):
    """Test photo access at trust level 1 (discovery)"""
    user_id = "user123"
    viewer_id = "viewer456"
    trust_level = 1
    
    result = await photo_service.get_photo_urls(user_id, viewer_id, trust_level)
    
    # Should return generated avatar only
    assert result['is_blurred'] == True
    assert result['can_reveal'] == False
    assert "dicebear" in result['photo_url']


@pytest.mark.asyncio
async def test_get_photo_urls_level_2_no_photo(photo_service):
    """Test photo access at level 2+ when user hasn't uploaded photo"""
    user_id = "user123"
    viewer_id = "viewer456"
    trust_level = 2
    
    # Mock S3 head_object to raise exception (no photo exists)
    photo_service.s3_client = MagicMock()
    photo_service.s3_client.head_object.side_effect = Exception("Not found")
    
    result = await photo_service.get_photo_urls(user_id, viewer_id, trust_level)
    
    # Should return generated avatar
    assert "dicebear" in result['photo_url']
    assert result['is_blurred'] == False


@pytest.mark.asyncio
async def test_get_photo_urls_level_2_with_photo(photo_service):
    """Test photo access at level 2+ when user has uploaded photo"""
    user_id = "user123"
    viewer_id = "viewer456"
    trust_level = 2
    
    # Mock S3 head_object to succeed (photo exists)
    photo_service.s3_client = MagicMock()
    photo_service.s3_client.head_object.return_value = True
    photo_service.s3_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/..."
    
    result = await photo_service.get_photo_urls(user_id, viewer_id, trust_level)
    
    # Should return real photo
    assert result['can_reveal'] == True
    assert "s3.amazonaws.com" in result['photo_url']


# ==========================================
# FULL UPLOAD FLOW TEST
# ==========================================

@pytest.mark.asyncio
async def test_full_upload_flow(photo_service, sample_image):
    """Test complete photo upload flow"""
    user_id = "user123"
    
    # Mock S3 client
    photo_service.s3_client = MagicMock()
    photo_service.s3_client.put_object.return_value = True
    
    # Disable moderation for faster test
    photo_service.ENABLE_MODERATION = False
    
    result = await photo_service.upload_photo(
        user_id=user_id,
        photo_data=sample_image,
        filename="test.jpg"
    )
    
    # Should be approved
    assert result['status'] == ModerationStatus.APPROVED
    
    # Should have called S3 twice (original + thumbnail)
    assert photo_service.s3_client.put_object.call_count == 2


@pytest.mark.asyncio
async def test_upload_flow_rejection(photo_service, small_image):
    """Test photo upload rejection due to validation"""
    user_id = "user123"
    
    result = await photo_service.upload_photo(
        user_id=user_id,
        photo_data=small_image,
        filename="small.jpg"
    )
    
    # Should be rejected
    assert result['status'] == ModerationStatus.REJECTED
    assert 'too small' in result['rejection_reason'].lower()


# ==========================================
# PHOTO DELETION TEST
# ==========================================

@pytest.mark.asyncio
async def test_delete_photo(photo_service):
    """Test photo deletion"""
    user_id = "user123"
    
    # Mock S3 client
    photo_service.s3_client = MagicMock()
    
    result = await photo_service.delete_photo(user_id)
    
    # Should call delete_object twice (original + thumbnail)
    assert photo_service.s3_client.delete_object.call_count == 2
    assert result == True


# ==========================================
# STATISTICS TEST
# ==========================================

@pytest.mark.asyncio
async def test_get_upload_stats_with_photo(photo_service):
    """Test getting upload stats when photo exists"""
    user_id = "user123"
    
    # Mock S3 response
    photo_service.s3_client = MagicMock()
    photo_service.s3_client.head_object.return_value = {
        'ContentLength': 2500000,  # 2.5 MB
        'Metadata': {'uploaded_at': '2024-02-06T10:00:00'}
    }
    
    result = await photo_service.get_upload_stats(user_id)
    
    assert result['has_photo'] == True
    assert result['photo_type'] == PhotoType.UPLOAD
    assert result['file_size_mb'] == 2.38


@pytest.mark.asyncio
async def test_get_upload_stats_no_photo(photo_service):
    """Test getting upload stats when no photo exists"""
    user_id = "user123"
    
    # Mock S3 to raise exception (no photo)
    photo_service.s3_client = MagicMock()
    photo_service.s3_client.head_object.side_effect = Exception("Not found")
    
    result = await photo_service.get_upload_stats(user_id)
    
    assert result['has_photo'] == False
    assert result['photo_type'] == PhotoType.GENERATED


# ==========================================
# RUN TESTS
# ==========================================

if __name__ == "__main__":
    print("🧪 Running Photo System Tests...")
    print("=" * 60)
    
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
