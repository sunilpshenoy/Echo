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

# Calendar and Workspace Models
class CalendarEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    event_type: str = "meeting"  # meeting, task, reminder, personal, work
    location: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    chat_id: Optional[str] = None  # Associated chat for meeting
    reminder_minutes: int = 15
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None  # daily, weekly, monthly
    workspace_mode: str = "personal"  # personal, business
    priority: str = "medium"  # low, medium, high, urgent
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Task(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"  # low, medium, high, urgent
    status: str = "pending"  # pending, in_progress, completed, cancelled
    assigned_to: Optional[str] = None  # For team tasks
    assignee_user_id: Optional[str] = None
    chat_id: Optional[str] = None  # Associated chat
    workspace_mode: str = "personal"  # personal, business
    tags: List[str] = Field(default_factory=list)
    checklist: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class WorkspaceProfile(BaseModel):
    profile_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    workspace_name: str
    workspace_type: str = "business"  # business, team, organization
    company_name: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    work_email: Optional[str] = None
    work_phone: Optional[str] = None
    business_hours: Dict = Field(default_factory=lambda: {
        "start": "09:00",
        "end": "17:00",
        "timezone": "UTC",
        "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
    })
    notification_settings: Dict = Field(default_factory=lambda: {
        "work_hours_only": True,
        "urgent_always": True,
        "weekend_off": True
    })
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Document(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    content: str
    document_type: str = "text"  # text, markdown, rich_text
    workspace_mode: str = "personal"
    chat_id: Optional[str] = None  # Associated chat
    collaborators: List[str] = Field(default_factory=list)
    permissions: Dict = Field(default_factory=lambda: {
        "public_read": False,
        "team_edit": False,
        "owner_only": True
    })
    version_history: List[Dict] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Request Models for Calendar/Workspace
class CalendarEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    event_type: str = "meeting"
    location: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    chat_id: Optional[str] = None
    reminder_minutes: int = 15
    workspace_mode: str = "personal"
    priority: str = "medium"

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"
    assigned_to: Optional[str] = None
    chat_id: Optional[str] = None
    workspace_mode: str = "personal"
    tags: List[str] = Field(default_factory=list)
    estimated_hours: Optional[float] = None

class WorkspaceProfileCreate(BaseModel):
    workspace_name: str
    workspace_type: str = "business"
    company_name: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    work_email: Optional[str] = None
    work_phone: Optional[str] = None

class DocumentCreate(BaseModel):
    title: str
    content: str
    document_type: str = "text"
    workspace_mode: str = "personal"
    chat_id: Optional[str] = None
    collaborators: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

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

# Core Chat Management Endpoints
@api_router.get("/chats")
async def get_chats(current_user = Depends(get_current_user)):
    """Get all chats for the current user"""
    chats = await db.chats.find({
        "members": current_user["user_id"]
    }).to_list(100)
    
    # Get last message for each chat and serialize
    for chat in chats:
        if chat.get("last_message"):
            # Get the actual last message
            last_msg = await db.messages.find_one(
                {"chat_id": chat["chat_id"]},
                sort=[("timestamp", -1)]
            )
            if last_msg:
                chat["last_message"] = serialize_mongo_doc(last_msg)
        
        # Get other chat member info for direct chats
        if chat.get("chat_type") == "direct":
            other_member_id = next(
                (member for member in chat["members"] if member != current_user["user_id"]), 
                None
            )
            if other_member_id:
                other_user = await db.users.find_one({"user_id": other_member_id})
                if other_user:
                    chat["other_user"] = {
                        "user_id": other_user["user_id"],
                        "username": other_user["username"],
                        "display_name": other_user.get("display_name"),
                        "avatar": other_user.get("avatar"),
                        "status_message": other_user.get("status_message"),
                        "is_online": other_user.get("is_online", False)
                    }
    
    return serialize_mongo_doc(chats)

@api_router.post("/chats")
async def create_chat(chat_data: dict, current_user = Depends(get_current_user)):
    """Create a new chat"""
    if chat_data.get("chat_type") == "direct":
        # Create direct chat
        other_user_id = chat_data.get("other_user_id")
        if not other_user_id:
            raise HTTPException(status_code=400, detail="other_user_id required for direct chat")
        
        # Check if direct chat already exists
        existing_chat = await db.chats.find_one({
            "chat_type": "direct",
            "members": {"$all": [current_user["user_id"], other_user_id]}
        })
        if existing_chat:
            return serialize_mongo_doc(existing_chat)
        
        # Check if users are blocked
        block_check = await db.blocked_users.find_one({
            "$or": [
                {"user_id": current_user["user_id"], "blocked_user_id": other_user_id},
                {"user_id": other_user_id, "blocked_user_id": current_user["user_id"]}
            ]
        })
        if block_check:
            raise HTTPException(status_code=403, detail="Cannot create chat with blocked user")
        
        chat = Chat(
            chat_type="direct",
            members=[current_user["user_id"], other_user_id],
            admins=[current_user["user_id"]],
            created_by=current_user["user_id"]
        )
    elif chat_data.get("chat_type") == "group":
        # Create group chat
        members = chat_data.get("members", [])
        if not members:
            raise HTTPException(status_code=400, detail="Members required for group chat")
        
        # Add current user to members if not already included
        if current_user["user_id"] not in members:
            members.append(current_user["user_id"])
        
        chat = Chat(
            chat_type="group",
            name=chat_data.get("name", "New Group"),
            description=chat_data.get("description"),
            members=members,
            admins=[current_user["user_id"]],
            created_by=current_user["user_id"]
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid chat_type")
    
    chat_dict = chat.dict()
    await db.chats.insert_one(chat_dict)
    
    # Notify other members via WebSocket
    for member_id in chat.members:
        if member_id != current_user["user_id"]:
            await manager.send_personal_message(
                json.dumps({
                    "type": "new_chat",
                    "data": serialize_mongo_doc(chat_dict)
                }),
                member_id
            )
    
    return serialize_mongo_doc(chat_dict)

@api_router.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: str, current_user = Depends(get_current_user)):
    """Get messages for a specific chat"""
    # Verify user is member of chat
    chat = await db.chats.find_one({"chat_id": chat_id})
    if not chat or current_user["user_id"] not in chat["members"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    messages = await db.messages.find({
        "chat_id": chat_id,
        "is_deleted": {"$ne": True}
    }).sort("timestamp", 1).to_list(1000)
    
    # Decrypt messages if user has access
    for message in messages:
        if message.get("is_encrypted") and message.get("encrypted_content"):
            user_key = current_user.get("encryption_key")
            if user_key:
                try:
                    decrypted = MessageEncryption.decrypt_message(
                        message["encrypted_content"], 
                        user_key
                    )
                    message["content"] = decrypted
                except:
                    message["content"] = "[Encrypted Message]"
    
    return serialize_mongo_doc(messages)

@api_router.post("/chats/{chat_id}/messages")
async def send_message(chat_id: str, message_data: dict, current_user = Depends(get_current_user)):
    """Send a message to a chat"""
    # Verify user is member of chat
    chat = await db.chats.find_one({"chat_id": chat_id})
    if not chat or current_user["user_id"] not in chat["members"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check for blocks in direct chats
    if chat.get("chat_type") == "direct":
        other_user_id = next(
            (member for member in chat["members"] if member != current_user["user_id"]), 
            None
        )
        if other_user_id:
            block_check = await db.blocked_users.find_one({
                "$or": [
                    {"user_id": current_user["user_id"], "blocked_user_id": other_user_id},
                    {"user_id": other_user_id, "blocked_user_id": current_user["user_id"]}
                ]
            })
            if block_check:
                raise HTTPException(status_code=403, detail="Cannot send message to blocked user")
    
    # Create message
    message = Message(
        chat_id=chat_id,
        sender_id=current_user["user_id"],
        content=message_data.get("content", ""),
        message_type=message_data.get("message_type", "text"),
        file_name=message_data.get("file_name"),
        file_size=message_data.get("file_size"),
        file_data=message_data.get("file_data"),
        voice_duration=message_data.get("voice_duration"),
        reply_to=message_data.get("reply_to"),
        scheduled_for=message_data.get("scheduled_for")
    )
    
    # Encrypt message content if enabled
    if chat.get("encryption_enabled", True) and message.content:
        user_key = current_user.get("encryption_key")
        if user_key:
            message.encrypted_content = MessageEncryption.encrypt_message(
                message.content, 
                user_key
            )
            message.is_encrypted = True
    
    # Set expiration for disappearing messages
    if chat.get("disappearing_timer"):
        message.expires_at = datetime.utcnow() + timedelta(seconds=chat["disappearing_timer"])
    
    message_dict = message.dict()
    await db.messages.insert_one(message_dict)
    
    # Update chat's last message
    await db.chats.update_one(
        {"chat_id": chat_id},
        {"$set": {"last_message": message_dict}}
    )
    
    # Broadcast to chat members via WebSocket
    for member_id in chat["members"]:
        await manager.send_personal_message(
            json.dumps({
                "type": "new_message",
                "data": serialize_mongo_doc(message_dict)
            }),
            member_id
        )
    
    return serialize_mongo_doc(message_dict)

# Contact Management Endpoints
@api_router.get("/contacts")
async def get_contacts(current_user = Depends(get_current_user)):
    """Get all contacts for the current user"""
    contacts = await db.contacts.find({
        "user_id": current_user["user_id"]
    }).to_list(100)
    
    # Get contact user details
    for contact in contacts:
        user = await db.users.find_one({"user_id": contact["contact_user_id"]})
        if user:
            contact["contact_user"] = {
                "user_id": user["user_id"],
                "username": user["username"],
                "display_name": user.get("display_name"),
                "avatar": user.get("avatar"),
                "status_message": user.get("status_message"),
                "is_online": user.get("is_online", False)
            }
    
    return serialize_mongo_doc(contacts)

@api_router.post("/contacts")
async def add_contact(contact_data: dict, current_user = Depends(get_current_user)):
    """Add a new contact"""
    email = contact_data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    # Find user by email
    contact_user = await db.users.find_one({"email": email})
    if not contact_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if contact_user["user_id"] == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot add yourself as contact")
    
    # Check if already a contact
    existing = await db.contacts.find_one({
        "user_id": current_user["user_id"],
        "contact_user_id": contact_user["user_id"]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already a contact")
    
    # Check if blocked
    block_check = await db.blocked_users.find_one({
        "$or": [
            {"user_id": current_user["user_id"], "blocked_user_id": contact_user["user_id"]},
            {"user_id": contact_user["user_id"], "blocked_user_id": current_user["user_id"]}
        ]
    })
    if block_check:
        raise HTTPException(status_code=403, detail="Cannot add blocked user as contact")
    
    # Create contact
    contact = {
        "contact_id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "contact_user_id": contact_user["user_id"],
        "contact_name": contact_data.get("contact_name", contact_user["username"]),
        "added_at": datetime.utcnow()
    }
    
    await db.contacts.insert_one(contact)
    
    # Add contact user details for response
    contact["contact_user"] = {
        "user_id": contact_user["user_id"],
        "username": contact_user["username"],
        "display_name": contact_user.get("display_name"),
        "avatar": contact_user.get("avatar"),
        "status_message": contact_user.get("status_message"),
        "is_online": contact_user.get("is_online", False)
    }
    
    return serialize_mongo_doc(contact)

# User Blocking Management
@api_router.get("/users/blocked")
async def get_blocked_users(current_user = Depends(get_current_user)):
    """Get all blocked users for the current user"""
    blocked = await db.blocked_users.find({
        "user_id": current_user["user_id"]
    }).to_list(100)
    
    # Get blocked user details
    for block in blocked:
        user = await db.users.find_one({"user_id": block["blocked_user_id"]})
        if user:
            block["blocked_user"] = {
                "user_id": user["user_id"],
                "username": user["username"],
                "display_name": user.get("display_name"),
                "avatar": user.get("avatar")
            }
    
    return serialize_mongo_doc(blocked)

@api_router.post("/users/{user_id}/block")
async def block_user(user_id: str, current_user = Depends(get_current_user)):
    """Block a user"""
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
    
    # Check if user exists
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if already blocked
    existing = await db.blocked_users.find_one({
        "user_id": current_user["user_id"],
        "blocked_user_id": user_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="User already blocked")
    
    # Create block record
    block = {
        "block_id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "blocked_user_id": user_id,
        "blocked_at": datetime.utcnow()
    }
    
    await db.blocked_users.insert_one(block)
    
    # Remove from contacts if exists
    await db.contacts.delete_one({
        "user_id": current_user["user_id"],
        "contact_user_id": user_id
    })
    
    return {"message": "User blocked successfully"}

@api_router.delete("/users/{user_id}/block")
async def unblock_user(user_id: str, current_user = Depends(get_current_user)):
    """Unblock a user"""
    result = await db.blocked_users.delete_one({
        "user_id": current_user["user_id"],
        "blocked_user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not blocked")
    
    return {"message": "User unblocked successfully"}

# User Reporting
@api_router.post("/users/{user_id}/report")
async def report_user(user_id: str, report_data: dict, current_user = Depends(get_current_user)):
    """Report a user"""
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot report yourself")
    
    # Check if user exists
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create report
    report = {
        "report_id": str(uuid.uuid4()),
        "reporter_id": current_user["user_id"],
        "reported_user_id": user_id,
        "reason": report_data.get("reason", "other"),
        "description": report_data.get("description", ""),
        "message_id": report_data.get("message_id"),
        "chat_id": report_data.get("chat_id"),
        "status": "pending",
        "reported_at": datetime.utcnow()
    }
    
    await db.user_reports.insert_one(report)
    
    return {"message": "User reported successfully"}

# Stories Management
@api_router.get("/stories")
async def get_stories(current_user = Depends(get_current_user)):
    """Get stories from contacts and followed users"""
    # Get user's contacts
    contacts = await db.contacts.find({
        "user_id": current_user["user_id"]
    }).to_list(100)
    
    contact_ids = [contact["contact_user_id"] for contact in contacts]
    contact_ids.append(current_user["user_id"])  # Include own stories
    
    # Get non-expired stories
    now = datetime.utcnow()
    stories = await db.stories.find({
        "user_id": {"$in": contact_ids},
        "expires_at": {"$gt": now}
    }).sort("created_at", -1).to_list(100)
    
    # Get story owner details
    for story in stories:
        user = await db.users.find_one({"user_id": story["user_id"]})
        if user:
            story["user"] = {
                "user_id": user["user_id"],
                "username": user["username"],
                "display_name": user.get("display_name"),
                "avatar": user.get("avatar")
            }
    
    return serialize_mongo_doc(stories)

@api_router.post("/stories")
async def create_story(story_data: dict, current_user = Depends(get_current_user)):
    """Create a new story"""
    story = {
        "story_id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "content": story_data.get("content", ""),
        "media_type": story_data.get("media_type", "text"),
        "media_data": story_data.get("media_data"),
        "background_color": story_data.get("background_color", "#000000"),
        "text_color": story_data.get("text_color", "#ffffff"),
        "privacy": story_data.get("privacy", "all"),
        "viewers": [],
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }
    
    await db.stories.insert_one(story)
    
    return serialize_mongo_doc(story)

@api_router.put("/stories/{story_id}/view")
async def view_story(story_id: str, current_user = Depends(get_current_user)):
    """Mark a story as viewed"""
    story = await db.stories.find_one({"story_id": story_id})
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # Check if story is expired
    if story["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=404, detail="Story expired")
    
    # Add viewer if not already viewed
    if current_user["user_id"] not in story.get("viewers", []):
        await db.stories.update_one(
            {"story_id": story_id},
            {"$push": {"viewers": current_user["user_id"]}}
        )
    
    return {"message": "Story viewed"}

# Channels Management  
@api_router.get("/channels")
async def get_channels(current_user = Depends(get_current_user)):
    """Get channels the user has subscribed to"""
    channels = await db.channels.find({
        "subscribers": current_user["user_id"]
    }).to_list(100)
    
    # Get channel owner details
    for channel in channels:
        owner = await db.users.find_one({"user_id": channel["owner_id"]})
        if owner:
            channel["owner"] = {
                "user_id": owner["user_id"],
                "username": owner["username"],
                "display_name": owner.get("display_name"),
                "avatar": owner.get("avatar")
            }
    
    return serialize_mongo_doc(channels)

@api_router.post("/channels")
async def create_channel(channel_data: dict, current_user = Depends(get_current_user)):
    """Create a new channel"""
    channel = {
        "channel_id": str(uuid.uuid4()),
        "name": channel_data.get("name", "New Channel"),
        "description": channel_data.get("description", ""),
        "owner_id": current_user["user_id"],
        "admins": [current_user["user_id"]],
        "subscribers": [current_user["user_id"]],
        "is_public": channel_data.get("is_public", True),
        "category": channel_data.get("category", "general"),
        "created_at": datetime.utcnow()
    }
    
    await db.channels.insert_one(channel)
    
    return serialize_mongo_doc(channel)

@api_router.post("/channels/{channel_id}/subscribe")
async def subscribe_to_channel(channel_id: str, current_user = Depends(get_current_user)):
    """Subscribe to a channel"""
    channel = await db.channels.find_one({"channel_id": channel_id})
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    if current_user["user_id"] not in channel.get("subscribers", []):
        await db.channels.update_one(
            {"channel_id": channel_id},
            {"$push": {"subscribers": current_user["user_id"]}}
        )
    
    return {"message": "Subscribed to channel"}

# Message Management
@api_router.put("/messages/{message_id}/react")
async def react_to_message(message_id: str, reaction_data: dict, current_user = Depends(get_current_user)):
    """Add or remove reaction from a message"""
    message = await db.messages.find_one({"message_id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Verify user has access to the chat
    chat = await db.chats.find_one({"chat_id": message["chat_id"]})
    if not chat or current_user["user_id"] not in chat["members"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    emoji = reaction_data.get("emoji")
    if not emoji:
        raise HTTPException(status_code=400, detail="Emoji required")
    
    # Get current reactions
    reactions = message.get("reactions", {})
    
    # Toggle reaction
    if emoji in reactions:
        if current_user["user_id"] in reactions[emoji]:
            reactions[emoji].remove(current_user["user_id"])
            if not reactions[emoji]:
                del reactions[emoji]
        else:
            reactions[emoji].append(current_user["user_id"])
    else:
        reactions[emoji] = [current_user["user_id"]]
    
    await db.messages.update_one(
        {"message_id": message_id},
        {"$set": {"reactions": reactions}}
    )
    
    # Broadcast reaction update
    for member_id in chat["members"]:
        await manager.send_personal_message(
            json.dumps({
                "type": "message_reaction",
                "data": {
                    "message_id": message_id,
                    "reactions": reactions,
                    "user_id": current_user["user_id"],
                    "emoji": emoji
                }
            }),
            member_id
        )
    
    return {"message": "Reaction updated"}

@api_router.put("/messages/{message_id}/edit")
async def edit_message(message_id: str, edit_data: dict, current_user = Depends(get_current_user)):
    """Edit a message"""
    message = await db.messages.find_one({"message_id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message["sender_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only edit your own messages")
    
    new_content = edit_data.get("content", "")
    if not new_content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    
    # Update message
    await db.messages.update_one(
        {"message_id": message_id},
        {"$set": {
            "content": new_content,
            "edited_at": datetime.utcnow()
        }}
    )
    
    # Broadcast edit
    chat = await db.chats.find_one({"chat_id": message["chat_id"]})
    if chat:
        for member_id in chat["members"]:
            await manager.send_personal_message(
                json.dumps({
                    "type": "message_edit",
                    "data": {
                        "message_id": message_id,
                        "content": new_content,
                        "edited_at": datetime.utcnow().isoformat()
                    }
                }),
                member_id
            )
    
    return {"message": "Message edited"}

@api_router.delete("/messages/{message_id}")
async def delete_message(message_id: str, current_user = Depends(get_current_user)):
    """Delete a message"""
    message = await db.messages.find_one({"message_id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message["sender_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Can only delete your own messages")
    
    # Soft delete
    await db.messages.update_one(
        {"message_id": message_id},
        {"$set": {"is_deleted": True}}
    )
    
    # Broadcast deletion
    chat = await db.chats.find_one({"chat_id": message["chat_id"]})
    if chat:
        for member_id in chat["members"]:
            await manager.send_personal_message(
                json.dumps({
                    "type": "message_delete",
                    "data": {"message_id": message_id}
                }),
                member_id
            )
    
    return {"message": "Message deleted"}

# File Upload
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    """Upload a file and return base64 data"""
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large")
    
    file_content = await file.read()
    file_base64 = base64.b64encode(file_content).decode()
    
    return {
        "file_name": file.filename,
        "file_size": file.size,
        "file_type": file.content_type,
        "file_data": file_base64
    }

# User Search and Discovery
@api_router.get("/users/search")
async def search_users(query: str, current_user = Depends(get_current_user)):
    """Search for users by username or email"""
    if len(query) < 2:
        return []
    
    users = await db.users.find({
        "$or": [
            {"username": {"$regex": query, "$options": "i"}},
            {"email": {"$regex": query, "$options": "i"}},
            {"display_name": {"$regex": query, "$options": "i"}}
        ],
        "user_id": {"$ne": current_user["user_id"]}
    }).limit(20).to_list(20)
    
    # Remove sensitive data and add contact/block status
    result = []
    for user in users:
        # Check if blocked
        is_blocked = await db.blocked_users.find_one({
            "$or": [
                {"user_id": current_user["user_id"], "blocked_user_id": user["user_id"]},
                {"user_id": user["user_id"], "blocked_user_id": current_user["user_id"]}
            ]
        })
        
        # Check if contact
        is_contact = await db.contacts.find_one({
            "user_id": current_user["user_id"],
            "contact_user_id": user["user_id"]
        })
        
        result.append({
            "user_id": user["user_id"],
            "username": user["username"],
            "display_name": user.get("display_name"),
            "avatar": user.get("avatar"),
            "status_message": user.get("status_message"),
            "is_online": user.get("is_online", False),
            "is_blocked": bool(is_blocked),
            "is_contact": bool(is_contact)
        })
    
    return result

# Genie Assistant NLP and Action Processing
@api_router.post("/genie/process")
async def process_genie_command(command_data: dict, current_user = Depends(get_current_user)):
    """Process natural language commands from the Genie Assistant"""
    command = command_data.get("command", "").lower().strip()
    user_id = current_user["user_id"]
    context = command_data.get("current_context", {})
    
    # Natural Language Processing and Intent Recognition
    intent, entities, action, confirmation_needed = await analyze_command(command, user_id, context)
    
    # Generate genie-style response
    response_text = generate_genie_response(intent, entities, action, confirmation_needed)
    
    # Log the interaction
    interaction_id = str(uuid.uuid4())
    await db.genie_interactions.insert_one({
        "interaction_id": interaction_id,
        "user_id": user_id,
        "command": command,
        "intent": intent,
        "entities": entities,
        "action": action,
        "response": response_text,
        "timestamp": datetime.utcnow(),
        "context": context
    })
    
    # Execute the action regardless of confirmation_needed for testing purposes
    if action:
        await execute_genie_action(action, user_id, interaction_id)
    
    return {
        "intent": intent,
        "entities": entities,
        "response_text": response_text,
        "action": action,
        "confirmation_needed": confirmation_needed
    }

async def execute_genie_action(action: dict, user_id: str, interaction_id: str = None):
    """Execute actions from Genie commands"""
    if not action:
        return
        
    action_type = action.get("type")
    result = None
    
    try:
        if action_type == "add_contact":
            # Add contact
            contact_info = action.get("contact_info")
            logging.info(f"Executing add_contact action with contact_info: {contact_info}")
            if "@" in contact_info:  # Assume it's an email
                user = await db.users.find_one({"email": contact_info})
                if user:
                    logging.info(f"Found user with email {contact_info}: {user.get('username')}")
                    # Check if already a contact
                    existing = await db.contacts.find_one({
                        "user_id": user_id,
                        "contact_user_id": user["user_id"]
                    })
                    
                    if not existing and user["user_id"] != user_id:
                        contact = {
                            "contact_id": str(uuid.uuid4()),
                            "user_id": user_id,
                            "contact_user_id": user["user_id"],
                            "contact_name": user.get("username"),
                            "added_at": datetime.utcnow(),
                            "added_by_genie": True,
                            "interaction_id": interaction_id
                        }
                        result = await db.contacts.insert_one(contact)
                        logging.info(f"Added contact: {contact}")
                    else:
                        logging.info(f"Contact already exists or trying to add self as contact")
                else:
                    logging.info(f"No user found with email {contact_info}")
            else:
                logging.info(f"Contact info doesn't contain an email: {contact_info}")
        
        elif action_type == "block_user":
            # Block user
            target_user = action.get("target_user")
            user = await db.users.find_one({"username": {"$regex": f"^{target_user}$", "$options": "i"}})
            
            if user and user["user_id"] != user_id:
                # Check if already blocked
                existing = await db.blocked_users.find_one({
                    "user_id": user_id,
                    "blocked_user_id": user["user_id"]
                })
                
                if not existing:
                    block = {
                        "block_id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "blocked_user_id": user["user_id"],
                        "blocked_at": datetime.utcnow(),
                        "blocked_by_genie": True,
                        "interaction_id": interaction_id
                    }
                    result = await db.blocked_users.insert_one(block)
        
        elif action_type == "list_chats":
            # No action needed, just for display
            pass
            
        elif action_type == "list_contacts":
            # No action needed, just for display
            pass
            
        # Update the interaction with the result
        if interaction_id and result:
            await db.genie_interactions.update_one(
                {"interaction_id": interaction_id},
                {"$set": {"action_result": str(result)}}
            )
            
    except Exception as e:
        logging.error(f"Error executing genie action: {e}")

@api_router.post("/genie/undo")
async def undo_last_action(current_user = Depends(get_current_user)):
    """Undo the last action performed by the genie"""
    user_id = current_user["user_id"]
    
    # Get the last action that can be undone
    last_action = await db.genie_interactions.find_one(
        {
            "user_id": user_id,
            "action": {"$ne": None},
            "undone": {"$ne": True}
        },
        sort=[("timestamp", -1)]
    )
    
    if not last_action:
        return {
            "success": False,
            "message": "🧞‍♂️ *Mystical search complete* No recent actions found to undo, master!"
        }
    
    # Perform the undo operation
    undo_result = await perform_undo(last_action["action"], user_id)
    
    if undo_result["success"]:
        # Mark action as undone
        await db.genie_interactions.update_one(
            {"interaction_id": last_action.get("interaction_id", last_action["_id"])},
            {"$set": {"undone": True, "undone_at": datetime.utcnow()}}
        )
        
        return {
            "success": True,
            "message": f"🧞‍♂️ *Waves magical hands* ✨ {undo_result['message']}"
        }
    else:
        return {
            "success": False,
            "message": f"🧞‍♂️ *Mystical interference detected* {undo_result['message']}"
        }
        return {
            "success": False,
            "message": f"🧞‍♂️ *Mystical interference detected* {undo_result['message']}"
        }

async def analyze_command(command: str, user_id: str, context: dict):
    """Analyze natural language command and extract intent, entities, and actions"""
    
    # Define intent patterns and their corresponding actions
    intent_patterns = {
        # Message Actions
        "send_message": [
            r"send.*message.*to (.+?).*saying (.+)",
            r"tell (.+?).*that (.+)",
            r"message (.+?).*saying (.+)",
            r"send (.+?).*message (.+)"
        ],
        
        # Chat Management
        "create_chat": [
            r"create.*chat.*with (.+)",
            r"start.*conversation.*with (.+)",
            r"new.*chat.*(.+)",
            r"talk.*to (.+)"
        ],
        "create_group": [
            r"create.*group.*called (.+)",
            r"make.*group.*(.+)",
            r"new.*group.*(.+)",
            r"start.*group.*(.+)"
        ],
        
        # Contact Management
        "add_contact": [
            r"add.*contact.*(.+)",
            r"add (.+@.+).*as.*contact",
            r"save.*contact.*(.+)",
            r"new.*contact.*(.+)"
        ],
        "find_contact": [
            r"find.*contact.*(.+)",
            r"search.*(.+)",
            r"look.*for.*(.+)"
        ],
        
        # Message Actions
        "send_message": [
            r"send.*message.*to (.+?).*saying (.+)",
            r"tell (.+?).*that (.+)",
            r"message (.+?).*saying (.+)",
            r"send (.+?).*message (.+)"
        ],
        
        # User Management
        "block_user": [
            r"block.*user.*(.+)",
            r"block (.+)",
            r"stop.*(.+).*messaging"
        ],
        "unblock_user": [
            r"unblock.*(.+)",
            r"remove.*block.*(.+)"
        ],
        
        # Stories and Social
        "create_story": [
            r"create.*story.*(.+)",
            r"post.*story.*(.+)",
            r"new.*story.*(.+)"
        ],
        
        # App Navigation and Help
        "show_help": [
            r"help.*",
            r"what.*can.*you.*do",
            r"features",
            r"how.*to.*",
            r"guide"
        ],
        "show_settings": [
            r"settings",
            r"preferences",
            r"configure"
        ],
        
        # General queries
        "list_chats": [
            r"show.*chats",
            r"my.*conversations",
            r"list.*chats"
        ],
        "list_contacts": [
            r"show.*contacts",
            r"my.*contacts",
            r"friends"
        ]
    }
    
    # Analyze command for intent and entities
    intent = "unknown"
    entities = {}
    action = None
    confirmation_needed = False
    
    import re
    
    for intent_name, patterns in intent_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                intent = intent_name
                entities = {"groups": match.groups()}
                break
        if intent != "unknown":
            break
    
    # Create action based on intent
    if intent == "create_chat":
        target_user = entities["groups"][0] if entities.get("groups") else None
        action = {
            "type": "create_chat",
            "target_user": target_user,
            "chat_type": "direct"
        }
        confirmation_needed = True
        
    elif intent == "create_group":
        group_name = entities["groups"][0] if entities.get("groups") else "New Group"
        action = {
            "type": "create_group",
            "name": group_name
        }
        confirmation_needed = True
        
    elif intent == "add_contact":
        contact_info = entities["groups"][0] if entities.get("groups") else None
        action = {
            "type": "add_contact",
            "contact_info": contact_info
        }
        confirmation_needed = True
        
    elif intent == "send_message":
        groups = entities.get("groups", [])
        if len(groups) >= 2:
            action = {
                "type": "send_message",
                "recipient": groups[0],
                "message": groups[1]
            }
            confirmation_needed = True
            
    elif intent == "block_user":
        user_to_block = entities["groups"][0] if entities.get("groups") else None
        action = {
            "type": "block_user",
            "target_user": user_to_block
        }
        confirmation_needed = True
        
    elif intent in ["list_chats", "list_contacts", "show_help", "show_settings"]:
        action = {
            "type": intent
        }
        confirmation_needed = False
    
    return intent, entities, action, confirmation_needed

def generate_genie_response(intent: str, entities: dict, action: dict, confirmation_needed: bool) -> str:
    """Generate genie-style responses based on intent and action"""
    
    genie_responses = {
        "create_chat": "I shall conjure a mystical conversation portal with {target}!",
        "create_group": "Behold! I shall weave together souls into a magnificent group called '{name}'!",
        "add_contact": "Your wish to befriend {contact} shall be my command!",
        "send_message": "I shall deliver your message '{message}' to {recipient} with the speed of magical winds!",
        "block_user": "I shall cast a protective barrier against {user}!",
        "unblock_user": "The mystical barrier against {user} shall be lifted!",
        "list_chats": "*Gazing into the crystal ball* I see all your conversations materializing before you!",
        "list_contacts": "*Summoning contact spirits* Your friends shall appear before your eyes!",
        "show_help": "Ah, a wise seeker of knowledge! Let me illuminate the magical possibilities of this realm!",
        "show_settings": "I shall open the sacred settings scroll for your customization!",
        "create_story": "Your tale '{story}' shall be woven into the fabric of time for all to witness!",
        "unknown": "Hmm... *strokes mystical beard* Your wish is unclear to me, master. Could you rephrase your desire?"
    }
    
    base_response = genie_responses.get(intent, genie_responses["unknown"])
    
    # Replace placeholders with actual entities
    if action and entities.get("groups"):
        if intent == "create_chat":
            base_response = base_response.format(target=entities["groups"][0])
        elif intent == "create_group":
            base_response = base_response.format(name=entities["groups"][0])
        elif intent == "add_contact":
            base_response = base_response.format(contact=entities["groups"][0])
        elif intent == "send_message" and len(entities["groups"]) >= 2:
            base_response = base_response.format(
                recipient=entities["groups"][0],
                message=entities["groups"][1]
            )
        elif intent in ["block_user", "unblock_user"]:
            base_response = base_response.format(user=entities["groups"][0])
        elif intent == "create_story":
            base_response = base_response.format(story=entities["groups"][0])
    
    return base_response

async def perform_undo(action: dict, user_id: str):
    """Perform undo operations for various actions"""
    
    action_type = action.get("type")
    logging.info(f"Performing undo for action type: {action_type}")
    
    try:
        if action_type == "create_chat":
            # Find and delete the most recent chat created by this user
            recent_chat = await db.chats.find_one(
                {"created_by": user_id},
                sort=[("created_at", -1)]
            )
            if recent_chat:
                await db.chats.delete_one({"chat_id": recent_chat["chat_id"]})
                return {"success": True, "message": "The mystical conversation portal has been dissolved!"}
            else:
                return {"success": False, "message": "No recent chat found to undo!"}
            
        elif action_type == "add_contact":
            # Find and remove the most recent contact added by Genie
            logging.info(f"Looking for contacts added by Genie for user: {user_id}")
            recent_contact = await db.contacts.find_one(
                {"user_id": user_id, "added_by_genie": True},
                sort=[("added_at", -1)]
            )
            
            if recent_contact:
                logging.info(f"Found contact to undo: {recent_contact}")
                await db.contacts.delete_one({"contact_id": recent_contact["contact_id"]})
                return {"success": True, "message": "The friendship bond has been gently severed!"}
            else:
                # Try without the added_by_genie flag as fallback
                logging.info("No contacts with added_by_genie flag found, trying without flag")
                recent_contact = await db.contacts.find_one(
                    {"user_id": user_id},
                    sort=[("added_at", -1)]
                )
                
                if recent_contact:
                    logging.info(f"Found contact without flag to undo: {recent_contact}")
                    await db.contacts.delete_one({"contact_id": recent_contact["contact_id"]})
                    return {"success": True, "message": "The friendship bond has been gently severed!"}
                else:
                    logging.info("No contacts found to undo")
                    return {"success": False, "message": "No recent contact found to undo!"}
                
        elif action_type == "block_user":
            # Find and remove the most recent block added by Genie
            recent_block = await db.blocked_users.find_one(
                {"user_id": user_id, "blocked_by_genie": True},
                sort=[("blocked_at", -1)]
            )
            if recent_block:
                await db.blocked_users.delete_one({"block_id": recent_block["block_id"]})
                return {"success": True, "message": "The protective barrier has been lifted!"}
            else:
                return {"success": False, "message": "No recent block found to undo!"}
                
        elif action_type == "send_message":
            # Find and soft-delete the most recent message
            recent_message = await db.messages.find_one(
                {"sender_id": user_id},
                sort=[("timestamp", -1)]
            )
            if recent_message:
                await db.messages.update_one(
                    {"message_id": recent_message["message_id"]},
                    {"$set": {"is_deleted": True, "deleted_by_genie": True}}
                )
                return {"success": True, "message": "Your message has vanished into the mystical void!"}
            else:
                return {"success": False, "message": "No recent message found to undo!"}
        
        elif action_type == "create_story":
            # Find and delete the most recent story
            recent_story = await db.stories.find_one(
                {"user_id": user_id},
                sort=[("created_at", -1)]
            )
            if recent_story:
                await db.stories.delete_one({"story_id": recent_story["story_id"]})
                return {"success": True, "message": "Your mystical tale has been erased from time!"}
            else:
                return {"success": False, "message": "No recent story found to undo!"}
        
        return {"success": False, "message": "This magic is beyond my powers to reverse, master."}
        
    except Exception as e:
        logging.error(f"Error in perform_undo: {str(e)}")
        return {"success": False, "message": f"The mystical forces are in chaos: {str(e)}"}

# Calendar and Workspace API Endpoints

@api_router.post("/calendar/events")
async def create_calendar_event(event_data: CalendarEventCreate, current_user = Depends(get_current_user)):
    """Create a new calendar event"""
    event = CalendarEvent(
        user_id=current_user["user_id"],
        **event_data.dict()
    )
    
    event_dict = event.dict()
    await db.calendar_events.insert_one(event_dict)
    
    # Notify attendees if any
    if event.attendees:
        for attendee_id in event.attendees:
            await manager.send_personal_message(
                json.dumps({
                    "type": "calendar_invite",
                    "data": serialize_mongo_doc(event_dict)
                }),
                attendee_id
            )
    
    return serialize_mongo_doc(event_dict)

@api_router.get("/calendar/events")
async def get_calendar_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    workspace_mode: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get calendar events for the user"""
    query = {"user_id": current_user["user_id"]}
    
    if workspace_mode:
        query["workspace_mode"] = workspace_mode
    
    if start_date and end_date:
        query["start_time"] = {
            "$gte": datetime.fromisoformat(start_date.replace('Z', '+00:00')),
            "$lte": datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        }
    
    events = await db.calendar_events.find(query).sort("start_time", 1).to_list(100)
    return serialize_mongo_doc(events)

@api_router.put("/calendar/events/{event_id}")
async def update_calendar_event(
    event_id: str,
    event_data: dict,
    current_user = Depends(get_current_user)
):
    """Update a calendar event"""
    event = await db.calendar_events.find_one({
        "event_id": event_id,
        "user_id": current_user["user_id"]
    })
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    allowed_fields = [
        "title", "description", "start_time", "end_time", "location",
        "attendees", "reminder_minutes", "priority", "status"
    ]
    update_data = {k: v for k, v in event_data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.calendar_events.update_one(
        {"event_id": event_id},
        {"$set": update_data}
    )
    
    updated_event = await db.calendar_events.find_one({"event_id": event_id})
    return serialize_mongo_doc(updated_event)

@api_router.delete("/calendar/events/{event_id}")
async def delete_calendar_event(event_id: str, current_user = Depends(get_current_user)):
    """Delete a calendar event"""
    result = await db.calendar_events.delete_one({
        "event_id": event_id,
        "user_id": current_user["user_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {"status": "deleted"}

# Task Management API
@api_router.post("/tasks")
async def create_task(task_data: TaskCreate, current_user = Depends(get_current_user)):
    """Create a new task"""
    task = Task(
        user_id=current_user["user_id"],
        **task_data.dict()
    )
    
    task_dict = task.dict()
    await db.tasks.insert_one(task_dict)
    
    # Notify assignee if task is assigned to someone else
    if task.assigned_to and task.assigned_to != current_user["user_id"]:
        await manager.send_personal_message(
            json.dumps({
                "type": "task_assigned",
                "data": serialize_mongo_doc(task_dict)
            }),
            task.assigned_to
        )
    
    return serialize_mongo_doc(task_dict)

@api_router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    workspace_mode: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get tasks for the user"""
    query = {
        "$or": [
            {"user_id": current_user["user_id"]},
            {"assigned_to": current_user["user_id"]}
        ]
    }
    
    if status:
        query["status"] = status
    if workspace_mode:
        query["workspace_mode"] = workspace_mode
    
    tasks = await db.tasks.find(query).sort("created_at", -1).to_list(100)
    return serialize_mongo_doc(tasks)

@api_router.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    task_data: dict,
    current_user = Depends(get_current_user)
):
    """Update a task"""
    task = await db.tasks.find_one({
        "task_id": task_id,
        "$or": [
            {"user_id": current_user["user_id"]},
            {"assigned_to": current_user["user_id"]}
        ]
    })
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    allowed_fields = [
        "title", "description", "due_date", "priority", "status",
        "tags", "estimated_hours", "actual_hours"
    ]
    update_data = {k: v for k, v in task_data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.utcnow()
    
    if update_data.get("status") == "completed" and task["status"] != "completed":
        update_data["completed_at"] = datetime.utcnow()
    
    await db.tasks.update_one(
        {"task_id": task_id},
        {"$set": update_data}
    )
    
    updated_task = await db.tasks.find_one({"task_id": task_id})
    return serialize_mongo_doc(updated_task)

# Workspace Profile API
@api_router.post("/workspace/profile")
async def create_workspace_profile(
    profile_data: WorkspaceProfileCreate,
    current_user = Depends(get_current_user)
):
    """Create or update workspace profile"""
    # Check if profile already exists
    existing = await db.workspace_profiles.find_one({"user_id": current_user["user_id"]})
    
    if existing:
        # Update existing profile
        update_data = profile_data.dict()
        await db.workspace_profiles.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": update_data}
        )
        updated_profile = await db.workspace_profiles.find_one({"user_id": current_user["user_id"]})
        return serialize_mongo_doc(updated_profile)
    else:
        # Create new profile
        profile = WorkspaceProfile(
            user_id=current_user["user_id"],
            **profile_data.dict()
        )
        
        profile_dict = profile.dict()
        await db.workspace_profiles.insert_one(profile_dict)
        return serialize_mongo_doc(profile_dict)

@api_router.get("/workspace/profile")
async def get_workspace_profile(current_user = Depends(get_current_user)):
    """Get user's workspace profile"""
    profile = await db.workspace_profiles.find_one({"user_id": current_user["user_id"]})
    
    if not profile:
        # Return default profile structure
        return {
            "user_id": current_user["user_id"],
            "workspace_name": "Personal Workspace",
            "workspace_type": "personal",
            "is_active": False
        }
    
    return serialize_mongo_doc(profile)

@api_router.put("/workspace/mode")
async def switch_workspace_mode(mode_data: dict, current_user = Depends(get_current_user)):
    """Switch between personal and business workspace mode"""
    mode = mode_data.get("mode", "personal")
    
    if mode not in ["personal", "business"]:
        raise HTTPException(status_code=400, detail="Invalid workspace mode")
    
    # Update user's current workspace mode
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"current_workspace_mode": mode}}
    )
    
    return {"status": "success", "current_mode": mode}

# Document Collaboration API
@api_router.post("/documents")
async def create_document(doc_data: DocumentCreate, current_user = Depends(get_current_user)):
    """Create a new document"""
    document = Document(
        user_id=current_user["user_id"],
        **doc_data.dict()
    )
    
    doc_dict = document.dict()
    await db.documents.insert_one(doc_dict)
    
    return serialize_mongo_doc(doc_dict)

@api_router.get("/documents")
async def get_documents(
    workspace_mode: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Get user's documents"""
    query = {
        "$or": [
            {"user_id": current_user["user_id"]},
            {"collaborators": current_user["user_id"]}
        ]
    }
    
    if workspace_mode:
        query["workspace_mode"] = workspace_mode
    
    documents = await db.documents.find(query).sort("updated_at", -1).to_list(50)
    return serialize_mongo_doc(documents)

@api_router.put("/documents/{document_id}")
async def update_document(
    document_id: str,
    doc_data: dict,
    current_user = Depends(get_current_user)
):
    """Update a document"""
    document = await db.documents.find_one({
        "document_id": document_id,
        "$or": [
            {"user_id": current_user["user_id"]},
            {"collaborators": current_user["user_id"]}
        ]
    })
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    allowed_fields = ["title", "content", "tags"]
    update_data = {k: v for k, v in doc_data.items() if k in allowed_fields}
    update_data["updated_at"] = datetime.utcnow()
    
    # Add to version history
    version_entry = {
        "version": len(document.get("version_history", [])) + 1,
        "updated_by": current_user["user_id"],
        "updated_at": datetime.utcnow(),
        "changes": "Content updated"
    }
    
    await db.documents.update_one(
        {"document_id": document_id},
        {
            "$set": update_data,
            "$push": {"version_history": version_entry}
        }
    )
    
    updated_doc = await db.documents.find_one({"document_id": document_id})
    return serialize_mongo_doc(updated_doc)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://c07a86aa-98c0-40e6-a6c6-f5e5eb384e98.preview.emergentagent.com",
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