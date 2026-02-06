"""
Meeting Safety Service

Implements strict safety protocols for in-person meetings (Problem C):
1. Mandatory Waiting Periods
2. Pre-Meeting Verification
3. Trust Deposit System
4. Safety Network Integration
5. First Meeting Protocol

All algorithms and scoring logic are confidential.
Users see results only, never the underlying rules.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from bson import ObjectId
from database.connection import Collections, get_db
import logging

logger = logging.getLogger(__name__)


class MeetingSafetyService:
    """Implements comprehensive meeting safety protocols"""

    # ==================== CONFIDENTIAL THRESHOLDS ====================
    # These values are NOT exposed to users
    _MIN_ACCOUNT_AGE_FOR_VOICE = 7  # days
    _MIN_ACCOUNT_AGE_FOR_VIDEO = 14  # days
    _MIN_ACCOUNT_AGE_FOR_MEETING = 30  # days
    
    _MIN_CONNECTION_AGE_FOR_VOICE = 24  # hours
    _MIN_CONNECTION_AGE_FOR_VIDEO = 48  # hours
    _MIN_CONNECTION_AGE_FOR_MEETING = 168  # hours (7 days)
    
    _MIN_VOICE_CALLS_FOR_VIDEO = 3
    _MIN_VIDEO_CALLS_FOR_MEETING = 2
    
    _TRUST_DEPOSIT_AMOUNT = 1.0  # Rating points at risk
    _PENALTY_MILD_MISCONDUCT = -0.5
    _PENALTY_MODERATE_MISCONDUCT = -1.5
    _PENALTY_SEVERE_MISCONDUCT = -3.0
    _PENALTY_ASSAULT = -5.0
    
    # ==================== PUBLIC METHODS ====================
    
    async def check_level_progression(
        self,
        user_id: str,
        target_user_id: str,
        current_level: int,
        target_level: int
    ) -> Dict:
        """
        Check if user can progress to target level with target_user.
        
        Returns public-facing result with waiting time if blocked.
        NEVER exposes internal threshold values.
        """
        if target_level <= current_level:
            return {
                "allowed": True,
                "message": "Level progression allowed",
                "waiting_required": False
            }
        
        # Level 1 → 2 (Voice Call)
        if current_level == 1 and target_level == 2:
            return await self._check_voice_progression(user_id, target_user_id)
        
        # Level 2 → 3 (Video Call)
        elif current_level == 2 and target_level == 3:
            return await self._check_video_progression(user_id, target_user_id)
        
        # Level 3 → 4 (In-Person Meeting)
        elif current_level == 3 and target_level == 4:
            return await self._check_meeting_progression(user_id, target_user_id)
        
        else:
            return {
                "allowed": False,
                "message": "Invalid level progression",
                "waiting_required": False
            }
    
    async def create_pre_meeting_verification(
        self,
        user_a_id: str,
        user_b_id: str,
        meeting_details: Dict
    ) -> Dict:
        """
        Create pre-meeting verification challenge.
        Both users must verify before meeting is allowed.
        """
        db = await get_db()
        
        verification = {
            "_id": ObjectId(),
            "user_a_id": ObjectId(user_a_id),
            "user_b_id": ObjectId(user_b_id),
            "meeting_location": meeting_details.get("location"),
            "meeting_time": meeting_details.get("time"),
            "status": "pending",
            "user_a_verified": False,
            "user_b_verified": False,
            "user_a_answers": None,
            "user_b_answers": None,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
        
        await db[Collections.MEETING_VERIFICATIONS].insert_one(verification)
        
        return {
            "verification_id": str(verification["_id"]),
            "status": "pending",
            "message": "Both users must complete verification before meeting",
            "expires_at": verification["expires_at"].isoformat()
        }
    
    async def submit_verification_answers(
        self,
        verification_id: str,
        user_id: str,
        answers: Dict
    ) -> Dict:
        """
        Submit verification answers for a user.
        Checks for consistency when both users have answered.
        """
        db = await get_db()
        
        verification = await db[Collections.MEETING_VERIFICATIONS].find_one(
            {"_id": ObjectId(verification_id)}
        )
        
        if not verification:
            return {
                "success": False,
                "message": "Verification not found"
            }
        
        # Determine which user is submitting
        user_oid = ObjectId(user_id)
        is_user_a = verification["user_a_id"] == user_oid
        
        # Update verification with user's answers
        update_fields = {}
        if is_user_a:
            update_fields["user_a_verified"] = True
            update_fields["user_a_answers"] = answers
        else:
            update_fields["user_b_verified"] = True
            update_fields["user_b_answers"] = answers
        
        await db[Collections.MEETING_VERIFICATIONS].update_one(
            {"_id": ObjectId(verification_id)},
            {"$set": update_fields}
        )
        
        # Reload verification
        verification = await db[Collections.MEETING_VERIFICATIONS].find_one(
            {"_id": ObjectId(verification_id)}
        )
        
        # If both verified, check consistency
        if verification["user_a_verified"] and verification["user_b_verified"]:
            consistency = await self._verify_answer_consistency(
                verification["user_a_answers"],
                verification["user_b_answers"]
            )
            
            if consistency["consistent"]:
                await db[Collections.MEETING_VERIFICATIONS].update_one(
                    {"_id": ObjectId(verification_id)},
                    {"$set": {"status": "verified"}}
                )
                return {
                    "success": True,
                    "message": "Meeting verified! You may proceed.",
                    "status": "verified"
                }
            else:
                await db[Collections.MEETING_VERIFICATIONS].update_one(
                    {"_id": ObjectId(verification_id)},
                    {"$set": {"status": "failed", "failure_reason": consistency["issues"]}}
                )
                
                # Alert safety team
                await self._alert_verification_mismatch(verification_id, consistency["issues"])
                
                return {
                    "success": False,
                    "message": "⚠️ Verification failed. Details do not match. Please contact support.",
                    "status": "failed"
                }
        
        return {
            "success": True,
            "message": "Your verification submitted. Waiting for other user.",
            "status": "partial"
        }
    
    async def create_trust_deposit(
        self,
        user_a_id: str,
        user_b_id: str,
        meeting_id: str
    ) -> Dict:
        """
        Create trust deposit for both users before meeting.
        Users stake their reputation on good behavior.
        """
        db = await get_db()
        
        # Get current ratings
        user_a = await db[Collections.USERS].find_one({"_id": ObjectId(user_a_id)})
        user_b = await db[Collections.USERS].find_one({"_id": ObjectId(user_b_id)})
        
        deposit = {
            "_id": ObjectId(),
            "meeting_id": ObjectId(meeting_id),
            "user_a_id": ObjectId(user_a_id),
            "user_b_id": ObjectId(user_b_id),
            "user_a_deposited_rating": user_a.get("authenticity_rating", 5.0),
            "user_b_deposited_rating": user_b.get("authenticity_rating", 5.0),
            "deposit_amount": self._TRUST_DEPOSIT_AMOUNT,
            "status": "active",
            "created_at": datetime.utcnow(),
            "resolved_at": None
        }
        
        await db[Collections.TRUST_DEPOSITS].insert_one(deposit)
        
        return {
            "deposit_id": str(deposit["_id"]),
            "message": "⚠️ Your rating is at stake. Any misconduct will result in penalties.",
            "at_risk": self._TRUST_DEPOSIT_AMOUNT,
            "current_rating": user_a.get("authenticity_rating", 5.0) if user_id == user_a_id else user_b.get("authenticity_rating", 5.0)
        }
    
    async def handle_post_meeting_report(
        self,
        meeting_id: str,
        reporter_id: str,
        reported_user_id: str,
        report_type: str,
        details: str
    ) -> Dict:
        """
        Handle post-meeting misconduct report.
        Applies penalties to reported user's trust deposit.
        
        Report types (confidential):
        - mild: Late, rude, uncomfortable
        - moderate: Lied about identity, inappropriate behavior
        - severe: Harassment, threats, unsafe situation
        - assault: Physical assault, attempted assault
        """
        db = await get_db()
        
        # Find trust deposit
        deposit = await db[Collections.TRUST_DEPOSITS].find_one({
            "meeting_id": ObjectId(meeting_id),
            "status": "active"
        })
        
        if not deposit:
            return {
                "success": False,
                "message": "No active trust deposit found for this meeting"
            }
        
        # Determine penalty (internal logic)
        penalty = self._calculate_penalty(report_type)
        
        # Apply penalty
        await db[Collections.USERS].update_one(
            {"_id": ObjectId(reported_user_id)},
            {
                "$inc": {"authenticity_rating": penalty},
                "$push": {
                    "reports_received": {
                        "reporter_id": ObjectId(reporter_id),
                        "meeting_id": ObjectId(meeting_id),
                        "type": report_type,
                        "penalty": penalty,
                        "timestamp": datetime.utcnow()
                    }
                }
            }
        )
        
        # Update deposit
        await db[Collections.TRUST_DEPOSITS].update_one(
            {"_id": deposit["_id"]},
            {
                "$set": {
                    "status": "resolved",
                    "resolution": "penalty_applied",
                    "penalty_amount": penalty,
                    "resolved_at": datetime.utcnow()
                }
            }
        )
        
        # Immediate ban for assault
        if report_type == "assault":
            await db[Collections.USERS].update_one(
                {"_id": ObjectId(reported_user_id)},
                {"$set": {"account_status": "banned", "banned_at": datetime.utcnow()}}
            )
        
        # Create safety alert
        await self._create_safety_alert(
            meeting_id, reporter_id, reported_user_id, report_type, penalty
        )
        
        return {
            "success": True,
            "message": "Report submitted. User has been penalized and investigation initiated.",
            "action_taken": "penalty_applied" if report_type != "assault" else "user_banned"
        }
    
    async def create_safety_network_check_in(
        self,
        meeting_id: str,
        user_id: str,
        safety_contacts: List[str]
    ) -> Dict:
        """
        Create safety network monitoring for meeting.
        Trusted contacts are notified and can monitor status.
        """
        db = await get_db()
        
        meeting = await db[Collections.MEETINGS].find_one({"_id": ObjectId(meeting_id)})
        if not meeting:
            return {"success": False, "message": "Meeting not found"}
        
        check_in = {
            "_id": ObjectId(),
            "meeting_id": ObjectId(meeting_id),
            "user_id": ObjectId(user_id),
            "safety_contacts": [ObjectId(c) for c in safety_contacts],
            "location": meeting.get("location"),
            "scheduled_time": meeting.get("scheduled_time"),
            "expected_duration": meeting.get("duration", 120),  # minutes
            "status": "scheduled",
            "last_check_in": None,
            "alerts": [],
            "created_at": datetime.utcnow()
        }
        
        await db[Collections.SAFETY_CHECK_INS].insert_one(check_in)
        
        # Notify safety contacts
        await self._notify_safety_network(check_in)
        
        return {
            "check_in_id": str(check_in["_id"]),
            "message": f"Safety network activated with {len(safety_contacts)} contact(s)",
            "safety_contacts_notified": len(safety_contacts)
        }
    
    async def validate_first_meeting_requirements(
        self,
        user_a_id: str,
        user_b_id: str,
        meeting_details: Dict
    ) -> Dict:
        """
        Validate first meeting protocol requirements.
        Extra strict checks for first in-person meeting.
        """
        db = await get_db()
        
        # Check if this is first meeting
        existing_meetings = await db[Collections.MEETINGS].count_documents({
            "$or": [
                {"user_a_id": ObjectId(user_a_id), "user_b_id": ObjectId(user_b_id)},
                {"user_a_id": ObjectId(user_b_id), "user_b_id": ObjectId(user_a_id)}
            ],
            "status": {"$in": ["completed", "in_progress"]}
        })
        
        if existing_meetings > 0:
            return {"is_first_meeting": False, "allowed": True}
        
        # First meeting - apply strict protocol
        checks = {
            "is_first_meeting": True,
            "video_calls_completed": False,
            "connection_age_sufficient": False,
            "emergency_contact_configured": False,
            "public_place_confirmed": False,
            "daylight_meeting": False,
            "location_sharing_enabled": False
        }
        
        # Check video call history
        video_calls = await db[Collections.CALLS].count_documents({
            "$or": [
                {"caller_id": ObjectId(user_a_id), "receiver_id": ObjectId(user_b_id)},
                {"caller_id": ObjectId(user_b_id), "receiver_id": ObjectId(user_a_id)}
            ],
            "call_type": "video",
            "status": "completed"
        })
        checks["video_calls_completed"] = video_calls >= self._MIN_VIDEO_CALLS_FOR_MEETING
        
        # Check connection age
        connection = await db[Collections.CONNECTIONS].find_one({
            "$or": [
                {"sender_id": ObjectId(user_a_id), "receiver_id": ObjectId(user_b_id)},
                {"sender_id": ObjectId(user_b_id), "receiver_id": ObjectId(user_a_id)}
            ],
            "status": "accepted"
        })
        
        if connection:
            conn_age = (datetime.utcnow() - connection["created_at"]).days
            checks["connection_age_sufficient"] = conn_age >= 14
        
        # Check emergency contacts
        user_a = await db[Collections.USERS].find_one({"_id": ObjectId(user_a_id)})
        checks["emergency_contact_configured"] = bool(
            user_a and user_a.get("emergency_contacts")
        )
        
        # Check meeting details
        location = meeting_details.get("location", "").lower()
        checks["public_place_confirmed"] = any(
            place in location for place in ["cafe", "mall", "restaurant", "park", "public"]
        )
        
        # Check meeting time (8 AM - 8 PM)
        meeting_time = meeting_details.get("time")
        if meeting_time:
            hour = meeting_time.hour if isinstance(meeting_time, datetime) else 12
            checks["daylight_meeting"] = 8 <= hour <= 20
        
        checks["location_sharing_enabled"] = meeting_details.get("location_sharing", False)
        
        # Calculate overall readiness
        all_checks_passed = all(checks.values())
        
        if all_checks_passed:
            return {
                **checks,
                "allowed": True,
                "message": "✅ All safety requirements met"
            }
        else:
            missing = [k for k, v in checks.items() if not v and k != "is_first_meeting"]
            return {
                **checks,
                "allowed": False,
                "message": "⚠️ Please complete all safety requirements before meeting",
                "missing_requirements": missing
            }
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    async def _check_voice_progression(
        self, user_id: str, target_user_id: str
    ) -> Dict:
        """Check if voice call can be initiated"""
        db = await get_db()
        
        user = await db[Collections.USERS].find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"allowed": False, "message": "User not found"}
        
        # Check account age
        account_age_days = (datetime.utcnow() - user["created_at"]).days
        if account_age_days < self._MIN_ACCOUNT_AGE_FOR_VOICE:
            wait_days = self._MIN_ACCOUNT_AGE_FOR_VOICE - account_age_days
            return {
                "allowed": False,
                "waiting_required": True,
                "wait_duration_hours": wait_days * 24,
                "message": f"⏳ Please continue building your connection. Voice calls will be available soon."
            }
        
        # Check connection age
        connection = await db[Collections.CONNECTIONS].find_one({
            "$or": [
                {"sender_id": ObjectId(user_id), "receiver_id": ObjectId(target_user_id)},
                {"sender_id": ObjectId(target_user_id), "receiver_id": ObjectId(user_id)}
            ],
            "status": "accepted"
        })
        
        if not connection:
            return {"allowed": False, "message": "No active connection found"}
        
        connection_age_hours = (datetime.utcnow() - connection["created_at"]).total_seconds() / 3600
        
        if connection_age_hours < self._MIN_CONNECTION_AGE_FOR_VOICE:
            wait_hours = int(self._MIN_CONNECTION_AGE_FOR_VOICE - connection_age_hours)
            return {
                "allowed": False,
                "waiting_required": True,
                "wait_duration_hours": wait_hours,
                "message": f"⏳ Take time to know each other better. Voice calls will unlock soon."
            }
        
        return {
            "allowed": True,
            "message": "✅ Voice call available",
            "waiting_required": False
        }
    
    async def _check_video_progression(
        self, user_id: str, target_user_id: str
    ) -> Dict:
        """Check if video call can be initiated"""
        db = await get_db()
        
        user = await db[Collections.USERS].find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"allowed": False, "message": "User not found"}
        
        # Check account age
        account_age_days = (datetime.utcnow() - user["created_at"]).days
        if account_age_days < self._MIN_ACCOUNT_AGE_FOR_VIDEO:
            wait_days = self._MIN_ACCOUNT_AGE_FOR_VIDEO - account_age_days
            return {
                "allowed": False,
                "waiting_required": True,
                "wait_duration_hours": wait_days * 24,
                "message": f"⏳ Trust takes time. Continue your journey together."
            }
        
        # Check voice call history
        voice_calls = await db[Collections.CALLS].count_documents({
            "$or": [
                {"caller_id": ObjectId(user_id), "receiver_id": ObjectId(target_user_id)},
                {"caller_id": ObjectId(target_user_id), "receiver_id": ObjectId(user_id)}
            ],
            "call_type": "voice",
            "status": "completed"
        })
        
        if voice_calls < self._MIN_VOICE_CALLS_FOR_VIDEO:
            remaining = self._MIN_VOICE_CALLS_FOR_VIDEO - voice_calls
            return {
                "allowed": False,
                "waiting_required": True,
                "requirements_missing": f"{remaining} more voice call(s)",
                "message": f"⏳ Complete a few more voice calls to build trust before video."
            }
        
        # Check connection age
        connection = await db[Collections.CONNECTIONS].find_one({
            "$or": [
                {"sender_id": ObjectId(user_id), "receiver_id": ObjectId(target_user_id)},
                {"sender_id": ObjectId(target_user_id), "receiver_id": ObjectId(user_id)}
            ],
            "status": "accepted"
        })
        
        if not connection:
            return {"allowed": False, "message": "No active connection found"}
        
        connection_age_hours = (datetime.utcnow() - connection["created_at"]).total_seconds() / 3600
        
        if connection_age_hours < self._MIN_CONNECTION_AGE_FOR_VIDEO:
            wait_hours = int(self._MIN_CONNECTION_AGE_FOR_VIDEO - connection_age_hours)
            return {
                "allowed": False,
                "waiting_required": True,
                "wait_duration_hours": wait_hours,
                "message": f"⏳ Building strong connections takes patience."
            }
        
        return {
            "allowed": True,
            "message": "✅ Video call available",
            "waiting_required": False
        }
    
    async def _check_meeting_progression(
        self, user_id: str, target_user_id: str
    ) -> Dict:
        """Check if in-person meeting can be scheduled"""
        db = await get_db()
        
        user = await db[Collections.USERS].find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"allowed": False, "message": "User not found"}
        
        # Check account age
        account_age_days = (datetime.utcnow() - user["created_at"]).days
        if account_age_days < self._MIN_ACCOUNT_AGE_FOR_MEETING:
            wait_days = self._MIN_ACCOUNT_AGE_FOR_MEETING - account_age_days
            return {
                "allowed": False,
                "waiting_required": True,
                "wait_duration_hours": wait_days * 24,
                "message": f"⏳ Great connections are worth waiting for. Meeting will unlock soon."
            }
        
        # Check video call history
        video_calls = await db[Collections.CALLS].count_documents({
            "$or": [
                {"caller_id": ObjectId(user_id), "receiver_id": ObjectId(target_user_id)},
                {"caller_id": ObjectId(target_user_id), "receiver_id": ObjectId(user_id)}
            ],
            "call_type": "video",
            "status": "completed"
        })
        
        if video_calls < self._MIN_VIDEO_CALLS_FOR_MEETING:
            remaining = self._MIN_VIDEO_CALLS_FOR_MEETING - video_calls
            return {
                "allowed": False,
                "waiting_required": True,
                "requirements_missing": f"{remaining} more video call(s)",
                "message": f"⏳ A few more video chats will help you both feel safer about meeting."
            }
        
        # Check connection age
        connection = await db[Collections.CONNECTIONS].find_one({
            "$or": [
                {"sender_id": ObjectId(user_id), "receiver_id": ObjectId(target_user_id)},
                {"sender_id": ObjectId(target_user_id), "receiver_id": ObjectId(user_id)}
            ],
            "status": "accepted"
        })
        
        if not connection:
            return {"allowed": False, "message": "No active connection found"}
        
        connection_age_hours = (datetime.utcnow() - connection["created_at"]).total_seconds() / 3600
        
        if connection_age_hours < self._MIN_CONNECTION_AGE_FOR_MEETING:
            wait_hours = int(self._MIN_CONNECTION_AGE_FOR_MEETING - connection_age_hours)
            wait_days = wait_hours // 24
            return {
                "allowed": False,
                "waiting_required": True,
                "wait_duration_hours": wait_hours,
                "message": f"⏳ Your safety is our priority. {wait_days} more day(s) to go!"
            }
        
        # Check safety check-in exists
        if not user.get("emergency_contacts"):
            return {
                "allowed": False,
                "message": "⚠️ Please configure emergency contacts before scheduling meetings"
            }
        
        return {
            "allowed": True,
            "message": "✅ Meeting can be scheduled with safety protocols",
            "waiting_required": False,
            "requires_verification": True
        }
    
    async def _verify_answer_consistency(
        self,
        answers_a: Dict,
        answers_b: Dict
    ) -> Dict:
        """Verify consistency between two users' verification answers"""
        issues = []
        
        # Check location match
        loc_a = answers_a.get("location", "").lower()
        loc_b = answers_b.get("location", "").lower()
        
        if loc_a != loc_b:
            if not (loc_a in loc_b or loc_b in loc_a):
                issues.append("Location mismatch")
        
        # Check time match (within 30 minutes)
        time_a = answers_a.get("time")
        time_b = answers_b.get("time")
        
        if time_a and time_b:
            if isinstance(time_a, str):
                time_a = datetime.fromisoformat(time_a)
            if isinstance(time_b, str):
                time_b = datetime.fromisoformat(time_b)
            
            time_diff = abs((time_a - time_b).total_seconds() / 60)
            if time_diff > 30:
                issues.append("Time mismatch (>30 min difference)")
        
        # Check description similarity
        desc_a = answers_a.get("description", "").lower()
        desc_b = answers_b.get("description", "").lower()
        
        # Simple word overlap check
        words_a = set(desc_a.split())
        words_b = set(desc_b.split())
        
        if words_a and words_b:
            overlap = len(words_a & words_b) / len(words_a | words_b)
            if overlap < 0.3:  # Less than 30% word overlap
                issues.append("Description mismatch")
        
        return {
            "consistent": len(issues) == 0,
            "issues": issues
        }
    
    def _calculate_penalty(self, report_type: str) -> float:
        """Calculate penalty based on report type (confidential)"""
        penalties = {
            "mild": self._PENALTY_MILD_MISCONDUCT,
            "moderate": self._PENALTY_MODERATE_MISCONDUCT,
            "severe": self._PENALTY_SEVERE_MISCONDUCT,
            "assault": self._PENALTY_ASSAULT
        }
        return penalties.get(report_type, self._PENALTY_MILD_MISCONDUCT)
    
    async def _alert_verification_mismatch(
        self, verification_id: str, issues: List[str]
    ):
        """Alert safety team about verification mismatch"""
        db = await get_db()
        
        alert = {
            "_id": ObjectId(),
            "type": "verification_mismatch",
            "verification_id": ObjectId(verification_id),
            "issues": issues,
            "priority": "high",
            "status": "open",
            "created_at": datetime.utcnow()
        }
        
        await db[Collections.SAFETY_ALERTS].insert_one(alert)
        logger.warning(f"Verification mismatch detected: {verification_id} - {issues}")
    
    async def _create_safety_alert(
        self,
        meeting_id: str,
        reporter_id: str,
        reported_user_id: str,
        report_type: str,
        penalty: float
    ):
        """Create safety alert for investigation"""
        db = await get_db()
        
        alert = {
            "_id": ObjectId(),
            "type": "post_meeting_report",
            "meeting_id": ObjectId(meeting_id),
            "reporter_id": ObjectId(reporter_id),
            "reported_user_id": ObjectId(reported_user_id),
            "report_type": report_type,
            "penalty_applied": penalty,
            "priority": "critical" if report_type == "assault" else "high",
            "status": "investigating",
            "created_at": datetime.utcnow()
        }
        
        await db[Collections.SAFETY_ALERTS].insert_one(alert)
        logger.critical(f"Safety alert created: {report_type} - Meeting {meeting_id}")
    
    async def _notify_safety_network(self, check_in: Dict):
        """Notify safety contacts about meeting"""
        db = await get_db()
        
        for contact_id in check_in["safety_contacts"]:
            notification = {
                "_id": ObjectId(),
                "user_id": contact_id,
                "type": "safety_network_activation",
                "check_in_id": check_in["_id"],
                "message": "A friend has added you to their safety network for an upcoming meeting",
                "priority": "high",
                "created_at": datetime.utcnow(),
                "read": False
            }
            
            await db[Collections.NOTIFICATIONS].insert_one(notification)


# Singleton instance
_meeting_safety_service = None


def get_meeting_safety_service() -> MeetingSafetyService:
    """Get MeetingSafetyService singleton instance"""
    global _meeting_safety_service
    if _meeting_safety_service is None:
        _meeting_safety_service = MeetingSafetyService()
    return _meeting_safety_service
