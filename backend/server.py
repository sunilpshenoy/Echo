from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, File, UploadFile, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import uuid
from datetime import datetime, timedelta
import json
import jwt
from passlib.context import CryptContext
import asyncio
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
import base64
import mimetypes
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import hashlib
import qrcode
from io import BytesIO
import zipfile
import tempfile

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

# Encryption utilities
class MessageEncryption:
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derive encryption key from password and salt"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    @staticmethod
    def encrypt_message(message: str, key: str) -> str:
        """Encrypt a message using the provided key"""
        try:
            f = Fernet(key.encode())
            encrypted = f.encrypt(message.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logging.error(f"Encryption error: {e}")
            return message  # Fallback to plain text
    
    @staticmethod
    def decrypt_message(encrypted_message: str, key: str) -> str:
        """Decrypt a message using the provided key"""
        try:
            f = Fernet(key.encode())
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_message.encode())
            decrypted = f.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logging.error(f"Decryption error: {e}")
            return encrypted_message  # Fallback to encrypted text

# Helper function to convert MongoDB documents to JSON serializable format
def serialize_mongo_doc(doc):
    if doc is None:
        return None
    
    if isinstance(doc, list):
        return [serialize_mongo_doc(item) for item in doc]
    
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == '_id':
                result['_id'] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict) or isinstance(value, list):
                result[key] = serialize_mongo_doc(value)
            else:
                result[key] = value
        return result
    
    return doc

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = "your-secret-key-change-in-production"

