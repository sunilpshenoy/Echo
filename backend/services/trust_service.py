"""
Pulse Backend - Trust Service
Business logic for trust levels, authenticity scoring, and progression
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

from models.connection import Connection, TrustLevelProgress, TrustMetrics
from models.safety import TrustScore
from config import settings, Collections
from database.connection import get_database

logger = logging.getLogger(__name__)


class TrustService:
    """Trust system business logic"""
    
    def __init__(self, db):
        self.db = db
    
    async def calculate_trust_score(self, user_id: str) -> TrustScore:
        """
        Calculate comprehensive trust/authenticity score (0-10 scale)
        
        **Components** (total 10.0):
        1. Profile Completeness (2.0 max)
        2. Interaction Consistency (2.0 max)
        3. Response Patterns (1.5 max)
        4. Sentiment Analysis (1.5 max)
        5. Community Feedback (1.5 max)
        6. Time Consistency (1.5 max)
        """
        user = await self.db[Collections.USERS].find_one({"user_id": user_id})
        if not user:
            raise ValueError("User not found")
        
        # Component 1: Profile Completeness (0-2.0)
        profile_score = await self._calculate_profile_completeness(user)
        
        # Component 2: Interaction Consistency (0-2.0)
        interaction_score = await self._calculate_interaction_consistency(user_id)
        
        # Component 3: Response Patterns (0-1.5)
        response_score = await self._calculate_response_patterns(user_id)
        
        # Component 4: Sentiment Analysis (0-1.5)
        sentiment_score = await self._calculate_sentiment_score(user_id)
        
        # Component 5: Community Feedback (0-1.5)
        feedback_score = await self._calculate_community_feedback(user_id)
        
        # Component 6: Time Consistency (0-1.5)
        time_score = await self._calculate_time_consistency(user)
        
        # Total score
        total_score = (
            profile_score +
            interaction_score +
            response_score +
            sentiment_score +
            feedback_score +
            time_score
        )
        
        trust_score = TrustScore(
            user_id=user_id,
            overall_score=round(total_score, 2),
            profile_completeness=round(profile_score, 2),
            interaction_consistency=round(interaction_score, 2),
            response_patterns=round(response_score, 2),
            sentiment_analysis=round(sentiment_score, 2),
            community_feedback=round(feedback_score, 2),
            time_consistency=round(time_score, 2),
            last_calculated=datetime.utcnow(),
            calculation_details={
                "total_connections": await self._get_connections_count(user_id),
                "days_active": (datetime.utcnow() - user["created_at"]).days,
                "verification_level": user.get("verification_level", "basic"),
                "reports_against": await self._get_reports_count(user_id)
            }
        )
        
        # Save to database
        await self.db[Collections.USERS].update_one(
            {"user_id": user_id},
            {"$set": {
                "authenticity_rating": trust_score.overall_score,
                "trust_score_breakdown": trust_score.dict()
            }}
        )
        
        logger.info(f"Trust score calculated for {user_id}: {trust_score.overall_score}/10.0")
        
        return trust_score
    
    async def _calculate_profile_completeness(self, user: Dict) -> float:
        """
        Profile completeness score (0-2.0)
        
        Checks:
        - Basic fields filled (0.5)
        - Avatar uploaded (0.3)
        - Bio/interests added (0.4)
        - Phone/email verified (0.5)
        - Government ID verified (0.3)
        """
        score = 0.0
        
        # Basic fields
        required_fields = ["username", "email", "display_name"]
        if all(user.get(field) for field in required_fields):
            score += 0.5
        
        # Avatar
        if user.get("avatar"):
            score += 0.3
        
        # Bio and interests
        if user.get("bio") or user.get("interests"):
            score += 0.4
        
        # Verification status
        if user.get("phone_verified") or user.get("email_verified"):
            score += 0.5
        
        if user.get("government_id_verified"):
            score += 0.3
        
        return min(score, 2.0)
    
    async def _calculate_interaction_consistency(self, user_id: str) -> float:
        """
        Interaction consistency score (0-2.0)
        
        Measures regular engagement patterns
        """
        # Get message activity last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        messages_count = await self.db[Collections.MESSAGES].count_documents({
            "sender_id": user_id,
            "timestamp": {"$gte": thirty_days_ago}
        })
        
        # Get connection count
        connections_count = await self._get_connections_count(user_id)
        
        # Score based on activity
        score = 0.0
        
        # Regular messaging (0-1.0)
        if messages_count > 100:
            score += 1.0
        elif messages_count > 50:
            score += 0.7
        elif messages_count > 20:
            score += 0.5
        elif messages_count > 5:
            score += 0.3
        
        # Active connections (0-1.0)
        if connections_count >= 10:
            score += 1.0
        elif connections_count >= 5:
            score += 0.7
        elif connections_count >= 3:
            score += 0.5
        elif connections_count >= 1:
            score += 0.3
        
        return min(score, 2.0)
    
    async def _calculate_response_patterns(self, user_id: str) -> float:
        """
        Response time patterns (0-1.5)
        
        Consistent response times indicate real person
        """
        # TODO: Analyze message response times
        # For now, return baseline
        return 1.0
    
    async def _calculate_sentiment_analysis(self, user_id: str) -> float:
        """
        Message sentiment analysis (0-1.5)
        
        Positive, constructive messages score higher
        """
        # TODO: Implement sentiment analysis on messages
        # For now, return baseline
        return 1.0
    
    async def _calculate_community_feedback(self, user_id: str) -> float:
        """
        Community feedback score (0-1.5)
        
        Based on reports, blocks, positive interactions
        """
        # Get reports against user
        reports = await self._get_reports_count(user_id)
        
        # Get blocks against user
        blocks = await self.db[Collections.BLOCKED_USERS].count_documents({
            "blocked_id": user_id
        })
        
        # Start with full score
        score = 1.5
        
        # Deduct for negative feedback
        score -= (reports * 0.3)  # -0.3 per report
        score -= (blocks * 0.2)   # -0.2 per block
        
        return max(score, 0.0)
    
    async def _calculate_time_consistency(self, user: Dict) -> float:
        """
        Time consistency score (0-1.5)
        
        Longer tenure = more trustworthy
        """
        days_active = (datetime.utcnow() - user["created_at"]).days
        
        if days_active >= 90:
            return 1.5
        elif days_active >= 60:
            return 1.2
        elif days_active >= 30:
            return 1.0
        elif days_active >= 14:
            return 0.7
        elif days_active >= 7:
            return 0.5
        else:
            return 0.3
    
    async def get_trust_progress(self, user_id: str) -> TrustLevelProgress:
        """
        Get user's trust level progression status
        
        Shows current level, next level, and requirements
        """
        user = await self.db[Collections.USERS].find_one({"user_id": user_id})
        if not user:
            raise ValueError("User not found")
        
        current_level = user.get("trust_level", 1)
        next_level = current_level + 1 if current_level < 5 else None
        
        # Get metrics
        metrics = await self._get_trust_metrics(user_id, user)
        
        # Check requirements for next level
        requirements_met = {}
        can_level_up = False
        
        if next_level and next_level in settings.TRUST_LEVELS:
            requirements = settings.TRUST_LEVELS[next_level].get("requirements", {})
            
            requirements_met = {
                "connections": metrics["total_connections"] >= requirements.get("connections", 0),
                "time_days": metrics["days_active"] >= requirements.get("time_days", 0),
                "interactions": metrics["total_interactions"] >= requirements.get("interactions", 0)
            }
            
            # Level 5 requires video calls
            if next_level == 5:
                requirements_met["video_calls"] = metrics["video_calls"] >= requirements.get("video_calls", 0)
            
            can_level_up = all(requirements_met.values())
        
        # Calculate progress percentage
        progress = 0.0
        if next_level and requirements_met:
            met_count = sum(1 for v in requirements_met.values() if v)
            progress = (met_count / len(requirements_met)) * 100
        
        return TrustLevelProgress(
            user_id=user_id,
            current_level=current_level,
            next_level=next_level,
            requirements_met=requirements_met,
            progress_percentage=round(progress, 1),
            can_level_up=can_level_up,
            **metrics
        )
    
    async def _get_trust_metrics(self, user_id: str, user: Dict) -> Dict:
        """Get detailed trust metrics"""
        connections_count = await self._get_connections_count(user_id)
        
        messages_count = await self.db[Collections.MESSAGES].count_documents({
            "sender_id": user_id
        })
        
        video_calls = await self.db[Collections.CALL_HISTORY].count_documents({
            "user_id": user_id,
            "call_type": {"$in": ["video", "group_video"]},
            "status": "completed"
        })
        
        days_active = (datetime.utcnow() - user["created_at"]).days
        
        return {
            "total_connections": connections_count,
            "days_active": days_active,
            "total_interactions": messages_count,
            "video_calls": video_calls
        }
    
    async def _get_connections_count(self, user_id: str) -> int:
        """Get count of accepted connections"""
        count = await self.db[Collections.CONNECTIONS].count_documents({
            "$or": [
                {"user1_id": user_id, "status": "accepted"},
                {"user2_id": user_id, "status": "accepted"}
            ]
        })
        return count
    
    async def _get_reports_count(self, user_id: str) -> int:
        """Get count of reports against user"""
        count = await self.db[Collections.REPORTED_USERS].count_documents({
            "reported_id": user_id
        })
        return count


async def get_trust_service():
    """Get trust service instance"""
    db = await get_database()
    return TrustService(db)
