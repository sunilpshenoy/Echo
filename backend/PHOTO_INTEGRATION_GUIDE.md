"""
Photo System Integration for server.py

Add this to your server.py to integrate the new photo upload system.
This keeps your existing code unchanged while adding new functionality.
"""

# STEP 1: Add these imports at the top of server.py (after line 518 where app is created)

# Import the photo router
from routers.photo_router import router as photo_router

# STEP 2: Add this line after 'app = FastAPI()' (around line 518)

# Include the photo router
app.include_router(photo_router, tags=["Photos"])

# That's it! The photo system is now integrated.

"""
ALTERNATIVE: If you want everything in server.py

Copy the endpoints from routers/photo_router.py into server.py and replace:
- 'router' with 'app'
- Remove the 'APIRouter' setup
- Keep all the endpoint decorators (@router.post, etc)
"""

# Example of what gets added to your API:
# POST   /api/v1/photos/upload          # Upload profile photo
# DELETE /api/v1/photos/delete          # Delete photo
# GET    /api/v1/photos/user/{id}       # Get user's photo
# GET    /api/v1/photos/my-photo        # Get own photo
# POST   /api/v1/photos/avatar/generate # Generate avatar
# GET    /api/v1/photos/stats           # Upload statistics
