"""
Pulse Backend - Connection & Trust Models
Data models for user connections and trust system
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
import uuid


class Connection(BaseModel):
    """User connection model"""
    connection_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user1_id: str
    user2_id: str
    status: str = "pending"  # pending, accepted, blocked, declined
    trust_level: int = 1  # 1-5 progressive trust levels
    connection_pin: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    interaction_count: int = 0
    
    # Trust progression
    trust_level_updated_at: Optional[datetime] = None
    trust_level_updated_by: Optional[str] = None  # Which user initiated level up
    mutual_consent: bool = False  # Both users agreed to level up
    
    # Metrics for trust calculation
    days_since_connection: int = 0
    video_calls_count: int = 0
    voice_calls_count: int = 0
    messages_count: int = 0
    
    @validator('trust_level')
    def validate_trust_level(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Trust level must be between 1 and 5')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        allowed = ['pending', 'accepted', 'blocked', 'declined']
        if v not in allowed:
            raise ValueError(f'Status must be one of {allowed}')
        return v


class ConnectionRequest(BaseModel):
    """Connection request model"""
    from_user_id: str
    to_user_id: str
    message: Optional[str] = None
    connection_pin: Optional[str] = None


class TrustLevelUpdate(BaseModel):
    """Request to update trust level"""
    connection_id: str
    new_trust_level: int = Field(..., ge=1, le=5)
    
    @validator('new_trust_level')
    def validate_level(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Trust level must be between 1 and 5')
        return v


class TrustLevelProgress(BaseModel):
    """Trust level progression tracking"""
    user_id: str
    current_level: int
    next_level: Optional[int] = None
    requirements_met: Dict[str, bool] = Field(default_factory=dict)
    progress_percentage: float = 0.0
    can_level_up: bool = False
    
    # Current metrics
    total_connections: int = 0
    days_active: int = 0
    total_interactions: int = 0
    video_calls: int = 0


class TrustMetrics(BaseModel):
    """Detailed trust metrics for a user"""
    user_id: str
    total_connections: int = 0
    verified_connections: int = 0
    days_since_registration: int = 0
    total_interactions: int = 0
    video_calls_completed: int = 0
    voice_calls_completed: int = 0
    messages_sent: int = 0
    safety_checkins_completed: int = 0
    reports_against: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0


class PinConnection(BaseModel):
    """PIN-based connection model"""
    user_id: str
    pin: str = Field(..., min_length=4, max_length=8)
    expires_at: datetime
    max_uses: int = 1
    current_uses: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BlockedUser(BaseModel):
    """Blocked user model"""
    blocker_id: str
    blocked_id: str
    reason: Optional[str] = None
    blocked_at: datetime = Field(default_factory=datetime.utcnow)


class MutualConsent(BaseModel):
    """Mutual consent for trust level upgrade"""
    connection_id: str
    proposed_level: int
    proposed_by: str
    proposed_at: datetime = Field(default_factory=datetime.utcnow)
    consented_by: Optional[str] = None
    consented_at: Optional[datetime] = None
    status: str = "pending"  # pending, approved, declined, expired
