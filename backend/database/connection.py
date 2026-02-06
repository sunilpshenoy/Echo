"""
Pulse Backend - Database Connection & Management
MongoDB connection pool and collection references
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging
from config import settings, Collections

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database manager with connection pooling"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls):
        """Establish database connection"""
        try:
            logger.info(f"🔌 Connecting to MongoDB: {settings.MONGO_URL}")
            cls.client = AsyncIOMotorClient(
                settings.MONGO_URL,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000
            )
            cls.db = cls.client[settings.MONGO_DB_NAME]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info("✅ MongoDB connected successfully")
            
            # Create indexes
            await cls.create_indexes()
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """Close database connection"""
        if cls.client:
            cls.client.close()
            logger.info("🔌 MongoDB disconnected")
    
    @classmethod
    async def create_indexes(cls):
        """Create database indexes for performance"""
        if not cls.db:
            return
        
        try:
            logger.info("📊 Creating database indexes...")
            
            # Users collection
            await cls.db[Collections.USERS].create_index("email", unique=True)
            await cls.db[Collections.USERS].create_index("username", unique=True)
            await cls.db[Collections.USERS].create_index("phone_number")
            await cls.db[Collections.USERS].create_index("created_at")
            
            # Chats collection
            await cls.db[Collections.CHATS].create_index([
                ("participants", 1),
                ("updated_at", -1)
            ])
            await cls.db[Collections.CHATS].create_index("chat_type")
            
            # Messages collection
            await cls.db[Collections.MESSAGES].create_index([
                ("chat_id", 1),
                ("timestamp", -1)
            ])
            await cls.db[Collections.MESSAGES].create_index("sender_id")
            await cls.db[Collections.MESSAGES].create_index("is_deleted")
            
            # Connections collection
            await cls.db[Collections.CONNECTIONS].create_index([
                ("user1_id", 1),
                ("user2_id", 1)
            ], unique=True)
            await cls.db[Collections.CONNECTIONS].create_index("trust_level")
            await cls.db[Collections.CONNECTIONS].create_index("status")
            
            # Safety check-ins collection
            await cls.db[Collections.SAFETY_CHECKINS].create_index([
                ("user_id", 1),
                ("status", 1)
            ])
            await cls.db[Collections.SAFETY_CHECKINS].create_index("meeting_time")
            await cls.db[Collections.SAFETY_CHECKINS].create_index([
                ("status", 1),
                ("meeting_time", 1)
            ])
            
            # Stories collection
            await cls.db[Collections.STORIES].create_index([
                ("user_id", 1),
                ("expires_at", 1)
            ])
            await cls.db[Collections.STORIES].create_index("created_at")
            
            # Channels collection
            await cls.db[Collections.CHANNELS].create_index("channel_type")
            await cls.db[Collections.CHANNELS].create_index([
                ("is_public", 1),
                ("subscriber_count", -1)
            ])
            
            # Marketplace collection
            await cls.db[Collections.MARKETPLACE].create_index([
                ("seller_id", 1),
                ("status", 1)
            ])
            await cls.db[Collections.MARKETPLACE].create_index("category")
            await cls.db[Collections.MARKETPLACE].create_index("price")
            
            # Game rooms collection
            await cls.db[Collections.GAME_ROOMS].create_index("game_type")
            await cls.db[Collections.GAME_ROOMS].create_index([
                ("status", 1),
                ("created_at", -1)
            ])
            
            # Call history collection
            await cls.db[Collections.CALL_HISTORY].create_index([
                ("participants", 1),
                ("start_time", -1)
            ])
            await cls.db[Collections.CALL_HISTORY].create_index("call_type")
            
            # Verification requests collection
            await cls.db[Collections.VERIFICATION_REQUESTS].create_index([
                ("user_id", 1),
                ("verification_type", 1),
                ("status", 1)
            ])
            
            # Blocked users collection
            await cls.db[Collections.BLOCKED_USERS].create_index([
                ("blocker_id", 1),
                ("blocked_id", 1)
            ], unique=True)
            
            # Audit logs collection
            await cls.db[Collections.AUDIT_LOGS].create_index([
                ("user_id", 1),
                ("timestamp", -1)
            ])
            await cls.db[Collections.AUDIT_LOGS].create_index("action_type")
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")
    
    @classmethod
    def get_collection(cls, collection_name: str):
        """Get a collection reference"""
        if not cls.db:
            raise RuntimeError("Database not connected")
        return cls.db[collection_name]


# Collection references (shorthand)
def get_db() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if not Database.db:
        raise RuntimeError("Database not connected")
    return Database.db


# Dependency injection for FastAPI
async def get_database():
    """FastAPI dependency for database access"""
    return get_db()


if __name__ == "__main__":
    # Test connection
    import asyncio
    
    async def test():
        await Database.connect()
        print("✅ Database connection test passed")
        await Database.disconnect()
    
    asyncio.run(test())
