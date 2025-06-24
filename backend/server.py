from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
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

# Custom JSON encoder for MongoDB ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

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

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, str] = {}  # user_id -> connection_id
    
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
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.user_connections:
            connection_id = self.user_connections[user_id]
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_text(message)
                except:
                    # Connection might be broken, clean up
                    self.disconnect(connection_id, user_id)
    
    async def broadcast_to_chat(self, message: str, chat_id: str, sender_id: str):
        # Get all members of the chat
        chat = await db.chats.find_one({"chat_id": chat_id})
        if chat:
            for member_id in chat['members']:
                if member_id != sender_id:  # Don't send back to sender
                    await self.send_personal_message(message, member_id)

manager = ConnectionManager()

# Enhanced Models
class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    status_message: str = "Available"
    is_online: bool = False
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    encryption_key: str = Field(default_factory=MessageEncryption.generate_key)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_id: str
    sender_id: str
    content: str
    encrypted_content: Optional[str] = None  # Encrypted version of content
    message_type: str = "text"  # text, image, file
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_data: Optional[str] = None  # base64 encoded for images
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = False
    read_by: List[Dict[str, Any]] = Field(default_factory=list)  # [{user_id, read_at}]
    reply_to: Optional[str] = None
    is_encrypted: bool = True

class Chat(BaseModel):
    chat_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_type: str  # direct, group
    name: Optional[str] = None  # For group chats
    description: Optional[str] = None  # For group chats
    avatar: Optional[str] = None  # For group chats
    members: List[str]
    admins: List[str] = Field(default_factory=list)  # For group chats
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_message: Optional[dict] = None
    encryption_enabled: bool = True

class Contact(BaseModel):
    contact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    contact_user_id: str
    contact_name: str
    added_at: datetime = Field(default_factory=datetime.utcnow)

class BlockedUser(BaseModel):
    block_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    blocker_id: str  # User who blocked
    blocked_id: str  # User who was blocked
    reason: Optional[str] = None
    blocked_at: datetime = Field(default_factory=datetime.utcnow)

class UserReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reporter_id: str
    reported_id: str
    reason: str
    description: Optional[str] = None
    message_id: Optional[str] = None  # If reporting a specific message
    chat_id: Optional[str] = None
    status: str = "pending"  # pending, reviewed, resolved
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None

class GroupChatCreate(BaseModel):
    name: str
    description: Optional[str] = None
    members: List[str]  # List of user_ids

class MessageReadUpdate(BaseModel):
    message_ids: List[str]

class BlockUserRequest(BaseModel):
    user_id: str
    reason: Optional[str] = None

class ReportUserRequest(BaseModel):
    user_id: str
    reason: str
    description: Optional[str] = None
    message_id: Optional[str] = None
    chat_id: Optional[str] = None

# Helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

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

# Authentication routes
@api_router.post("/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone
    )
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    # Create token
    access_token = create_access_token(data={"sub": user.user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "avatar": user.avatar,
            "status_message": user.status_message,
            "encryption_key": user.encryption_key
        }
    }

@api_router.post("/login")
async def login(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update user online status
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
            "email": user["email"],
            "phone": user.get("phone"),
            "avatar": user.get("avatar"),
            "status_message": user.get("status_message", "Available"),
            "encryption_key": user.get("encryption_key")
        }
    }

# User profile routes
@api_router.put("/profile")
async def update_profile(profile_data: dict, current_user = Depends(get_current_user)):
    allowed_fields = ["username", "status_message", "avatar"]
    update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
    
    if update_data:
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": update_data}
        )
    
    updated_user = await db.users.find_one({"user_id": current_user["user_id"]})
    return serialize_mongo_doc({
        "user_id": updated_user["user_id"],
        "username": updated_user["username"],
        "email": updated_user["email"],
        "phone": updated_user.get("phone"),
        "avatar": updated_user.get("avatar"),
        "status_message": updated_user.get("status_message", "Available"),
        "encryption_key": updated_user.get("encryption_key")
    })

# File upload route
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    # Check file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    # Check file type
    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'text/plain', 'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not supported")
    
    # Convert to base64
    file_data = base64.b64encode(content).decode('utf-8')
    
    return {
        "file_name": file.filename,
        "file_size": len(content),
        "file_type": file.content_type,
        "file_data": file_data
    }

