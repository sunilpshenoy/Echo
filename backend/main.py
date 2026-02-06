"""
Pulse Backend - Main Application Entry Point
Refactored modular architecture with legacy compatibility
"""

import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Pulse - Connect Securely",
    description="Secure social networking platform with modular architecture",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "*.emergentagent.com", "127.0.0.1", "*"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Pulse Backend",
        "version": "2.0.0",
        "architecture": "modular"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Pulse API v2.0",
        "version": "2.0.0",
        "architecture": "modular",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "health": "/health",
            "api": "/api/*"
        }
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("=" * 60)
    logger.info("🚀 STARTING PULSE BACKEND v2.0")
    logger.info("=" * 60)
    
    # Import database connection
    try:
        from database.connection import Database
        await Database.connect()
        logger.info("✅ Database connected successfully")
        
        # Set database for middleware
        from middleware.auth import set_database
        set_database(Database.db)
        logger.info("✅ Auth middleware configured")
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.warning("⚠️  App will continue but database features won't work")
    
    # Load legacy routes (all existing endpoints)
    try:
        logger.info("📦 Loading legacy server routes...")
        from server_legacy import api_router as legacy_router
        app.include_router(legacy_router)
        logger.info("✅ Legacy routes loaded (all existing endpoints available)")
    except Exception as e:
        logger.error(f"❌ Could not load legacy routes: {e}")
        logger.info("💡 This is expected if running for first time")
    
    # Load new modular routers
    try:
        logger.info("📦 Loading new modular routers...")
        
        # Photo router
        try:
            from routers.photo_router import router as photo_router
            app.include_router(photo_router)
            logger.info("  ✅ Photo router loaded (/api/v1/photos/*)")
        except Exception as e:
            logger.warning(f"  ⚠️  Photo router not available: {e}")
        
        logger.info("✅ New routers loaded")
        
    except Exception as e:
        logger.warning(f"⚠️  Some new routers not available: {e}")
    
    logger.info("=" * 60)
    logger.info("✅ PULSE BACKEND STARTED SUCCESSFULLY")
    logger.info("=" * 60)
    logger.info("📍 API available at: http://localhost:8000")
    logger.info("📚 Documentation at: http://localhost:8000/docs")
    logger.info("🏥 Health check at: http://localhost:8000/health")
    logger.info("=" * 60)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Pulse Backend...")
    
    # Disconnect database
    try:
        from database.connection import Database
        await Database.disconnect()
        logger.info("✅ Database disconnected")
    except:
        pass
    
    logger.info("✅ Pulse Backend shut down successfully")

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 60)
    print("🚀 PULSE BACKEND - Starting Development Server")
    print("=" * 60)
    print()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
