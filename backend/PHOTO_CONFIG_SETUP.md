# Photo System - Configuration Changes

## Config.py Updates Required

Add the following to your `backend/config.py` file:

```python
# AWS S3 (Photo Storage)
AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "pulse-user-photos")
AWS_REGION: str = os.getenv("AWS_REGION", "ap-south-1")  # Mumbai
CLOUDFRONT_DOMAIN: Optional[str] = os.getenv("CLOUDFRONT_DOMAIN")

# Google Vision API (Photo Moderation)
GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
ENABLE_PHOTO_MODERATION: bool = os.getenv("ENABLE_PHOTO_MODERATION", "true").lower() == "true"

# Photo Settings
PHOTO_MIN_SIZE: int = 200  # 200x200 minimum
PHOTO_MAX_SIZE: int = 10 * 1024 * 1024  # 10 MB
PHOTO_THUMBNAIL_SIZE: int = 200
PHOTO_ALLOWED_FORMATS: set = {'JPEG', 'PNG', 'HEIC', 'WEBP'}
```

## Environment Variables (.env file)

Add these to your `.env` file:

```bash
# AWS S3
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_S3_BUCKET=pulse-user-photos
AWS_REGION=ap-south-1

# Google Vision API
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
ENABLE_PHOTO_MODERATION=true

# Optional: CloudFront CDN
CLOUDFRONT_DOMAIN=d1234abcd.cloudfront.net
```

## Setup Guides

For detailed setup instructions, see:
- **AWS Setup:** See documentation in `/mnt/user-data/outputs/AWS_SETUP_GUIDE.md`
- **Google Vision:** See documentation in `/mnt/user-data/outputs/GOOGLE_VISION_SETUP.md`
