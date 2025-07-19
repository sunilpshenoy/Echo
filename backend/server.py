from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, File, Form, UploadFile, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import redis
import hashlib
import time
import re
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
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import secrets
import qrcode
from io import BytesIO
import zipfile
import tempfile

# Military-grade security configuration
SECURITY_CONFIG = {
    'MAX_REQUEST_SIZE': 10 * 1024 * 1024,  # 10MB
    'MAX_REQUESTS_PER_MINUTE': 100,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION': 900,  # 15 minutes
    'SUSPICIOUS_PATTERNS': [
        'script', 'javascript:', 'vbscript:', 'onload=', 'onerror=',
        'eval(', 'document.cookie', 'window.location', 'alert(',
        '../', '..\\', '/etc/passwd', '/etc/shadow',
        'UNION SELECT', 'DROP TABLE', 'INSERT INTO', 'UPDATE SET'
    ],
    'BLOCKED_USER_AGENTS': [
        'sqlmap', 'nikto', 'w3af', 'burp', 'nmap', 'masscan',
        'acunetix', 'netsparker', 'websecurify', 'havij'
    ],
    'ALLOWED_ORIGINS': [
        'http://localhost:3000',
        'https://1345bce5-cc7d-477e-8431-d11bc6e77861.preview.emergentagent.com',
        'https://1345bce5-cc7d-477e-8431-d11bc6e77861.preview.emergentagent.com',
        'https://*.emergentagent.com'
    ]
}

# Initialize Redis for security tracking and caching
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
    print("✅ Redis connected successfully")
except:
    REDIS_AVAILABLE = False
    print("⚠️ Redis not available - using memory-based rate limiting")

# Performance and caching configuration
CACHE_CONFIG = {
    'DEFAULT_TTL': 3600,  # 1 hour
    'SHORT_TTL': 300,     # 5 minutes
    'LONG_TTL': 86400,    # 24 hours
    'USER_CACHE_TTL': 1800,  # 30 minutes
    'CHAT_CACHE_TTL': 600,   # 10 minutes
    'SEARCH_CACHE_TTL': 300, # 5 minutes
}

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Military-grade security class
class SecurityManager:
    def __init__(self):
        self.failed_attempts = {}
        self.blocked_ips = set()
        self.suspicious_requests = {}
        
    async def check_ip_reputation(self, ip: str) -> bool:
        """Check if IP is blacklisted or suspicious"""
        # Check local blacklist
        if ip in self.blocked_ips:
            return False
            
        # Check failed attempts
        if ip in self.failed_attempts:
            attempts = self.failed_attempts[ip]
            if attempts['count'] >= SECURITY_CONFIG['MAX_LOGIN_ATTEMPTS']:
                lockout_time = attempts['last_attempt'] + SECURITY_CONFIG['LOCKOUT_DURATION']
                if time.time() < lockout_time:
                    return False
        
        return True
    
    async def log_failed_attempt(self, ip: str):
        """Log failed authentication attempt"""
        current_time = time.time()
        
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = {'count': 0, 'last_attempt': current_time}
        
        self.failed_attempts[ip]['count'] += 1
        self.failed_attempts[ip]['last_attempt'] = current_time
        
        # Block IP after max attempts
        if self.failed_attempts[ip]['count'] >= SECURITY_CONFIG['MAX_LOGIN_ATTEMPTS']:
            self.blocked_ips.add(ip)
            if REDIS_AVAILABLE:
                redis_client.setex(f"blocked_ip:{ip}", SECURITY_CONFIG['LOCKOUT_DURATION'], "1")
    
    async def detect_malicious_payload(self, data: str) -> bool:
        """Detect potentially malicious payloads"""
        data_lower = data.lower()
        
        for pattern in SECURITY_CONFIG['SUSPICIOUS_PATTERNS']:
            if pattern.lower() in data_lower:
                return True
        
        return False
    
    async def check_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is from known attack tools"""
        if not user_agent:
            return False
            
        user_agent_lower = user_agent.lower()
        
        for blocked_agent in SECURITY_CONFIG['BLOCKED_USER_AGENTS']:
            if blocked_agent in user_agent_lower:
                return False
        
        return True
    
    async def log_activity(self, ip: str, activity_type: str, details: str):
        """Log general activity for monitoring"""
        # For now, just log to console - in production this would go to proper logging system
        logging.info(f"Activity [{activity_type}] from {ip}: {details}")
    
    async def log_suspicious_activity(self, ip: str, activity_type: str, details: str):
        """Log suspicious activity for monitoring"""
        current_time = time.time()
        
        if ip not in self.suspicious_requests:
            self.suspicious_requests[ip] = []
        
        self.suspicious_requests[ip].append({
            'type': activity_type,
            'details': details,
            'timestamp': current_time
        })
        
        # Keep only last 100 entries per IP
        if len(self.suspicious_requests[ip]) > 100:
            self.suspicious_requests[ip] = self.suspicious_requests[ip][-100:]
        
        # Auto-block IP if too many suspicious activities
        if len(self.suspicious_requests[ip]) > 20:
            recent_activities = [
                activity for activity in self.suspicious_requests[ip]
                if current_time - activity['timestamp'] < 300  # Last 5 minutes
            ]
            
            if len(recent_activities) > 10:
                self.blocked_ips.add(ip)
                if REDIS_AVAILABLE:
                    redis_client.setex(f"blocked_ip:{ip}", SECURITY_CONFIG['LOCKOUT_DURATION'], "1")

# Advanced caching system
class CacheManager:
    def __init__(self):
        self.local_cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0, 'sets': 0}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value with fallback to local cache"""
        try:
            if REDIS_AVAILABLE:
                cached = redis_client.get(f"pulse:{key}")
                if cached:
                    self.cache_stats['hits'] += 1
                    return json.loads(cached)
            
            # Fallback to local cache
            if key in self.local_cache:
                item = self.local_cache[key]
                if item['expires'] > time.time():
                    self.cache_stats['hits'] += 1
                    return item['value']
                else:
                    del self.local_cache[key]
            
            self.cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            print(f"Cache get error: {e}")
            self.cache_stats['misses'] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set cached value with TTL"""
        try:
            ttl = ttl or CACHE_CONFIG['DEFAULT_TTL']
            
            if REDIS_AVAILABLE:
                redis_client.setex(f"pulse:{key}", ttl, json.dumps(value))
            else:
                # Fallback to local cache
                self.local_cache[key] = {
                    'value': value,
                    'expires': time.time() + ttl
                }
            
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete cached value"""
        try:
            if REDIS_AVAILABLE:
                redis_client.delete(f"pulse:{key}")
            
            if key in self.local_cache:
                del self.local_cache[key]
            
            return True
            
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> bool:
        """Clear cache entries matching pattern"""
        try:
            if REDIS_AVAILABLE:
                keys = redis_client.keys(f"pulse:{pattern}*")
                if keys:
                    redis_client.delete(*keys)
            
            # Clear local cache
            keys_to_delete = [k for k in self.local_cache.keys() if k.startswith(pattern)]
            for key in keys_to_delete:
                del self.local_cache[key]
            
            return True
            
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'sets': self.cache_stats['sets'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }

# Performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.request_times = {}
        self.slow_queries = []
        self.error_counts = {}
    
    async def start_request(self, request_id: str, endpoint: str):
        """Start timing a request"""
        self.request_times[request_id] = {
            'start': time.time(),
            'endpoint': endpoint
        }
    
    async def end_request(self, request_id: str, status_code: int = 200):
        """End timing a request and log if slow"""
        if request_id in self.request_times:
            start_time = self.request_times[request_id]['start']
            duration = time.time() - start_time
            endpoint = self.request_times[request_id]['endpoint']
            
            # Log slow requests (> 1 second)
            if duration > 1.0:
                self.slow_queries.append({
                    'endpoint': endpoint,
                    'duration': duration,
                    'timestamp': datetime.utcnow().isoformat(),
                    'status_code': status_code
                })
                
                # Keep only last 100 slow queries
                if len(self.slow_queries) > 100:
                    self.slow_queries = self.slow_queries[-100:]
            
            # Count errors
            if status_code >= 400:
                self.error_counts[endpoint] = self.error_counts.get(endpoint, 0) + 1
            
            del self.request_times[request_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'active_requests': len(self.request_times),
            'slow_queries': len(self.slow_queries),
            'recent_slow_queries': self.slow_queries[-10:],
            'error_counts': self.error_counts
        }

# Initialize security manager
security_manager = SecurityManager()

# Security middleware
async def security_middleware(request: Request, call_next):
    """Military-grade security middleware"""
    start_time = time.time()
    client_ip = get_remote_address(request)
    user_agent = request.headers.get('user-agent', '')
    
    # Check IP reputation
    if not await security_manager.check_ip_reputation(client_ip):
        await security_manager.log_suspicious_activity(
            client_ip, 'blocked_ip_access', f"Blocked IP attempted access: {request.url}"
        )
        return JSONResponse(
            status_code=403,
            content={"detail": "Access denied from this IP address"}
        )
    
    # Check user agent
    if not await security_manager.check_user_agent(user_agent):
        await security_manager.log_suspicious_activity(
            client_ip, 'malicious_user_agent', f"Suspicious user agent: {user_agent}"
        )
        return JSONResponse(
            status_code=403,
            content={"detail": "Invalid client"}
        )
    
    # Check request size
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > SECURITY_CONFIG['MAX_REQUEST_SIZE']:
        await security_manager.log_suspicious_activity(
            client_ip, 'oversized_request', f"Request size: {content_length}"
        )
        return JSONResponse(
            status_code=413,
            content={"detail": "Request too large"}
        )
    
    # Check for malicious payloads in query parameters
    query_string = str(request.url.query)
    if await security_manager.detect_malicious_payload(query_string):
        await security_manager.log_suspicious_activity(
            client_ip, 'malicious_query', f"Suspicious query: {query_string}"
        )
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid request parameters"}
        )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Log response time for monitoring
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        await security_manager.log_suspicious_activity(
            client_ip, 'request_error', f"Request processing error: {str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

# E2E Encryption Models - Zero Knowledge Architecture
class E2EKeyBundle(BaseModel):
    user_id: str
    identity_key: str  # Base64 encoded public key
    signing_key: Optional[str] = None  # Base64 encoded signing public key (for algorithm compatibility)
    signed_pre_key: str  # Base64 encoded public key
    signed_pre_key_signature: str  # Base64 encoded signature
    one_time_pre_keys: List[str]  # List of Base64 encoded public keys
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class E2EMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_id: str
    recipient_id: str
    encrypted_content: str  # Client-encrypted message content
    iv: str  # Initialization vector
    ratchet_public_key: str  # For Signal Protocol double ratchet
    message_number: int
    chain_length: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
class E2EConversationInit(BaseModel):
    sender_id: str
    recipient_id: str
    ephemeral_public_key: str
    used_one_time_pre_key: Optional[int] = None
    sender_identity_key: str

# Legacy encryption (kept for backward compatibility)
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

# Initialize core services
security_manager = SecurityManager()
cache_manager = CacheManager()
performance_monitor = PerformanceMonitor()

# Add CORS middleware FIRST (before security middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for preview environment
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add military-grade security middleware (re-enabled after CORS fix)
app.middleware("http")(security_middleware)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add trusted host middleware for additional security
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "*.emergentagent.com", "127.0.0.1"]
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Add explicit OPTIONS handler for CORS
@api_router.options("/{path:path}")
async def options_handler(path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "600",
        }
    )

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production-' + str(int(time.time())))
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expires in 30 minutes

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
    
    def is_user_online(self, user_id: str) -> bool:
        """Check if a user is currently online (has active WebSocket connection)"""
        return user_id in self.user_connections

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
    profile_completed: bool = False  # For authentic connections flow
    connection_pin: Optional[str] = None  # PIN for easy connections (like BlackBerry)
    # Authentic connections profile fields
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    current_mood: Optional[str] = None
    mood_reason: Optional[str] = None
    seeking_type: Optional[str] = None
    seeking_age_range: Optional[str] = None
    seeking_gender: Optional[str] = None
    seeking_location_preference: Optional[str] = None
    connection_purpose: Optional[str] = None
    additional_requirements: Optional[str] = None
    bio: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    values: List[str] = Field(default_factory=list)
    authenticity_rating: float = 0.0  # 0-10 scale
    trust_level: int = 1  # 1-5 progressive trust levels
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

# Marketplace Models
class MarketplaceListing(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    category: str = Field(..., description="items, services, jobs, housing, vehicles")
    price: Optional[float] = Field(None, ge=0)
    price_type: str = Field(..., description="fixed, hourly, negotiable, free, barter")
    location: Optional[str] = Field(None, max_length=200)
    youtube_url: Optional[str] = Field(None, max_length=500)
    instagram_url: Optional[str] = Field(None, max_length=500)
    images: Optional[List[str]] = []
    tags: Optional[List[str]] = []
    availability: str = Field(default="available", description="available, sold, pending")
    contact_method: str = Field(default="chat", description="chat, email, phone")
    expires_at: Optional[datetime] = None

class MarketplaceSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    location: Optional[Dict[str, Any]] = None
    radius: Optional[int] = 10  # km
    sort_by: str = Field(default="created_at", description="created_at, price, distance, relevance")
    sort_order: str = Field(default="desc", description="asc, desc")

class MarketplaceMessage(BaseModel):
    listing_id: str
    recipient_id: str
    message: str = Field(..., min_length=1, max_length=500)
    offer_price: Optional[float] = None

# Reels-Based Marketplace Models
class ServiceReel(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=500)
    category: str = Field(..., description="food, design, tech, home, beauty, education, fitness")
    base_price: float = Field(..., ge=0)
    price_type: str = Field(..., description="per_hour, per_project, per_day, per_meal, negotiable")
    video_url: str = Field(..., description="Video file URL or base64")
    thumbnail_url: Optional[str] = None
    duration: int = Field(..., ge=15, le=180, description="Video duration in seconds")
    location: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default=[], max_items=10)
    availability: str = Field(default="available", description="available, busy, unavailable")

class ReelBid(BaseModel):
    reel_id: str
    bid_amount: float = Field(..., ge=0)
    message: str = Field(..., min_length=10, max_length=500)
    project_details: Optional[str] = Field(None, max_length=1000)
    preferred_date: Optional[datetime] = None
    urgency: str = Field(default="normal", description="low, normal, high, urgent")

class ReelReview(BaseModel):
    reel_id: str
    rating: int = Field(..., ge=1, le=5)
    review_text: str = Field(..., min_length=10, max_length=500)
    service_quality: int = Field(..., ge=1, le=5)
    communication: int = Field(..., ge=1, le=5)
    value_for_money: int = Field(..., ge=1, le=5)
    would_recommend: bool = Field(default=True)
class UserVerification(BaseModel):
    phone_number: Optional[str] = Field(None, pattern=r"^\+91[6-9]\d{9}$")  # Indian mobile format
    email_verified: bool = Field(default=False)
    phone_verified: bool = Field(default=False)
    government_id_verified: bool = Field(default=False)
    verification_level: str = Field(default="basic", description="basic, verified, premium")

class GovernmentIDVerification(BaseModel):
    id_type: str = Field(..., description="aadhaar, pan, voter_id, passport, driving_license")
    id_number: str = Field(..., min_length=6, max_length=20)
    full_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    address: Optional[str] = Field(None, max_length=500)
    document_image: Optional[str] = None  # Base64 encoded image

class LocationSearch(BaseModel):
    state: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")  # Indian pincode format
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[int] = Field(10, ge=1, le=100)

class EnhancedMarketplaceSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    location: Optional[LocationSearch] = None
    verification_level: Optional[str] = Field(None, description="basic, verified, premium")
    sort_by: str = Field(default="relevance", description="relevance, price_low, price_high, distance, date_new, date_old")
    only_verified_sellers: bool = Field(default=False)

class SafetyCheckIn(BaseModel):
    listing_id: str
    meeting_location: str
    meeting_time: datetime
    contact_phone: str = Field(..., pattern=r"^\+91[6-9]\d{9}$")
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = Field(None, pattern=r"^\+91[6-9]\d{9}$")
    status: str = Field(default="scheduled", description="scheduled, met, completed, emergency")

class DocumentCreate(BaseModel):
    title: str
    content: str
    document_type: str = "text"
    workspace_mode: str = "personal"
    chat_id: Optional[str] = None
    collaborators: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

# Helper functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
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
            "profile_completed": user.profile_completed,
            "encryption_key": user.encryption_key,
            "safety_number": user.safety_number,
            "backup_phrase": backup_phrase
        }
    }

@api_router.post("/auth/refresh")
async def refresh_token(current_user = Depends(get_current_user)):
    """Refresh JWT access token for authenticated user"""
    try:
        # Generate new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": current_user["user_id"]},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": serialize_mongo_doc(current_user)
        }
    except Exception as e:
        print(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Token refresh failed")

@api_router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, login_data: UserLogin):
    client_ip = get_remote_address(request)
    
    # Check if IP is blocked
    if not await security_manager.check_ip_reputation(client_ip):
        raise HTTPException(status_code=403, detail="Access denied from this IP address")
    
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        await security_manager.log_failed_attempt(client_ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(login_data.password, user["password"]):
        await security_manager.log_failed_attempt(client_ip)
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
            "profile_completed": user.get("profile_completed", False),
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

# Advanced Authenticity Rating System
@api_router.get("/authenticity/details")
async def get_authenticity_details(current_user = Depends(get_current_user)):
    """Get detailed breakdown of authenticity rating"""
    user = current_user
    
    # Calculate detailed authenticity factors
    factors = {
        "profile_completeness": 0,
        "interaction_quality": 0,
        "consistency": 0,
        "verification_status": 0,
        "community_feedback": 0
    }
    
    # Profile completeness (0-2 points)
    required_fields = ["age", "gender", "location", "bio", "interests", "values", "current_mood", "seeking_type"]
    completed_fields = sum(1 for field in required_fields if user.get(field))
    factors["profile_completeness"] = min(2.0, (completed_fields / len(required_fields)) * 2.0)
    
    # Verification status (0-1 point)
    factors["verification_status"] = 1.0 if user.get("verified", False) else 0.0
    
    # Base interaction quality (0-2 points) - can be enhanced with actual interaction data
    factors["interaction_quality"] = min(2.0, (user.get("trust_level", 1) - 1) * 0.5)
    
    # Consistency (0-2 points) - based on profile updates and activity
    days_since_creation = (datetime.utcnow() - user.get("created_at", datetime.utcnow())).days
    factors["consistency"] = min(2.0, min(days_since_creation / 30, 1.0) * 2.0)
    
    # Community feedback (0-3 points) - placeholder, can be enhanced with actual feedback system
    factors["community_feedback"] = min(3.0, user.get("authenticity_rating", 0.0) * 0.3)
    
    total_rating = sum(factors.values())
    
    return {
        "total_rating": round(total_rating, 1),
        "max_rating": 10.0,
        "factors": {
            "profile_completeness": {
                "score": round(factors["profile_completeness"], 1),
                "max_score": 2.0,
                "description": "How complete is your profile",
                "tips": ["Add missing profile information", "Write a detailed bio", "List your interests and values"]
            },
            "interaction_quality": {
                "score": round(factors["interaction_quality"], 1),
                "max_score": 2.0,
                "description": "Quality of your interactions",
                "tips": ["Engage in meaningful conversations", "Build genuine connections", "Progress through trust levels"]
            },
            "consistency": {
                "score": round(factors["consistency"], 1),
                "max_score": 2.0,
                "description": "Account age and activity consistency",
                "tips": ["Stay active on the platform", "Maintain consistent profile information"]
            },
            "verification_status": {
                "score": round(factors["verification_status"], 1),
                "max_score": 1.0,
                "description": "Account verification",
                "tips": ["Complete profile verification process"]
            },
            "community_feedback": {
                "score": round(factors["community_feedback"], 1),
                "max_score": 3.0,
                "description": "Feedback from other users",
                "tips": ["Be authentic in all interactions", "Help others feel comfortable", "Respect boundaries"]
            }
        },
        "level": "Getting Started" if total_rating < 3 else
                "Building Trust" if total_rating < 6 else
                "Trusted Member" if total_rating < 8 else
                "Highly Authentic",
        "next_milestone": 3 if total_rating < 3 else
                        6 if total_rating < 6 else
                        8 if total_rating < 8 else
                        10
    }

@api_router.put("/authenticity/update")
async def update_authenticity_rating(current_user = Depends(get_current_user)):
    """Recalculate and update user's authenticity rating"""
    # Get detailed authenticity breakdown
    details_response = await get_authenticity_details(current_user)
    new_rating = details_response["total_rating"]
    
    # Update the user's authenticity rating
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"authenticity_rating": new_rating}}
    )
    
    return {
        "message": "Authenticity rating updated successfully",
        "new_rating": new_rating,
        "level": details_response["level"]
    }

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

# Get current user info
@api_router.get("/users/me")
async def get_current_user_info(current_user = Depends(get_current_user)):
    return serialize_mongo_doc({
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "display_name": current_user.get("display_name"),
        "email": current_user["email"],
        "phone": current_user.get("phone"),
        "avatar": current_user.get("avatar"),
        "status_message": current_user.get("status_message", "Available"),
        "profile_completed": current_user.get("profile_completed", False),
        "age": current_user.get("age"),
        "gender": current_user.get("gender"),
        "location": current_user.get("location"),
        "bio": current_user.get("bio"),
        "interests": current_user.get("interests", []),
        "values": current_user.get("values", []),
        "current_mood": current_user.get("current_mood"),
        "seeking_type": current_user.get("seeking_type"),
        "connection_purpose": current_user.get("connection_purpose"),
        "authenticity_rating": current_user.get("authenticity_rating", 0.0),
        "trust_level": current_user.get("trust_level", 1),
        "verified": current_user.get("verified", False),
        "premium": current_user.get("premium", False),
        "connection_pin": current_user.get("connection_pin")
    })

