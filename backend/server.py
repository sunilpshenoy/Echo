from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

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

# Models
class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    phone: Optional[str] = None
    avatar: Optional[str] = None
    is_online: bool = False
    last_seen: datetime = Field(default_factory=datetime.utcnow)
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
    message_type: str = "text"  # text, image, file
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = False
    reply_to: Optional[str] = None

class Chat(BaseModel):
    chat_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_type: str  # direct, group
    name: Optional[str] = None  # For group chats
    members: List[str]
    admin: Optional[str] = None  # For group chats
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_message: Optional[dict] = None

class Contact(BaseModel):
    contact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    contact_user_id: str
    contact_name: str
    added_at: datetime = Field(default_factory=datetime.utcnow)

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
            "avatar": user.avatar
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
            "avatar": user.get("avatar")
        }
    }

# Chat routes
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
            if other_user:
                chat["other_user"] = {
                    "user_id": other_user["user_id"],
                    "username": other_user["username"],
                    "avatar": other_user.get("avatar"),
                    "is_online": other_user.get("is_online", False)
                }
    
    return serialize_mongo_doc(chats)

@api_router.post("/chats")
async def create_chat(chat_data: dict, current_user = Depends(get_current_user)):
    if chat_data["chat_type"] == "direct":
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
            members=[current_user["user_id"]] + chat_data["members"],
            admin=current_user["user_id"]
        )
    
    chat_dict = chat.dict()
    await db.chats.insert_one(chat_dict)
    return serialize_mongo_doc(chat_dict)

@api_router.get("/chats/{chat_id}/messages")
async def get_chat_messages(chat_id: str, current_user = Depends(get_current_user)):
    # Verify user is member of chat
    chat = await db.chats.find_one({"chat_id": chat_id, "members": current_user["user_id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = await db.messages.find({"chat_id": chat_id}).sort("timestamp", 1).to_list(1000)
    
    # Populate sender info
    for message in messages:
        sender = await db.users.find_one({"user_id": message["sender_id"]})
        if sender:
            message["sender_name"] = sender["username"]
            message["sender_avatar"] = sender.get("avatar")
    
    return serialize_mongo_doc(messages)

@api_router.post("/chats/{chat_id}/messages")
async def send_message(chat_id: str, message_data: dict, current_user = Depends(get_current_user)):
    # Verify user is member of chat
    chat = await db.chats.find_one({"chat_id": chat_id, "members": current_user["user_id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Create message
    message = Message(
        chat_id=chat_id,
        sender_id=current_user["user_id"],
        content=message_data["content"],
        message_type=message_data.get("message_type", "text")
    )
    
    message_dict = message.dict()
    await db.messages.insert_one(message_dict)
    
    # Update chat's last message
    await db.chats.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "last_message": {
                "content": message.content,
                "sender_id": message.sender_id,
                "timestamp": message.timestamp
            }
        }}
    )
    
    # Send real-time message to chat members
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

# Contacts routes
@api_router.get("/contacts")
async def get_contacts(current_user = Depends(get_current_user)):
    contacts = await db.contacts.find({"user_id": current_user["user_id"]}).to_list(100)
    
    # Populate contact user info
    for contact in contacts:
        contact_user = await db.users.find_one({"user_id": contact["contact_user_id"]})
        if contact_user:
            contact["contact_info"] = {
                "user_id": contact_user["user_id"],
                "username": contact_user["username"],
                "email": contact_user["email"],
                "phone": contact_user.get("phone"),
                "avatar": contact_user.get("avatar"),
                "is_online": contact_user.get("is_online", False)
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
    
    return contact_dict

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
    
    # Remove sensitive info
    for user in users:
        user.pop("password", None)
        user.pop("_id", None)
    
    return users

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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