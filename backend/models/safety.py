"""
Pulse Backend - Safety & Trust Score Models
Data models for safety features and trust scoring
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
import uuid


class TrustScore(BaseModel):
    """Trust score model for user reputation"""
    user_id: str
    score: float = Field(default=0.0, ge=0.0, le=100.0)  # 0-100 score
    trust_level: int = Field(default=1, ge=1, le=5)  # 1-5 trust levels
    verification_count: int = 0
    connection_count: int = 0
    positive_interactions: int = 0
    negative_interactions: int = 0
    reported_count: int = 0
    blocked_count: int = 0
    
    # Trust factors
    profile_completeness: float = 0.0  # 0-1
    account_age_days: int = 0
    last_active: Optional[datetime] = None
    
    # Score breakdown
    verification_score: float = 0.0
    interaction_score: float = 0.0
    network_score: float = 0.0
    safety_score: float = 0.0
    
    # Timestamps
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('score')
    def validate_score(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Score must be between 0 and 100')
        return v
    
    @validator('trust_level')
    def validate_trust_level(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Trust level must be between 1 and 5')
        return v


class SafetyCheckin(BaseModel):
    """Safety check-in for meeting safety"""
    checkin_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    meeting_id: Optional[str] = None
    connection_id: Optional[str] = None
    
    # Check-in details
    checkin_time: datetime = Field(default_factory=datetime.utcnow)
    expected_duration_minutes: int = 60
    location: Optional[Dict] = None  # lat, lng, address
    emergency_contact: Optional[str] = None
    
    # Status tracking
    status: str = "active"  # active, completed, overdue, emergency
    reminder_sent: bool = False
    reminder_time: Optional[datetime] = None
    escalation_level: int = 0  # 0=none, 1=reminder, 2=emergency contact, 3=admin
    
    # Completion
    completed_at: Optional[datetime] = None
    completion_status: Optional[str] = None  # safe, emergency, cancelled
    
    @validator('status')
    def validate_status(cls, v):
        allowed = ['active', 'completed', 'overdue', 'emergency']
        if v not in allowed:
            raise ValueError(f'Status must be one of {allowed}')
        return v


class VerificationRequest(BaseModel):
    """Verification request model"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    verification_type: str  # ai, live_video, social, phone, email
    status: str = "pending"  # pending, in_progress, completed, failed, expired
    
    # Request details
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Verification data
    verification_data: Optional[Dict] = None
    result: Optional[Dict] = None
    confidence_score: Optional[float] = None
    
    # Challenge (for live video verification)
    challenge_code: Optional[str] = None
    challenge_type: Optional[str] = None  # text, gesture, sequence
    
    @validator('verification_type')
    def validate_verification_type(cls, v):
        allowed = ['ai', 'live_video', 'social', 'phone', 'email', 'aadhaar']
        if v not in allowed:
            raise ValueError(f'Verification type must be one of {allowed}')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        allowed = ['pending', 'in_progress', 'completed', 'failed', 'expired']
        if v not in allowed:
            raise ValueError(f'Status must be one of {allowed}')
        return v


class NetworkAnalysisResult(BaseModel):
    """Network trust analysis result"""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Risk factors
    fake_rating_risk: float = 0.0  # 0-1
    circular_rating_detected: bool = False
    suspicious_device_pattern: bool = False
    rapid_connection_pattern: bool = False
    
    # Network metrics
    connection_graph_density: float = 0.0
    average_trust_distance: float = 0.0
    shared_connections_count: int = 0
    
    # Risk score
    overall_risk_score: float = 0.0  # 0-1
    risk_level: str = "low"  # low, medium, high, critical
    
    # Recommendations
    recommendations: List[str] = []
    flags: List[str] = []
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        allowed = ['low', 'medium', 'high', 'critical']
        if v not in allowed:
            raise ValueError(f'Risk level must be one of {allowed}')
        return v


class MeetingSafety(BaseModel):
    """Meeting safety record"""
    meeting_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    connection_id: str
    user1_id: str
    user2_id: str
    
    # Meeting details
    scheduled_time: Optional[datetime] = None
    meeting_start: Optional[datetime] = None
    meeting_end: Optional[datetime] = None
    location: Optional[Dict] = None
    
    # Safety measures
    safety_checkin_enabled: bool = True
    emergency_contacts_notified: bool = False
    trust_deposit_held: bool = False
    pre_meeting_verification: bool = False
    
    # Status
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled, emergency
    safety_status: str = "normal"  # normal, overdue, alert, emergency
    
    # Safety checkins
    checkin_ids: List[str] = []
    last_checkin: Optional[datetime] = None
    
    @validator('status')
    def validate_status(cls, v):
        allowed = ['scheduled', 'in_progress', 'completed', 'cancelled', 'emergency']
        if v not in allowed:
            raise ValueError(f'Status must be one of {allowed}')
        return v
    
    @validator('safety_status')
    def validate_safety_status(cls, v):
        allowed = ['normal', 'overdue', 'alert', 'emergency']
        if v not in allowed:
            raise ValueError(f'Safety status must be one of {allowed}')
        return v