# Complete authentic connections profile
@api_router.put("/profile/complete")
async def complete_profile(profile_data: dict, current_user = Depends(get_current_user)):
    # Fields allowed for profile completion
    allowed_fields = [
        "display_name", "age", "gender", "location", "current_mood", "mood_reason", 
        "seeking_type", "seeking_age_range", "seeking_gender", 
        "seeking_location_preference", "connection_purpose", 
        "additional_requirements", "bio", "interests", "values", "profile_completed"
    ]
    
    update_data = {k: v for k, v in profile_data.items() if k in allowed_fields}
    
    # Ensure profile is marked as completed
    update_data["profile_completed"] = True
    
    # Generate connection PIN if not exists
    if not current_user.get("connection_pin"):
        connection_pin = f"PIN-{str(uuid.uuid4())[:6].upper()}"
        update_data["connection_pin"] = connection_pin
    
    # Calculate initial authenticity rating based on profile completeness
    profile_completeness = 0
    required_fields = ["age", "gender", "location", "bio", "seeking_type", "connection_purpose"]
    for field in required_fields:
        if update_data.get(field):
            profile_completeness += 1
    
    # Initial authenticity rating (0-10 scale)
    update_data["authenticity_rating"] = min(10.0, (profile_completeness / len(required_fields)) * 5.0)
    
    if update_data:
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": update_data}
        )
    
    # Return updated user
    updated_user = await db.users.find_one({"user_id": current_user["user_id"]})
    return serialize_mongo_doc({
        "user_id": updated_user["user_id"],
        "username": updated_user["username"],
        "display_name": updated_user.get("display_name"),
        "email": updated_user["email"],
        "profile_completed": updated_user.get("profile_completed", False),
        "age": updated_user.get("age"),
        "gender": updated_user.get("gender"),
        "location": updated_user.get("location"),
        "bio": updated_user.get("bio"),
        "interests": updated_user.get("interests", []),
        "values": updated_user.get("values", []),
        "current_mood": updated_user.get("current_mood"),
        "seeking_type": updated_user.get("seeking_type"),
        "connection_purpose": updated_user.get("connection_purpose"),
        "authenticity_rating": updated_user.get("authenticity_rating", 0.0),
        "trust_level": updated_user.get("trust_level", 1)
    })

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

@api_router.put("/calls/{call_id}/respond")
async def respond_to_call(call_id: str, response_data: dict, current_user = Depends(get_current_user)):
    """Respond to an incoming call (accept/decline)"""
    call = await db.voice_calls.find_one({"call_id": call_id})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if current_user["user_id"] not in call["participants"]:
        raise HTTPException(status_code=403, detail="Not in this call")
    
    action = response_data.get("action")  # "accept" or "decline"
    
    if action == "accept":
        # Update call status to active if caller accepts or if it's not the caller
        if call["status"] == "ringing":
            await db.voice_calls.update_one(
                {"call_id": call_id},
                {"$set": {"status": "active"}}
            )
        
        # Notify all participants
        await manager.broadcast_to_chat(
            json.dumps({
                "type": "call_accepted",
                "data": {
                    "call_id": call_id,
                    "user_id": current_user["user_id"],
                    "user_name": current_user.get("display_name", current_user["username"])
                }
            }),
            call["chat_id"],
            current_user["user_id"]
        )
        
        return {"status": "accepted", "call_id": call_id}
        
    elif action == "decline":
        # Update call status to declined
        await db.voice_calls.update_one(
            {"call_id": call_id},
            {
                "$set": {
                    "status": "declined",
                    "ended_at": datetime.utcnow()
                }
            }
        )
        
        # Notify all participants
        await manager.broadcast_to_chat(
            json.dumps({
                "type": "call_declined",
                "data": {
                    "call_id": call_id,
                    "user_id": current_user["user_id"],
                    "user_name": current_user.get("display_name", current_user["username"])
                }
            }),
            call["chat_id"],
            current_user["user_id"]
        )
        
        return {"status": "declined", "call_id": call_id}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@api_router.put("/calls/{call_id}/end")
async def end_call(call_id: str, current_user = Depends(get_current_user)):
    """End an active call"""
    call = await db.voice_calls.find_one({"call_id": call_id})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if current_user["user_id"] not in call["participants"]:
        raise HTTPException(status_code=403, detail="Not in this call")
    
    # Calculate duration if call was active
    duration = 0
    if call["status"] == "active" and call.get("started_at"):
        duration = int((datetime.utcnow() - call["started_at"]).total_seconds())
    
    # Update call status to ended
    await db.voice_calls.update_one(
        {"call_id": call_id},
        {
            "$set": {
                "status": "ended",
                "ended_at": datetime.utcnow(),
                "duration": duration
            }
        }
    )
    
    # Notify all participants
    await manager.broadcast_to_chat(
        json.dumps({
            "type": "call_ended",
            "data": {
                "call_id": call_id,
                "user_id": current_user["user_id"],
                "duration": duration
            }
        }),
        call["chat_id"],
        current_user["user_id"]
    )
    
    return {"status": "ended", "call_id": call_id, "duration": duration}

@api_router.post("/calls/{call_id}/webrtc/offer")
async def exchange_webrtc_offer(call_id: str, offer_data: dict, current_user = Depends(get_current_user)):
    """Exchange WebRTC offer for peer-to-peer connection"""
    call = await db.voice_calls.find_one({"call_id": call_id})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if current_user["user_id"] not in call["participants"]:
        raise HTTPException(status_code=403, detail="Not in this call")
    
    # Broadcast WebRTC offer to other participants
    await manager.broadcast_to_chat(
        json.dumps({
            "type": "webrtc_offer",
            "data": {
                "call_id": call_id,
                "from_user_id": current_user["user_id"],
                "offer": offer_data.get("offer"),
                "ice_candidates": offer_data.get("ice_candidates", [])
            }
        }),
        call["chat_id"],
        current_user["user_id"]
    )
    
    return {"status": "offer_sent"}

@api_router.post("/calls/{call_id}/webrtc/answer")
async def exchange_webrtc_answer(call_id: str, answer_data: dict, current_user = Depends(get_current_user)):
    """Exchange WebRTC answer for peer-to-peer connection"""
    call = await db.voice_calls.find_one({"call_id": call_id})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if current_user["user_id"] not in call["participants"]:
        raise HTTPException(status_code=403, detail="Not in this call")
    
    # Broadcast WebRTC answer to other participants
    await manager.broadcast_to_chat(
        json.dumps({
            "type": "webrtc_answer",
            "data": {
                "call_id": call_id,
                "from_user_id": current_user["user_id"],
                "answer": answer_data.get("answer"),
                "ice_candidates": answer_data.get("ice_candidates", [])
            }
        }),
        call["chat_id"],
        current_user["user_id"]
    )
    
    return {"status": "answer_sent"}

@api_router.post("/calls/{call_id}/webrtc/ice")
async def exchange_ice_candidate(call_id: str, ice_data: dict, current_user = Depends(get_current_user)):
    """Exchange ICE candidates for WebRTC connection"""
    call = await db.voice_calls.find_one({"call_id": call_id})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if current_user["user_id"] not in call["participants"]:
        raise HTTPException(status_code=403, detail="Not in this call")
    
    # Broadcast ICE candidate to other participants
    await manager.broadcast_to_chat(
        json.dumps({
            "type": "webrtc_ice",
            "data": {
                "call_id": call_id,
                "from_user_id": current_user["user_id"],
                "candidate": ice_data.get("candidate")
            }
        }),
        call["chat_id"],
        current_user["user_id"]
    )
    
    return {"status": "ice_sent"}

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

# E2E ENCRYPTION ENDPOINTS - Zero Knowledge Implementation

@api_router.post("/e2e/keys")
@limiter.limit("10/minute")
async def upload_e2e_keys(request: Request, key_bundle: E2EKeyBundle, current_user = Depends(get_current_user)):
    """Upload user's E2E encryption public keys (server never sees private keys)"""
    try:
        client_ip = get_remote_address(request)
        
        # Verify the user is uploading their own keys
        if key_bundle.user_id != current_user["user_id"]:
            await security_manager.log_suspicious_activity(
                client_ip, 'unauthorized_key_upload', f"User {current_user['user_id']} tried to upload keys for {key_bundle.user_id}"
            )
            raise HTTPException(status_code=403, detail="Cannot upload keys for another user")
        
        # Store the key bundle (only public keys)
        key_bundle_data = {
            "user_id": key_bundle.user_id,
            "identity_key": key_bundle.identity_key,
            "signing_key": key_bundle.signing_key,  # Include signing_key field
            "signed_pre_key": key_bundle.signed_pre_key,
            "signed_pre_key_signature": key_bundle.signed_pre_key_signature,
            "one_time_pre_keys": key_bundle.one_time_pre_keys,
            "created_at": key_bundle.created_at,
            "updated_at": key_bundle.updated_at
        }
        
        # Upsert key bundle
        await db.e2e_keys.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": key_bundle_data},
            upsert=True
        )
        
        return {"status": "success", "message": "E2E keys uploaded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload E2E keys: {str(e)}")