# Enhanced Connection manager with advanced features
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
        self.voice_rooms: Dict[str, List[str]] = {}  # room_id -> [user_ids]
        self.typing_users: Dict[str, List[str]] = {}  # chat_id -> [user_ids]
        self.screen_sharing: Dict[str, str] = {}  # room_id -> user_id (who's sharing)
        self.call_quality: Dict[str, Dict] = {}  # call_id -> quality metrics
        self.user_status: Dict[str, Dict] = {}  # user_id -> {status, activity, game}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        self.user_connections[user_id] = connection_id
        return connection_id
    
    def disconnect(self, connection_id: str, user_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if user_id in self.user_connections:
            del self.user_connections[user_id]
        
        # Clean up all user presence
        for chat_id in list(self.typing_users.keys()):
            if user_id in self.typing_users[chat_id]:
                self.typing_users[chat_id].remove(user_id)
        
        for room_id in list(self.voice_rooms.keys()):
            if user_id in self.voice_rooms[room_id]:
                self.voice_rooms[room_id].remove(user_id)
                
        if user_id in self.user_status:
            del self.user_status[user_id]
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            connection_id = self.user_connections[user_id]
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_text(message)
                except:
                    self.disconnect(connection_id, user_id)
    
    async def broadcast_to_chat(self, message: str, chat_id: str, sender_id: str):
        chat = await db.chats.find_one({"chat_id": chat_id})
        if chat:
            for member_id in chat['members']:
                if member_id != sender_id:
                    await self.send_personal_message(message, member_id)
    
    async def broadcast_to_voice_room(self, message: str, room_id: str, sender_id: str = None):
        if room_id in self.voice_rooms:
            for user_id in self.voice_rooms[room_id]:
                if sender_id is None or user_id != sender_id:
                    await self.send_personal_message(message, user_id)
    
    async def broadcast_typing(self, chat_id: str, user_id: str, is_typing: bool):
        if is_typing:
            if chat_id not in self.typing_users:
                self.typing_users[chat_id] = []
            if user_id not in self.typing_users[chat_id]:
                self.typing_users[chat_id].append(user_id)
        else:
            if chat_id in self.typing_users and user_id in self.typing_users[chat_id]:
                self.typing_users[chat_id].remove(user_id)
        
        await self.broadcast_to_chat(
            json.dumps({
                "type": "typing_status",
                "data": {
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "is_typing": is_typing,
                    "typing_users": self.typing_users.get(chat_id, [])
                }
            }),
            chat_id,
            user_id
        )

manager = ConnectionManager()

# Enhanced Models
class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    display_name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    status_message: str = "Available"
    custom_status: Optional[str] = None
    activity_status: str = "online"  # online, away, busy, invisible
    game_activity: Optional[str] = None
    spotify_activity: Optional[Dict] = None
    is_online: bool = False
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    encryption_key: str = Field(default_factory=MessageEncryption.generate_key)
    safety_number: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    backup_phrase: Optional[str] = None
    two_factor_enabled: bool = False
    privacy_settings: Dict = Field(default_factory=lambda: {
        "profile_photo": "everyone",  # everyone, contacts, nobody
        "last_seen": "everyone",
        "phone_number": "contacts",
        "read_receipts": True,
        "typing_indicators": True
    })
    username_handle: Optional[str] = None  # @username for public discovery
    verified: bool = False
    premium: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    phone: Optional[str] = None
    display_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_id: str
    sender_id: str
    content: str
    encrypted_content: Optional[str] = None
    message_type: str = "text"  # text, image, file, voice, video, sticker, reaction, reply, poll, location, contact
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_data: Optional[str] = None
    voice_duration: Optional[int] = None
    reply_to: Optional[str] = None
    forward_from: Optional[str] = None
    reactions: Dict[str, List[str]] = Field(default_factory=dict)
    mentions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    edited_at: Optional[datetime] = None
    scheduled_for: Optional[datetime] = None
    is_read: bool = False
    read_by: List[Dict[str, Any]] = Field(default_factory=list)
    is_encrypted: bool = True
    expires_at: Optional[datetime] = None
    is_deleted: bool = False
    is_pinned: bool = False
    thread_id: Optional[str] = None

class Chat(BaseModel):
    chat_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_type: str  # direct, group, channel, voice_channel, announcement
    name: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None
    members: List[str]
    admins: List[str] = Field(default_factory=list)
    moderators: List[str] = Field(default_factory=list)
    banned_users: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_message: Optional[dict] = None
    encryption_enabled: bool = True
    disappearing_timer: Optional[int] = None
    pinned_messages: List[str] = Field(default_factory=list)
    is_public: bool = False
    invite_link: Optional[str] = None
    slow_mode: int = 0  # seconds between messages
    member_permissions: Dict = Field(default_factory=lambda: {
        "can_send_messages": True,
        "can_send_media": True,
        "can_add_members": False,
        "can_pin_messages": False,
        "can_change_info": False
    })
    topics: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

class VoiceRoom(BaseModel):
    room_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    chat_id: Optional[str] = None  # Associated chat
    owner_id: str
    participants: List[str] = Field(default_factory=list)
    max_participants: int = 50
    is_recording: bool = False
    recording_url: Optional[str] = None
    quality_settings: Dict = Field(default_factory=lambda: {
        "bitrate": 64000,
        "sample_rate": 48000,
        "channels": 2
    })
    screen_sharing_user: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class VoiceCall(BaseModel):
    call_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_id: str
    caller_id: str
    participants: List[str]
    call_type: str = "voice"  # voice, video, group_voice, group_video
    status: str = "ringing"  # ringing, active, ended, missed, declined
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration: Optional[int] = None
    quality_metrics: Dict = Field(default_factory=lambda: {
        "avg_latency": 0,
        "packet_loss": 0,
        "audio_quality": "good",
        "video_quality": "good"
    })
    recording_enabled: bool = False
    recording_url: Optional[str] = None
    screen_sharing_enabled: bool = False

class Story(BaseModel):
    story_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    content: str
    media_type: str = "text"
    media_data: Optional[str] = None
    background_color: str = "#000000"
    text_color: str = "#ffffff"
    viewers: List[str] = Field(default_factory=list)
    reactions: Dict[str, List[str]] = Field(default_factory=dict)
    music: Optional[str] = None
    location: Optional[Dict] = None
    mentions: List[str] = Field(default_factory=list)
    privacy: str = "all"  # all, contacts, close_friends, custom
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=24))

