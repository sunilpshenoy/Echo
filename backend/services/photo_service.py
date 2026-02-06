"""
Pulse Backend - Photo Management Service
Handles profile photo uploads, moderation, storage, and avatar generation
"""

import os
import io
import hashlib
import boto3
from botocore.exceptions import ClientError
from google.cloud import vision
from PIL import Image
import logging
from typing import Optional, Dict, Tuple, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class PhotoType(str, Enum):
    """Profile photo type options"""
    UPLOAD = "upload"          # User uploaded photo
    GENERATED = "generated"    # DiceBear geometric avatar
    EMOJI = "emoji"           # Emoji selection
    INITIALS = "initials"     # Gmail-style initials


class ModerationStatus(str, Enum):
    """Photo moderation status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class PhotoService:
    """
    Manages user profile photos with:
    - Upload & storage (AWS S3)
    - AI moderation (Google Vision API)
    - Avatar generation (DiceBear, Emoji, Initials)
    - Privacy controls (Level 2+ visibility)
    - Signed URL generation
    """
    
    # Image constraints
    MIN_SIZE = 200  # 200x200 minimum
    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_FORMATS = {'JPEG', 'PNG', 'HEIC', 'WEBP'}
    THUMBNAIL_SIZE = (200, 200)
    
    # AWS S3 configuration
    S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'pulse-user-photos')
    S3_REGION = os.getenv('AWS_REGION', 'ap-south-1')  # Mumbai
    CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN', '')
    
    # Google Vision API
    VISION_CLIENT = None
    ENABLE_MODERATION = os.getenv('ENABLE_PHOTO_MODERATION', 'true').lower() == 'true'
    
    # DiceBear API
    DICEBEAR_BASE_URL = "https://api.dicebear.com/7.x"
    DICEBEAR_STYLE = "avataaars"  # Or: bottts, shapes, lorelei
    
    def __init__(self):
        """Initialize photo service with AWS S3 and Google Vision"""
        try:
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                region_name=self.S3_REGION,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
            )
            logger.info(f"✅ S3 client initialized (bucket: {self.S3_BUCKET})")
            
            # Initialize Google Vision API client
            if self.ENABLE_MODERATION:
                try:
                    self.VISION_CLIENT = vision.ImageAnnotatorClient()
                    logger.info("✅ Google Vision API initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Google Vision not available: {e}")
                    self.ENABLE_MODERATION = False
                    
        except Exception as e:
            logger.error(f"❌ Photo service initialization failed: {e}")
            raise
    
    
    # ==========================================
    # PHOTO UPLOAD & PROCESSING
    # ==========================================
    
    async def upload_photo(
        self,
        user_id: str,
        photo_data: bytes,
        filename: str
    ) -> Dict:
        """
        Upload and process user profile photo
        
        Steps:
        1. Validate file format and size
        2. Process image (crop, resize, optimize)
        3. Run AI moderation
        4. Upload to S3 (original + thumbnail)
        5. Return signed URLs
        
        Args:
            user_id: User's unique ID
            photo_data: Raw photo bytes
            filename: Original filename
            
        Returns:
            {
                "status": "approved" | "rejected" | "pending",
                "photo_url": "https://...",
                "thumbnail_url": "https://...",
                "moderation_result": {...},
                "rejection_reason": "..." (if rejected)
            }
        """
        try:
            # Step 1: Validate
            validation = self._validate_photo(photo_data, filename)
            if not validation['valid']:
                return {
                    "status": ModerationStatus.REJECTED,
                    "rejection_reason": validation['error']
                }
            
            # Step 2: Process image
            processed = self._process_image(photo_data)
            original_data = processed['original']
            thumbnail_data = processed['thumbnail']
            
            # Step 3: Run AI moderation (if enabled)
            if self.ENABLE_MODERATION:
                moderation = await self._moderate_photo(original_data)
                if not moderation['safe']:
                    return {
                        "status": ModerationStatus.REJECTED,
                        "rejection_reason": moderation['reason'],
                        "moderation_result": moderation
                    }
            else:
                moderation = {"safe": True, "reason": "Moderation disabled"}
            
            # Step 4: Upload to S3
            s3_keys = self._get_s3_keys(user_id)
            
            # Upload original
            original_url = self._upload_to_s3(
                original_data,
                s3_keys['original'],
                'image/jpeg'
            )
            
            # Upload thumbnail
            thumbnail_url = self._upload_to_s3(
                thumbnail_data,
                s3_keys['thumbnail'],
                'image/jpeg'
            )
            
            logger.info(f"✅ Photo uploaded for user {user_id}")
            
            return {
                "status": ModerationStatus.APPROVED,
                "photo_url": original_url,
                "thumbnail_url": thumbnail_url,
                "moderation_result": moderation,
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Photo upload failed: {e}")
            raise
    
    
    def _validate_photo(self, photo_data: bytes, filename: str) -> Dict:
        """
        Validate photo format and size
        
        Returns:
            {"valid": True/False, "error": "..."}
        """
        try:
            # Check size
            if len(photo_data) > self.MAX_SIZE:
                return {
                    "valid": False,
                    "error": f"File too large (max {self.MAX_SIZE // (1024*1024)} MB)"
                }
            
            # Check format
            img = Image.open(io.BytesIO(photo_data))
            if img.format not in self.ALLOWED_FORMATS:
                return {
                    "valid": False,
                    "error": f"Invalid format. Allowed: {', '.join(self.ALLOWED_FORMATS)}"
                }
            
            # Check dimensions
            width, height = img.size
            if width < self.MIN_SIZE or height < self.MIN_SIZE:
                return {
                    "valid": False,
                    "error": f"Image too small (min {self.MIN_SIZE}x{self.MIN_SIZE})"
                }
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Invalid image file: {str(e)}"}
    
    
    def _process_image(self, photo_data: bytes) -> Dict[str, bytes]:
        """
        Process image: crop to square, resize, optimize
        
        Returns:
            {
                "original": bytes,  # 1024x1024 JPEG
                "thumbnail": bytes  # 200x200 JPEG
            }
        """
        img = Image.open(io.BytesIO(photo_data))
        
        # Convert RGBA to RGB (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Crop to square (center crop)
        width, height = img.size
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        img = img.crop((left, top, left + size, top + size))
        
        # Resize original to 1024x1024
        original = img.resize((1024, 1024), Image.Resampling.LANCZOS)
        original_bytes = io.BytesIO()
        original.save(original_bytes, format='JPEG', quality=90, optimize=True)
        
        # Create thumbnail 200x200
        thumbnail = img.resize(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        thumbnail_bytes = io.BytesIO()
        thumbnail.save(thumbnail_bytes, format='JPEG', quality=85, optimize=True)
        
        return {
            "original": original_bytes.getvalue(),
            "thumbnail": thumbnail_bytes.getvalue()
        }
    
    
    # ==========================================
    # AI MODERATION (Google Vision API)
    # ==========================================
    
    async def _moderate_photo(self, photo_data: bytes) -> Dict:
        """
        Run AI moderation using Google Vision API
        
        Checks for:
        - Adult content
        - Violence
        - Racy content
        - Medical content
        - Offensive symbols
        - Multiple faces (should be 1 or 0)
        - Image quality
        
        Returns:
            {
                "safe": True/False,
                "reason": "...",
                "scores": {...},
                "face_count": 1,
                "labels": [...]
            }
        """
        try:
            if not self.VISION_CLIENT:
                return {"safe": True, "reason": "Moderation unavailable"}
            
            # Prepare image
            image = vision.Image(content=photo_data)
            
            # Run multiple detections
            safe_search = self.VISION_CLIENT.safe_search_detection(image=image)
            faces = self.VISION_CLIENT.face_detection(image=image)
            labels = self.VISION_CLIENT.label_detection(image=image)
            image_props = self.VISION_CLIENT.image_properties(image=image)
            
            # Extract results
            safe = safe_search.safe_search_annotation
            face_count = len(faces.face_annotations)
            detected_labels = [label.description.lower() for label in labels.label_annotations[:10]]
            
            # Check Safe Search scores
            # Likelihood: UNKNOWN=0, VERY_UNLIKELY=1, UNLIKELY=2, POSSIBLE=3, LIKELY=4, VERY_LIKELY=5
            adult_score = safe.adult
            violence_score = safe.violence
            racy_score = safe.racy
            medical_score = safe.medical
            
            # Define rejection thresholds (3 = POSSIBLE, 4 = LIKELY)
            if adult_score >= 3:
                return {
                    "safe": False,
                    "reason": "Adult content detected",
                    "scores": {"adult": adult_score}
                }
            
            if violence_score >= 4:
                return {
                    "safe": False,
                    "reason": "Violence detected",
                    "scores": {"violence": violence_score}
                }
            
            if racy_score >= 4:
                return {
                    "safe": False,
                    "reason": "Inappropriate content detected",
                    "scores": {"racy": racy_score}
                }
            
            # Check for offensive labels
            offensive_keywords = [
                'weapon', 'gun', 'knife', 'blood', 'drug',
                'nazi', 'hate', 'offensive', 'nudity'
            ]
            
            for keyword in offensive_keywords:
                if any(keyword in label for label in detected_labels):
                    return {
                        "safe": False,
                        "reason": f"Inappropriate content: {keyword}",
                        "labels": detected_labels
                    }
            
            # Check face count (max 1 face for selfies)
            if face_count > 1:
                return {
                    "safe": False,
                    "reason": "Multiple faces detected (max 1 allowed)",
                    "face_count": face_count
                }
            
            # Check image quality
            if face_count == 1:
                face = faces.face_annotations[0]
                # Check for blur
                if face.detection_confidence < 0.7:
                    return {
                        "safe": False,
                        "reason": "Image quality too low or blurry",
                        "confidence": face.detection_confidence
                    }
            
            # All checks passed
            return {
                "safe": True,
                "reason": "All checks passed",
                "scores": {
                    "adult": adult_score,
                    "violence": violence_score,
                    "racy": racy_score,
                    "medical": medical_score
                },
                "face_count": face_count,
                "labels": detected_labels[:5]
            }
            
        except Exception as e:
            logger.error(f"❌ Moderation failed: {e}")
            # Fail open (allow upload) on API errors
            return {
                "safe": True,
                "reason": f"Moderation error: {str(e)}",
                "error": True
            }
    
    
    # ==========================================
    # AWS S3 STORAGE
    # ==========================================
    
    def _get_s3_keys(self, user_id: str) -> Dict[str, str]:
        """Generate S3 keys for user photos"""
        return {
            "original": f"users/{user_id}/profile.jpg",
            "thumbnail": f"users/{user_id}/profile_thumb.jpg"
        }
    
    
    def _upload_to_s3(self, data: bytes, key: str, content_type: str) -> str:
        """
        Upload file to S3 with private ACL
        
        Returns:
            S3 key (not public URL - we use signed URLs)
        """
        try:
            self.s3_client.put_object(
                Bucket=self.S3_BUCKET,
                Key=key,
                Body=data,
                ContentType=content_type,
                ACL='private',  # Private by default
                CacheControl='max-age=31536000',  # 1 year cache
                Metadata={
                    'uploaded_at': datetime.utcnow().isoformat()
                }
            )
            
            return key
            
        except ClientError as e:
            logger.error(f"❌ S3 upload failed: {e}")
            raise
    
    
    def generate_signed_url(
        self,
        s3_key: str,
        expiry_seconds: int = 3600
    ) -> str:
        """
        Generate signed URL for private S3 object
        
        Args:
            s3_key: S3 object key
            expiry_seconds: URL validity (default 1 hour)
            
        Returns:
            Signed URL (valid for expiry_seconds)
        """
        try:
            # Use CloudFront if configured
            if self.CLOUDFRONT_DOMAIN:
                # TODO: Implement CloudFront signed URLs
                # For now, return S3 signed URL
                pass
            
            # Generate S3 signed URL
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.S3_BUCKET,
                    'Key': s3_key
                },
                ExpiresIn=expiry_seconds
            )
            
            return url
            
        except ClientError as e:
            logger.error(f"❌ Signed URL generation failed: {e}")
            raise
    
    
    async def get_photo_urls(
        self,
        user_id: str,
        viewer_id: str,
        viewer_trust_level: int
    ) -> Dict:
        """
        Get photo URLs with privacy checks
        
        Privacy rules:
        - Level 1: No photo (show generated avatar)
        - Level 2+: Show photo (if uploaded)
        
        Args:
            user_id: User whose photo to fetch
            viewer_id: Who's viewing
            viewer_trust_level: Trust level between users
            
        Returns:
            {
                "photo_url": "https://...",
                "thumbnail_url": "https://...",
                "is_blurred": True/False,
                "can_reveal": True/False
            }
        """
        try:
            # Check trust level
            if viewer_trust_level < 2:
                # Level 1: Return generated avatar
                return {
                    "photo_url": self.generate_avatar_url(user_id),
                    "thumbnail_url": self.generate_avatar_url(user_id),
                    "is_blurred": True,
                    "can_reveal": False,
                    "message": "Connect to Level 2+ to view photo"
                }
            
            # Level 2+: Check if user has uploaded photo
            s3_keys = self._get_s3_keys(user_id)
            
            # Check if photo exists
            try:
                self.s3_client.head_object(
                    Bucket=self.S3_BUCKET,
                    Key=s3_keys['original']
                )
                photo_exists = True
            except ClientError:
                photo_exists = False
            
            if not photo_exists:
                # No photo uploaded, return generated avatar
                return {
                    "photo_url": self.generate_avatar_url(user_id),
                    "thumbnail_url": self.generate_avatar_url(user_id),
                    "is_blurred": False,
                    "can_reveal": False,
                    "message": "User hasn't uploaded a photo"
                }
            
            # Generate signed URLs
            photo_url = self.generate_signed_url(s3_keys['original'])
            thumbnail_url = self.generate_signed_url(s3_keys['thumbnail'])
            
            return {
                "photo_url": photo_url,
                "thumbnail_url": thumbnail_url,
                "is_blurred": False,
                "can_reveal": True,
                "message": "Photo available"
            }
            
        except Exception as e:
            logger.error(f"❌ Get photo URLs failed: {e}")
            # Fallback to generated avatar
            return {
                "photo_url": self.generate_avatar_url(user_id),
                "thumbnail_url": self.generate_avatar_url(user_id),
                "is_blurred": False,
                "can_reveal": False,
                "error": str(e)
            }
    
    
    async def delete_photo(self, user_id: str) -> bool:
        """
        Delete user's profile photo from S3
        
        Returns:
            True if deleted successfully
        """
        try:
            s3_keys = self._get_s3_keys(user_id)
            
            # Delete original
            self.s3_client.delete_object(
                Bucket=self.S3_BUCKET,
                Key=s3_keys['original']
            )
            
            # Delete thumbnail
            self.s3_client.delete_object(
                Bucket=self.S3_BUCKET,
                Key=s3_keys['thumbnail']
            )
            
            logger.info(f"✅ Deleted photo for user {user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"❌ Photo deletion failed: {e}")
            return False
    
    
    # ==========================================
    # AVATAR GENERATION
    # ==========================================
    
    def generate_avatar_url(
        self,
        user_id: str,
        style: str = "avataaars",
        background_color: str = "4A1A5C"
    ) -> str:
        """
        Generate DiceBear avatar URL
        
        Styles:
        - avataaars: Cartoon faces (default)
        - bottts: Robot avatars
        - shapes: Geometric shapes
        - lorelei: Illustrated characters
        - thumbs: Thumbs up/down
        
        Args:
            user_id: User ID (used as seed)
            style: DiceBear style
            background_color: Hex color (no #)
            
        Returns:
            Avatar URL
        """
        # Hash user_id for consistent seed
        seed = hashlib.md5(user_id.encode()).hexdigest()[:8]
        
        return (
            f"{self.DICEBEAR_BASE_URL}/{style}/svg"
            f"?seed={seed}"
            f"&backgroundColor={background_color}"
            f"&size=200"
        )
    
    
    def generate_initials_avatar(
        self,
        initials: str,
        background_color: str = "4A1A5C",
        text_color: str = "FFFFFF",
        size: int = 200
    ) -> str:
        """
        Generate initials avatar URL (Gmail style)
        
        Uses DiceBear initials style
        
        Args:
            initials: 1-2 characters
            background_color: Hex (no #)
            text_color: Hex (no #)
            size: Image size in pixels
            
        Returns:
            Avatar URL
        """
        return (
            f"{self.DICEBEAR_BASE_URL}/initials/svg"
            f"?seed={initials.upper()}"
            f"&backgroundColor={background_color}"
            f"&textColor={text_color}"
            f"&size={size}"
        )
    
    
    def get_emoji_avatar_url(self, emoji: str, size: int = 200) -> str:
        """
        Generate emoji avatar URL
        
        Uses Twemoji CDN for consistent emoji display
        
        Args:
            emoji: Single emoji character
            size: Image size (72, 144, 288, 512)
            
        Returns:
            Twemoji CDN URL
        """
        # Convert emoji to Unicode codepoint
        codepoint = hex(ord(emoji))[2:].lower()
        
        # Twemoji CDN URL
        return f"https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/72x72/{codepoint}.png"
    
    
    # ==========================================
    # HELPER METHODS
    # ==========================================
    
    async def get_upload_stats(self, user_id: str) -> Dict:
        """
        Get photo upload statistics for user
        
        Returns:
            {
                "has_photo": True/False,
                "photo_type": "upload" | "generated" | "emoji" | "initials",
                "uploaded_at": "...",
                "file_size_mb": 2.5,
                "moderation_status": "approved"
            }
        """
        try:
            s3_keys = self._get_s3_keys(user_id)
            
            # Check if photo exists
            try:
                response = self.s3_client.head_object(
                    Bucket=self.S3_BUCKET,
                    Key=s3_keys['original']
                )
                
                return {
                    "has_photo": True,
                    "photo_type": PhotoType.UPLOAD,
                    "uploaded_at": response['Metadata'].get('uploaded_at', 'Unknown'),
                    "file_size_mb": round(response['ContentLength'] / (1024 * 1024), 2),
                    "moderation_status": ModerationStatus.APPROVED
                }
                
            except ClientError:
                return {
                    "has_photo": False,
                    "photo_type": PhotoType.GENERATED,
                    "message": "Using generated avatar"
                }
                
        except Exception as e:
            logger.error(f"❌ Get upload stats failed: {e}")
            return {"error": str(e)}


# ==========================================
# FACTORY FUNCTION
# ==========================================

_photo_service_instance = None

def get_photo_service() -> PhotoService:
    """
    Get or create PhotoService singleton
    
    Usage:
        photo_service = get_photo_service()
        result = await photo_service.upload_photo(...)
    """
    global _photo_service_instance
    if _photo_service_instance is None:
        _photo_service_instance = PhotoService()
    return _photo_service_instance