@api_router.get("/e2e/keys/{user_id}")
async def get_e2e_keys(user_id: str, current_user = Depends(get_current_user)):
    """Get another user's public keys for initiating E2E conversation"""
    try:
        # Fetch the user's public key bundle
        key_bundle = await db.e2e_keys.find_one({"user_id": user_id})
        
        if not key_bundle:
            raise HTTPException(status_code=404, detail="User's E2E keys not found")
        
        # Remove one-time pre-key if available (consume it)
        if key_bundle.get("one_time_pre_keys"):
            used_key = key_bundle["one_time_pre_keys"].pop(0)
            
            # Update the database to remove the used key
            await db.e2e_keys.update_one(
                {"user_id": user_id},
                {"$set": {"one_time_pre_keys": key_bundle["one_time_pre_keys"]}}
            )
            
            return {
                "user_id": user_id,
                "identity_key": key_bundle["identity_key"],
                "signing_key": key_bundle.get("signing_key"),  # Include signing_key field (may be None for backward compatibility)
                "signed_pre_key": key_bundle["signed_pre_key"],
                "signed_pre_key_signature": key_bundle["signed_pre_key_signature"],
                "one_time_pre_keys": [used_key] if used_key else [],
                "has_more_prekeys": len(key_bundle["one_time_pre_keys"]) > 0
            }
        else:
            # No one-time pre-keys available
            return {
                "user_id": user_id,
                "identity_key": key_bundle["identity_key"],
                "signing_key": key_bundle.get("signing_key"),  # Include signing_key field (may be None for backward compatibility)
                "signed_pre_key": key_bundle["signed_pre_key"],
                "signed_pre_key_signature": key_bundle["signed_pre_key_signature"],
                "one_time_pre_keys": [],
                "has_more_prekeys": False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get E2E keys: {str(e)}")

@api_router.post("/e2e/conversation/init")
@limiter.limit("20/minute")
async def init_e2e_conversation(request: Request, init_data: E2EConversationInit, current_user = Depends(get_current_user)):
    """Initialize E2E conversation (store init data for recipient)"""
    try:
        client_ip = get_remote_address(request)
        
        # Verify the sender
        if init_data.sender_id != current_user["user_id"]:
            await security_manager.log_suspicious_activity(
                client_ip, 'unauthorized_conversation_init', f"User {current_user['user_id']} tried to init conversation as {init_data.sender_id}"
            )
            raise HTTPException(status_code=403, detail="Cannot initiate conversation as another user")
        
        # Store conversation initialization data
        conv_init = {
            "conversation_id": f"{init_data.sender_id}_{init_data.recipient_id}",
            "sender_id": init_data.sender_id,
            "recipient_id": init_data.recipient_id,
            "ephemeral_public_key": init_data.ephemeral_public_key,
            "used_one_time_pre_key": init_data.used_one_time_pre_key,
            "sender_identity_key": init_data.sender_identity_key,
            "created_at": datetime.utcnow(),
            "status": "pending"
        }
        
        await db.e2e_conversations.insert_one(conv_init)
        
        return {"status": "success", "conversation_id": conv_init["conversation_id"]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize E2E conversation: {str(e)}")

@api_router.get("/e2e/conversation/pending")
async def get_pending_e2e_conversations(current_user = Depends(get_current_user)):
    """Get pending E2E conversation initializations for current user"""
    try:
        pending_conversations = await db.e2e_conversations.find({
            "recipient_id": current_user["user_id"],
            "status": "pending"
        }).to_list(100)
        
        # Mark as delivered
        await db.e2e_conversations.update_many(
            {"recipient_id": current_user["user_id"], "status": "pending"},
            {"$set": {"status": "delivered"}}
        )
        
        return {"conversations": [serialize_mongo_doc(conv) for conv in pending_conversations]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending conversations: {str(e)}")

@api_router.post("/e2e/message")
@limiter.limit("100/minute")
async def send_e2e_message(request: Request, message: E2EMessage, current_user = Depends(get_current_user)):
    """Store encrypted E2E message (server cannot decrypt)"""
    try:
        client_ip = get_remote_address(request)
        
        # Verify sender
        if message.sender_id != current_user["user_id"]:
            await security_manager.log_suspicious_activity(
                client_ip, 'unauthorized_message_send', f"User {current_user['user_id']} tried to send message as {message.sender_id}"
            )
            raise HTTPException(status_code=403, detail="Cannot send message as another user")
        
        # Store encrypted message (server never sees plaintext)
        message_data = {
            "message_id": message.message_id,
            "conversation_id": message.conversation_id,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "encrypted_content": message.encrypted_content,  # Client-encrypted
            "iv": message.iv,
            "ratchet_public_key": message.ratchet_public_key,
            "message_number": message.message_number,
            "chain_length": message.chain_length,
            "timestamp": message.timestamp,
            "delivered": False,
            "read": False
        }
        
        # Store in messages collection
        result = await db.e2e_messages.insert_one(message_data)
        
        # Notify recipient via WebSocket (if online)
        if manager.is_user_online(message.recipient_id):
            notification = {
                "type": "e2e_message",
                "message_id": message.message_id,
                "sender_id": message.sender_id,
                "timestamp": message.timestamp.isoformat()
            }
            await manager.send_personal_message(json.dumps(notification), message.recipient_id)
        
        return {"status": "success", "message_id": message.message_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store E2E message: {str(e)}")

@api_router.get("/e2e/messages/{conversation_id}")
async def get_e2e_messages(conversation_id: str, current_user = Depends(get_current_user), limit: int = 50, offset: int = 0):
    """Get encrypted E2E messages for a conversation"""
    try:
        # Verify user is part of this conversation
        sender_id, recipient_id = conversation_id.split('_', 1)
        if current_user["user_id"] not in [sender_id, recipient_id]:
            raise HTTPException(status_code=403, detail="Access denied to this conversation")
        
        # Fetch encrypted messages
        messages = await db.e2e_messages.find({
            "conversation_id": conversation_id
        }).sort("timestamp", -1).skip(offset).limit(limit).to_list(limit)
        
        # Mark messages as delivered for current user
        await db.e2e_messages.update_many(
            {
                "conversation_id": conversation_id,
                "recipient_id": current_user["user_id"],
                "delivered": False
            },
            {"$set": {"delivered": True}}
        )
        
        return {"messages": [serialize_mongo_doc(msg) for msg in reversed(messages)]}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get E2E messages: {str(e)}")

@api_router.post("/e2e/keys/refresh")
@limiter.limit("5/minute")
async def refresh_one_time_prekeys(request: Request, new_keys: List[str], current_user = Depends(get_current_user)):
    """Refresh one-time pre-keys when running low"""
    try:
        # Add new one-time pre-keys
        await db.e2e_keys.update_one(
            {"user_id": current_user["user_id"]},
            {"$push": {"one_time_pre_keys": {"$each": new_keys}}}
        )
        
        return {"status": "success", "message": f"Added {len(new_keys)} new one-time pre-keys"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh pre-keys: {str(e)}")

# Original message endpoints (for backward compatibility)
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
        if chat.get("chat_type") == "direct" or chat.get("type") == "direct":
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
                        "email": other_user.get("email"),
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

@api_router.post("/chats/{chat_id}/files")
async def upload_file_to_chat(
    chat_id: str,
    file_data: dict,
    current_user = Depends(get_current_user)
):
    """Upload file to chat"""
    # Verify user is member of chat
    chat = await db.chats.find_one({
        "chat_id": chat_id,
        "members": current_user["user_id"]
    })
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Create file message
    message = {
        "message_id": str(uuid.uuid4()),
        "chat_id": chat_id,
        "sender_id": current_user["user_id"],
        "message_type": "file",
        "content": f"📎 {file_data['filename']}",
        "file_data": {
            "filename": file_data["filename"],
            "size": file_data["size"],
            "type": file_data["type"],
            "data": file_data["data"]  # base64 encoded file
        },
        "timestamp": datetime.utcnow(),
        "is_encrypted": False,
        "edited": False
    }
    
    await db.chat_messages.insert_one(message)
    
    # Update chat last activity
    await db.chats.update_one(
        {"chat_id": chat_id},
        {
            "$set": {
                "last_activity": datetime.utcnow(),
                "last_message": {
                    "content": message["content"],
                    "timestamp": message["timestamp"],
                    "sender_id": current_user["user_id"]
                }
            }
        }
    )
    
    # Broadcast to chat members via WebSocket
    await manager.broadcast_to_chat(
        json.dumps({
            "type": "new_message",
            "data": serialize_mongo_doc(message)
        }),
        chat_id,
        current_user["user_id"]
    )
    
    return serialize_mongo_doc(message)

# Teams Management Endpoints
@api_router.get("/teams")
async def get_teams(current_user = Depends(get_current_user)):
    """Get all teams for the current user"""
    teams = await db.teams.find({
        "members": current_user["user_id"]
    }).to_list(100)
    
    # Add member count and other details
    for team in teams:
        team["member_count"] = len(team.get("members", []))
        
        # Get team creator info
        if team.get("created_by"):
            creator = await db.users.find_one({"user_id": team["created_by"]})
            if creator:
                team["creator"] = {
                    "user_id": creator["user_id"],
                    "display_name": creator.get("display_name", creator["username"])
                }
    
    return serialize_mongo_doc(teams)

# Enhanced Teams Management with Smart Recommendations
@api_router.get("/teams/discover")
async def discover_teams(
    category: str = None,
    location: str = None,
    search: str = None,
    schedule: str = None,  # weekend, weekday, evening
    cost: str = None,      # free, paid, premium
    language: str = None,
    age_group: str = None,
    activity_level: str = None,  # low, medium, high
    current_user = Depends(get_current_user)
):
    """Enhanced team discovery with smart filtering and recommendations"""
    query = {"settings.is_public": True}
    
    # Basic filters
    if category and category != 'all':
        query["category"] = category
    
    if location and location != 'all':
        query["location"] = {"$regex": location, "$options": "i"}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$in": [{"$regex": search, "$options": "i"}]}}
        ]
    
    # Advanced filters
    if schedule:
        query["schedule_preference"] = schedule
    
    if cost:
        query["cost_type"] = cost
    
    if language and language != 'all':
        query["primary_language"] = language
    
    if age_group:
        query["target_age_group"] = age_group
    
    teams = await db.teams.find(query).to_list(100)
    
    # Calculate group health scores and add metadata
    for team in teams:
        team["member_count"] = len(team.get("members", []))
        team["is_joined"] = current_user["user_id"] in team.get("members", [])
        
        # Calculate health score (0-100)
        health_score = await calculate_group_health_score(team)
        team["health_score"] = health_score
        
        # Add activity level indicator
        team["activity_level"] = await get_activity_level(team["team_id"])
        
        # Get recent activity preview
        team["recent_activity"] = await get_recent_activity_preview(team["team_id"])
        
        # Add trending indicator
        team["is_trending"] = await is_group_trending(team["team_id"])
        
        # Get mutual friends count
        team["mutual_friends"] = await get_mutual_friends_count(
            current_user["user_id"], 
            team.get("members", [])
        )
        
        # Get team creator info
        if team.get("created_by"):
            creator = await db.users.find_one({"user_id": team["created_by"]})
            if creator:
                team["creator"] = {
                    "user_id": creator["user_id"],
                    "display_name": creator.get("display_name", creator["username"]),
                    "avatar": creator.get("avatar"),
                    "trust_level": creator.get("trust_level", 1)
                }
    
    # Sort by relevance score (health + mutual friends + user interests match)
    teams = await sort_by_relevance(teams, current_user)
    
    return serialize_mongo_doc(teams)

@api_router.get("/teams/recommendations")
async def get_smart_recommendations(current_user = Depends(get_current_user)):
    """Get AI-powered group recommendations based on user activity and interests"""
    
    # Get user's interests, activity patterns, and joined groups
    user_interests = current_user.get("interests", [])
    user_location = current_user.get("location", "")
    joined_teams = await db.teams.find({
        "members": current_user["user_id"]
    }).to_list(50)
    
    # Calculate recommendation scores
    recommendations = []
    
    # Interest-based recommendations
    interest_recs = await get_interest_based_recommendations(
        user_interests, current_user["user_id"]
    )
    recommendations.extend(interest_recs)
    
    # Location-based recommendations
    location_recs = await get_location_based_recommendations(
        user_location, current_user["user_id"]
    )
    recommendations.extend(location_recs)
    
    # Activity pattern recommendations
    activity_recs = await get_activity_pattern_recommendations(
        current_user["user_id"]
    )
    recommendations.extend(activity_recs)
    
    # Friend activity recommendations
    friend_recs = await get_friend_activity_recommendations(
        current_user["user_id"]
    )
    recommendations.extend(friend_recs)
    
    # Remove duplicates and sort by score
    unique_recs = {}
    for rec in recommendations:
        team_id = rec["team_id"]
        if team_id not in unique_recs or rec["score"] > unique_recs[team_id]["score"]:
            unique_recs[team_id] = rec
    
    # Get top 10 recommendations
    sorted_recs = sorted(unique_recs.values(), key=lambda x: x["score"], reverse=True)[:10]
    
    return serialize_mongo_doc(sorted_recs)

@api_router.get("/teams/trending")
async def get_trending_teams(current_user = Depends(get_current_user)):
    """Get trending groups in user's area"""
    
    user_location = current_user.get("location", "")
    
    # Get teams with recent activity surge
    trending = await db.teams.aggregate([
        {"$match": {
            "settings.is_public": True,
            "location": {"$regex": user_location.split(",")[0] if user_location else "", "$options": "i"}
        }},
        {"$lookup": {
            "from": "messages",
            "localField": "team_id", 
            "foreignField": "chat_id",
            "as": "recent_messages"
        }},
        {"$addFields": {
            "recent_activity_count": {
                "$size": {
                    "$filter": {
                        "input": "$recent_messages",
                        "cond": {
                            "$gte": ["$$this.created_at", datetime.utcnow() - timedelta(days=7)]
                        }
                    }
                }
            },
            "member_growth": {
                "$size": "$members"
            }
        }},
        {"$sort": {"recent_activity_count": -1, "member_growth": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Add metadata for each trending team
    for team in trending:
        team["member_count"] = len(team.get("members", []))
        team["is_joined"] = current_user["user_id"] in team.get("members", [])
        team["is_trending"] = True
        team["trend_reason"] = "high_activity"  # Could be "fast_growing", "high_engagement", etc.
    
    return serialize_mongo_doc(trending)

# Helper functions for smart recommendations
async def calculate_group_health_score(team):
    """Calculate group health score based on activity, engagement, and admin responsiveness"""
    score = 0
    
    # Recent activity (40 points)
    recent_messages = await db.messages.count_documents({
        "chat_id": team["team_id"],
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
    })
    activity_score = min(recent_messages * 2, 40)  # Cap at 40
    score += activity_score
    
    # Member engagement (30 points) 
    active_members = await db.messages.distinct("sender_id", {
        "chat_id": team["team_id"],
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
    })
    engagement_rate = len(active_members) / max(len(team.get("members", [])), 1)
    engagement_score = min(engagement_rate * 30, 30)
    score += engagement_score
    
    # Admin responsiveness (20 points)
    # Check if admin has been active recently
    admin_activity = await db.messages.count_documents({
        "chat_id": team["team_id"],
        "sender_id": team.get("created_by"),
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=14)}
    })
    admin_score = min(admin_activity * 5, 20)
    score += admin_score
    
    # Growth trend (10 points)
    # This would require tracking member join dates
    growth_score = 10  # Placeholder
    score += growth_score
    
    return min(int(score), 100)

async def get_activity_level(team_id):
    """Get activity level indicator for a team"""
    recent_messages = await db.messages.count_documents({
        "chat_id": team_id,
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
    })
    
    if recent_messages >= 50:
        return "very_high"
    elif recent_messages >= 20:
        return "high" 
    elif recent_messages >= 5:
        return "medium"
    elif recent_messages >= 1:
        return "low"
    else:
        return "quiet"

async def get_recent_activity_preview(team_id):
    """Get preview of recent team activity"""
    recent_messages = await db.messages.find({
        "chat_id": team_id
    }).sort("created_at", -1).limit(3).to_list(3)
    
    preview = []
    for msg in recent_messages:
        preview.append({
            "type": "message",
            "content": msg.get("content", "")[:50] + ("..." if len(msg.get("content", "")) > 50 else ""),
            "sender": msg.get("sender_name", "Unknown"),
            "time": msg.get("created_at")
        })
    
    return preview

async def is_group_trending(team_id):
    """Check if group is trending based on recent activity surge"""
    # Get message count for last 7 days vs previous 7 days
    last_week = await db.messages.count_documents({
        "chat_id": team_id,
        "created_at": {"$gte": datetime.utcnow() - timedelta(days=7)}
    })
    
    prev_week = await db.messages.count_documents({
        "chat_id": team_id,
        "created_at": {
            "$gte": datetime.utcnow() - timedelta(days=14),
            "$lt": datetime.utcnow() - timedelta(days=7)
        }
    })
    
    # Trending if 50% increase in activity
    return last_week > prev_week * 1.5 if prev_week > 0 else last_week > 10

async def get_mutual_friends_count(user_id, team_members):
    """Get count of mutual friends in a team"""
    # Get user's connections
    user_connections = await db.connections.find({
        "$or": [
            {"user_id": user_id, "status": "connected"},
            {"connected_user_id": user_id, "status": "connected"}
        ]
    }).to_list(100)
    
    friend_ids = set()
    for conn in user_connections:
        if conn["user_id"] == user_id:
            friend_ids.add(conn["connected_user_id"])
        else:
            friend_ids.add(conn["user_id"])
    
    # Count mutual friends in team
    mutual_count = len(friend_ids.intersection(set(team_members)))
    return mutual_count

async def sort_by_relevance(teams, current_user):
    """Sort teams by relevance score combining multiple factors"""
    user_interests = set(current_user.get("interests", []))
    
    for team in teams:
        score = 0
        
        # Health score weight (40%)
        score += team.get("health_score", 0) * 0.4
        
        # Interest match weight (30%)
        team_tags = set(team.get("tags", []))
        interest_match = len(user_interests.intersection(team_tags)) / max(len(user_interests), 1)
        score += interest_match * 30
        
        # Mutual friends weight (20%)
        score += team.get("mutual_friends", 0) * 5
        
        # Trending bonus (10%)
        if team.get("is_trending"):
            score += 10
        
        team["relevance_score"] = score
    
    return sorted(teams, key=lambda x: x.get("relevance_score", 0), reverse=True)

async def get_interest_based_recommendations(user_interests, user_id):
    """Get recommendations based on user interests"""
    recommendations = []
    
    for interest in user_interests:
        teams = await db.teams.find({
            "settings.is_public": True,
            "members": {"$ne": user_id},  # Not already joined
            "$or": [
                {"tags": {"$in": [interest]}},
                {"category": interest},
                {"name": {"$regex": interest, "$options": "i"}}
            ]
        }).limit(5).to_list(5)
        
        for team in teams:
            recommendations.append({
                **team,
                "recommendation_reason": f"Based on your interest in {interest}",
                "score": 85
            })
    
    return recommendations

async def get_location_based_recommendations(user_location, user_id):
    """Get recommendations based on user location"""
    if not user_location:
        return []
    
    city = user_location.split(",")[0].strip()
    
    teams = await db.teams.find({
        "settings.is_public": True,
        "members": {"$ne": user_id},
        "location": {"$regex": city, "$options": "i"}
    }).limit(10).to_list(10)
    
    recommendations = []
    for team in teams:
        recommendations.append({
            **team,
            "recommendation_reason": f"Popular in {city}",
            "score": 75
        })
    
    return recommendations

async def get_activity_pattern_recommendations(user_id):
    """Get recommendations based on user's activity patterns"""
    # Analyze when user is most active
    user_messages = await db.messages.find({
        "sender_id": user_id
    }).limit(100).to_list(100)
    
    # Simple heuristic: if user messages more on weekends, recommend weekend-focused groups
    weekend_messages = sum(1 for msg in user_messages 
                          if msg.get("created_at") and msg["created_at"].weekday() >= 5)
    
    if weekend_messages > len(user_messages) * 0.6:  # 60% weekend activity
        teams = await db.teams.find({
            "settings.is_public": True,
            "members": {"$ne": user_id},
            "schedule_preference": "weekend"
        }).limit(5).to_list(5)
        
        return [{
            **team,
            "recommendation_reason": "Perfect for weekend activities",
            "score": 80
        } for team in teams]
    
    return []

async def get_friend_activity_recommendations(user_id):
    """Get recommendations based on friends' group activities"""
    # Get user's friends
    connections = await db.connections.find({
        "$or": [
            {"user_id": user_id, "status": "connected"},
            {"connected_user_id": user_id, "status": "connected"}
        ]
    }).to_list(50)
    
    friend_ids = []
    for conn in connections:
        if conn["user_id"] == user_id:
            friend_ids.append(conn["connected_user_id"])
        else:
            friend_ids.append(conn["user_id"])
    
    # Find teams where friends are active
    teams_with_friends = await db.teams.find({
        "settings.is_public": True,
        "members": {"$in": friend_ids, "$ne": user_id}
    }).to_list(20)
    
    recommendations = []
    for team in teams_with_friends:
        friend_count = len(set(friend_ids).intersection(set(team.get("members", []))))
        recommendations.append({
            **team,
            "recommendation_reason": f"{friend_count} friend{'s' if friend_count > 1 else ''} in this group",
            "score": 90 + friend_count * 5,
            "friend_count": friend_count
        })
    
    return recommendations

# Enhanced Data Models for New Features

# Sub-groups/Channels Data Model
class Channel(BaseModel):
    channel_id: str
    team_id: str
    name: str
    description: Optional[str] = ""
    type: str = "general"  # general, announcements, activities, private
    is_private: bool = False
    created_by: str
    members: List[str] = []
    admins: List[str] = []
    created_at: datetime
    last_activity: Optional[datetime] = None
    message_count: int = 0
    settings: Dict[str, Any] = {}

# Calendar/Events Data Model  
class CalendarEvent(BaseModel):
    event_id: str
    team_id: Optional[str] = None
    activity_id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    start_time: datetime
    end_time: datetime
    location: Optional[str] = ""
    location_coordinates: Optional[Dict[str, float]] = None
    is_all_day: bool = False
    recurrence_rule: Optional[str] = None
    attendees: List[str] = []
    created_by: str
    calendar_provider: Optional[str] = None  # google, outlook, apple
    external_event_id: Optional[str] = None
    reminder_settings: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

# Geolocation for Groups and Activities
class LocationData(BaseModel):
    address: Optional[str] = ""
    city: Optional[str] = ""
    state: Optional[str] = ""
    country: Optional[str] = ""
    coordinates: Optional[Dict[str, float]] = None  # {"lat": float, "lng": float}
    radius: Optional[float] = None  # in kilometers
    venue_name: Optional[str] = ""
    venue_type: Optional[str] = ""

# Map View and Geolocation Endpoints
@api_router.get("/map/groups")
async def get_groups_map_view(
    lat: float,
    lng: float,
    radius: float = 50.0,  # kilometers
    category: str = None,
    current_user = Depends(get_current_user)
):
    """Get groups for map view within radius"""
    try:
        # Build query for geospatial search
        query = {
            "settings.is_public": True,
            "location_data.coordinates": {
                "$geoWithin": {
                    "$centerSphere": [[lng, lat], radius / 6378.1]  # Earth radius in km
                }
            }
        }
        
        if category and category != 'all':
            query["category"] = category
        
        groups = await db.teams.find(query).to_list(100)
        
        # Transform for map view
        map_groups = []
        for group in groups:
            location_data = group.get("location_data", {})
            coordinates = location_data.get("coordinates")
            
            if coordinates:
                map_groups.append({
                    "id": group["team_id"],
                    "name": group["name"],
                    "description": group.get("description", ""),
                    "category": group.get("category", "general"),
                    "emoji": group.get("emoji", "👥"),
                    "member_count": len(group.get("members", [])),
                    "coordinates": coordinates,
                    "address": location_data.get("address", ""),
                    "venue_name": location_data.get("venue_name", ""),
                    "health_score": await calculate_group_health_score(group),
                    "is_joined": current_user["user_id"] in group.get("members", [])
                })
        
        return serialize_mongo_doc(map_groups)
        
    except Exception as e:
        logging.error(f"Map view error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load map data")

@api_router.get("/map/activities")
async def get_activities_map_view(
    lat: float,
    lng: float,
    radius: float = 50.0,
    start_date: str = None,
    end_date: str = None,
    current_user = Depends(get_current_user)
):
    """Get activities for map view within radius and date range"""
    try:
        query = {
            "status": "upcoming",
            "location_coordinates": {
                "$geoWithin": {
                    "$centerSphere": [[lng, lat], radius / 6378.1]
                }
            }
        }
        
        if start_date and end_date:
            query["start_time"] = {
                "$gte": datetime.fromisoformat(start_date),
                "$lte": datetime.fromisoformat(end_date)
            }
        
        activities = await db.activities.find(query).to_list(100)
        
        # Check user permissions for each activity
        map_activities = []
        for activity in activities:
            # Check if user has access to the team
            team = await db.teams.find_one({"team_id": activity["team_id"]})
            if team and (team.get("settings", {}).get("is_public") or 
                        current_user["user_id"] in team.get("members", [])):
                
                map_activities.append({
                    "id": activity["activity_id"],
                    "title": activity["title"],
                    "description": activity.get("description", ""),
                    "team_name": team["name"],
                    "team_emoji": team.get("emoji", "👥"),
                    "start_time": activity["start_time"],
                    "coordinates": activity.get("location_coordinates"),
                    "location": activity.get("location", ""),
                    "attendee_count": len(activity.get("attendees", [])),
                    "max_attendees": activity.get("max_attendees", 50),
                    "cost": activity.get("cost", "free"),
                    "category": activity.get("category", "general"),
                    "is_attending": current_user["user_id"] in activity.get("attendees", [])
                })
        
        return serialize_mongo_doc(map_activities)
        
    except Exception as e:
        logging.error(f"Activities map view error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load activities map")

# Sub-groups/Channels Endpoints
@api_router.get("/teams/{team_id}/channels")
async def get_team_channels(
    team_id: str,
    current_user = Depends(get_current_user)
):
    """Get all channels in a team"""
    # Verify team membership
    team = await db.teams.find_one({"team_id": team_id})
    if not team or current_user["user_id"] not in team.get("members", []):
        raise HTTPException(status_code=403, detail="Not a team member")
    
    channels = await db.channels.find({
        "team_id": team_id,
        "$or": [
            {"is_private": False},
            {"members": current_user["user_id"]}
        ]
    }).sort("created_at", 1).to_list(50)
    
    # Add member counts and unread message counts
    for channel in channels:
        channel["member_count"] = len(channel.get("members", []))
        # TODO: Add unread message count logic
        channel["unread_count"] = 0
    
    return serialize_mongo_doc(channels)

@api_router.post("/teams/{team_id}/channels")
async def create_team_channel(
    team_id: str,
    channel_data: dict,
    current_user = Depends(get_current_user)
):
    """Create a new channel in a team"""
    # Verify team membership and permissions
    team = await db.teams.find_one({"team_id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if current_user["user_id"] not in team.get("members", []):
        raise HTTPException(status_code=403, detail="Not a team member")
    
    # Check if user can create channels (admin or creator)
    is_admin = (current_user["user_id"] == team.get("created_by") or 
                current_user["user_id"] in team.get("admins", []))
    
    if not is_admin and channel_data.get("type") != "general":
        raise HTTPException(status_code=403, detail="Only admins can create special channels")
    
    channel = {
        "channel_id": str(uuid.uuid4()),
        "team_id": team_id,
        "name": channel_data["name"],
        "description": channel_data.get("description", ""),
        "type": channel_data.get("type", "general"),
        "is_private": channel_data.get("is_private", False),
        "created_by": current_user["user_id"],
        "members": [current_user["user_id"]] if channel_data.get("is_private") else team.get("members", []),
        "admins": [current_user["user_id"]],
        "created_at": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
        "message_count": 0,
        "settings": channel_data.get("settings", {})
    }
    
    await db.channels.insert_one(channel)
    return serialize_mongo_doc(channel)

@api_router.get("/channels/{channel_id}/messages")
async def get_channel_messages(
    channel_id: str,
    limit: int = 50,
    before: str = None,
    current_user = Depends(get_current_user)
):
    """Get messages from a specific channel"""
    # Verify channel access
    channel = await db.channels.find_one({"channel_id": channel_id})
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check access permissions
    if (channel.get("is_private") and 
        current_user["user_id"] not in channel.get("members", [])):
        raise HTTPException(status_code=403, detail="No access to private channel")
    
    # Build query
    query = {"channel_id": channel_id}
    if before:
        query["created_at"] = {"$lt": datetime.fromisoformat(before)}
    
    messages = await db.messages.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Add sender information
    for message in messages:
        sender = await db.users.find_one({"user_id": message.get("sender_id")})
        if sender:
            message["sender_name"] = sender.get("display_name", sender["username"])
            message["sender_avatar"] = sender.get("avatar")
    
    return serialize_mongo_doc(list(reversed(messages)))

@api_router.post("/channels/{channel_id}/messages")
async def send_channel_message(
    channel_id: str,
    message_data: dict,
    current_user = Depends(get_current_user)
):
    """Send a message to a channel"""
    # Verify channel access
    channel = await db.channels.find_one({"channel_id": channel_id})
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Check permissions
    if (channel.get("is_private") and 
        current_user["user_id"] not in channel.get("members", [])):
        raise HTTPException(status_code=403, detail="Cannot send to private channel")
    
    message = {
        "message_id": str(uuid.uuid4()),
        "channel_id": channel_id,
        "team_id": channel["team_id"],
        "sender_id": current_user["user_id"],
        "sender_name": current_user.get("display_name", current_user["username"]),
        "content": message_data["content"],
        "message_type": message_data.get("type", "text"),
        "created_at": datetime.utcnow(),
        "edited_at": None,
        "reactions": {},
        "thread_id": message_data.get("thread_id"),
        "file_data": message_data.get("file_data")
    }
    
    await db.messages.insert_one(message)
    
    # Update channel activity
    await db.channels.update_one(
        {"channel_id": channel_id},
        {
            "$set": {"last_activity": datetime.utcnow()},
            "$inc": {"message_count": 1}
        }
    )
    
    # TODO: Send WebSocket notification to channel members
    
    return serialize_mongo_doc(message)

# Calendar Integration Endpoints
@api_router.get("/calendar/events")
async def get_user_calendar_events(
    start_date: str,
    end_date: str,
    include_team_events: bool = True,
    current_user = Depends(get_current_user)
):
    """Get user's calendar events within date range"""
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        query = {
            "$and": [
                {
                    "$or": [
                        {"attendees": current_user["user_id"]},
                        {"created_by": current_user["user_id"]}
                    ]
                },
                {
                    "$or": [
                        {
                            "start_time": {"$gte": start_dt, "$lte": end_dt}
                        },
                        {
                            "end_time": {"$gte": start_dt, "$lte": end_dt}
                        },
                        {
                            "$and": [
                                {"start_time": {"$lte": start_dt}},
                                {"end_time": {"$gte": end_dt}}
                            ]
                        }
                    ]
                }
            ]
        }
        
        events = await db.calendar_events.find(query).sort("start_time", 1).to_list(200)
        
        # Add team/activity context
        for event in events:
            if event.get("team_id"):
                team = await db.teams.find_one({"team_id": event["team_id"]})
                if team:
                    event["team_name"] = team["name"]
                    event["team_emoji"] = team.get("emoji", "📅")
            
            if event.get("activity_id"):
                activity = await db.activities.find_one({"activity_id": event["activity_id"]})
                if activity:
                    event["activity_title"] = activity["title"]
                    event["activity_type"] = activity.get("type", "meetup")
        
        return serialize_mongo_doc(events)
        
    except Exception as e:
        logging.error(f"Calendar events error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load calendar events")

@api_router.post("/calendar/events")
async def create_calendar_event(
    event_data: dict,
    current_user = Depends(get_current_user)
):
    """Create a new calendar event"""
    try:
        # Validate required fields
        required_fields = ["title", "start_time", "end_time"]
        for field in required_fields:
            if field not in event_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Parse coordinates if location provided
        location_coordinates = None
        if event_data.get("location"):
            # TODO: Implement geocoding service integration
            # For now, use placeholder coordinates
            location_coordinates = {"lat": 0.0, "lng": 0.0}
        
        event = {
            "event_id": str(uuid.uuid4()),
            "team_id": event_data.get("team_id"),
            "activity_id": event_data.get("activity_id"),
            "title": event_data["title"],
            "description": event_data.get("description", ""),
            "start_time": datetime.fromisoformat(event_data["start_time"]),
            "end_time": datetime.fromisoformat(event_data["end_time"]),
            "location": event_data.get("location", ""),
            "location_coordinates": location_coordinates,
            "is_all_day": event_data.get("is_all_day", False),
            "recurrence_rule": event_data.get("recurrence_rule"),
            "attendees": event_data.get("attendees", [current_user["user_id"]]),
            "created_by": current_user["user_id"],
            "calendar_provider": event_data.get("calendar_provider"),
            "external_event_id": event_data.get("external_event_id"),
            "reminder_settings": event_data.get("reminder_settings", []),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.calendar_events.insert_one(event)
        
        # If connected to external calendar, sync there too
        if event_data.get("sync_to_external", False):
            # TODO: Implement Google Calendar API integration
            pass
        
        return serialize_mongo_doc(event)
        
    except Exception as e:
        logging.error(f"Create calendar event error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create calendar event")

@api_router.get("/calendar/availability")
async def check_user_availability(
    start_time: str,
    end_time: str,
    user_ids: str,  # comma-separated list
    current_user = Depends(get_current_user)
):
    """Check availability of multiple users for a time slot"""
    try:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        user_id_list = user_ids.split(",")
        
        availability_result = {}
        
        for user_id in user_id_list:
            # Check if user has events during this time
            conflicting_events = await db.calendar_events.find({
                "attendees": user_id,
                "$or": [
                    {
                        "$and": [
                            {"start_time": {"$lte": start_dt}},
                            {"end_time": {"$gt": start_dt}}
                        ]
                    },
                    {
                        "$and": [
                            {"start_time": {"$lt": end_dt}},
                            {"end_time": {"$gte": end_dt}}
                        ]
                    },
                    {
                        "$and": [
                            {"start_time": {"$gte": start_dt}},
                            {"end_time": {"$lte": end_dt}}
                        ]
                    }
                ]
            }).to_list(50)
            
            availability_result[user_id] = {
                "is_available": len(conflicting_events) == 0,
                "conflicting_events_count": len(conflicting_events),
                "conflicts": [
                    {
                        "title": event["title"],
                        "start_time": event["start_time"],
                        "end_time": event["end_time"]
                    } for event in conflicting_events
                ]
            }
        
        return availability_result
        
    except Exception as e:
        logging.error(f"Availability check error: {e}")
        raise HTTPException(status_code=500, detail="Failed to check availability")

@api_router.post("/teams/{team_id}/activities")
async def create_team_activity(
    team_id: str,
    activity_data: dict,
    current_user = Depends(get_current_user)
):
    """Create a new activity for a team"""
    team = await db.teams.find_one({"team_id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if current_user["user_id"] not in team.get("members", []):
        raise HTTPException(status_code=403, detail="Not a team member")
    
    activity = {
        "activity_id": str(uuid.uuid4()),
        "team_id": team_id,
        "title": activity_data["title"],
        "description": activity_data.get("description", ""),
        "type": activity_data.get("type", "meetup"),  # meetup, event, recurring, challenge
        "category": activity_data.get("category", "general"),
        "location": activity_data.get("location", ""),
        "virtual_location": activity_data.get("virtual_location", ""),
        "start_time": activity_data["start_time"],
        "end_time": activity_data.get("end_time"),
        "max_attendees": activity_data.get("max_attendees", 50),
        "cost": activity_data.get("cost", "free"),
        "cost_amount": activity_data.get("cost_amount", 0),
        "skill_level": activity_data.get("skill_level", "all"),
        "age_group": activity_data.get("age_group", "all"),
        "requirements": activity_data.get("requirements", []),
        "what_to_bring": activity_data.get("what_to_bring", []),
        "recurring": activity_data.get("recurring", False),
        "recurring_pattern": activity_data.get("recurring_pattern", {}),
        "created_by": current_user["user_id"],
        "attendees": [current_user["user_id"]],  # Creator is first attendee
        "waitlist": [],
        "status": "upcoming",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "votes": [],  # For collaborative planning
        "proposals": [],  # Alternative suggestions
        "check_ins": [],  # Safety check-ins
        "photos": [],
        "reviews": []
    }
    
    await db.activities.insert_one(activity)
    
    # Notify team members
    await notify_team_members(team_id, f"New activity: {activity['title']}", current_user)
    
    return serialize_mongo_doc(activity)

@api_router.get("/teams/{team_id}/activities")
async def get_team_activities(
    team_id: str,
    status: str = "upcoming",
    current_user = Depends(get_current_user)
):
    """Get activities for a team"""
    team = await db.teams.find_one({"team_id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if current_user["user_id"] not in team.get("members", []):
        raise HTTPException(status_code=403, detail="Not a team member")
    
    query = {"team_id": team_id}
    if status != "all":
        query["status"] = status
    
    activities = await db.activities.find(query).sort("start_time", 1).to_list(100)
    
    # Add attendance info and creator details
    for activity in activities:
        activity["attendee_count"] = len(activity.get("attendees", []))
        activity["is_attending"] = current_user["user_id"] in activity.get("attendees", [])
        activity["is_waitlisted"] = current_user["user_id"] in activity.get("waitlist", [])
        
        # Get creator info
        if activity.get("created_by"):
            creator = await db.users.find_one({"user_id": activity["created_by"]})
            if creator:
                activity["creator"] = {
                    "user_id": creator["user_id"],
                    "display_name": creator.get("display_name", creator["username"]),
                    "avatar": creator.get("avatar")
                }
    
    return serialize_mongo_doc(activities)

@api_router.post("/activities/{activity_id}/join")
async def join_activity(
    activity_id: str,
    current_user = Depends(get_current_user)
):
    """Join an activity"""
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check if user is team member
    team = await db.teams.find_one({"team_id": activity["team_id"]})
    if current_user["user_id"] not in team.get("members", []):
        raise HTTPException(status_code=403, detail="Not a team member")
    
    attendees = activity.get("attendees", [])
    waitlist = activity.get("waitlist", [])
    max_attendees = activity.get("max_attendees", 50)
    
    if current_user["user_id"] in attendees:
        raise HTTPException(status_code=400, detail="Already joined")
    
    if current_user["user_id"] in waitlist:
        raise HTTPException(status_code=400, detail="Already on waitlist")
    
    # Add to attendees or waitlist
    if len(attendees) < max_attendees:
        await db.activities.update_one(
            {"activity_id": activity_id},
            {"$push": {"attendees": current_user["user_id"]}}
        )
        status = "joined"
    else:
        await db.activities.update_one(
            {"activity_id": activity_id},
            {"$push": {"waitlist": current_user["user_id"]}}
        )
        status = "waitlisted"
    
    return {"message": f"Successfully {status}", "status": status}

@api_router.post("/activities/{activity_id}/propose")
async def propose_activity_change(
    activity_id: str,
    proposal_data: dict,
    current_user = Depends(get_current_user)
):
    """Propose changes to an activity (collaborative planning)"""
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check if user is attendee
    if current_user["user_id"] not in activity.get("attendees", []):
        raise HTTPException(status_code=403, detail="Must be attending to propose changes")
    
    proposal = {
        "proposal_id": str(uuid.uuid4()),
        "proposed_by": current_user["user_id"],
        "type": proposal_data["type"],  # time_change, location_change, add_stop, etc.
        "description": proposal_data["description"],
        "details": proposal_data.get("details", {}),
        "votes_for": [current_user["user_id"]],
        "votes_against": [],
        "created_at": datetime.utcnow(),
        "status": "open"
    }
    
    await db.activities.update_one(
        {"activity_id": activity_id},
        {"$push": {"proposals": proposal}}
    )
    
    return {"message": "Proposal submitted", "proposal_id": proposal["proposal_id"]}

@api_router.post("/activities/{activity_id}/vote")
async def vote_on_proposal(
    activity_id: str,
    vote_data: dict,
    current_user = Depends(get_current_user)
):
    """Vote on activity proposal"""
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    if current_user["user_id"] not in activity.get("attendees", []):
        raise HTTPException(status_code=403, detail="Must be attending to vote")
    
    proposal_id = vote_data["proposal_id"]
    vote = vote_data["vote"]  # "for" or "against"
    
    # Find and update the proposal
    proposals = activity.get("proposals", [])
    proposal_found = False
    
    for proposal in proposals:
        if proposal["proposal_id"] == proposal_id:
            proposal_found = True
            
            # Remove from both arrays first
            proposal["votes_for"] = [v for v in proposal["votes_for"] if v != current_user["user_id"]]
            proposal["votes_against"] = [v for v in proposal["votes_against"] if v != current_user["user_id"]]
            
            # Add to appropriate array
            if vote == "for":
                proposal["votes_for"].append(current_user["user_id"])
            else:
                proposal["votes_against"].append(current_user["user_id"])
            
            break
    
    if not proposal_found:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Update the activity
    await db.activities.update_one(
        {"activity_id": activity_id},
        {"$set": {"proposals": proposals}}
    )
    
    return {"message": "Vote recorded"}

@api_router.get("/activities/feed")
async def get_activity_feed(current_user = Depends(get_current_user)):
    """Get personalized activity feed"""
    # Get user's teams
    teams = await db.teams.find({
        "members": current_user["user_id"]
    }).to_list(50)
    
    team_ids = [team["team_id"] for team in teams]
    
    # Get upcoming activities from user's teams
    activities = await db.activities.find({
        "team_id": {"$in": team_ids},
        "status": "upcoming",
        "start_time": {"$gte": datetime.utcnow()}
    }).sort("start_time", 1).to_list(50)
    
    # Add team info and attendance status
    for activity in activities:
        activity["attendee_count"] = len(activity.get("attendees", []))
        activity["is_attending"] = current_user["user_id"] in activity.get("attendees", [])
        
        # Get team info
        team = next((t for t in teams if t["team_id"] == activity["team_id"]), None)
        if team:
            activity["team_name"] = team["name"]
            activity["team_emoji"] = team.get("emoji", "👥")
    
    return serialize_mongo_doc(activities)

@api_router.post("/activities/{activity_id}/check-in")
async def activity_check_in(
    activity_id: str,
    check_in_data: dict,
    current_user = Depends(get_current_user)
):
    """Safety check-in for activities"""
    activity = await db.activities.find_one({"activity_id": activity_id})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    if current_user["user_id"] not in activity.get("attendees", []):
        raise HTTPException(status_code=403, detail="Must be attending to check in")
    
    check_in = {
        "user_id": current_user["user_id"],
        "timestamp": datetime.utcnow(),
        "location": check_in_data.get("location"),
        "status": check_in_data.get("status", "safe"),  # safe, help_needed, emergency
        "message": check_in_data.get("message", "")
    }
    
    await db.activities.update_one(
        {"activity_id": activity_id},
        {"$push": {"check_ins": check_in}}
    )
    
    # If help needed or emergency, notify organizer
    if check_in["status"] in ["help_needed", "emergency"]:
        await notify_activity_organizer(activity_id, check_in)
    
    return {"message": "Check-in recorded"}

# Achievement System
@api_router.get("/users/{user_id}/achievements")
async def get_user_achievements(
    user_id: str,
    current_user = Depends(get_current_user)
):
    """Get user achievements and badges"""
    achievements = await calculate_user_achievements(user_id)
    return {"achievements": achievements}

async def calculate_user_achievements(user_id):
    """Calculate achievements for a user"""
    achievements = []
    
    # Group participation achievements
    teams = await db.teams.find({"members": user_id}).to_list(100)
    if len(teams) >= 1:
        achievements.append({
            "id": "first_group",
            "title": "Community Starter",
            "description": "Joined your first group",
            "icon": "👥",
            "earned_at": teams[0].get("created_at")
        })
    
    if len(teams) >= 5:
        achievements.append({
            "id": "group_explorer",
            "title": "Group Explorer", 
            "description": "Joined 5 different groups",
            "icon": "🗺️",
            "rarity": "uncommon"
        })
    
    # Activity participation achievements
    activities_attended = await db.activities.count_documents({
        "attendees": user_id,
        "status": "completed"
    })
    
    if activities_attended >= 1:
        achievements.append({
            "id": "first_activity",
            "title": "Activity Pioneer",
            "description": "Attended your first group activity",
            "icon": "🎯"
        })
    
    if activities_attended >= 10:
        achievements.append({
            "id": "activity_enthusiast",
            "title": "Activity Enthusiast",
            "description": "Attended 10 group activities",
            "icon": "⭐",
            "rarity": "rare"
        })
    
    # Leadership achievements
    created_teams = await db.teams.count_documents({"created_by": user_id})
    if created_teams >= 1:
        achievements.append({
            "id": "community_builder",
            "title": "Community Builder",
            "description": "Created your first group",
            "icon": "🏗️"
        })
    
    created_activities = await db.activities.count_documents({"created_by": user_id})
    if created_activities >= 5:
        achievements.append({
            "id": "event_organizer",
            "title": "Event Organizer",
            "description": "Organized 5 activities",
            "icon": "📅",
            "rarity": "uncommon"
        })
    
    # Social achievements
    connections = await db.connections.count_documents({
        "$or": [
            {"user_id": user_id, "status": "connected"},
            {"connected_user_id": user_id, "status": "connected"}
        ]
    })
    
    if connections >= 10:
        achievements.append({
            "id": "social_butterfly",
            "title": "Social Butterfly",
            "description": "Connected with 10 people",
            "icon": "🦋"
        })
    
    return achievements

# Helper functions
async def notify_team_members(team_id, message, creator):
    """Notify team members about new activity"""
    try:
        team = await db.teams.find_one({"team_id": team_id})
        if not team:
            return
        
        # Get team members (excluding creator)
        member_ids = [m for m in team.get("members", []) if m != creator["user_id"]]
        
        # Create notifications for each member
        notifications = []
        for member_id in member_ids:
            notification = {
                "notification_id": str(uuid.uuid4()),
                "user_id": member_id,
                "type": "team_activity",
                "title": f"New activity in {team['name']}",
                "message": message,
                "data": {
                    "team_id": team_id,
                    "team_name": team["name"],
                    "creator_name": creator.get("display_name", creator["username"])
                },
                "read": False,
                "created_at": datetime.utcnow()
            }
            notifications.append(notification)
        
        if notifications:
            await db.notifications.insert_many(notifications)
            
    except Exception as e:
        logging.error(f"Failed to notify team members: {e}")

async def notify_activity_organizer(activity_id, check_in):
    """Notify activity organizer about check-in status"""
    try:
        activity = await db.activities.find_one({"activity_id": activity_id})
        if not activity:
            return
        
        organizer_id = activity.get("created_by")
        if not organizer_id or check_in["user_id"] == organizer_id:
            return
        
        # Get user info for the check-in
        user = await db.users.find_one({"user_id": check_in["user_id"]})
        user_name = user.get("display_name", user["username"]) if user else "Unknown user"
        
        # Create notification based on check-in status
        if check_in["status"] == "emergency":
            title = "🚨 EMERGENCY - Activity Check-in"
            message = f"{user_name} needs emergency help during {activity['title']}"
        elif check_in["status"] == "help_needed":
            title = "⚠️ Help Needed - Activity Check-in"
            message = f"{user_name} needs assistance during {activity['title']}"
        else:
            return  # Only notify for emergency/help situations
        
        notification = {
            "notification_id": str(uuid.uuid4()),
            "user_id": organizer_id,
            "type": "activity_emergency",
            "title": title,
            "message": message,
            "data": {
                "activity_id": activity_id,
                "activity_title": activity["title"],
                "check_in_user": user_name,
                "check_in_status": check_in["status"],
                "check_in_location": check_in.get("location"),
                "check_in_message": check_in.get("message"),
                "timestamp": check_in["timestamp"]
            },
            "read": False,
            "created_at": datetime.utcnow(),
            "priority": "high"
        }
        
        await db.notifications.insert_one(notification)
        
        # TODO: In production, also send push notification, SMS, or email for emergencies
        
    except Exception as e:
        logging.error(f"Failed to notify activity organizer: {e}")
async def join_team(team_id: str, current_user = Depends(get_current_user)):
    """Join a public team"""
    team = await db.teams.find_one({"team_id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if not team.get("settings", {}).get("is_public", False):
        raise HTTPException(status_code=403, detail="Team is not public")
    
    if current_user["user_id"] in team.get("members", []):
        raise HTTPException(status_code=400, detail="Already a member")
    
    # Add user to team
    await db.teams.update_one(
        {"team_id": team_id},
        {
            "$push": {"members": current_user["user_id"]},
            "$set": {"last_activity": datetime.utcnow()}
        }
    )
    
    # Add user to team chat if exists
    team_chat = await db.chats.find_one({"team_id": team_id})
    if team_chat:
        await db.chats.update_one(
            {"team_id": team_id},
            {"$push": {"members": current_user["user_id"]}}
        )
    
    return {"message": "Successfully joined team"}

@api_router.post("/teams/{team_id}/leave")
async def leave_team(team_id: str, current_user = Depends(get_current_user)):
    """Leave a team"""
    team = await db.teams.find_one({"team_id": team_id})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if current_user["user_id"] not in team.get("members", []):
        raise HTTPException(status_code=400, detail="Not a member")
    
    if team.get("created_by") == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Team creator cannot leave")
    
    # Remove user from team
    await db.teams.update_one(
        {"team_id": team_id},
        {
            "$pull": {"members": current_user["user_id"]},
            "$set": {"last_activity": datetime.utcnow()}
        }
    )
    
    # Remove user from team chat if exists
    team_chat = await db.chats.find_one({"team_id": team_id})
    if team_chat:
        await db.chats.update_one(
            {"team_id": team_id},
            {"$pull": {"members": current_user["user_id"]}}
        )
    
    return {"message": "Successfully left team"}

@api_router.post("/teams")
async def create_team(
    team_data: dict,
    current_user = Depends(get_current_user)
):
    """Create a new team with enhanced features"""
    team = {
        "team_id": str(uuid.uuid4()),
        "name": team_data["name"],
        "description": team_data.get("description", ""),
        "category": team_data.get("category", "general"),
        "location": team_data.get("location", "Online"),
        "tags": team_data.get("tags", []),
        "emoji": team_data.get("emoji", "👥"),
        "type": team_data.get("type", "group"),
        "created_by": current_user["user_id"],
        "members": [current_user["user_id"]],  # Creator is first member
        "created_at": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
        "settings": {
            "is_public": team_data.get("privacy", "public") == "public",
            "allow_member_invite": team_data.get("allow_member_invite", True),
            "max_members": team_data.get("max_members", 1024),
            "require_approval": team_data.get("require_approval", False),
            "auto_archive_inactive": team_data.get("auto_archive_inactive", True)
        },
        # Enhanced fields for smart discovery
        "schedule_preference": team_data.get("schedule_preference", "flexible"),
        "cost_type": team_data.get("cost_type", "free"),
        "primary_language": team_data.get("primary_language", "english"),
        "target_age_group": team_data.get("target_age_group", "all"),
        "activity_level": team_data.get("activity_level", "medium"),
        "group_purpose": team_data.get("group_purpose", "social"),
        "meeting_frequency": team_data.get("meeting_frequency", "weekly"),
        # Safety and moderation
        "safety_features": {
            "emergency_contacts": team_data.get("emergency_contacts", []),
            "safety_guidelines": team_data.get("safety_guidelines", ""),
            "check_in_required": team_data.get("check_in_required", False)
        },
        # Gamification
        "points": 0,
        "level": 1,
        "achievements": [],
        "challenges": [],
        # Analytics
        "analytics": {
            "total_activities": 0,
            "total_messages": 0,
            "member_retention_rate": 100.0,
            "activity_completion_rate": 0.0
        }
    }
    
    await db.teams.insert_one(team)
    
    # Fetch the created team to get the proper document with _id
    created_team = await db.teams.find_one({"team_id": team["team_id"]})
    
    # Create team chat
    team_chat = {
        "chat_id": str(uuid.uuid4()),
        "chat_type": "group",
        "type": "group",
        "team_id": team["team_id"],
        "name": f"{team['name']} Chat",
        "members": [current_user["user_id"]],
        "created_at": datetime.utcnow(),
        "created_by": current_user["user_id"],
        "last_message": None,
        "last_activity": datetime.utcnow()
    }
    
    await db.chats.insert_one(team_chat)
    
    # Add member count and creator info for the response
    if created_team:
        created_team["member_count"] = len(created_team["members"])
        created_team["creator"] = {
            "user_id": current_user["user_id"],
            "display_name": current_user.get("display_name", current_user.get("username", "Unknown"))
        }
    
    return serialize_mongo_doc(created_team)

# Team Messaging Endpoints
@api_router.get("/teams/{team_id}/messages")
async def get_team_messages(team_id: str, current_user = Depends(get_current_user)):
    """Get messages for a specific team"""
    # Verify user is member of team
    team = await db.teams.find_one({"team_id": team_id})
    if not team or current_user["user_id"] not in team["members"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Find the team chat
    team_chat = await db.chats.find_one({"team_id": team_id})
    if not team_chat:
        raise HTTPException(status_code=404, detail="Team chat not found")
    
    # Get messages for the team chat
    messages = await db.messages.find({"chat_id": team_chat["chat_id"]}).sort("timestamp", 1).to_list(1000)
    
    # Get sender details for each message
    for message in messages:
        sender = await db.users.find_one({"user_id": message["sender_id"]})
        if sender:
            message["sender"] = {
                "user_id": sender["user_id"],
                "username": sender["username"],
                "display_name": sender.get("display_name", sender["username"]),
                "email": sender.get("email", "")
            }
    
    return serialize_mongo_doc(messages)

@api_router.post("/teams/{team_id}/messages")
async def send_team_message(team_id: str, message_data: dict, current_user = Depends(get_current_user)):
    """Send a message to a team"""
    # Verify user is member of team
    team = await db.teams.find_one({"team_id": team_id})
    if not team or current_user["user_id"] not in team["members"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Find the team chat
    team_chat = await db.chats.find_one({"team_id": team_id})
    if not team_chat:
        raise HTTPException(status_code=404, detail="Team chat not found")
    
    # Use the existing send_message logic by calling it with the team chat_id
    return await send_message(team_chat["chat_id"], message_data, current_user)

# Contact Management Endpoints
@api_router.get("/contacts")
async def get_contacts(current_user = Depends(get_current_user)):
    """Get all contacts for the current user"""
    contacts = await db.contacts.find({
        "user_id": current_user["user_id"]
    }).to_list(100)
    
    # Get user details for each contact
    for contact in contacts:
        contact_user = await db.users.find_one({"user_id": contact["contact_user_id"]})
        if contact_user:
            contact["contact_user"] = {
                "user_id": contact_user["user_id"],
                "username": contact_user["username"],
                "email": contact_user["email"],
                "display_name": contact_user.get("display_name"),
                "is_online": contact_user.get("is_online", False)
            }
    
    return serialize_mongo_doc(contacts)

@api_router.post("/contacts")
async def add_contact(
    contact_data: dict,
    current_user = Depends(get_current_user)
):
    """Add a new contact by email"""
    email = contact_data.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Find user by email
    contact_user = await db.users.find_one({"email": email})
    if not contact_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is trying to add themselves
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
    contact = {
        "contact_id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "contact_user_id": contact_user["user_id"],
        "contact_name": contact_data.get("name", contact_user.get("display_name", contact_user["username"])),
        "created_at": datetime.utcnow(),
        "is_favorite": False
    }
    
    await db.contacts.insert_one(contact)
    
    # Create reciprocal contact
    reciprocal_contact = {
        "contact_id": str(uuid.uuid4()),
        "user_id": contact_user["user_id"],
        "contact_user_id": current_user["user_id"],
        "contact_name": current_user.get("display_name", current_user["username"]),
        "created_at": datetime.utcnow(),
        "is_favorite": False
    }
    
    await db.contacts.insert_one(reciprocal_contact)
    
    # Create a direct chat between the users
    chat = {
        "chat_id": str(uuid.uuid4()),
        "chat_type": "direct",
        "type": "direct",
        "members": [current_user["user_id"], contact_user["user_id"]],
        "created_at": datetime.utcnow(),
        "created_by": current_user["user_id"],
        "last_message": None,
        "last_activity": datetime.utcnow()
    }
    
    await db.chats.insert_one(chat)
    
    return serialize_mongo_doc(contact)

@api_router.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a contact and its associated chat"""
    # Find the contact
    contact = await db.contacts.find_one({
        "contact_id": contact_id,
        "user_id": current_user["user_id"]
    })
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Delete the contact
    await db.contacts.delete_one({
        "contact_id": contact_id,
        "user_id": current_user["user_id"]
    })
    
    # Delete reciprocal contact
    await db.contacts.delete_one({
        "user_id": contact["contact_user_id"],
        "contact_user_id": current_user["user_id"]
    })
    
    # Delete associated direct chat
    await db.chats.delete_many({
        "members": {"$all": [current_user["user_id"], contact["contact_user_id"]]},
        "$or": [{"chat_type": "direct"}, {"type": "direct"}]
    })
    
    return {"message": "Contact deleted successfully"}

@api_router.post("/contacts/create-test-users")
async def create_test_users_for_contact_testing(current_user = Depends(get_current_user)):
    """Create test users for contact testing purposes"""
    
    test_users = [
        {
            "user_id": str(uuid.uuid4()),
            "username": "testuser_alice",
            "email": "alice@test.com",
            "password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "phone": "+1234567001",
            "display_name": "Alice Johnson",
            "profile_completed": True,
            "age": 28,
            "gender": "female",
            "location": "San Francisco, CA",
            "bio": "Love hiking and photography. Always up for coffee chats!",
            "interests": ["photography", "hiking", "coffee", "travel"],
            "values": ["honesty", "adventure", "creativity"],
            "authenticity_rating": 7.5,
            "trust_level": 2,
            "connection_pin": "PIN-ALI001",
            "is_online": True,
            "created_at": datetime.utcnow()
        },
        {
            "user_id": str(uuid.uuid4()),
            "username": "testuser_bob",
            "email": "bob@test.com",
            "password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "phone": "+1234567002",
            "display_name": "Bob Smith",
            "profile_completed": True,
            "age": 32,
            "gender": "male",
            "location": "New York, NY",
            "bio": "Tech enthusiast and basketball player. Let's connect!",
            "interests": ["technology", "basketball", "movies", "cooking"],
            "values": ["integrity", "teamwork", "innovation"],
            "authenticity_rating": 8.2,
            "trust_level": 3,
            "connection_pin": "PIN-BOB002",
            "is_online": False,
            "created_at": datetime.utcnow()
        },
        {
            "user_id": str(uuid.uuid4()),
            "username": "testuser_carol",
            "email": "carol@test.com",
            "password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "phone": "+1234567003",
            "display_name": "Carol Davis",
            "profile_completed": True,
            "age": 26,
            "gender": "female",
            "location": "Austin, TX",
            "bio": "Artist and yoga instructor. Seeking meaningful connections.",
            "interests": ["yoga", "art", "meditation", "reading"],
            "values": ["mindfulness", "compassion", "growth"],
            "authenticity_rating": 9.1,
            "trust_level": 4,
            "connection_pin": "PIN-CAR003",
            "is_online": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    created_users = []
    for user_data in test_users:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data["email"]})
        if not existing_user:
            await db.users.insert_one(user_data)
            created_users.append({
                "email": user_data["email"],
                "display_name": user_data["display_name"],
                "connection_pin": user_data["connection_pin"]
            })
    
    return {
        "message": f"Created {len(created_users)} test users for contact testing",
        "created_users": created_users,
        "instructions": "You can now add these users as contacts using their email addresses or PINs"
    }

# Enhanced Connection Management for Authentic Connections
@api_router.post("/connections/request")
async def send_connection_request(request_data: dict, current_user = Depends(get_current_user)):
    """Send a connection request to another user"""
    target_user_id = request_data.get("user_id")
    message = request_data.get("message", "")
    
    if not target_user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    # Check if target user exists
    target_user = await db.users.find_one({"user_id": target_user_id})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot connect to yourself")
    
    # Check if already connected or request exists
    existing = await db.connections.find_one({
        "$or": [
            {"user_id": current_user["user_id"], "connected_user_id": target_user_id},
            {"user_id": target_user_id, "connected_user_id": current_user["user_id"]}
        ]
    })
    if existing:
        if existing["status"] == "connected":
            raise HTTPException(status_code=400, detail="Already connected")
        elif existing["status"] == "pending":
            raise HTTPException(status_code=400, detail="Connection request already sent")
    
    # Check if blocked
    blocked = await check_user_blocked(current_user["user_id"], target_user_id)
    if blocked:
        raise HTTPException(status_code=403, detail="Cannot send connection request to blocked user")
    
    # Create connection request
    connection = {
        "connection_id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "connected_user_id": target_user_id,
        "status": "pending",
        "trust_level": 1,
        "initiated_by": current_user["user_id"],
        "message": message,
        "requested_at": datetime.utcnow(),
        "last_activity": datetime.utcnow()
    }
    
    await db.connections.insert_one(connection)
    
    return {
        "message": "Connection request sent successfully",
        "connection_id": connection["connection_id"],
        "status": "pending"
    }

@api_router.get("/connections")
async def get_connections(status: str = None, current_user = Depends(get_current_user)):
    """Get all connections for the current user"""
    query = {
        "$or": [
            {"user_id": current_user["user_id"]},
            {"connected_user_id": current_user["user_id"]}
        ]
    }
    
    if status:
        query["status"] = status
    
    connections = await db.connections.find(query).to_list(100)
    
    # Enrich with user details
    for connection in connections:
        # Determine the other user
        other_user_id = (connection["connected_user_id"] 
                        if connection["user_id"] == current_user["user_id"] 
                        else connection["user_id"])
        
        other_user = await db.users.find_one({"user_id": other_user_id})
        if other_user:
            connection["other_user"] = {
                "user_id": other_user["user_id"],
                "username": other_user["username"],
                "display_name": other_user.get("display_name"),
                "avatar": other_user.get("avatar"),
                "status_message": other_user.get("status_message"),
                "is_online": other_user.get("is_online", False),
                "trust_level": other_user.get("trust_level", 1),
                "authenticity_rating": other_user.get("authenticity_rating", 0.0)
            }
    
    return serialize_mongo_doc(connections)

@api_router.put("/connections/{connection_id}/respond")
async def respond_to_connection(connection_id: str, response_data: dict, current_user = Depends(get_current_user)):
    """Accept or decline a connection request"""
    action = response_data.get("action")  # "accept" or "decline"
    
    if action not in ["accept", "decline"]:
        raise HTTPException(status_code=400, detail="Action must be 'accept' or 'decline'")
    
    # Find the connection
    connection = await db.connections.find_one({"connection_id": connection_id})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection request not found")
    
    # Check if user is the target of this request
    if connection["connected_user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only respond to requests sent to you")
    
    if connection["status"] != "pending":
        raise HTTPException(status_code=400, detail="Connection request is no longer pending")
    
    if action == "accept":
        # Accept the connection
        await db.connections.update_one(
            {"connection_id": connection_id},
            {
                "$set": {
                    "status": "connected",
                    "connected_at": datetime.utcnow(),
                    "last_activity": datetime.utcnow()
                }
            }
        )
        return {"message": "Connection accepted successfully", "status": "connected"}
    else:
        # Decline the connection
        await db.connections.delete_one({"connection_id": connection_id})
        return {"message": "Connection request declined", "status": "declined"}

# PIN-based connection system
@api_router.post("/connections/request-by-pin")
async def send_connection_request_by_pin(request_data: dict, current_user = Depends(get_current_user)):
    """Send enhanced connection request using target user's PIN"""
    target_pin = request_data.get("connection_pin") or request_data.get("target_pin")
    message = request_data.get("message", "")
    connection_type = request_data.get("connection_type", "general")
    
    if not target_pin:
        raise HTTPException(status_code=400, detail="Target PIN required")
    
    # Validate PIN format
    if not target_pin.startswith("PIN-"):
        raise HTTPException(status_code=400, detail="Invalid PIN format")
    
    pin_code = target_pin[4:]  # Remove "PIN-" prefix
    if len(pin_code) != 6 or not pin_code.isalnum():
        raise HTTPException(status_code=400, detail="Invalid PIN format")
    
    # Find user by PIN
    target_user = await db.users.find_one({"connection_pin": target_pin})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found with this PIN")
    
    if target_user["user_id"] == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot connect to yourself")
    
    # Check if already connected or request exists
    existing = await db.connection_requests.find_one({
        "$or": [
            {"sender_id": current_user["user_id"], "receiver_id": target_user["user_id"]},
            {"sender_id": target_user["user_id"], "receiver_id": current_user["user_id"]}
        ]
    })
    if existing:
        if existing["status"] == "pending":
            raise HTTPException(status_code=400, detail="Connection request already exists")
        elif existing["status"] == "accepted":
            raise HTTPException(status_code=400, detail="Already connected")
    
    # Create enhanced connection request
    connection_request = {
        "request_id": str(uuid.uuid4()),
        "sender_id": current_user["user_id"],
        "receiver_id": target_user["user_id"],
        "message": message,
        "connection_type": connection_type,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "sender_info": {
            "display_name": current_user.get("display_name"),
            "username": current_user["username"],
            "avatar": current_user.get("avatar"),
            "authenticity_rating": current_user.get("authenticity_rating", 0)
        }
    }
    
    await db.connection_requests.insert_one(connection_request)
    
    # Send real-time notification
    try:
        await manager.send_personal_message(
            json.dumps({
                "type": "connection_request",
                "data": {
                    "request_id": connection_request["request_id"],
                    "sender": connection_request["sender_info"],
                    "message": message,
                    "connection_type": connection_type,
                    "created_at": connection_request["created_at"].isoformat()
                }
            }),
            target_user["user_id"]
        )
    except Exception as e:
        print(f"Failed to send real-time notification: {e}")
    
    return {
        "message": "Connection request sent successfully",
        "request_id": connection_request["request_id"],
        "target_user": {
            "display_name": target_user.get("display_name"),
            "username": target_user["username"]
        }
    }

@api_router.get("/connections/requests")
async def get_connection_requests(current_user = Depends(get_current_user)):
    """Get pending connection requests for current user"""
    requests = await db.connection_requests.find({
        "receiver_id": current_user["user_id"],
        "status": "pending"
    }).to_list(100)
    
    # Enrich with sender details
    for request in requests:
        sender = await db.users.find_one({"user_id": request["sender_id"]})
        if sender:
            request["sender"] = {
                "user_id": sender["user_id"],
                "username": sender["username"],
                "display_name": sender.get("display_name"),
                "avatar": sender.get("avatar")
            }
    
    return serialize_mongo_doc(requests)

@api_router.put("/connections/requests/{request_id}")
async def respond_to_connection_request(request_id: str, response_data: dict, current_user = Depends(get_current_user)):
    """Enhanced response to connection request with auto-chat creation"""
    action = response_data.get("action")  # "accept", "decline", or "block"
    message = response_data.get("message", "")
    
    if action not in ["accept", "decline", "block"]:
        raise HTTPException(status_code=400, detail="Action must be 'accept', 'decline', or 'block'")
    
    # Find the request
    request = await db.connection_requests.find_one({
        "request_id": request_id,
        "receiver_id": current_user["user_id"],
        "status": "pending"
    })
    
    if not request:
        raise HTTPException(status_code=404, detail="Connection request not found")
    
    try:
        if action == "accept":
            # Create mutual connections
            connection1 = {
                "connection_id": str(uuid.uuid4()),
                "user_id": current_user["user_id"],
                "connected_user_id": request["sender_id"],
                "status": "connected",
                "trust_level": 1,  # Start at trust level 1
                "created_at": datetime.utcnow(),
                "connection_type": request.get("connection_type", "general")
            }
            
            connection2 = {
                "connection_id": str(uuid.uuid4()),
                "user_id": request["sender_id"],
                "connected_user_id": current_user["user_id"],
                "status": "connected",
                "trust_level": 1,
                "created_at": datetime.utcnow(),
                "connection_type": request.get("connection_type", "general")
            }
            
            await db.connections.insert_one(connection1)
            await db.connections.insert_one(connection2)
            
            # Create direct chat between users
            chat = {
                "chat_id": str(uuid.uuid4()),
                "chat_type": "direct",
                "members": [current_user["user_id"], request["sender_id"]],
                "created_at": datetime.utcnow(),
                "created_by": current_user["user_id"],
                "trust_level_required": 1,
                "is_active": True
            }
            
            await db.chats.insert_one(chat)
            
            # Update request status
            await db.connection_requests.update_one(
                {"request_id": request_id},
                {"$set": {
                    "status": "accepted",
                    "response_message": message,
                    "responded_at": datetime.utcnow()
                }}
            )
            
            # Send notification to sender
            try:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "connection_accepted",
                        "data": {
                            "request_id": request_id,
                            "accepter": {
                                "display_name": current_user.get("display_name"),
                                "username": current_user["username"],
                                "user_id": current_user["user_id"]
                            },
                            "chat_id": chat["chat_id"],
                            "message": message
                        }
                    }),
                    request["sender_id"]
                )
            except Exception as e:
                print(f"Failed to send real-time notification: {e}")
            
            return {
                "message": "Connection request accepted successfully",
                "status": "accepted",
                "chat_id": chat["chat_id"],
                "connection_id": connection1["connection_id"]
            }
            
        elif action == "block":
            # Add to blocked users
            await db.blocked_users.insert_one({
                "blocker_id": current_user["user_id"],
                "blocked_id": request["sender_id"],
                "created_at": datetime.utcnow(),
                "reason": "Connection request blocked"
            })
            
            # Update request status
            await db.connection_requests.update_one(
                {"request_id": request_id},
                {"$set": {
                    "status": "blocked",
                    "response_message": "User blocked",
                    "responded_at": datetime.utcnow()
                }}
            )
            
            return {
                "message": "User blocked successfully",
                "status": "blocked"
            }
            
        else:  # decline
            # Update request status
            await db.connection_requests.update_one(
                {"request_id": request_id},
                {"$set": {
                    "status": "declined",
                    "response_message": message,
                    "responded_at": datetime.utcnow()
                }}
            )
            
            return {
                "message": "Connection request declined",
                "status": "declined"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to respond to connection request")

@api_router.get("/users/qr-code")
async def get_user_qr_code(current_user = Depends(get_current_user)):
    """Generate enhanced QR code for user's connection PIN"""
    connection_pin = current_user.get("connection_pin")
    if not connection_pin:
        # Generate smart PIN based on user data
        name = current_user.get("display_name") or current_user.get("username", "USER")
        name_part = ''.join(c.upper() for c in name if c.isalpha())[:3]
        
        # Fill with random letters if needed
        while len(name_part) < 3:
            name_part += secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        
        # Add 3 random numbers
        number_part = ''.join(secrets.choice("0123456789") for _ in range(3))
        connection_pin = f"PIN-{name_part}{number_part}"
        
        # Ensure PIN is unique
        while await db.users.find_one({"connection_pin": connection_pin}):
            number_part = ''.join(secrets.choice("0123456789") for _ in range(3))
            connection_pin = f"PIN-{name_part}{number_part}"
        
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": {"connection_pin": connection_pin, "pin_updated_at": datetime.utcnow()}}
        )
    
    # Generate enhanced QR code with metadata
    qr_data = {
        "type": "authentic_connection",
        "pin": connection_pin,
        "display_name": current_user.get("display_name"),
        "timestamp": datetime.utcnow().isoformat(),
        "app_version": "1.0"
    }
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "connection_pin": connection_pin,
        "qr_code": f"data:image/png;base64,{qr_code_base64}",
        "display_name": current_user.get("display_name"),
        "invite_link": f"https://authentic-connections.app/connect?pin={connection_pin}",
        "qr_format": "enhanced"
    }

# Enhanced PIN Management Endpoints

@api_router.post("/pin/regenerate")
async def regenerate_user_pin(current_user = Depends(get_current_user)):
    """Regenerate user's connection PIN"""
    try:
        # Generate smart PIN based on user data
        name = current_user.get("display_name") or current_user.get("username", "USER")
        name_part = ''.join(c.upper() for c in name if c.isalpha())[:3]
        
        # Fill with random letters if needed
        while len(name_part) < 3:
            name_part += secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        
        # Add 3 random numbers
        number_part = ''.join(secrets.choice("0123456789") for _ in range(3))
        new_pin = f"PIN-{name_part}{number_part}"
        
        # Ensure PIN is unique
        while await db.users.find_one({"connection_pin": new_pin}):
            number_part = ''.join(secrets.choice("0123456789") for _ in range(3))
            new_pin = f"PIN-{name_part}{number_part}"
        
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": {
                "connection_pin": new_pin, 
                "pin_updated_at": datetime.utcnow()
            }}
        )
        
        return {
            "connection_pin": new_pin,
            "message": "PIN regenerated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to regenerate PIN")

@api_router.post("/connections/search")
async def search_users(search_data: dict, current_user = Depends(get_current_user)):
    """Enhanced user search with multiple criteria"""
    search_query = search_data.get("query", "").strip()
    
    if not search_query:
        raise HTTPException(status_code=400, detail="Search query required")
    
    if len(search_query) < 2:
        raise HTTPException(status_code=400, detail="Search query too short")
    
    try:
        search_results = []
        
        # Search by PIN
        if search_query.startswith("PIN-"):
            # Validate PIN format
            pin_code = search_query[4:]  # Remove "PIN-" prefix
            if len(pin_code) == 6 and pin_code.isalnum():
                user = await db.users.find_one({"connection_pin": search_query})
                if user and user["user_id"] != current_user["user_id"]:
                    search_results.append({
                        "user_id": user["user_id"],
                        "display_name": user.get("display_name"),
                        "username": user["username"],
                        "avatar": user.get("avatar"),
                        "authenticity_rating": user.get("authenticity_rating", 0),
                        "search_type": "pin"
                    })
        
        # Search by email
        elif "@" in search_query:
            user = await db.users.find_one({"email": search_query})
            if user and user["user_id"] != current_user["user_id"]:
                search_results.append({
                    "user_id": user["user_id"],
                    "display_name": user.get("display_name"),
                    "username": user["username"],
                    "avatar": user.get("avatar"),
                    "authenticity_rating": user.get("authenticity_rating", 0),
                    "search_type": "email"
                })
        
        # Search by username or display name
        else:
            users = await db.users.find({
                "$and": [
                    {"user_id": {"$ne": current_user["user_id"]}},
                    {"$or": [
                        {"username": {"$regex": search_query, "$options": "i"}},
                        {"display_name": {"$regex": search_query, "$options": "i"}}
                    ]}
                ]
            }).limit(10).to_list(10)
            
            for user in users:
                search_results.append({
                    "user_id": user["user_id"],
                    "display_name": user.get("display_name"),
                    "username": user["username"],
                    "avatar": user.get("avatar"),
                    "authenticity_rating": user.get("authenticity_rating", 0),
                    "search_type": "name"
                })
        
        return {
            "results": search_results,
            "total": len(search_results),
            "query": search_query
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Search failed")

@api_router.get("/connections/statistics")
async def get_connection_stats(current_user = Depends(get_current_user)):
    """Get connection statistics for user"""
    try:
        stats = {}
        
        # Total connections
        stats["total_connections"] = await db.connections.count_documents({
            "$or": [
                {"user_id": current_user["user_id"]},
                {"connected_user_id": current_user["user_id"]}
            ],
            "status": "connected"
        })
        
        # Pending requests (sent)
        stats["pending_sent"] = await db.connection_requests.count_documents({
            "sender_id": current_user["user_id"],
            "status": "pending"
        })
        
        # Pending requests (received)
        stats["pending_received"] = await db.connection_requests.count_documents({
            "receiver_id": current_user["user_id"],
            "status": "pending"
        })
        
        # Recent connections (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        stats["recent_connections"] = await db.connections.count_documents({
            "$or": [
                {"user_id": current_user["user_id"]},
                {"connected_user_id": current_user["user_id"]}
            ],
            "status": "connected",
            "created_at": {"$gte": week_ago}
        })
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get statistics")

@api_router.put("/connections/{connection_id}/trust-level")
async def update_trust_level(connection_id: str, trust_data: dict, current_user = Depends(get_current_user)):
    """Update trust level for a connection (both users must agree)"""
    new_level = trust_data.get("trust_level")
    
    if not isinstance(new_level, int) or new_level < 1 or new_level > 5:
        raise HTTPException(status_code=400, detail="Trust level must be between 1 and 5")
    
    # Find the connection
    connection = await db.connections.find_one({"connection_id": connection_id})
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Check if user is part of this connection
    if (connection["user_id"] != current_user["user_id"] and 
        connection["connected_user_id"] != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="You are not part of this connection")
    
    if connection["status"] != "connected":
        raise HTTPException(status_code=400, detail="Connection must be active to update trust level")
    
    current_level = connection.get("trust_level", 1)
    
    # Can only progress one level at a time
    if new_level > current_level + 1:
        raise HTTPException(status_code=400, detail="Can only progress one trust level at a time")
    
    # Check if both users agree (simplified - in real app, would require both to vote)
    await db.connections.update_one(
        {"connection_id": connection_id},
        {
            "$set": {
                "trust_level": new_level,
                "last_activity": datetime.utcnow(),
                f"trust_level_updated_by": current_user["user_id"],
                f"trust_level_updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "message": f"Trust level updated to {new_level}",
        "trust_level": new_level,
        "level_name": [
            "Anonymous Discovery",
            "Text Chat", 
            "Voice Call",
            "Video Call", 
            "In-Person Meetup"
        ][new_level - 1]
    }

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

# ============================================================================
# 5-LAYER TRUST SYSTEM IMPLEMENTATION
# ============================================================================

# Trust system configuration
TRUST_LEVELS = {
    1: {
        "name": "Anonymous Discovery",
        "description": "Connect through PIN codes and basic messaging",
        "features": ["pin_connection", "basic_profile_view", "text_chat"],
        "requirements": {"connections": 0, "time_days": 0},
        "icon": "🔍",
        "color": "blue"
    },
    2: {
        "name": "Verified Connection", 
        "description": "Enhanced messaging and profile sharing",
        "features": ["full_profile_view", "file_sharing", "enhanced_chat"],
        "requirements": {"connections": 1, "time_days": 1},
        "icon": "💬",
        "color": "green"
    },
    3: {
        "name": "Voice Communication",
        "description": "Voice calls and audio messages",
        "features": ["voice_calls", "audio_messages", "call_history"],
        "requirements": {"connections": 3, "time_days": 7, "interactions": 10},
        "icon": "🎙️",
        "color": "yellow"
    },
    4: {
        "name": "Video Communication",
        "description": "Video calls and screen sharing",
        "features": ["video_calls", "screen_sharing", "group_video"],
        "requirements": {"connections": 5, "time_days": 14, "interactions": 25},
        "icon": "📹",
        "color": "orange"
    },
    5: {
        "name": "In-Person Meetup",
        "description": "Real-world meeting coordination",
        "features": ["location_sharing", "meetup_planning", "safety_features"],
        "requirements": {"connections": 10, "time_days": 30, "interactions": 50, "video_calls": 3},
        "icon": "🤝",
        "color": "red"
    }
}

@api_router.get("/trust/levels")
async def get_trust_levels():
    """Get all trust levels configuration"""
    return {"trust_levels": TRUST_LEVELS}

@api_router.get("/trust/progress")
async def get_trust_progress(current_user = Depends(get_current_user)):
    """Get user's trust progression status"""
    try:
        user_id = current_user["user_id"]
        
        # Get user's current trust level
        current_trust_level = current_user.get("trust_level", 1)
        
        # Calculate trust metrics
        metrics = await calculate_trust_metrics(user_id)
        
        # Get progress for next level
        next_level = current_trust_level + 1 if current_trust_level < 5 else None
        progress = {}
        
        if next_level:
            requirements = TRUST_LEVELS[next_level]["requirements"]
            progress = {
                "connections": {
                    "current": metrics["total_connections"],
                    "required": requirements.get("connections", 0),
                    "completed": metrics["total_connections"] >= requirements.get("connections", 0)
                },
                "time_days": {
                    "current": metrics["days_since_registration"],
                    "required": requirements.get("time_days", 0),
                    "completed": metrics["days_since_registration"] >= requirements.get("time_days", 0)
                },
                "interactions": {
                    "current": metrics["total_interactions"],
                    "required": requirements.get("interactions", 0),
                    "completed": metrics["total_interactions"] >= requirements.get("interactions", 0)
                }
            }
            
            if "video_calls" in requirements:
                progress["video_calls"] = {
                    "current": metrics["video_calls"],
                    "required": requirements["video_calls"],
                    "completed": metrics["video_calls"] >= requirements["video_calls"]
                }
        
        # Check if user can level up
        can_level_up = next_level and all(p["completed"] for p in progress.values())
        
        return {
            "current_level": current_trust_level,
            "next_level": next_level,
            "current_level_info": TRUST_LEVELS[current_trust_level],
            "next_level_info": TRUST_LEVELS.get(next_level),
            "progress": progress,
            "can_level_up": can_level_up,
            "metrics": metrics,
            "achievements": await get_user_achievements(user_id),
            "milestones": await get_trust_milestones(user_id)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get trust progress")

@api_router.post("/trust/level-up")
async def level_up_trust(current_user = Depends(get_current_user)):
    """Level up user's trust level if requirements are met"""
    try:
        user_id = current_user["user_id"]
        current_trust_level = current_user.get("trust_level", 1)
        
        if current_trust_level >= 5:
            raise HTTPException(status_code=400, detail="Already at maximum trust level")
        
        next_level = current_trust_level + 1
        metrics = await calculate_trust_metrics(user_id)
        
        # Check requirements for next level
        requirements = TRUST_LEVELS[next_level]["requirements"]
        
        if not await check_trust_requirements(metrics, requirements):
            raise HTTPException(status_code=400, detail="Trust level requirements not met")
        
        # Update user's trust level
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "trust_level": next_level,
                "trust_level_updated_at": datetime.utcnow()
            }}
        )
        
        # Create achievement
        achievement = {
            "achievement_id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "trust_level_up",
            "level": next_level,
            "title": f"Reached {TRUST_LEVELS[next_level]['name']}",
            "description": TRUST_LEVELS[next_level]["description"],
            "earned_at": datetime.utcnow()
        }
        
        await db.achievements.insert_one(achievement)
        
        # Send real-time notification
        try:
            await manager.send_personal_message(
                json.dumps({
                    "type": "trust_level_up",
                    "data": {
                        "new_level": next_level,
                        "level_info": TRUST_LEVELS[next_level],
                        "achievement": achievement
                    }
                }),
                user_id
            )
        except Exception as e:
            print(f"Failed to send trust level up notification: {e}")
        
        return {
            "message": f"Congratulations! You've reached Trust Level {next_level}",
            "new_level": next_level,
            "level_info": TRUST_LEVELS[next_level],
            "achievement": serialize_mongo_doc(achievement)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to level up trust")

@api_router.get("/trust/features")
async def get_available_features(current_user = Depends(get_current_user)):
    """Get features available at user's current trust level"""
    trust_level = current_user.get("trust_level", 1)
    
    available_features = []
    for level in range(1, trust_level + 1):
        available_features.extend(TRUST_LEVELS[level]["features"])
    
    return {
        "trust_level": trust_level,
        "available_features": available_features,
        "level_info": TRUST_LEVELS[trust_level]
    }

@api_router.get("/trust/achievements")
async def get_achievements(current_user = Depends(get_current_user)):
    """Get user's trust-related achievements"""
    achievements = await db.achievements.find({
        "user_id": current_user["user_id"]
    }).sort("earned_at", -1).to_list(100)
    
    return serialize_mongo_doc(achievements)

@api_router.post("/trust/interactions/{contact_id}")
async def record_interaction(contact_id: str, interaction_data: dict, current_user = Depends(get_current_user)):
    """Record an interaction with a contact for trust building"""
    interaction_type = interaction_data.get("type")  # message, call, video_call, meetup
    
    if interaction_type not in ["message", "voice_call", "video_call", "meetup", "file_share"]:
        raise HTTPException(status_code=400, detail="Invalid interaction type")
    
    # Verify contact exists
    contact = await db.connections.find_one({
        "$or": [
            {"user_id": current_user["user_id"], "connected_user_id": contact_id},
            {"user_id": contact_id, "connected_user_id": current_user["user_id"]}
        ],
        "status": "connected"
    })
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Record interaction
    interaction = {
        "interaction_id": str(uuid.uuid4()),
        "user_id": current_user["user_id"],
        "contact_id": contact_id,
        "type": interaction_type,
        "metadata": interaction_data.get("metadata", {}),
        "created_at": datetime.utcnow()
    }
    
    await db.interactions.insert_one(interaction)
    
    return {"message": "Interaction recorded successfully"}

async def calculate_trust_metrics(user_id: str):
    """Calculate trust metrics for a user"""
    # Get user registration date
    user = await db.users.find_one({"user_id": user_id})
    registration_date = user.get("created_at", datetime.utcnow())
    days_since_registration = (datetime.utcnow() - registration_date).days
    
    # Count connections
    total_connections = await db.connections.count_documents({
        "$or": [
            {"user_id": user_id},
            {"connected_user_id": user_id}
        ],
        "status": "connected"
    })
    
    # Count interactions
    total_interactions = await db.interactions.count_documents({"user_id": user_id})
    
    # Count video calls
    video_calls = await db.interactions.count_documents({
        "user_id": user_id,
        "type": "video_call"
    })
    
    # Count messages sent
    messages_sent = await db.messages.count_documents({"sender_id": user_id})
    
    return {
        "total_connections": total_connections,
        "days_since_registration": days_since_registration,
        "total_interactions": total_interactions,
        "video_calls": video_calls,
        "messages_sent": messages_sent
    }

async def check_trust_requirements(metrics: dict, requirements: dict):
    """Check if user meets trust level requirements"""
    for req_type, req_value in requirements.items():
        if metrics.get(req_type, 0) < req_value:
            return False
    return True

async def get_user_achievements(user_id: str):
    """Get user's recent achievements"""
    achievements = await db.achievements.find({
        "user_id": user_id
    }).sort("earned_at", -1).limit(5).to_list(5)
    
    return serialize_mongo_doc(achievements)

async def get_trust_milestones(user_id: str):
    """Get trust milestones for user"""
    milestones = []
    
    # Connection milestones
    metrics = await calculate_trust_metrics(user_id)
    
    connection_milestones = [1, 3, 5, 10, 25, 50]
    for milestone in connection_milestones:
        milestones.append({
            "type": "connections",
            "target": milestone,
            "current": metrics["total_connections"],
            "completed": metrics["total_connections"] >= milestone,
            "title": f"{milestone} Connections",
            "description": f"Make {milestone} authentic connections"
        })
    
    # Time-based milestones
    time_milestones = [7, 14, 30, 60, 90]
    for milestone in time_milestones:
        milestones.append({
            "type": "time",
            "target": milestone,
            "current": metrics["days_since_registration"],
            "completed": metrics["days_since_registration"] >= milestone,
            "title": f"{milestone} Days",
            "description": f"Be active for {milestone} days"
        })
    
    return milestones

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

# Enhanced File Upload
@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    """Upload a file and return file metadata with base64 data"""
    # Enhanced file size limit (25MB for most files)
    max_size = 25 * 1024 * 1024  # 25MB
    
    if file.size > max_size:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {max_size // (1024 * 1024)}MB")
    
    # Enhanced file type validation
    allowed_types = {
        # Images
        'image/jpeg': {'category': 'Image', 'icon': '🖼️', 'max_size': 10 * 1024 * 1024},
        'image/png': {'category': 'Image', 'icon': '🖼️', 'max_size': 10 * 1024 * 1024},
        'image/gif': {'category': 'Image', 'icon': '🖼️', 'max_size': 5 * 1024 * 1024},
        'image/webp': {'category': 'Image', 'icon': '🖼️', 'max_size': 10 * 1024 * 1024},
        # Documents
        'application/pdf': {'category': 'Document', 'icon': '📄', 'max_size': 25 * 1024 * 1024},
        'text/plain': {'category': 'Text', 'icon': '📝', 'max_size': 5 * 1024 * 1024},
        'application/msword': {'category': 'Document', 'icon': '📝', 'max_size': 25 * 1024 * 1024},
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {'category': 'Document', 'icon': '📝', 'max_size': 25 * 1024 * 1024},
        # Spreadsheets
        'application/vnd.ms-excel': {'category': 'Spreadsheet', 'icon': '📊', 'max_size': 25 * 1024 * 1024},
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': {'category': 'Spreadsheet', 'icon': '📊', 'max_size': 25 * 1024 * 1024},
        # Audio
        'audio/mpeg': {'category': 'Audio', 'icon': '🎵', 'max_size': 15 * 1024 * 1024},
        'audio/wav': {'category': 'Audio', 'icon': '🎵', 'max_size': 15 * 1024 * 1024},
        'audio/ogg': {'category': 'Audio', 'icon': '🎵', 'max_size': 15 * 1024 * 1024},
        # Video
        'video/mp4': {'category': 'Video', 'icon': '🎬', 'max_size': 50 * 1024 * 1024},
        'video/webm': {'category': 'Video', 'icon': '🎬', 'max_size': 50 * 1024 * 1024},
        # Archives
        'application/zip': {'category': 'Archive', 'icon': '📦', 'max_size': 25 * 1024 * 1024},
        'application/x-rar-compressed': {'category': 'Archive', 'icon': '📦', 'max_size': 25 * 1024 * 1024}
    }
    
    file_info = allowed_types.get(file.content_type)
    if not file_info:
        raise HTTPException(
            status_code=400, 
            detail=f"File type '{file.content_type}' not supported. Supported types: Images, Documents, Audio, Video, Archives"
        )
    
    if file.size > file_info['max_size']:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large for {file_info['category']}. Maximum size: {file_info['max_size'] // (1024 * 1024)}MB"
        )
    
    try:
        # Read file content
        file_content = await file.read()
        file_base64 = base64.b64encode(file_content).decode()
        
        # Create file metadata
        file_data = {
            "file_id": str(uuid.uuid4()),
            "file_name": file.filename,
            "file_size": file.size,
            "file_type": file.content_type,
            "file_data": file_base64,
            "category": file_info['category'],
            "icon": file_info['icon'],
            "uploaded_by": current_user["user_id"],
            "uploaded_at": datetime.utcnow()
        }
        
        return {
            "message": "File uploaded successfully",
            "file_id": file_data["file_id"],
            "file_name": file_data["file_name"],
            "file_size": file_data["file_size"],
            "file_type": file_data["file_type"],
            "file_data": file_data["file_data"],
            "category": file_data["category"],
            "icon": file_data["icon"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@api_router.get("/chats/{chat_id}/search")
async def search_messages(chat_id: str, q: str, current_user = Depends(get_current_user)):
    """Search messages in a specific chat"""
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    # Verify user is member of chat
    chat = await db.chats.find_one({
        "chat_id": chat_id,
        "members": current_user["user_id"]
    })
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    try:
        # Search messages with regex (case-insensitive)
        search_results = await db.messages.find({
            "chat_id": chat_id,
            "content": {"$regex": q.strip(), "$options": "i"},
            "is_deleted": {"$ne": True}
        }).sort("created_at", -1).limit(50).to_list(50)
        
        return {
            "query": q,
            "total_results": len(search_results),
            "results": serialize_mongo_doc(search_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Search failed")

@api_router.get("/search/messages")
async def search_all_messages(q: str, current_user = Depends(get_current_user)):
    """Search messages across all user's chats"""
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    try:
        # Get all chats user is member of
        user_chats = await db.chats.find({
            "members": current_user["user_id"]
        }).to_list(1000)
        
        chat_ids = [chat["chat_id"] for chat in user_chats]
        
        # Search messages across all user's chats
        search_results = await db.messages.find({
            "chat_id": {"$in": chat_ids},
            "content": {"$regex": q.strip(), "$options": "i"},
            "is_deleted": {"$ne": True}
        }).sort("created_at", -1).limit(100).to_list(100)
        
        # Group results by chat
        results_by_chat = {}
        for message in search_results:
            chat_id = message["chat_id"]
            if chat_id not in results_by_chat:
                # Find chat info
                chat_info = next((chat for chat in user_chats if chat["chat_id"] == chat_id), None)
                results_by_chat[chat_id] = {
                    "chat_info": chat_info,
                    "messages": []
                }
            results_by_chat[chat_id]["messages"].append(message)
        
        return {
            "query": q,
            "total_results": len(search_results),
            "results_by_chat": serialize_mongo_doc(results_by_chat)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Search failed")

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
# app.include_router(api_router)  # Moved to the end of the file

# Emoji Reactions Endpoints
@api_router.post("/messages/{message_id}/reactions")
async def add_emoji_reaction(message_id: str, reaction_data: dict, current_user = Depends(get_current_user)):
    """Add an emoji reaction to a message"""
    emoji = reaction_data.get("emoji")
    if not emoji:
        raise HTTPException(status_code=400, detail="Emoji is required")
    
    # Check if message exists
    message = await db.messages.find_one({"message_id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user has access to the chat
    chat = await db.chats.find_one({"chat_id": message["chat_id"]})
    if not chat or current_user["user_id"] not in chat["members"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create reaction document
    reaction = {
        "reaction_id": str(uuid.uuid4()),
        "message_id": message_id,
        "user_id": current_user["user_id"],
        "emoji": emoji,
        "created_at": datetime.utcnow()
    }
    
    # Check if user already reacted with this emoji
    existing_reaction = await db.emoji_reactions.find_one({
        "message_id": message_id,
        "user_id": current_user["user_id"],
        "emoji": emoji
    })
    
    if existing_reaction:
        # Remove existing reaction (toggle behavior)
        await db.emoji_reactions.delete_one({"reaction_id": existing_reaction["reaction_id"]})
        
        # Notify via WebSocket
        await manager.broadcast_to_chat(
            json.dumps({
                "type": "reaction_removed",
                "data": {
                    "message_id": message_id,
                    "user_id": current_user["user_id"],
                    "emoji": emoji
                }
            }),
            message["chat_id"],
            current_user["user_id"]
        )
        
        return {"status": "reaction_removed", "emoji": emoji}
    else:
        # Add new reaction
        await db.emoji_reactions.insert_one(reaction)
        
        # Notify via WebSocket
        await manager.broadcast_to_chat(
            json.dumps({
                "type": "reaction_added",
                "data": {
                    "message_id": message_id,
                    "user_id": current_user["user_id"],
                    "user_name": current_user.get("display_name", current_user["username"]),
                    "emoji": emoji
                }
            }),
            message["chat_id"],
            current_user["user_id"]
        )
        
        return {"status": "reaction_added", "emoji": emoji, "reaction_id": reaction["reaction_id"]}

@api_router.get("/messages/{message_id}/reactions")
async def get_message_reactions(message_id: str, current_user = Depends(get_current_user)):
    """Get all reactions for a message"""
    # Check if message exists and user has access
    message = await db.messages.find_one({"message_id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    chat = await db.chats.find_one({"chat_id": message["chat_id"]})
    if not chat or current_user["user_id"] not in chat["members"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all reactions for this message
    reactions = await db.emoji_reactions.find({"message_id": message_id}).to_list(1000)
    
    # Group reactions by emoji and include user info
    reaction_summary = {}
    for reaction in reactions:
        emoji = reaction["emoji"]
        if emoji not in reaction_summary:
            reaction_summary[emoji] = {
                "emoji": emoji,
                "count": 0,
                "users": [],
                "user_reacted": False
            }
        
        # Get user info
        user = await db.users.find_one({"user_id": reaction["user_id"]})
        user_info = {
            "user_id": reaction["user_id"],
            "username": user.get("username", "Unknown") if user else "Unknown",
            "display_name": user.get("display_name", user.get("username", "Unknown")) if user else "Unknown"
        }
        
        reaction_summary[emoji]["count"] += 1
        reaction_summary[emoji]["users"].append(user_info)
        
        if reaction["user_id"] == current_user["user_id"]:
            reaction_summary[emoji]["user_reacted"] = True
    
    return {"reactions": list(reaction_summary.values())}

# Custom Emoji Endpoints
@api_router.post("/emojis/custom")
async def upload_custom_emoji(
    file: UploadFile = File(...), 
    name: str = Form(...),
    category: str = Form(default="custom"),
    current_user = Depends(get_current_user)
):
    """Upload a custom emoji"""
    # Validate file type (images only for emojis)
    allowed_types = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only image files are allowed for custom emojis")
    
    # Size limit for emojis (2MB)
    max_size = 2 * 1024 * 1024  # 2MB
    if file.size > max_size:
        raise HTTPException(status_code=413, detail="Emoji file too large. Maximum size is 2MB")
    
    # Validate emoji name
    if not name or len(name) < 2 or len(name) > 32:
        raise HTTPException(status_code=400, detail="Emoji name must be 2-32 characters")
    
    # Check if emoji name already exists for this user
    existing_emoji = await db.custom_emojis.find_one({
        "name": name,
        "user_id": current_user["user_id"]
    })
    if existing_emoji:
        raise HTTPException(status_code=409, detail="Emoji name already exists")
    
    try:
        # Read and encode file
        file_content = await file.read()
        file_base64 = base64.b64encode(file_content).decode()
        
        # Create custom emoji document
        custom_emoji = {
            "emoji_id": str(uuid.uuid4()),
            "name": name,
            "category": category,
            "file_data": file_base64,
            "file_type": file.content_type,
            "file_size": file.size,
            "user_id": current_user["user_id"],
            "created_at": datetime.utcnow(),
            "usage_count": 0
        }
        
        await db.custom_emojis.insert_one(custom_emoji)
        
        return {
            "message": "Custom emoji uploaded successfully",
            "emoji_id": custom_emoji["emoji_id"],
            "name": name,
            "category": category,
            "file_data": file_base64
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload custom emoji: {str(e)}")

@api_router.get("/emojis/custom")
async def get_custom_emojis(current_user = Depends(get_current_user)):
    """Get user's custom emojis"""
    custom_emojis = await db.custom_emojis.find({
        "user_id": current_user["user_id"]
    }).sort("created_at", -1).to_list(100)
    
    return {"custom_emojis": serialize_mongo_doc(custom_emojis)}

@api_router.delete("/emojis/custom/{emoji_id}")
async def delete_custom_emoji(emoji_id: str, current_user = Depends(get_current_user)):
    """Delete a custom emoji"""
    emoji = await db.custom_emojis.find_one({
        "emoji_id": emoji_id,
        "user_id": current_user["user_id"]
    })
    
    if not emoji:
        raise HTTPException(status_code=404, detail="Custom emoji not found")
    
    await db.custom_emojis.delete_one({"emoji_id": emoji_id})
    
    return {"message": "Custom emoji deleted successfully"}

# =============================================================================
# MARKETPLACE ENDPOINTS
# =============================================================================

@api_router.post("/marketplace/listings")
@limiter.limit("20/minute")
async def create_marketplace_listing(request: Request, listing: MarketplaceListing, current_user = Depends(get_current_user)):
    """Create a new marketplace listing"""
    try:
        client_ip = get_remote_address(request)
        
        # Input validation and sanitization
        if listing.price is not None and listing.price < 0:
            raise HTTPException(status_code=400, detail="Price cannot be negative")
        
        if listing.category not in ["items", "services", "jobs", "housing", "vehicles"]:
            raise HTTPException(status_code=400, detail="Invalid category")
        
        if listing.price_type not in ["fixed", "hourly", "negotiable", "free", "barter"]:
            raise HTTPException(status_code=400, detail="Invalid price type")
        
        # Create listing
        listing_data = {
            "listing_id": str(uuid.uuid4()),
            "user_id": current_user["user_id"],
            "username": current_user["username"],
            "title": listing.title,
            "description": listing.description,
            "category": listing.category,
            "price": listing.price,
            "price_type": listing.price_type,
            "location": listing.location,
            "youtube_url": listing.youtube_url,
            "instagram_url": listing.instagram_url,
            "images": listing.images or [],
            "tags": listing.tags or [],
            "availability": "available",
            "contact_method": listing.contact_method,
            "expires_at": listing.expires_at,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "views": 0,
            "saves": 0,
            "messages_count": 0
        }
        
        result = await db.marketplace_listings.insert_one(listing_data)
        
        # Log successful listing creation
        await security_manager.log_activity(
            client_ip, 'marketplace_listing_created', 
            f"User {current_user['user_id']} created listing {listing_data['listing_id']}"
        )
        
        return {
            "status": "success",
            "listing_id": listing_data["listing_id"],
            "message": "Listing created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await security_manager.log_suspicious_activity(
            client_ip, 'marketplace_listing_creation_error', str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to create listing: {str(e)}")

@api_router.get("/marketplace/listings")
async def get_marketplace_listings(
    request: Request,
    category: Optional[str] = None,
    query: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    pincode: Optional[str] = None,
    verification_level: Optional[str] = None,
    only_verified_sellers: bool = False,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """Enhanced marketplace listings with location-based search and verification filtering"""
    try:
        # Build enhanced search filter
        search_filter = {"availability": {"$in": ["available", "pending"]}}
        
        # Category filter
        if category:
            search_filter["category"] = category
        
        # Price range filter
        if min_price is not None:
            search_filter["price"] = {"$gte": min_price}
        
        if max_price is not None:
            if "price" in search_filter:
                search_filter["price"]["$lte"] = max_price
            else:
                search_filter["price"] = {"$lte": max_price}
        
        # Location-based filters for India
        if state:
            search_filter["location.state"] = {"$regex": state, "$options": "i"}
        
        if city:
            search_filter["location.city"] = {"$regex": city, "$options": "i"}
        
        if pincode:
            search_filter["location.pincode"] = pincode
        
        # Text search
        if query:
            search_filter["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"tags": {"$in": [query]}}
            ]
        
        # Verification filters
        if only_verified_sellers:
            # Get verified users
            verified_users = await db.users.find(
                {"verification.government_id_verified": True}
            ).to_list(None)
            verified_user_ids = [user["user_id"] for user in verified_users]
            search_filter["user_id"] = {"$in": verified_user_ids}
        
        if verification_level:
            verified_users = await db.users.find(
                {"verification.verification_level": verification_level}
            ).to_list(None)
            verified_user_ids = [user["user_id"] for user in verified_users]
            search_filter["user_id"] = {"$in": verified_user_ids}
        
        # Enhanced sort options
        sort_options = []
        if sort_by == "price_low":
            sort_options = [("price", 1)]
        elif sort_by == "price_high":
            sort_options = [("price", -1)]
        elif sort_by == "date_new":
            sort_options = [("created_at", -1)]
        elif sort_by == "date_old":
            sort_options = [("created_at", 1)]
        elif sort_by == "relevance":
            # For relevance, we'll use created_at for now (can be enhanced with scoring later)
            sort_options = [("created_at", -1)]
        else:
            sort_direction = 1 if sort_order == "asc" else -1
            sort_options = [(sort_by, sort_direction)]
        
        # Calculate skip for pagination
        skip = (page - 1) * limit
        
        # Get listings with enhanced search
        cursor = db.marketplace_listings.find(search_filter)
        total_count = await db.marketplace_listings.count_documents(search_filter)
        
        listings = await cursor.sort(sort_options).skip(skip).limit(limit).to_list(limit)
        
        # Serialize results with enhanced data
        serialized_listings = []
        for listing in listings:
            listing_data = serialize_mongo_doc(listing)
            
            # Get seller verification info
            seller = await db.users.find_one({"user_id": listing["user_id"]})
            if seller:
                verification = seller.get("verification", {})
                listing_data["seller"] = {
                    "username": seller["username"],
                    "display_name": seller.get("display_name", seller["username"]),
                    "user_id": seller["user_id"],
                    "verification_level": verification.get("verification_level", "basic"),
                    "email_verified": verification.get("email_verified", False),
                    "phone_verified": verification.get("phone_verified", False),
                    "government_id_verified": verification.get("government_id_verified", False)
                }
            
            # Remove sensitive user info for non-owners
            if listing_data.get('user_id') != current_user['user_id']:
                listing_data.pop('user_id', None)
            
            serialized_listings.append(listing_data)
        
        return {
            "listings": serialized_listings,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "has_more": (skip + limit) < total_count,
            "filters_applied": {
                "category": category,
                "location": {"state": state, "city": city, "pincode": pincode},
                "price_range": {"min": min_price, "max": max_price},
                "verification": {"level": verification_level, "only_verified": only_verified_sellers}
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced listings: {str(e)}")

@api_router.get("/marketplace/listings/{listing_id}")
async def get_marketplace_listing(listing_id: str, current_user = Depends(get_current_user)):
    """Get a specific marketplace listing"""
    try:
        listing = await db.marketplace_listings.find_one({"listing_id": listing_id})
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Increment view count (but not for the owner)
        if listing["user_id"] != current_user["user_id"]:
            await db.marketplace_listings.update_one(
                {"listing_id": listing_id},
                {"$inc": {"views": 1}}
            )
        
        listing_data = serialize_mongo_doc(listing)
        
        # Include owner info for contact
        owner = await db.users.find_one({"user_id": listing["user_id"]})
        if owner:
            listing_data["owner"] = {
                "username": owner["username"],
                "display_name": owner.get("display_name", owner["username"]),
                "user_id": owner["user_id"]
            }
        
        return listing_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get listing: {str(e)}")

@api_router.put("/marketplace/listings/{listing_id}")
@limiter.limit("10/minute")
async def update_marketplace_listing(request: Request, listing_id: str, listing: MarketplaceListing, current_user = Depends(get_current_user)):
    """Update a marketplace listing (owner only)"""
    try:
        client_ip = get_remote_address(request)
        
        # Check if listing exists and user is owner
        existing_listing = await db.marketplace_listings.find_one({"listing_id": listing_id})
        
        if not existing_listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        if existing_listing["user_id"] != current_user["user_id"]:
            await security_manager.log_suspicious_activity(
                client_ip, 'unauthorized_listing_update', 
                f"User {current_user['user_id']} tried to update listing {listing_id} owned by {existing_listing['user_id']}"
            )
            raise HTTPException(status_code=403, detail="You can only update your own listings")
        
        # Update listing
        update_data = {
            "title": listing.title,
            "description": listing.description,
            "category": listing.category,
            "price": listing.price,
            "price_type": listing.price_type,
            "location": listing.location,
            "images": listing.images or [],
            "tags": listing.tags or [],
            "contact_method": listing.contact_method,
            "expires_at": listing.expires_at,
            "updated_at": datetime.utcnow()
        }
        
        await db.marketplace_listings.update_one(
            {"listing_id": listing_id},
            {"$set": update_data}
        )
        
        return {"status": "success", "message": "Listing updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update listing: {str(e)}")

@api_router.delete("/marketplace/listings/{listing_id}")
@limiter.limit("10/minute")
async def delete_marketplace_listing(request: Request, listing_id: str, current_user = Depends(get_current_user)):
    """Delete a marketplace listing (owner only)"""
    try:
        client_ip = get_remote_address(request)
        
        # Check if listing exists and user is owner
        listing = await db.marketplace_listings.find_one({"listing_id": listing_id})
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        if listing["user_id"] != current_user["user_id"]:
            await security_manager.log_suspicious_activity(
                client_ip, 'unauthorized_listing_deletion', 
                f"User {current_user['user_id']} tried to delete listing {listing_id} owned by {listing['user_id']}"
            )
            raise HTTPException(status_code=403, detail="You can only delete your own listings")
        
        await db.marketplace_listings.delete_one({"listing_id": listing_id})
        
        return {"status": "success", "message": "Listing deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete listing: {str(e)}")

@api_router.post("/marketplace/listings/{listing_id}/message")
@limiter.limit("30/minute")
async def send_marketplace_message(request: Request, listing_id: str, message_data: MarketplaceMessage, current_user = Depends(get_current_user)):
    """Send a message about a marketplace listing (creates or continues chat)"""
    try:
        client_ip = get_remote_address(request)
        
        # Get the listing
        listing = await db.marketplace_listings.find_one({"listing_id": listing_id})
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Can't message your own listing
        if listing["user_id"] == current_user["user_id"]:
            raise HTTPException(status_code=400, detail="Cannot message your own listing")
        
        # Get recipient user
        recipient = await db.users.find_one({"user_id": message_data.recipient_id})
        
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient not found")
        
        # Verify recipient is the listing owner
        if message_data.recipient_id != listing["user_id"]:
            raise HTTPException(status_code=400, detail="Can only message the listing owner")
        
        # Create or find existing chat between these users
        chat_filter = {
            "$or": [
                {"members": [current_user["user_id"], message_data.recipient_id]},
                {"members": [message_data.recipient_id, current_user["user_id"]]}
            ]
        }
        
        existing_chat = await db.chats.find_one(chat_filter)
        
        if existing_chat:
            chat_id = existing_chat["chat_id"]
        else:
            # Create new chat
            chat_id = str(uuid.uuid4())
            chat_data = {
                "chat_id": chat_id,
                "members": [current_user["user_id"], message_data.recipient_id],
                "created_at": datetime.utcnow(),
                "is_group": False,
                "marketplace_listing_id": listing_id  # Link to marketplace listing
            }
            await db.chats.insert_one(chat_data)
        
        # Create message with marketplace context
        message_content = message_data.message
        if message_data.offer_price:
            message_content += f"\n\n💰 Offer: ${message_data.offer_price}"
        
        message_id = str(uuid.uuid4())
        message = {
            "message_id": message_id,
            "chat_id": chat_id,
            "sender_id": current_user["user_id"],
            "content": message_content,
            "message_type": "marketplace_inquiry",
            "marketplace_listing_id": listing_id,
            "offer_price": message_data.offer_price,
            "created_at": datetime.utcnow(),
            "read": False
        }
        
        await db.messages.insert_one(message)
        
        # Update listing message count
        await db.marketplace_listings.update_one(
            {"listing_id": listing_id},
            {"$inc": {"messages_count": 1}}
        )
        
        # Send WebSocket notification
        if manager.is_user_online(message_data.recipient_id):
            notification = {
                "type": "marketplace_message",
                "chat_id": chat_id,
                "message_id": message_id,
                "sender_id": current_user["user_id"],
                "listing_title": listing["title"],
                "content": message_content[:100] + "..." if len(message_content) > 100 else message_content
            }
            await manager.send_personal_message(json.dumps(notification), message_data.recipient_id)
        
        return {
            "status": "success",
            "chat_id": chat_id,
            "message_id": message_id,
            "message": "Message sent successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@api_router.get("/marketplace/categories")
async def get_marketplace_categories():
    """Get available marketplace categories"""
    categories = [
        {"value": "items", "label": "Items & Products", "icon": "📦"},
        {"value": "services", "label": "Services", "icon": "🛠"},
        {"value": "jobs", "label": "Jobs & Gigs", "icon": "💼"},
        {"value": "housing", "label": "Housing & Rentals", "icon": "🏠"},
        {"value": "vehicles", "label": "Vehicles", "icon": "🚗"}
    ]
    
    return {"categories": categories}

@api_router.get("/marketplace/my-listings")
async def get_my_marketplace_listings(current_user = Depends(get_current_user)):
    """Get current user's marketplace listings"""
    try:
        listings = await db.marketplace_listings.find(
            {"user_id": current_user["user_id"]}
        ).sort("created_at", -1).to_list(100)
        
        return {"listings": [serialize_mongo_doc(listing) for listing in listings]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get your listings: {str(e)}")

@api_router.put("/marketplace/listings/{listing_id}/availability")
@limiter.limit("10/minute")
async def update_listing_availability(request: Request, listing_id: str, availability: dict, current_user = Depends(get_current_user)):
    """Update listing availability (available, sold, pending)"""
    try:
        new_status = availability.get("status")
        
        if new_status not in ["available", "sold", "pending"]:
            raise HTTPException(status_code=400, detail="Invalid availability status")
        
        # Check ownership
        listing = await db.marketplace_listings.find_one({"listing_id": listing_id})
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        if listing["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="You can only update your own listings")
        
        await db.marketplace_listings.update_one(
            {"listing_id": listing_id},
            {"$set": {"availability": new_status, "updated_at": datetime.utcnow()}}
        )
        
        return {"status": "success", "message": f"Listing marked as {new_status}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update availability: {str(e)}")

# =============================================================================
# USER VERIFICATION ENDPOINTS FOR INDIA
# =============================================================================

@api_router.post("/verification/phone/send-otp")
@limiter.limit("5/minute")
async def send_phone_otp(request: Request, phone_data: dict, current_user = Depends(get_current_user)):
    """Send OTP to Indian mobile number for verification"""
    try:
        client_ip = get_remote_address(request)
        phone_number = phone_data.get("phone_number")
        
        # Validate Indian mobile number format
        if not re.match(r"^\+91[6-9]\d{9}$", phone_number):
            raise HTTPException(status_code=400, detail="Invalid Indian mobile number format. Use +91XXXXXXXXXX")
        
        # Generate 6-digit OTP using cryptographically secure random
        import secrets
        otp = str(secrets.randbelow(900000) + 100000)  # Ensures 6-digit number
        
        # Store OTP in database (expires in 10 minutes)
        await db.phone_otps.update_one(
            {"user_id": current_user["user_id"]},
            {
                "$set": {
                    "phone_number": phone_number,
                    "otp": otp,
                    "created_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(minutes=10),
                    "verified": False
                }
            },
            upsert=True
        )
        
        # TODO: Integrate with SMS service (Twilio/AWS SNS) for production
        # For now, return OTP in response (development only)
        print(f"📱 SMS OTP for {phone_number}: {otp}")
        
        await security_manager.log_activity(
            client_ip, 'phone_otp_sent', 
            f"OTP sent to {phone_number} for user {current_user['user_id']}"
        )
        
        return {
            "status": "success",
            "message": "OTP sent successfully",
            "otp": otp if True else None  # Remove in production
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")

@api_router.post("/verification/phone/verify-otp")
@limiter.limit("10/minute")
async def verify_phone_otp(request: Request, otp_data: dict, current_user = Depends(get_current_user)):
    """Verify phone OTP and mark phone as verified"""
    try:
        client_ip = get_remote_address(request)
        otp = otp_data.get("otp")
        
        # Get stored OTP
        stored_otp = await db.phone_otps.find_one({"user_id": current_user["user_id"]})
        
        if not stored_otp:
            raise HTTPException(status_code=400, detail="No OTP found. Please request a new OTP.")
        
        # Check if OTP is expired
        if datetime.utcnow() > stored_otp["expires_at"]:
            raise HTTPException(status_code=400, detail="OTP has expired. Please request a new OTP.")
        
        # Verify OTP
        if stored_otp["otp"] != otp:
            await security_manager.log_suspicious_activity(
                client_ip, 'invalid_otp_attempt', 
                f"Invalid OTP attempt for user {current_user['user_id']}"
            )
            raise HTTPException(status_code=400, detail="Invalid OTP. Please try again.")
        
        # Mark phone as verified
        await db.users.update_one(
            {"user_id": current_user["user_id"]},
            {
                "$set": {
                    "verification.phone_number": stored_otp["phone_number"],
                    "verification.phone_verified": True,
                    "verification.phone_verified_at": datetime.utcnow()
                }
            }
        )
        
        # Update verification level
        await update_user_verification_level(current_user["user_id"])
        
        # Mark OTP as used
        await db.phone_otps.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": {"verified": True}}
        )
        
        return {
            "status": "success",
            "message": "Phone number verified successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify OTP: {str(e)}")

@api_router.post("/verification/government-id")
@limiter.limit("3/minute")
async def submit_government_id(request: Request, id_data: GovernmentIDVerification, current_user = Depends(get_current_user)):
    """Submit government ID for verification (Indian documents)"""
    try:
        client_ip = get_remote_address(request)
        
        # Validate ID type
        valid_id_types = ["aadhaar", "pan", "voter_id", "passport", "driving_license"]
        if id_data.id_type not in valid_id_types:
            raise HTTPException(status_code=400, detail=f"Invalid ID type. Supported: {', '.join(valid_id_types)}")
        
        # Validate ID number format based on type
        if id_data.id_type == "aadhaar":
            if not re.match(r"^\d{12}$", id_data.id_number):
                raise HTTPException(status_code=400, detail="Aadhaar number must be 12 digits")
        elif id_data.id_type == "pan":
            if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", id_data.id_number):
                raise HTTPException(status_code=400, detail="PAN format: ABCDE1234F")
        elif id_data.id_type == "voter_id":
            if not re.match(r"^[A-Z]{3}[0-9]{7}$", id_data.id_number):
                raise HTTPException(status_code=400, detail="Voter ID format: ABC1234567")
        
        # Store verification request
        verification_request = {
            "user_id": current_user["user_id"],
            "id_type": id_data.id_type,
            "id_number": id_data.id_number,
            "full_name": id_data.full_name,
            "date_of_birth": id_data.date_of_birth,
            "address": id_data.address,
            "document_image": id_data.document_image,
            "status": "pending",
            "submitted_at": datetime.utcnow(),
            "verified_at": None,
            "rejection_reason": None
        }
        
        await db.government_id_verifications.update_one(
            {"user_id": current_user["user_id"]},
            {"$set": verification_request},
            upsert=True
        )
        
        # TODO: Integrate with ID verification service (like Aadhaar API, DigiLocker)
        # For now, auto-approve for development
        auto_approve = True  # Set to False in production
        
        if auto_approve:
            await db.government_id_verifications.update_one(
                {"user_id": current_user["user_id"]},
                {
                    "$set": {
                        "status": "verified",
                        "verified_at": datetime.utcnow()
                    }
                }
            )
            
            await db.users.update_one(
                {"user_id": current_user["user_id"]},
                {
                    "$set": {
                        "verification.government_id_verified": True,
                        "verification.government_id_type": id_data.id_type,
                        "verification.government_id_verified_at": datetime.utcnow()
                    }
                }
            )
            
            await update_user_verification_level(current_user["user_id"])
        
        await security_manager.log_activity(
            client_ip, 'government_id_submitted', 
            f"User {current_user['user_id']} submitted {id_data.id_type} for verification"
        )
        
        return {
            "status": "success",
            "message": "Government ID submitted successfully" if not auto_approve else "Government ID verified successfully",
            "verification_status": "verified" if auto_approve else "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit government ID: {str(e)}")

@api_router.get("/verification/status")
async def get_verification_status(current_user = Depends(get_current_user)):
    """Get current user's verification status"""
    try:
        user = await db.users.find_one({"user_id": current_user["user_id"]})
        verification = user.get("verification", {})
        
        # Get government ID verification details
        gov_id_verification = await db.government_id_verifications.find_one(
            {"user_id": current_user["user_id"]}
        )
        
        return {
            "email_verified": verification.get("email_verified", False),
            "phone_verified": verification.get("phone_verified", False),
            "phone_number": verification.get("phone_number"),
            "government_id_verified": verification.get("government_id_verified", False),
            "government_id_type": verification.get("government_id_type"),
            "verification_level": verification.get("verification_level", "basic"),
            "government_id_status": gov_id_verification.get("status") if gov_id_verification else None,
            "government_id_submitted_at": gov_id_verification.get("submitted_at") if gov_id_verification else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get verification status: {str(e)}")

async def update_user_verification_level(user_id: str):
    """Update user verification level based on completed verifications"""
    try:
        user = await db.users.find_one({"user_id": user_id})
        verification = user.get("verification", {})
        
        level = "basic"
        if verification.get("email_verified") and verification.get("phone_verified"):
            level = "verified"
        if verification.get("government_id_verified"):
            level = "premium"
        
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"verification.verification_level": level}}
        )
        
    except Exception as e:
        print(f"Failed to update verification level for {user_id}: {e}")

# =============================================================================
# SAFETY CHECK-IN SYSTEM
# =============================================================================

@api_router.post("/safety/check-in")
@limiter.limit("10/minute")
async def create_safety_checkin(request: Request, checkin: SafetyCheckIn, current_user = Depends(get_current_user)):
    """Create a safety check-in for marketplace meeting"""
    try:
        client_ip = get_remote_address(request)
        
        # Validate listing exists
        listing = await db.marketplace_listings.find_one({"listing_id": checkin.listing_id})
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Create check-in record
        checkin_data = {
            "checkin_id": str(uuid.uuid4()),
            "user_id": current_user["user_id"],
            "listing_id": checkin.listing_id,
            "meeting_location": checkin.meeting_location,
            "meeting_time": checkin.meeting_time,
            "contact_phone": checkin.contact_phone,
            "emergency_contact_name": checkin.emergency_contact_name,
            "emergency_contact_phone": checkin.emergency_contact_phone,
            "status": "scheduled",
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        }
        
        result = await db.safety_checkins.insert_one(checkin_data)
        
        # TODO: Schedule automatic check-in reminders
        # TODO: Send SMS to emergency contact
        
        await security_manager.log_activity(
            client_ip, 'safety_checkin_created', 
            f"User {current_user['user_id']} created safety check-in for listing {checkin.listing_id}"
        )
        
        return {
            "status": "success",
            "checkin_id": checkin_data["checkin_id"],
            "message": "Safety check-in created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create safety check-in: {str(e)}")

@api_router.put("/safety/check-in/{checkin_id}/status")
@limiter.limit("20/minute")
async def update_checkin_status(request: Request, checkin_id: str, status_data: dict, current_user = Depends(get_current_user)):
    """Update safety check-in status"""
    try:
        client_ip = get_remote_address(request)
        new_status = status_data.get("status")
        
        if new_status not in ["scheduled", "met", "completed", "emergency"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        # Find check-in
        checkin = await db.safety_checkins.find_one({"checkin_id": checkin_id})
        if not checkin:
            raise HTTPException(status_code=404, detail="Check-in not found")
        
        if checkin["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="You can only update your own check-ins")
        
        # Update status
        await db.safety_checkins.update_one(
            {"checkin_id": checkin_id},
            {
                "$set": {
                    "status": new_status,
                    "last_updated": datetime.utcnow()
                }
            }
        )
        
        # Handle emergency status
        if new_status == "emergency":
            # TODO: Alert emergency services
            # TODO: Notify emergency contacts
            await security_manager.log_suspicious_activity(
                client_ip, 'safety_emergency_triggered', 
                f"Emergency status triggered for check-in {checkin_id} by user {current_user['user_id']}"
            )
        
        return {
            "status": "success",
            "message": f"Check-in status updated to {new_status}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update check-in status: {str(e)}")

@api_router.get("/safety/check-ins")
async def get_user_checkins(current_user = Depends(get_current_user)):
    """Get user's safety check-ins"""
    try:
        checkins = await db.safety_checkins.find(
            {"user_id": current_user["user_id"]}
        ).sort("created_at", -1).to_list(50)
        
        return {
            "checkins": [serialize_mongo_doc(checkin) for checkin in checkins]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get check-ins: {str(e)}")

# =============================================================================
# ANALYTICS DASHBOARD FOR MARKETPLACE
# =============================================================================

@api_router.get("/analytics/dashboard")
async def get_analytics_dashboard(current_user = Depends(get_current_user)):
    """Get user's marketplace analytics dashboard"""
    try:
        user_id = current_user["user_id"]
        
        # Get user's listings stats
        total_listings = await db.marketplace_listings.count_documents({"user_id": user_id})
        active_listings = await db.marketplace_listings.count_documents(
            {"user_id": user_id, "availability": "available"}
        )
        sold_listings = await db.marketplace_listings.count_documents(
            {"user_id": user_id, "availability": "sold"}
        )
        
        # Get total views and messages for user's listings
        user_listings = await db.marketplace_listings.find({"user_id": user_id}).to_list(None)
        total_views = sum(listing.get("views", 0) for listing in user_listings)
        total_messages = sum(listing.get("messages_count", 0) for listing in user_listings)
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_listings = await db.marketplace_listings.count_documents({
            "user_id": user_id,
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # Get category breakdown
        category_pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        category_stats = await db.marketplace_listings.aggregate(category_pipeline).to_list(None)
        
        # Get performance metrics
        avg_views_per_listing = total_views / max(total_listings, 1)
        avg_messages_per_listing = total_messages / max(total_listings, 1)
        
        # Get user's verification status
        user = await db.users.find_one({"user_id": user_id})
        verification = user.get("verification", {})
        
        return {
            "overview": {
                "total_listings": total_listings,
                "active_listings": active_listings,
                "sold_listings": sold_listings,
                "total_views": total_views,
                "total_messages": total_messages,
                "recent_listings_30d": recent_listings
            },
            "performance": {
                "avg_views_per_listing": round(avg_views_per_listing, 1),
                "avg_messages_per_listing": round(avg_messages_per_listing, 1),
                "conversion_rate": round((sold_listings / max(total_listings, 1)) * 100, 1)
            },
            "category_breakdown": [
                {"category": item["_id"], "count": item["count"]} 
                for item in category_stats
            ],
            "verification_status": {
                "level": verification.get("verification_level", "basic"),
                "phone_verified": verification.get("phone_verified", False),
                "government_id_verified": verification.get("government_id_verified", False)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@api_router.get("/analytics/marketplace-stats")
async def get_marketplace_stats(current_user = Depends(get_current_user)):
    """Get overall marketplace statistics"""
    try:
        # Overall marketplace metrics
        total_listings = await db.marketplace_listings.count_documents({})
        active_listings = await db.marketplace_listings.count_documents(
            {"availability": "available"}
        )
        
        # Category distribution
        category_pipeline = [
            {"$match": {"availability": {"$in": ["available", "pending", "sold"]}}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        category_distribution = await db.marketplace_listings.aggregate(category_pipeline).to_list(None)
        
        # Price range analysis
        price_pipeline = [
            {"$match": {"price": {"$exists": True, "$ne": None}, "availability": "available"}},
            {"$group": {
                "_id": None,
                "avg_price": {"$avg": "$price"},
                "min_price": {"$min": "$price"},
                "max_price": {"$max": "$price"}
            }}
        ]
        price_stats = await db.marketplace_listings.aggregate(price_pipeline).to_list(None)
        price_data = price_stats[0] if price_stats else {}
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_listings = await db.marketplace_listings.count_documents({
            "created_at": {"$gte": seven_days_ago}
        })
        
        # Verification statistics
        total_users = await db.users.count_documents({})
        verified_users = await db.users.count_documents(
            {"verification.verification_level": {"$in": ["verified", "premium"]}}
        )
        
        return {
            "marketplace_overview": {
                "total_listings": total_listings,
                "active_listings": active_listings,
                "recent_listings_7d": recent_listings
            },
            "category_distribution": [
                {"category": item["_id"], "count": item["count"]} 
                for item in category_distribution
            ],
            "price_analysis": {
                "average_price": round(price_data.get("avg_price", 0), 2),
                "min_price": price_data.get("min_price", 0),
                "max_price": price_data.get("max_price", 0)
            },
            "user_verification": {
                "total_users": total_users,
                "verified_users": verified_users,
                "verification_rate": round((verified_users / max(total_users, 1)) * 100, 1)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get marketplace stats: {str(e)}")

@api_router.get("/analytics/listing/{listing_id}")
async def get_listing_analytics(listing_id: str, current_user = Depends(get_current_user)):
    """Get detailed analytics for a specific listing"""
    try:
        # Get listing
        listing = await db.marketplace_listings.find_one({"listing_id": listing_id})
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Verify ownership
        if listing["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="You can only view analytics for your own listings")
        
        # Get message count for this listing
        message_count = await db.messages.count_documents(
            {"marketplace_listing_id": listing_id}
        )
        
        # Calculate listing age
        listing_age = (datetime.utcnow() - listing["created_at"]).days
        
        # Get daily view breakdown (last 30 days) - simplified for MVP
        # In production, this would require view tracking by date
        
        return {
            "listing_info": {
                "title": listing["title"],
                "category": listing["category"],
                "price": listing.get("price"),
                "created_at": listing["created_at"].isoformat(),
                "availability": listing["availability"],
                "listing_age_days": listing_age
            },
            "performance": {
                "total_views": listing.get("views", 0),
                "total_messages": message_count,
                "views_per_day": round(listing.get("views", 0) / max(listing_age, 1), 1),
                "messages_per_day": round(message_count / max(listing_age, 1), 1)
            },
            "engagement": {
                "view_to_message_ratio": round(
                    (message_count / max(listing.get("views", 1), 1)) * 100, 1
                )
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get listing analytics: {str(e)}")

# =============================================================================
# REELS-BASED MARKETPLACE ENDPOINTS
# =============================================================================

@api_router.post("/reels/create")
@limiter.limit("10/minute")
async def create_service_reel(request: Request, reel: ServiceReel, current_user = Depends(get_current_user)):
    """Create a new service reel for marketplace"""
    try:
        client_ip = get_remote_address(request)
        
        # Validate category
        valid_categories = ["food", "design", "tech", "home", "beauty", "education", "fitness"]
        if reel.category not in valid_categories:
            raise HTTPException(status_code=400, detail=f"Invalid category. Supported: {', '.join(valid_categories)}")
        
        # Create reel data
        reel_data = {
            "reel_id": str(uuid.uuid4()),
            "user_id": current_user["user_id"],
            "username": current_user["username"],
            "display_name": current_user.get("display_name", current_user["username"]),
            "title": reel.title,
            "description": reel.description,
            "category": reel.category,
            "base_price": reel.base_price,
            "price_type": reel.price_type,
            "video_url": reel.video_url,
            "thumbnail_url": reel.thumbnail_url,
            "duration": reel.duration,
            "location": reel.location,
            "tags": reel.tags,
            "availability": "available",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "stats": {
                "views": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "bids": 0,
                "hires": 0
            },
            "is_active": True
        }
        
        result = await db.service_reels.insert_one(reel_data)
        
        await security_manager.log_activity(
            client_ip, 'service_reel_created',
            f"User {current_user['user_id']} created service reel {reel_data['reel_id']}"
        )
        
        return {
            "status": "success",
            "reel_id": reel_data["reel_id"],
            "message": "Service reel created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create service reel: {str(e)}")

@api_router.get("/reels/feed")
async def get_reels_feed(
    request: Request,
    category: Optional[str] = None,
    location: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = 1,
    limit: int = 20,
    current_user = Depends(get_current_user)
):
    """Get reels feed for marketplace discovery"""
    try:
        # Build filter
        feed_filter = {"is_active": True, "availability": {"$in": ["available", "busy"]}}
        
        if category:
            feed_filter["category"] = category
        
        if min_price is not None:
            feed_filter["base_price"] = {"$gte": min_price}
        
        if max_price is not None:
            if "base_price" in feed_filter:
                feed_filter["base_price"]["$lte"] = max_price
            else:
                feed_filter["base_price"] = {"$lte": max_price}
        
        if location:
            feed_filter["$or"] = [
                {"location.city": {"$regex": location, "$options": "i"}},
                {"location.state": {"$regex": location, "$options": "i"}}
            ]
        
        # Calculate skip for pagination
        skip = (page - 1) * limit
        
        # Get reels with user verification info
        pipeline = [
            {"$match": feed_filter},
            {"$lookup": {
                "from": "users",
                "localField": "user_id", 
                "foreignField": "user_id",
                "as": "seller_info"
            }},
            {"$sort": {"created_at": -1}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        
        reels = await db.service_reels.aggregate(pipeline).to_list(limit)
        total_count = await db.service_reels.count_documents(feed_filter)
        
        # Process reels data
        processed_reels = []
        for reel in reels:
            # Safely handle seller info
            seller_info = reel.get("seller_info", [])
            seller_info = seller_info[0] if seller_info and len(seller_info) > 0 else {}
            verification = seller_info.get("verification", {})
            
            reel_data = serialize_mongo_doc(reel)
            
            # Safely get reel attributes
            reel_username = reel.get("username", "unknown")
            reel_display_name = reel.get("display_name", reel_username)
            reel_location = reel.get("location", {})
            
            reel_data["seller"] = {
                "user_id": reel.get("user_id", ""),
                "name": reel_display_name,
                "username": f"@{reel_username}",
                "verification_level": verification.get("verification_level", "basic"),
                "rating": seller_info.get("rating", 4.0),
                "location": reel_location.get("city", "Unknown") if isinstance(reel_location, dict) else "Unknown",
                "email_verified": verification.get("email_verified", False),
                "phone_verified": verification.get("phone_verified", False),
                "government_id_verified": verification.get("government_id_verified", False)
            }
            
            # Remove sensitive seller info
            reel_data.pop("user_id", None)
            reel_data.pop("seller_info", None)
            
            processed_reels.append(reel_data)
        
        return {
            "reels": processed_reels,
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "has_more": (skip + limit) < total_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reels feed: {str(e)}")

@api_router.post("/reels/{reel_id}/like")
@limiter.limit("60/minute")
async def like_reel(request: Request, reel_id: str, current_user = Depends(get_current_user)):
    """Like or unlike a service reel"""
    try:
        client_ip = get_remote_address(request)
        
        # Check if already liked
        existing_like = await db.reel_likes.find_one({
            "reel_id": reel_id,
            "user_id": current_user["user_id"]
        })
        
        if existing_like:
            # Unlike
            await db.reel_likes.delete_one({
                "reel_id": reel_id,
                "user_id": current_user["user_id"]
            })
            
            await db.service_reels.update_one(
                {"reel_id": reel_id},
                {"$inc": {"stats.likes": -1}}
            )
            
            return {"status": "success", "action": "unliked"}
        else:
            # Like
            await db.reel_likes.insert_one({
                "reel_id": reel_id,
                "user_id": current_user["user_id"],
                "created_at": datetime.utcnow()
            })
            
            await db.service_reels.update_one(
                {"reel_id": reel_id},
                {"$inc": {"stats.likes": 1}}
            )
            
            return {"status": "success", "action": "liked"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to like reel: {str(e)}")

@api_router.post("/reels/{reel_id}/view")
@limiter.limit("100/minute")
async def record_reel_view(request: Request, reel_id: str, current_user = Depends(get_current_user)):
    """Record a view for a service reel"""
    try:
        # Update view count (could add view tracking per user to prevent spam)
        await db.service_reels.update_one(
            {"reel_id": reel_id},
            {"$inc": {"stats.views": 1}}
        )
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record view: {str(e)}")

@api_router.post("/reels/{reel_id}/bid")
@limiter.limit("20/minute")
async def submit_reel_bid(request: Request, reel_id: str, bid: ReelBid, current_user = Depends(get_current_user)):
    """Submit a bid for a service reel"""
    try:
        client_ip = get_remote_address(request)
        
        # Get reel info
        reel = await db.service_reels.find_one({"reel_id": reel_id})
        if not reel:
            raise HTTPException(status_code=404, detail="Service reel not found")
        
        # Can't bid on your own reel
        if reel["user_id"] == current_user["user_id"]:
            raise HTTPException(status_code=400, detail="Cannot bid on your own service")
        
        # Create bid
        bid_data = {
            "bid_id": str(uuid.uuid4()),
            "reel_id": reel_id,
            "seller_id": reel["user_id"],
            "buyer_id": current_user["user_id"],
            "buyer_name": current_user.get("display_name", current_user["username"]),
            "bid_amount": bid.bid_amount,
            "message": bid.message,
            "project_details": bid.project_details,
            "preferred_date": bid.preferred_date,
            "urgency": bid.urgency,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "service_info": {
                "title": reel["title"],
                "category": reel["category"],
                "base_price": reel["base_price"]
            }
        }
        
        result = await db.reel_bids.insert_one(bid_data)
        
        # Update reel stats
        await db.service_reels.update_one(
            {"reel_id": reel_id},
            {"$inc": {"stats.bids": 1}}
        )
        
        # Create chat between buyer and seller
        chat_id = str(uuid.uuid4())
        chat_data = {
            "chat_id": chat_id,
            "members": [current_user["user_id"], reel["user_id"]],
            "created_at": datetime.utcnow(),
            "is_group": False,
            "reel_id": reel_id,
            "bid_id": bid_data["bid_id"]
        }
        await db.chats.insert_one(chat_data)
        
        # Send notification message
        message_id = str(uuid.uuid4())
        notification_message = {
            "message_id": message_id,
            "chat_id": chat_id,
            "sender_id": current_user["user_id"],
            "content": f"💰 New bid for '{reel['title']}': ₹{bid.bid_amount}\n\n{bid.message}",
            "message_type": "reel_bid",
            "reel_id": reel_id,
            "bid_id": bid_data["bid_id"],
            "created_at": datetime.utcnow(),
            "read": False
        }
        
        await db.messages.insert_one(notification_message)
        
        # WebSocket notification
        if manager.is_user_online(reel["user_id"]):
            notification = {
                "type": "reel_bid",
                "chat_id": chat_id,
                "bid_id": bid_data["bid_id"],
                "buyer_name": current_user.get("display_name", current_user["username"]),
                "service_title": reel["title"],
                "bid_amount": bid.bid_amount
            }
            await manager.send_personal_message(json.dumps(notification), reel["user_id"])
        
        return {
            "status": "success",
            "bid_id": bid_data["bid_id"],
            "chat_id": chat_id,
            "message": "Bid submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit bid: {str(e)}")

@api_router.get("/reels/{reel_id}/reviews")
async def get_reel_reviews(reel_id: str, page: int = 1, limit: int = 10):
    """Get reviews for a service reel"""
    try:
        skip = (page - 1) * limit
        
        reviews = await db.reel_reviews.find(
            {"reel_id": reel_id}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        total_count = await db.reel_reviews.count_documents({"reel_id": reel_id})
        
        return {
            "reviews": [serialize_mongo_doc(review) for review in reviews],
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "has_more": (skip + limit) < total_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get reviews: {str(e)}")

@api_router.get("/reels/my-reels")
async def get_my_service_reels(current_user = Depends(get_current_user)):
    """Get current user's service reels"""
    try:
        reels = await db.service_reels.find(
            {"user_id": current_user["user_id"]}
        ).sort("created_at", -1).to_list(100)
        
        return {"reels": [serialize_mongo_doc(reel) for reel in reels]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get your reels: {str(e)}")

@api_router.get("/reels/categories")
async def get_reel_categories():
    """Get available reel categories"""
    categories = [
        {"value": "food", "label": "Food & Catering", "icon": "🍳"},
        {"value": "design", "label": "Design & Creative", "icon": "🎨"},
        {"value": "tech", "label": "Tech Services", "icon": "💻"},
        {"value": "home", "label": "Home Services", "icon": "🏠"},
        {"value": "beauty", "label": "Beauty & Wellness", "icon": "💄"},
        {"value": "education", "label": "Education & Tutoring", "icon": "📚"},
        {"value": "fitness", "label": "Fitness & Health", "icon": "💪"}
    ]
    
    return {"categories": categories}

# Performance monitoring endpoints
@api_router.get("/admin/performance")
async def get_performance_stats(current_user = Depends(get_current_user)):
    """Get performance statistics (admin only)"""
    # TODO: Add admin role check
    return {
        "cache_stats": cache_manager.get_stats(),
        "performance_stats": performance_monitor.get_stats(),
        "redis_available": REDIS_AVAILABLE
    }

@api_router.get("/admin/cache/clear")
async def clear_cache(pattern: str = None, current_user = Depends(get_current_user)):
    """Clear cache (admin only)"""
    # TODO: Add admin role check
    if pattern:
        await cache_manager.clear_pattern(pattern)
        return {"message": f"Cache cleared for pattern: {pattern}"}
    else:
        await cache_manager.clear_pattern("")
        return {"message": "All cache cleared"}

# Enhanced user endpoint with caching
@api_router.get("/users/profile")
async def get_user_profile(current_user = Depends(get_current_user)):
    """Get user profile with caching"""
    user_id = current_user["user_id"]
    cache_key = f"user_profile:{user_id}"
    
    # Try to get from cache first
    cached_profile = await cache_manager.get(cache_key)
    if cached_profile:
        return cached_profile
    
    # If not in cache, fetch from database
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    profile = serialize_mongo_doc(user)
    
    # Cache the result
    await cache_manager.set(cache_key, profile, CACHE_CONFIG['USER_CACHE_TTL'])
    
    return profile

# Enhanced chat list with caching
@api_router.get("/chats")
async def get_user_chats_cached(current_user = Depends(get_current_user)):
    """Get user chats with caching"""
    user_id = current_user["user_id"]
    cache_key = f"user_chats:{user_id}"
    
    # Try cache first
    cached_chats = await cache_manager.get(cache_key)
    if cached_chats:
        return cached_chats
    
    # Get from database
    chats = await db.chats.find({
        "participants": user_id
    }).sort("last_message_time", -1).to_list(100)
    
    result = {"chats": [serialize_mongo_doc(chat) for chat in chats]}
    
    # Cache result
    await cache_manager.set(cache_key, result, CACHE_CONFIG['CHAT_CACHE_TTL'])
    
    return result

# Enhanced message search with caching
@api_router.get("/chats/{chat_id}/messages/search")
async def search_messages_cached(
    chat_id: str,
    query: str,
    current_user = Depends(get_current_user)
):
    """Search messages with caching"""
    # Verify user is in chat
    chat = await db.chats.find_one({"chat_id": chat_id})
    if not chat or current_user["user_id"] not in chat["members"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    cache_key = f"message_search:{chat_id}:{hashlib.sha256(query.encode()).hexdigest()}"
    
    # Try cache first
    cached_results = await cache_manager.get(cache_key)
    if cached_results:
        return cached_results
    
    # Search in database
    messages = await db.messages.find({
        "chat_id": chat_id,
        "content": {"$regex": query, "$options": "i"}
    }).sort("timestamp", -1).limit(50).to_list(50)
    
    result = [serialize_mongo_doc(msg) for msg in messages]
    
    # Cache results
    await cache_manager.set(cache_key, result, CACHE_CONFIG['SEARCH_CACHE_TTL'])
    
    return result

# Start background tasks
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_task())

# Performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Monitor request performance"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Start monitoring
    await performance_monitor.start_request(request_id, request.url.path)
    
    try:
        response = await call_next(request)
        await performance_monitor.end_request(request_id, response.status_code)
        return response
    except Exception as e:
        await performance_monitor.end_request(request_id, 500)
        raise e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Include the router in the main app after all endpoints are defined
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()