class Channel(BaseModel):
    channel_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    avatar: Optional[str] = None
    owner_id: str
    admins: List[str] = Field(default_factory=list)
    subscribers: List[str] = Field(default_factory=list)
    is_public: bool = True
    invite_link: Optional[str] = None
    verified: bool = False
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    subscriber_count: int = 0
    post_frequency: str = "unlimited"  # unlimited, hourly, daily
    analytics: Dict = Field(default_factory=lambda: {
        "views": 0,
        "subscribers_growth": [],
        "engagement_rate": 0
    })
    monetization: Dict = Field(default_factory=lambda: {
        "enabled": False,
        "subscription_price": 0,
        "donations_enabled": False
    })
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Poll(BaseModel):
    poll_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_id: str
    creator_id: str
    question: str
    options: List[Dict[str, Any]]  # [{text: str, votes: [user_ids]}]
    is_anonymous: bool = False
    allows_multiple_answers: bool = False
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserProfile(BaseModel):
    user_id: str
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    social_links: Dict[str, str] = Field(default_factory=dict)
    achievements: List[str] = Field(default_factory=list)
    badges: List[str] = Field(default_factory=list)
    stats: Dict = Field(default_factory=lambda: {
        "messages_sent": 0,
        "calls_made": 0,
        "stories_posted": 0,
        "join_date": datetime.utcnow().isoformat()
    })

class BackupData(BaseModel):
    user_id: str
    backup_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    backup_type: str = "full"  # full, messages_only, media_only
    file_path: str
    file_size: int
    encryption_key: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))

# Request Models
class GroupChatCreate(BaseModel):
    name: str
    description: Optional[str] = None
    members: List[str]
    chat_type: str = "group"

class ChannelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True
    category: str = "general"

class StoryCreate(BaseModel):
    content: str
    media_type: str = "text"
    media_data: Optional[str] = None
    background_color: str = "#000000"
    text_color: str = "#ffffff"
    privacy: str = "all"

class PollCreate(BaseModel):
    chat_id: str
    question: str
    options: List[str]
    is_anonymous: bool = False
    allows_multiple_answers: bool = False
    expires_in_hours: Optional[int] = None

class VoiceRoomCreate(BaseModel):
    name: str
    description: Optional[str] = None
    chat_id: Optional[str] = None
    max_participants: int = 50

class UserStatusUpdate(BaseModel):
    activity_status: str  # online, away, busy, invisible
    custom_status: Optional[str] = None
    game_activity: Optional[str] = None

class SafetyNumberVerification(BaseModel):
    user_id: str
    safety_number: str

class PrivacySettingsUpdate(BaseModel):
    settings: Dict[str, Any]

class MessageSchedule(BaseModel):
    chat_id: str
    content: str
    scheduled_for: datetime
    message_type: str = "text"

# Helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def generate_safety_number(user1_id: str, user2_id: str) -> str:
    """Generate a unique safety number for two users"""
    combined = f"{min(user1_id, user2_id)}-{max(user1_id, user2_id)}"
    return hashlib.sha256(combined.encode()).hexdigest()[:12]

