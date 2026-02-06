"""
Pulse Backend - Photo API Endpoints
Handles profile photo upload, moderation, and avatar generation
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict
from pydantic import BaseModel, Field
import logging

from services.photo_service import get_photo_service, PhotoType, PhotoService
from middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/photos", tags=["photos"])


# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================

class PhotoUploadResponse(BaseModel):
    """Response after photo upload"""
    status: str
    photo_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    moderation_result: Optional[Dict] = None
    rejection_reason: Optional[str] = None
    uploaded_at: Optional[str] = None


class PhotoURLResponse(BaseModel):
    """Photo URLs with privacy controls"""
    photo_url: str
    thumbnail_url: str
    is_blurred: bool
    can_reveal: bool
    message: Optional[str] = None


class AvatarRequest(BaseModel):
    """Request to set avatar"""
    avatar_type: PhotoType
    avatar_data: Optional[str] = Field(
        None,
        description="Emoji for emoji type, initials for initials type"
    )
    background_color: Optional[str] = Field("4A1A5C", description="Hex color (no #)")


class AvatarResponse(BaseModel):
    """Avatar URL response"""
    avatar_url: str
    avatar_type: PhotoType
    message: str


# ==========================================
# PHOTO UPLOAD ENDPOINTS
# ==========================================

@router.post("/upload", response_model=PhotoUploadResponse)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Upload profile photo
    
    **Flow:**
    1. User selects/captures photo
    2. Frontend uploads to this endpoint
    3. Backend validates, processes, moderates
    4. Photo stored in S3 (if approved)
    5. Returns status + URLs
    
    **Privacy:**
    - Photos only visible to Level 2+ connections
    - Not shown in Discovery (Level 1)
    
    **Moderation:**
    - AI checks for inappropriate content
    - Max 1 face allowed
    - Rejects violent/sexual/offensive content
    
    **Requirements:**
    - Min size: 200x200px
    - Max size: 10 MB
    - Formats: JPG, PNG, HEIC, WEBP
    
    **Returns:**
    - status: "approved" | "rejected" | "pending"
    - photo_url: Signed S3 URL (1 hour validity)
    - thumbnail_url: Thumbnail URL
    - rejection_reason: Why photo was rejected (if applicable)
    """
    try:
        user_id = current_user['user_id']
        
        # Read file data
        photo_data = await file.read()
        
        # Upload and process
        result = await photo_service.upload_photo(
            user_id=user_id,
            photo_data=photo_data,
            filename=file.filename
        )
        
        # Log result
        if result['status'] == 'approved':
            logger.info(f"✅ Photo approved for user {user_id}")
        else:
            logger.warning(f"❌ Photo rejected for user {user_id}: {result.get('rejection_reason')}")
        
        return PhotoUploadResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Photo upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Photo upload failed: {str(e)}"
        )