# Blocking and Reporting routes
@api_router.post("/users/block")
async def block_user(block_data: BlockUserRequest, current_user = Depends(get_current_user)):
    # Check if user exists
    target_user = await db.users.find_one({"user_id": block_data.user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if block_data.user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
    
    # Check if already blocked
    existing_block = await db.blocked_users.find_one({
        "blocker_id": current_user["user_id"],
        "blocked_id": block_data.user_id
    })
    if existing_block:
        raise HTTPException(status_code=400, detail="User already blocked")
    
    # Create block record
    block = BlockedUser(
        blocker_id=current_user["user_id"],
        blocked_id=block_data.user_id,
        reason=block_data.reason
    )
    
    await db.blocked_users.insert_one(block.dict())
    return {"status": "User blocked successfully"}

@api_router.delete("/users/block/{user_id}")
async def unblock_user(user_id: str, current_user = Depends(get_current_user)):
    # Remove block record
    result = await db.blocked_users.delete_one({
        "blocker_id": current_user["user_id"],
        "blocked_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Block not found")
    
    return {"status": "User unblocked successfully"}

@api_router.get("/users/blocked")
async def get_blocked_users(current_user = Depends(get_current_user)):
    blocks = await db.blocked_users.find({"blocker_id": current_user["user_id"]}).to_list(100)
    
    # Populate blocked user info
    for block in blocks:
        blocked_user = await db.users.find_one({"user_id": block["blocked_id"]})
        if blocked_user:
            block["blocked_user"] = {
                "user_id": blocked_user["user_id"],
                "username": blocked_user["username"],
                "avatar": blocked_user.get("avatar")
            }
    
    return serialize_mongo_doc(blocks)

@api_router.post("/users/report")
async def report_user(report_data: ReportUserRequest, current_user = Depends(get_current_user)):
    # Check if user exists
    target_user = await db.users.find_one({"user_id": report_data.user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if report_data.user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot report yourself")
    
    # Create report record
    report = UserReport(
        reporter_id=current_user["user_id"],
        reported_id=report_data.user_id,
        reason=report_data.reason,
        description=report_data.description,
        message_id=report_data.message_id,
        chat_id=report_data.chat_id
    )
    
    await db.user_reports.insert_one(report.dict())
    return {"status": "Report submitted successfully"}

@api_router.get("/admin/reports")
async def get_reports(current_user = Depends(get_current_user)):
    # In a real app, you'd check if user is admin
    reports = await db.user_reports.find({"status": "pending"}).to_list(100)
    
    # Populate user info
    for report in reports:
        reporter = await db.users.find_one({"user_id": report["reporter_id"]})
        reported = await db.users.find_one({"user_id": report["reported_id"]})
        
        if reporter:
            report["reporter"] = {
                "user_id": reporter["user_id"],
                "username": reporter["username"]
            }
        
        if reported:
            report["reported_user"] = {
                "user_id": reported["user_id"],
                "username": reported["username"]
            }
    
    return serialize_mongo_doc(reports)

# Enhanced Chat routes
@api_router.get("/chats")
async def get_user_chats(current_user = Depends(get_current_user)):
    chats = await db.chats.find({"members": current_user["user_id"]}).to_list(100)
    
    # Populate chat details
    for chat in chats:
        if chat.get("last_message"):
            # Get sender info for last message
            sender = await db.users.find_one({"user_id": chat["last_message"]["sender_id"]})
            if sender:
                chat["last_message"]["sender_name"] = sender["username"]
        
        # For direct chats, get the other user's info
        if chat["chat_type"] == "direct":
            other_user_id = [m for m in chat["members"] if m != current_user["user_id"]][0]
            other_user = await db.users.find_one({"user_id": other_user_id})
            
            # Check if other user is blocked
            is_blocked = await check_user_blocked(current_user["user_id"], other_user_id)
            
            if other_user:
                chat["other_user"] = {
                    "user_id": other_user["user_id"],
                    "username": other_user["username"],
                    "avatar": other_user.get("avatar"),
                    "status_message": other_user.get("status_message", "Available"),
                    "is_online": other_user.get("is_online", False),
                    "is_blocked": is_blocked
                }
        
        # For group chats, get member info
        elif chat["chat_type"] == "group":
            members_info = []
            for member_id in chat["members"]:
                member = await db.users.find_one({"user_id": member_id})
                if member:
                    members_info.append({
                        "user_id": member["user_id"],
                        "username": member["username"],
                        "avatar": member.get("avatar"),
                        "is_online": member.get("is_online", False)
                    })
            chat["members_info"] = members_info
    
    return serialize_mongo_doc(chats)

@api_router.post("/chats")
async def create_chat(chat_data: dict, current_user = Depends(get_current_user)):
    if chat_data["chat_type"] == "direct":
        # Check if users are blocked
        is_blocked = await check_user_blocked(current_user["user_id"], chat_data["other_user_id"])
        if is_blocked:
            raise HTTPException(status_code=403, detail="Cannot create chat with blocked user")
        
        # Check if direct chat already exists
        existing_chat = await db.chats.find_one({
            "chat_type": "direct",
            "members": {"$all": [current_user["user_id"], chat_data["other_user_id"]]}
        })
        if existing_chat:
            return serialize_mongo_doc(existing_chat)
        
        # Create new direct chat
        chat = Chat(
            chat_type="direct",
            members=[current_user["user_id"], chat_data["other_user_id"]]
        )
    else:
        # Group chat
        chat = Chat(
            chat_type="group",
            name=chat_data["name"],
            description=chat_data.get("description"),
            members=[current_user["user_id"]] + chat_data["members"],
            admins=[current_user["user_id"]],
            created_by=current_user["user_id"]
        )
    
    chat_dict = chat.dict()
    await db.chats.insert_one(chat_dict)
    return serialize_mongo_doc(chat_dict)

@api_router.post("/chats/group")
async def create_group_chat(group_data: GroupChatCreate, current_user = Depends(get_current_user)):
    # Verify all members exist
    for member_id in group_data.members:
        member = await db.users.find_one({"user_id": member_id})
        if not member:
            raise HTTPException(status_code=404, detail=f"User {member_id} not found")
    
    # Create group chat
    chat = Chat(
        chat_type="group",
        name=group_data.name,
        description=group_data.description,
        members=[current_user["user_id"]] + group_data.members,
        admins=[current_user["user_id"]],
        created_by=current_user["user_id"]
    )
    
    chat_dict = chat.dict()
    await db.chats.insert_one(chat_dict)
    
    # Populate member info
    members_info = []
    for member_id in chat_dict["members"]:
        member = await db.users.find_one({"user_id": member_id})
        if member:
            members_info.append({
                "user_id": member["user_id"],
                "username": member["username"],
                "avatar": member.get("avatar"),
                "is_online": member.get("is_online", False)
            })
    chat_dict["members_info"] = members_info
    
    return serialize_mongo_doc(chat_dict)

@api_router.put("/chats/{chat_id}/members")
async def manage_group_members(chat_id: str, action_data: dict, current_user = Depends(get_current_user)):
    # Verify user is admin of the group
    chat = await db.chats.find_one({"chat_id": chat_id, "chat_type": "group"})
    if not chat:
        raise HTTPException(status_code=404, detail="Group chat not found")
    
    if current_user["user_id"] not in chat.get("admins", []):
        raise HTTPException(status_code=403, detail="Only admins can manage members")
    
    action = action_data["action"]  # "add" or "remove"
    user_id = action_data["user_id"]
    
    if action == "add":
        # Add member
        if user_id not in chat["members"]:
            await db.chats.update_one(
                {"chat_id": chat_id},
                {"$push": {"members": user_id}}
            )
    elif action == "remove":
        # Remove member
        if user_id in chat["members"] and user_id != chat["created_by"]:
            await db.chats.update_one(
                {"chat_id": chat_id},
                {"$pull": {"members": user_id, "admins": user_id}}
            )
    
    # Return updated chat
    updated_chat = await db.chats.find_one({"chat_id": chat_id})
    return serialize_mongo_doc(updated_chat)

@api_router.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: str, current_user = Depends(get_current_user)):
    # Verify user is member of chat
    chat = await db.chats.find_one({"chat_id": chat_id, "members": current_user["user_id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = await db.messages.find({"chat_id": chat_id}).sort("timestamp", 1).to_list(1000)
    
    # Decrypt and populate sender info
    user_encryption_key = current_user.get("encryption_key")
    
    for message in messages:
        sender = await db.users.find_one({"user_id": message["sender_id"]})
        if sender:
            message["sender_name"] = sender["username"]
            message["sender_avatar"] = sender.get("avatar")
        
        # Decrypt message content if encrypted
        if message.get("is_encrypted") and message.get("encrypted_content") and user_encryption_key:
            try:
                message["content"] = MessageEncryption.decrypt_message(
                    message["encrypted_content"], 
                    user_encryption_key
                )
            except Exception as e:
                logging.error(f"Failed to decrypt message: {e}")
                message["content"] = "[Encrypted Message]"
        
        # Determine read status for current user
        if message["sender_id"] == current_user["user_id"]:
            # For sender, show if others have read
            read_count = len([r for r in message.get("read_by", []) if r["user_id"] != current_user["user_id"]])
            total_recipients = len(chat["members"]) - 1
            message["read_status"] = "read" if read_count == total_recipients else "delivered"
        else:
            # For recipient, check if they've read it
            user_read = any(r["user_id"] == current_user["user_id"] for r in message.get("read_by", []))
            message["read_status"] = "read" if user_read else "unread"
    
    return serialize_mongo_doc(messages)

@api_router.post("/chats/{chat_id}/messages")
async def send_message(chat_id: str, message_data: dict, current_user = Depends(get_current_user)):
    # Verify user is member of chat
    chat = await db.chats.find_one({"chat_id": chat_id, "members": current_user["user_id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # For direct chats, check if users are blocked
    if chat["chat_type"] == "direct":
        other_user_id = [m for m in chat["members"] if m != current_user["user_id"]][0]
        is_blocked = await check_user_blocked(current_user["user_id"], other_user_id)
        if is_blocked:
            raise HTTPException(status_code=403, detail="Cannot send message to blocked user")
    
    # Get sender's encryption key
    user_encryption_key = current_user.get("encryption_key")
    
    # Encrypt message content
    encrypted_content = None
    if user_encryption_key and chat.get("encryption_enabled", True):
        encrypted_content = MessageEncryption.encrypt_message(message_data["content"], user_encryption_key)
    
    # Create message
    message = Message(
        chat_id=chat_id,
        sender_id=current_user["user_id"],
        content=message_data["content"],
        encrypted_content=encrypted_content,
        message_type=message_data.get("message_type", "text"),
        file_name=message_data.get("file_name"),
        file_size=message_data.get("file_size"),
        file_data=message_data.get("file_data"),
        is_encrypted=encrypted_content is not None
    )
    
    message_dict = message.dict()
    # Store encrypted version in database, but remove plain text for storage
    if encrypted_content:
        message_dict["content"] = "[Encrypted]"  # Don't store plain text
    
    await db.messages.insert_one(message_dict)
    
    # Update chat's last message
    last_message_content = message_data["content"]
    if message.message_type != "text":
        last_message_content = f"📎 {message.file_name}" if message.file_name else "📎 File"
    
    await db.chats.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "last_message": {
                "content": last_message_content,
                "sender_id": message.sender_id,
                "timestamp": message.timestamp,
                "message_type": message.message_type
            }
        }}
    )
    
    # Send real-time message to chat members (with original content for display)
    message_dict["content"] = message_data["content"]  # Restore original for broadcast
    message_dict["sender_name"] = current_user["username"]
    message_dict["sender_avatar"] = current_user.get("avatar")
    await manager.broadcast_to_chat(
        json.dumps({
            "type": "new_message",
            "data": serialize_mongo_doc(message_dict)
        }),
        chat_id,
        current_user["user_id"]
    )
    
    return serialize_mongo_doc(message_dict)

@api_router.post("/messages/read")
async def mark_messages_read(read_data: MessageReadUpdate, current_user = Depends(get_current_user)):
    # Mark messages as read
    read_entry = {
        "user_id": current_user["user_id"],
        "read_at": datetime.utcnow()
    }
    
    await db.messages.update_many(
        {
            "message_id": {"$in": read_data.message_ids},
            "sender_id": {"$ne": current_user["user_id"]},
            "read_by.user_id": {"$ne": current_user["user_id"]}
        },
        {"$push": {"read_by": read_entry}}
    )
    
    # Broadcast read receipts to other users
    for message_id in read_data.message_ids:
        message = await db.messages.find_one({"message_id": message_id})
        if message:
            await manager.send_personal_message(
                json.dumps({
                    "type": "message_read",
                    "data": {
                        "message_id": message_id,
                        "read_by": current_user["user_id"],
                        "read_at": read_entry["read_at"].isoformat()
                    }
                }),
                message["sender_id"]
            )
    
    return {"status": "success"}

# Contacts routes
@api_router.get("/contacts")
async def get_contacts(current_user = Depends(get_current_user)):
    contacts = await db.contacts.find({"user_id": current_user["user_id"]}).to_list(100)
    
    # Populate contact user info
    for contact in contacts:
        contact_user = await db.users.find_one({"user_id": contact["contact_user_id"]})
        if contact_user:
            # Check if contact is blocked
            is_blocked = await check_user_blocked(current_user["user_id"], contact["contact_user_id"])
            
            contact["contact_info"] = {
                "user_id": contact_user["user_id"],
                "username": contact_user["username"],
                "email": contact_user["email"],
                "phone": contact_user.get("phone"),
                "avatar": contact_user.get("avatar"),
                "status_message": contact_user.get("status_message", "Available"),
                "is_online": contact_user.get("is_online", False),
                "is_blocked": is_blocked
            }
    
    return serialize_mongo_doc(contacts)

@api_router.post("/contacts")
async def add_contact(contact_data: dict, current_user = Depends(get_current_user)):
    # Find user by email or phone
    user_query = {}
    if contact_data.get("email"):
        user_query["email"] = contact_data["email"]
    elif contact_data.get("phone"):
        user_query["phone"] = contact_data["phone"]
    else:
        raise HTTPException(status_code=400, detail="Email or phone required")
    
    contact_user = await db.users.find_one(user_query)
    if not contact_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if contact_user["user_id"] == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot add yourself as contact")
    
    # Check if users are blocked
    is_blocked = await check_user_blocked(current_user["user_id"], contact_user["user_id"])
    if is_blocked:
        raise HTTPException(status_code=403, detail="Cannot add blocked user as contact")
    
    # Check if contact already exists
    existing_contact = await db.contacts.find_one({
        "user_id": current_user["user_id"],
        "contact_user_id": contact_user["user_id"]
    })
    if existing_contact:
        raise HTTPException(status_code=400, detail="Contact already exists")
    
    # Create contact
    contact = Contact(
        user_id=current_user["user_id"],
        contact_user_id=contact_user["user_id"],
        contact_name=contact_data.get("contact_name", contact_user["username"])
    )
    
    contact_dict = contact.dict()
    await db.contacts.insert_one(contact_dict)
    
    return serialize_mongo_doc(contact_dict)

# WebSocket endpoint
@api_router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    connection_id = await manager.connect(websocket, user_id)
    
    # Update user online status
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_online": True, "last_seen": datetime.utcnow()}}
    )
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages if needed
            pass
    except WebSocketDisconnect:
        manager.disconnect(connection_id, user_id)
        
        # Update user offline status
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"is_online": False, "last_seen": datetime.utcnow()}}
        )

# Search users
@api_router.get("/users/search")
async def search_users(q: str, current_user = Depends(get_current_user)):
    users = await db.users.find({
        "$or": [
            {"username": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
            {"phone": {"$regex": q, "$options": "i"}}
        ],
        "user_id": {"$ne": current_user["user_id"]}
    }).to_list(20)
    
    # Remove sensitive info and add block status
    for user in users:
        user.pop("password", None)
        user.pop("_id", None)
        user.pop("encryption_key", None)
        
        # Check if user is blocked
        user["is_blocked"] = await check_user_blocked(current_user["user_id"], user["user_id"])
    
    return serialize_mongo_doc(users)

# Include the router in the main app
app.include_router(api_router)

# Add a simple test endpoint
@app.get("/api/test-connection")
async def test_connection():
    return "Connection successful"

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()