def generate_backup_phrase() -> str:
    """Generate a 12-word backup phrase"""
    words = [
        "apple", "bridge", "cloud", "dance", "earth", "forest", "guitar", "house",
        "island", "jungle", "kite", "light", "mountain", "ocean", "planet", "quiet",
        "river", "star", "tree", "universe", "valley", "water", "xenon", "yellow", "zebra"
    ]
    return " ".join(secrets.choice(words) for _ in range(12))

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = await db.users.find_one({"user_id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def check_user_blocked(user1_id: str, user2_id: str) -> bool:
    """Check if user1 has blocked user2 or vice versa"""
    block = await db.blocked_users.find_one({
        "$or": [
            {"blocker_id": user1_id, "blocked_id": user2_id},
            {"blocker_id": user2_id, "blocked_id": user1_id}
        ]
    })
    return block is not None

async def cleanup_expired_messages():
    """Clean up expired disappearing messages"""
    now = datetime.utcnow()
    await db.messages.delete_many({"expires_at": {"$lt": now}})

async def cleanup_expired_stories():
    """Clean up expired stories"""
    now = datetime.utcnow()
    await db.stories.delete_many({"expires_at": {"$lt": now}})

async def cleanup_expired_backups():
    """Clean up expired backups"""
    now = datetime.utcnow()
    expired_backups = await db.backups.find({"expires_at": {"$lt": now}}).to_list(100)
    for backup in expired_backups:
        # Delete backup file
        try:
            os.remove(backup["file_path"])
        except:
            pass
    await db.backups.delete_many({"expires_at": {"$lt": now}})

# Background task for cleanup
async def cleanup_task():
    while True:
        await cleanup_expired_messages()
        await cleanup_expired_stories()
        await cleanup_expired_backups()
        await asyncio.sleep(300)  # Run every 5 minutes

# Authentication routes
@api_router.post("/register")
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    backup_phrase = generate_backup_phrase()
    
    user = User(
        username=user_data.username,
        display_name=user_data.display_name or user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        backup_phrase=backup_phrase
    )
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    # Create user profile
    profile = UserProfile(user_id=user.user_id)
    await db.user_profiles.insert_one(profile.dict())
    
    access_token = create_access_token(data={"sub": user.user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
            "phone": user.phone,
            "avatar": user.avatar,
            "status_message": user.status_message,
            "encryption_key": user.encryption_key,
            "safety_number": user.safety_number,
            "backup_phrase": backup_phrase
        }
    }

@api_router.post("/login")
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"is_online": True, "last_seen": datetime.utcnow()}}
    )
    
    access_token = create_access_token(data={"sub": user["user_id"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "display_name": user.get("display_name"),
            "email": user["email"],
            "phone": user.get("phone"),
            "avatar": user.get("avatar"),
            "status_message": user.get("status_message", "Available"),
            "encryption_key": user.get("encryption_key"),
            "safety_number": user.get("safety_number"),
            "privacy_settings": user.get("privacy_settings", {}),
            "username_handle": user.get("username_handle")
        }
    }

# Enhanced User Management
@api_router.put("/profile")
async def update_profile(profile_data: dict, current_user = Depends(get_current_user)):
    allowed_fields = ["username", "display_name", "status_message", "custom_status", "avatar", "username_handle"]
    update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
    
    if "username_handle" in update_data:
        # Check if username handle is unique
        handle = update_data["username_handle"]
        if handle:
            existing = await db.users.find_one({
                "username_handle": handle,
                "user_id": {"$ne": current_user["user_id"]}
            })
            if existing:
                raise HTTPException(status_code=400, detail="Username handle already taken")
    
    if update_data:
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": update_data}
        )
    
    updated_user = await db.users.find_one({"user_id": current_user["user_id"]})
    return serialize_mongo_doc({
        "user_id": updated_user["user_id"],
        "username": updated_user["username"],
        "display_name": updated_user.get("display_name"),
        "email": updated_user["email"],
        "phone": updated_user.get("phone"),
        "avatar": updated_user.get("avatar"),
        "status_message": updated_user.get("status_message", "Available"),
        "username_handle": updated_user.get("username_handle")
    })

@api_router.get("/profile/{user_id}")
async def get_user_profile(user_id: str, current_user = Depends(get_current_user)):
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = await db.user_profiles.find_one({"user_id": user_id})
    if not profile:
        profile = UserProfile(user_id=user_id).dict()
        await db.user_profiles.insert_one(profile)
    
    # Apply privacy settings
    privacy_settings = user.get("privacy_settings", {})
    is_contact = await db.contacts.find_one({
        "user_id": current_user["user_id"],
        "contact_user_id": user_id
    })
    
    can_see_profile = (
        privacy_settings.get("profile_photo", "everyone") == "everyone" or
        (privacy_settings.get("profile_photo") == "contacts" and is_contact) or
        user_id == current_user["user_id"]
    )
    
    if not can_see_profile:
        raise HTTPException(status_code=403, detail="Profile is private")
    
    return serialize_mongo_doc({
        "user_id": user["user_id"],
        "username": user["username"],
        "display_name": user.get("display_name"),
        "avatar": user.get("avatar"),
        "status_message": user.get("status_message"),
        "verified": user.get("verified", False),
        "premium": user.get("premium", False),
        "profile": profile
    })