@router.delete("/delete")
async def delete_profile_photo(
    current_user: Dict = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Delete profile photo
    
    **Effect:**
    - Removes photo from S3
    - User will see generated avatar instead
    
    **Returns:**
    - success: True/False
    - message: Status message
    """
    try:
        user_id = current_user['user_id']
        
        success = await photo_service.delete_photo(user_id)
        
        if success:
            return {
                "success": True,
                "message": "Photo deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Photo deletion failed"
            )
            
    except Exception as e:
        logger.error(f"❌ Photo deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==========================================
# PHOTO RETRIEVAL ENDPOINTS
# ==========================================

@router.get("/user/{user_id}", response_model=PhotoURLResponse)
async def get_user_photo(
    user_id: str,
    current_user: Dict = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Get user's profile photo with privacy checks
    
    **Privacy Rules:**
    - Level 1 (Discovery): Returns generated avatar only
    - Level 2+ (Connected): Returns real photo (if uploaded)
    
    **Parameters:**
    - user_id: User whose photo to fetch
    
    **Returns:**
    - photo_url: Photo URL (signed, 1 hour expiry)
    - thumbnail_url: Thumbnail URL
    - is_blurred: Should UI show blur effect?
    - can_reveal: Can user tap to reveal?
    - message: Explanation
    
    **Example:**
    ```json
    {
        "photo_url": "https://s3.amazonaws.com/...",
        "thumbnail_url": "https://s3.amazonaws.com/...",
        "is_blurred": false,
        "can_reveal": true,
        "message": "Photo available"
    }
    ```
    """
    try:
        viewer_id = current_user['user_id']
        
        # TODO: Get trust level from connections collection
        # For now, assume Level 2 if viewer != user (connected)
        viewer_trust_level = 2 if viewer_id != user_id else 5
        
        result = await photo_service.get_photo_urls(
            user_id=user_id,
            viewer_id=viewer_id,
            viewer_trust_level=viewer_trust_level
        )
        
        return PhotoURLResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Get photo error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/my-photo")
async def get_my_photo(
    current_user: Dict = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Get current user's own photo (always accessible)
    
    **Returns:**
    - photo_url: Full resolution photo
    - thumbnail_url: Thumbnail
    - stats: Upload statistics
    """
    try:
        user_id = current_user['user_id']
        
        # Get photo URLs (trust level 5 = self)
        urls = await photo_service.get_photo_urls(
            user_id=user_id,
            viewer_id=user_id,
            viewer_trust_level=5
        )
        
        # Get upload stats
        stats = await photo_service.get_upload_stats(user_id)
        
        return {
            **urls,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Get my photo error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==========================================
# AVATAR GENERATION ENDPOINTS
# ==========================================

@router.post("/avatar/generate", response_model=AvatarResponse)
async def generate_avatar(
    request: AvatarRequest,
    current_user: Dict = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Generate avatar without uploading photo
    
    **Avatar Types:**
    
    1. **Generated (DiceBear)**
       - Unique geometric/cartoon avatar
       - Based on your User ID
       - Example: `{"avatar_type": "generated"}`
    
    2. **Emoji**
       - Choose any emoji
       - Example: `{"avatar_type": "emoji", "avatar_data": "😊"}`
    
    3. **Initials**
       - Gmail/Slack style
       - Example: `{"avatar_type": "initials", "avatar_data": "PK"}`
    
    **Parameters:**
    - avatar_type: "generated" | "emoji" | "initials"
    - avatar_data: Emoji or initials (required for emoji/initials)
    - background_color: Hex color without # (default: "4A1A5C")
    
    **Returns:**
    - avatar_url: Generated avatar URL
    - avatar_type: Type of avatar
    - message: Success message
    """
    try:
        user_id = current_user['user_id']
        
        # Generate avatar based on type
        if request.avatar_type == PhotoType.GENERATED:
            avatar_url = photo_service.generate_avatar_url(
                user_id=user_id,
                background_color=request.background_color
            )
            message = "Generated unique avatar"
            
        elif request.avatar_type == PhotoType.EMOJI:
            if not request.avatar_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="avatar_data (emoji) required for emoji type"
                )
            avatar_url = photo_service.get_emoji_avatar_url(request.avatar_data)
            message = f"Emoji avatar: {request.avatar_data}"
            
        elif request.avatar_type == PhotoType.INITIALS:
            if not request.avatar_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="avatar_data (initials) required for initials type"
                )
            avatar_url = photo_service.generate_initials_avatar(
                initials=request.avatar_data,
                background_color=request.background_color
            )
            message = f"Initials avatar: {request.avatar_data}"
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid avatar_type: {request.avatar_type}"
            )
        
        return AvatarResponse(
            avatar_url=avatar_url,
            avatar_type=request.avatar_type,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Avatar generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/avatar/preview/{avatar_type}")
async def preview_avatar(
    avatar_type: str,
    emoji: Optional[str] = None,
    initials: Optional[str] = None,
    background_color: str = "4A1A5C",
    current_user: Dict = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Preview avatar before setting
    
    **Use Case:**
    Frontend shows preview grid of different avatars
    
    **Parameters:**
    - avatar_type: "generated" | "emoji" | "initials"
    - emoji: Emoji character (for emoji type)
    - initials: 1-2 characters (for initials type)
    - background_color: Hex without # (default: "4A1A5C")
    
    **Returns:**
    - avatar_url: Preview URL
    
    **Example:**
    ```
    GET /api/v1/photos/avatar/preview/emoji?emoji=😊
    GET /api/v1/photos/avatar/preview/initials?initials=PK
    GET /api/v1/photos/avatar/preview/generated
    ```
    """
    try:
        user_id = current_user['user_id']
        
        if avatar_type == "generated":
            avatar_url = photo_service.generate_avatar_url(
                user_id=user_id,
                background_color=background_color
            )
        elif avatar_type == "emoji":
            if not emoji:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="emoji parameter required"
                )
            avatar_url = photo_service.get_emoji_avatar_url(emoji)
        elif avatar_type == "initials":
            if not initials:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="initials parameter required"
                )
            avatar_url = photo_service.generate_initials_avatar(
                initials=initials,
                background_color=background_color
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid avatar_type: {avatar_type}"
            )
        
        return {"avatar_url": avatar_url}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Avatar preview error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==========================================
# ADMIN/DEBUG ENDPOINTS
# ==========================================

@router.get("/stats")
async def get_photo_stats(
    current_user: Dict = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service)
):
    """
    Get photo upload statistics for current user
    
    **Returns:**
    - has_photo: Boolean
    - photo_type: "upload" | "generated" | "emoji" | "initials"
    - uploaded_at: ISO timestamp
    - file_size_mb: File size
    - moderation_status: "approved" | "rejected" | "pending"
    """
    try:
        user_id = current_user['user_id']
        
        stats = await photo_service.get_upload_stats(user_id)
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Get stats error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