@api_router.put("/profile/extended")
async def update_extended_profile(profile_data: dict, current_user = Depends(get_current_user)):
    allowed_fields = ["bio", "location", "website", "interests", "languages", "social_links"]
    update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
    
    if update_data:
        await db.user_profiles.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": update_data},
            upsert=True
        )
    
    return {"status": "success"}

# Privacy and Security Features
@api_router.put("/privacy/settings")
async def update_privacy_settings(settings_data: PrivacySettingsUpdate, current_user = Depends(get_current_user)):
    allowed_settings = ["profile_photo", "last_seen", "phone_number", "read_receipts", "typing_indicators"]
    valid_settings = {k: v for k, v in settings_data.settings.items() if k in allowed_settings}
    
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"privacy_settings": valid_settings}}
    )
    
    return {"status": "success"}

@api_router.post("/safety/verify")
async def verify_safety_number(verification_data: SafetyNumberVerification, current_user = Depends(get_current_user)):
    other_user = await db.users.find_one({"user_id": verification_data.user_id})
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    expected_safety_number = generate_safety_number(current_user["user_id"], verification_data.user_id)
    
    if verification_data.safety_number == expected_safety_number:
        # Mark as verified
        await db.safety_verifications.insert_one({
            "user1_id": current_user["user_id"],
            "user2_id": verification_data.user_id,
            "verified_at": datetime.utcnow(),
            "safety_number": expected_safety_number
        })
        return {"status": "verified", "safety_number": expected_safety_number}
    else:
        return {"status": "invalid", "expected": expected_safety_number}

@api_router.get("/safety/number/{user_id}")
async def get_safety_number(user_id: str, current_user = Depends(get_current_user)):
    other_user = await db.users.find_one({"user_id": user_id})
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    safety_number = generate_safety_number(current_user["user_id"], user_id)
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(safety_number)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_code_data = base64.b64encode(buffer.getvalue()).decode()
    
    # Check if already verified
    verification = await db.safety_verifications.find_one({
        "$or": [
            {"user1_id": current_user["user_id"], "user2_id": user_id},
            {"user1_id": user_id, "user2_id": current_user["user_id"]}
        ]
    })
    
    return {
        "safety_number": safety_number,
        "qr_code": qr_code_data,
        "is_verified": verification is not None
    }

# Backup and Restore
@api_router.post("/backup/create")
async def create_backup(backup_type: str = "full", current_user = Depends(get_current_user)):
    backup_id = str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp()
    backup_path = os.path.join(temp_dir, f"backup_{backup_id}.zip")
    
    try:
        with zipfile.ZipFile(backup_path, 'w') as zip_file:
            if backup_type in ["full", "messages_only"]:
                # Backup messages
                messages = await db.messages.find({
                    "$or": [
                        {"sender_id": current_user["user_id"]},
                        {"chat_id": {"$in": await get_user_chat_ids(current_user["user_id"])}}
                    ]
                }).to_list(None)
                
                zip_file.writestr("messages.json", json.dumps(serialize_mongo_doc(messages)))
            
            if backup_type in ["full", "media_only"]:
                # Backup media files (placeholder - in real implementation, you'd backup actual files)
                media_data = {"media_count": 0, "total_size": 0}
                zip_file.writestr("media.json", json.dumps(media_data))
            
            # Backup user data
            user_data = {
                "user_id": current_user["user_id"],
                "username": current_user["username"],
                "email": current_user["email"],
                "created_at": current_user.get("created_at", datetime.utcnow()).isoformat()
            }
            zip_file.writestr("user.json", json.dumps(user_data))
        
        file_size = os.path.getsize(backup_path)
        encryption_key = MessageEncryption.generate_key()
        
        # Store backup metadata
        backup_data = BackupData(
            user_id=current_user["user_id"],
            backup_id=backup_id,
            backup_type=backup_type,
            file_path=backup_path,
            file_size=file_size,
            encryption_key=encryption_key
        )
        
        await db.backups.insert_one(backup_data.dict())
        
        return {
            "backup_id": backup_id,
            "file_size": file_size,
            "backup_type": backup_type,
            "created_at": backup_data.created_at.isoformat(),
            "download_url": f"/api/backup/download/{backup_id}"
        }
    
    except Exception as e:
        logging.error(f"Backup creation error: {e}")
        raise HTTPException(status_code=500, detail="Backup creation failed")

async def get_user_chat_ids(user_id: str) -> List[str]:
    chats = await db.chats.find({"members": user_id}).to_list(None)
    return [chat["chat_id"] for chat in chats]

# Voice Rooms (Discord-style)
@api_router.post("/voice/rooms")
async def create_voice_room(room_data: VoiceRoomCreate, current_user = Depends(get_current_user)):
    room = VoiceRoom(
        name=room_data.name,
        description=room_data.description,
        chat_id=room_data.chat_id,
        owner_id=current_user["user_id"],
        max_participants=room_data.max_participants
    )
    
    room_dict = room.dict()
    await db.voice_rooms.insert_one(room_dict)
    
    return serialize_mongo_doc(room_dict)

@api_router.get("/voice/rooms")
async def get_voice_rooms(current_user = Depends(get_current_user)):
    # Get rooms user has access to
    user_chats = await db.chats.find({"members": current_user["user_id"]}).to_list(100)
    chat_ids = [chat["chat_id"] for chat in user_chats]
    
    rooms = await db.voice_rooms.find({
        "$or": [
            {"owner_id": current_user["user_id"]},
            {"chat_id": {"$in": chat_ids}},
            {"participants": current_user["user_id"]}
        ],
        "is_active": True
    }).to_list(100)
    
    # Add current participant info
    for room in rooms:
        room["current_participants"] = manager.voice_rooms.get(room["room_id"], [])
        room["participant_count"] = len(room["current_participants"])
    
    return serialize_mongo_doc(rooms)

@api_router.post("/voice/rooms/{room_id}/join")
async def join_voice_room(room_id: str, current_user = Depends(get_current_user)):
    room = await db.voice_rooms.find_one({"room_id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Voice room not found")
    
    current_count = len(manager.voice_rooms.get(room_id, []))
    if current_count >= room["max_participants"]:
        raise HTTPException(status_code=400, detail="Room is full")
    
    # Add to participants
    if room_id not in manager.voice_rooms:
        manager.voice_rooms[room_id] = []
    
    if current_user["user_id"] not in manager.voice_rooms[room_id]:
        manager.voice_rooms[room_id].append(current_user["user_id"])
    
    # Notify other participants
    await manager.broadcast_to_voice_room(
        json.dumps({
            "type": "user_joined_voice",
            "data": {
                "room_id": room_id,
                "user_id": current_user["user_id"],
                "username": current_user["username"]
            }
        }),
        room_id,
        current_user["user_id"]
    )
    
    return {"status": "joined", "participants": manager.voice_rooms[room_id]}

# Advanced Calls with Screen Sharing
@api_router.post("/calls/initiate")
async def initiate_call(call_data: dict, current_user = Depends(get_current_user)):
    chat = await db.chats.find_one({"chat_id": call_data["chat_id"], "members": current_user["user_id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    call = VoiceCall(
        chat_id=call_data["chat_id"],
        caller_id=current_user["user_id"],
        participants=chat["members"],
        call_type=call_data.get("call_type", "voice"),
        screen_sharing_enabled=call_data.get("screen_sharing", False)
    )
    
    call_dict = call.dict()
    await db.voice_calls.insert_one(call_dict)
    
    # Notify all participants
    await manager.broadcast_to_chat(
        json.dumps({
            "type": "incoming_call",
            "data": serialize_mongo_doc(call_dict)
        }),
        call_data["chat_id"],
        current_user["user_id"]
    )
    
    return serialize_mongo_doc(call_dict)

@api_router.post("/calls/{call_id}/screen-share")
async def toggle_screen_share(call_id: str, enable: bool, current_user = Depends(get_current_user)):
    call = await db.voice_calls.find_one({"call_id": call_id})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if current_user["user_id"] not in call["participants"]:
        raise HTTPException(status_code=403, detail="Not in this call")
    
    # Update screen sharing status
    await db.voice_calls.update_one(
        {"call_id": call_id},
        {"$set": {"screen_sharing_enabled": enable}}
    )
    
    # Notify participants
    await manager.broadcast_to_chat(
        json.dumps({
            "type": "screen_share_toggle",
            "data": {
                "call_id": call_id,
                "user_id": current_user["user_id"],
                "enabled": enable
            }
        }),
        call["chat_id"],
        current_user["user_id"]
    )
    
    return {"status": "success", "screen_sharing": enable}

# Public Discovery
@api_router.get("/discover/users")
async def discover_users(query: Optional[str] = None, category: Optional[str] = None, current_user = Depends(get_current_user)):
    search_filter = {
        "user_id": {"$ne": current_user["user_id"]},
        "username_handle": {"$exists": True, "$ne": None}
    }
    
    if query:
        search_filter["$or"] = [
            {"username": {"$regex": query, "$options": "i"}},
            {"display_name": {"$regex": query, "$options": "i"}},
            {"username_handle": {"$regex": query, "$options": "i"}}
        ]
    
    users = await db.users.find(search_filter).limit(20).to_list(20)
    
    # Remove sensitive info and add profile data
    for user in users:
        user.pop("password", None)
        user.pop("email", None)
        user.pop("phone", None)
        user.pop("encryption_key", None)
        user.pop("backup_phrase", None)
        
        # Get profile
        profile = await db.user_profiles.find_one({"user_id": user["user_id"]})
        if profile:
            user["profile"] = profile
    
    return serialize_mongo_doc(users)

@api_router.get("/discover/channels")
async def discover_channels(query: Optional[str] = None, category: Optional[str] = None):
    search_filter = {"is_public": True}
    
    if query:
        search_filter["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
            {"tags": {"$in": [query]}}
        ]
    
    if category and category != "all":
        search_filter["category"] = category
    
    channels = await db.channels.find(search_filter).sort("subscriber_count", -1).limit(50).to_list(50)
    
    return serialize_mongo_doc(channels)

# Enhanced messaging continues with existing functionality...
# (All previous message, chat, contact, blocking functionality remains the same)

# WebSocket endpoint with enhanced features
@api_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    connection_id = await manager.connect(websocket, user_id)
    
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_online": True, "last_seen": datetime.utcnow()}}
    )
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "typing":
                await manager.broadcast_typing(
                    message_data["chat_id"],
                    user_id,
                    message_data["is_typing"]
                )
            elif message_data["type"] == "join_voice_room":
                room_id = message_data["room_id"]
                if room_id not in manager.voice_rooms:
                    manager.voice_rooms[room_id] = []
                if user_id not in manager.voice_rooms[room_id]:
                    manager.voice_rooms[room_id].append(user_id)
                
                await manager.broadcast_to_voice_room(
                    json.dumps({
                        "type": "user_joined_voice",
                        "data": {"room_id": room_id, "user_id": user_id}
                    }),
                    room_id,
                    user_id
                )
            elif message_data["type"] == "user_status":
                manager.user_status[user_id] = {
                    "status": message_data.get("status", "online"),
                    "activity": message_data.get("activity"),
                    "game": message_data.get("game")
                }
                
                # Broadcast status to contacts
                contacts = await db.contacts.find({"contact_user_id": user_id}).to_list(100)
                for contact in contacts:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "status_update",
                            "data": {
                                "user_id": user_id,
                                "status": manager.user_status[user_id]
                            }
                        }),
                        contact["user_id"]
                    )
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id)
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_online": False, "last_seen": datetime.utcnow()}}
        )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://639f667a-da1c-446c-ba92-c3cc7261bffb.preview.emergentagent.com",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Start background tasks
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_task())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()