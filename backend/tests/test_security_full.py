"""
Security Testing Suite - Malicious User Scenarios

Tests all 3 security problems with dummy scammer accounts:
1. AI Verification (stolen identities, fake profiles)
2. Network Analysis (fake rating networks, coordinated behavior)
3. Meeting Safety (one-time scammers, rapid escalation)

All tests are designed to FAIL the scammers and PASS legitimate users.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from bson import ObjectId
from database.connection import Collections, get_db
from services.verification_service import VerificationService
from services.network_analysis_service import NetworkAnalysisService
from services.meeting_safety_service import MeetingSafetyService


# ==================== PROBLEM A: AI VERIFICATION TESTS ====================

class TestAIVerification:
    """Test AI verification against stolen identities and fake profiles"""
    
    @pytest.mark.asyncio
    async def test_stolen_identity_blocked(self):
        """Test that stolen identity with matching profiles is detected"""
        service = VerificationService()
        
        # Scammer with stolen LinkedIn but can't post verification code
        result = await service.verify_linkedin_ownership(
            user_id="fake_scammer_1",
            linkedin_url="https://linkedin.com/in/stolen-profile",
            verification_code="PULSE-A7K9M2"
        )
        
        # Should FAIL - cannot post code
        assert result["verified"] == False
        assert "Cannot verify" in result["message"]
        
    @pytest.mark.asyncio
    async def test_new_account_age_penalty(self):
        """Test that newly created social accounts get penalized"""
        service = VerificationService()
        
        # Scammer with brand new accounts
        score, flags = await service.calculate_account_age_score(
            linkedin_url="https://linkedin.com/in/new-account-10days",
            instagram_url="https://instagram.com/new_account_30days",
            facebook_url=None  # No Facebook
        )
        
        # Should have LOW score and multiple flags
        assert score < 0.5  # Out of 2.0
        assert "linkedin_age_low" in flags
        assert "instagram_age_low" in flags
        
    @pytest.mark.asyncio
    async def test_inactive_profile_penalty(self):
        """Test that inactive profiles get penalized"""
        service = VerificationService()
        
        # Scammer with fake accounts (no real activity)
        score, flags = await service.calculate_activity_score(
            linkedin_url="https://linkedin.com/in/no-posts",
            instagram_url="https://instagram.com/no_posts",
            facebook_url="https://facebook.com/no.posts"
        )
        
        # Should have LOW score
        assert score < 0.5  # Out of 2.0
        assert len(flags) > 0
        
    @pytest.mark.asyncio
    async def test_live_video_deepfake_detection(self):
        """Test that pre-recorded/deepfake videos are detected"""
        service = VerificationService()
        
        # Scammer uploads pre-recorded video
        result = await service.analyze_live_video(
            video_file="/fake/path/prerecorded.mp4",
            challenges_given=["say_your_name", "show_3_fingers", "turn_left", "smile"]
        )
        
        # Should FAIL liveness check
        assert result["liveness_passed"] == False
        assert "deepfake" in result["flags"] or "prerecorded" in result["flags"]
    
    @pytest.mark.asyncio
    async def test_legitimate_user_passes_all_checks(self):
        """Test that legitimate user with real profiles PASSES"""
        service = VerificationService()
        
        # Real user with established accounts
        age_score, age_flags = await service.calculate_account_age_score(
            linkedin_url="https://linkedin.com/in/real-user-3years",
            instagram_url="https://instagram.com/real_user_2years",
            facebook_url="https://facebook.com/real.user.5years"
        )
        
        activity_score, activity_flags = await service.calculate_activity_score(
            linkedin_url="https://linkedin.com/in/real-user-active",
            instagram_url="https://instagram.com/real_user_active",
            facebook_url="https://facebook.com/real.user.active"
        )
        
        # Should have HIGH scores
        assert age_score >= 1.5  # Out of 2.0
        assert activity_score >= 1.5  # Out of 2.0
        assert len(age_flags) == 0
        assert len(activity_flags) == 0


# ==================== PROBLEM B: NETWORK ANALYSIS TESTS ====================

class TestNetworkAnalysis:
    """Test network analysis against fake rating networks"""
    
    @pytest.mark.asyncio
    async def test_circular_rating_pattern_detected(self):
        """Test that circular rating networks are detected"""
        service = NetworkAnalysisService()
        db = await get_db()
        
        # Create 10 fake accounts that all rate each other
        fake_ids = [ObjectId() for _ in range(10)]
        
        # Create circular connections
        for i, user_id in enumerate(fake_ids):
            # Each user connects to next 3 users in circle
            connections = [
                fake_ids[(i + 1) % 10],
                fake_ids[(i + 2) % 10],
                fake_ids[(i + 3) % 10]
            ]
            
            for conn_id in connections:
                await db[Collections.CONNECTIONS].insert_one({
                    "sender_id": user_id,
                    "receiver_id": conn_id,
                    "status": "accepted",
                    "created_at": datetime.utcnow()
                })
        
        # Test detection on first fake account
        result = await service.detect_circular_rating_patterns(str(fake_ids[0]))
        
        # Should be FLAGGED
        assert result["suspicious"] == True
        assert result["penalty"] == -2.0
        
    @pytest.mark.asyncio
    async def test_account_creation_cluster_detected(self):
        """Test that accounts created together are detected"""
        service = NetworkAnalysisService()
        db = await get_db()
        
        # Scammer creates 5 accounts on same day
        base_time = datetime.utcnow() - timedelta(days=5)
        fake_ids = []
        
        for i in range(5):
            user_id = ObjectId()
            fake_ids.append(user_id)
            
            await db[Collections.USERS].insert_one({
                "_id": user_id,
                "username": f"fake_user_{i}",
                "created_at": base_time + timedelta(hours=i)  # Within 5 hours
            })
        
        # All connect to each other
        for i, user_id in enumerate(fake_ids):
            for j, conn_id in enumerate(fake_ids):
                if i != j:
                    await db[Collections.CONNECTIONS].insert_one({
                        "sender_id": user_id,
                        "receiver_id": conn_id,
                        "status": "accepted",
                        "created_at": base_time + timedelta(days=1)
                    })
        
        # Test detection
        result = await service.detect_account_creation_clusters(str(fake_ids[0]))
        
        # Should be FLAGGED
        assert result["suspicious"] == True
        assert result["penalty"] == -1.5
    
    @pytest.mark.asyncio
    async def test_same_device_detection(self):
        """Test that multiple accounts from same device are detected"""
        service = NetworkAnalysisService()
        db = await get_db()
        
        # Scammer creates 3 accounts from same phone
        device_fingerprint = "iPhone13-iOS16-Safari-192.168.1.100"
        fake_ids = []
        
        for i in range(3):
            user_id = ObjectId()
            fake_ids.append(user_id)
            
            await db[Collections.USERS].insert_one({
                "_id": user_id,
                "username": f"fake_user_{i}",
                "device_fingerprint": device_fingerprint,
                "created_at": datetime.utcnow()
            })
        
        # Test detection
        result = await service.detect_same_device_usage(str(fake_ids[0]))
        
        # Should be FLAGGED with HIGH penalty
        assert result["suspicious"] == True
        assert result["penalty"] == -3.0
    
    @pytest.mark.asyncio
    async def test_rating_velocity_detection(self):
        """Test that rapid rating accumulation is detected"""
        service = NetworkAnalysisService()
        db = await get_db()
        
        # Scammer gets 10 ratings in 3 days
        user_id = ObjectId()
        await db[Collections.USERS].insert_one({
            "_id": user_id,
            "username": "rapid_rater",
            "created_at": datetime.utcnow() - timedelta(days=3)
        })
        
        # Create 10 connections in last 3 days
        for i in range(10):
            conn_id = ObjectId()
            await db[Collections.CONNECTIONS].insert_one({
                "sender_id": user_id,
                "receiver_id": conn_id,
                "status": "accepted",
                "created_at": datetime.utcnow() - timedelta(days=3 - i*0.3),
                "rating": 5.0
            })
        
        # Test detection
        result = await service.detect_rating_velocity_manipulation(str(user_id))
        
        # Should be FLAGGED
        assert result["suspicious"] == True
        assert result["penalty"] < 0
    
    @pytest.mark.asyncio
    async def test_isolated_network_detection(self):
        """Test that isolated fake networks are detected"""
        service = NetworkAnalysisService()
        db = await get_db()
        
        # Create 5 fake accounts that only connect to each other
        fake_ids = [ObjectId() for _ in range(5)]
        
        for user_id in fake_ids:
            await db[Collections.USERS].insert_one({
                "_id": user_id,
                "username": f"isolated_{user_id}",
                "created_at": datetime.utcnow()
            })
        
        # All connect only to each other (no external connections)
        for i, user_id in enumerate(fake_ids):
            for j, conn_id in enumerate(fake_ids):
                if i != j:
                    await db[Collections.CONNECTIONS].insert_one({
                        "sender_id": user_id,
                        "receiver_id": conn_id,
                        "status": "accepted",
                        "created_at": datetime.utcnow()
                    })
        
        # Test detection
        result = await service.detect_isolated_network(str(fake_ids[0]))
        
        # Should be FLAGGED
        assert result["suspicious"] == True
        assert result["penalty"] == -1.5


# ==================== PROBLEM C: MEETING SAFETY TESTS ====================

class TestMeetingSafety:
    """Test meeting safety protocols against one-time scammers"""
    
    @pytest.mark.asyncio
    async def test_rapid_progression_blocked(self):
        """Test that rapid Level 1 -> Level 4 is blocked"""
        service = MeetingSafetyService()
        db = await get_db()
        
        # Scammer tries to progress quickly
        scammer_id = ObjectId()
        victim_id = ObjectId()
        
        # Scammer created account today
        await db[Collections.USERS].insert_one({
            "_id": scammer_id,
            "username": "fast_scammer",
            "created_at": datetime.utcnow() - timedelta(hours=2)
        })
        
        await db[Collections.USERS].insert_one({
            "_id": victim_id,
            "username": "victim",
            "created_at": datetime.utcnow() - timedelta(days=60)
        })
        
        # Connected 2 hours ago
        await db[Collections.CONNECTIONS].insert_one({
            "sender_id": scammer_id,
            "receiver_id": victim_id,
            "status": "accepted",
            "created_at": datetime.utcnow() - timedelta(hours=2)
        })
        
        # Try to progress to Level 2 (voice)
        result = await service.check_level_progression(
            user_id=str(scammer_id),
            target_user_id=str(victim_id),
            current_level=1,
            target_level=2
        )
        
        # Should be BLOCKED
        assert result["allowed"] == False
        assert result["waiting_required"] == True
        assert result["wait_duration_hours"] > 0
    
    @pytest.mark.asyncio
    async def test_meeting_without_video_calls_blocked(self):
        """Test that meeting without required video calls is blocked"""
        service = MeetingSafetyService()
        db = await get_db()
        
        # Scammer meets account age requirement but has no video calls
        scammer_id = ObjectId()
        victim_id = ObjectId()
        
        await db[Collections.USERS].insert_one({
            "_id": scammer_id,
            "username": "no_video_scammer",
            "created_at": datetime.utcnow() - timedelta(days=35)  # Meets age requirement
        })
        
        await db[Collections.CONNECTIONS].insert_one({
            "sender_id": scammer_id,
            "receiver_id": victim_id,
            "status": "accepted",
            "created_at": datetime.utcnow() - timedelta(days=20)  # Meets connection age
        })
        
        # Try to progress to Level 4 (meeting) without video calls
        result = await service.check_level_progression(
            user_id=str(scammer_id),
            target_user_id=str(victim_id),
            current_level=3,
            target_level=4
        )
        
        # Should be BLOCKED
        assert result["allowed"] == False
        assert "video call" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_pre_meeting_verification_mismatch(self):
        """Test that mismatched pre-meeting details are caught"""
        service = MeetingSafetyService()
        
        # Create verification
        verification = await service.create_pre_meeting_verification(
            user_a_id="scammer_123",
            user_b_id="victim_456",
            meeting_details={
                "location": "Coffee Shop Downtown",
                "time": datetime.utcnow() + timedelta(days=1)
            }
        )
        
        # Scammer gives different location
        result_a = await service.submit_verification_answers(
            verification_id=verification["verification_id"],
            user_id="scammer_123",
            answers={
                "location": "Different Mall Location",  # MISMATCH
                "time": datetime.utcnow() + timedelta(days=1),
                "description": "Meeting for coffee"
            }
        )
        
        # Victim gives correct location
        result_b = await service.submit_verification_answers(
            verification_id=verification["verification_id"],
            user_id="victim_456",
            answers={
                "location": "Coffee Shop Downtown",
                "time": datetime.utcnow() + timedelta(days=1),
                "description": "Coffee meetup"
            }
        )
        
        # Should FAIL verification
        assert result_b["success"] == False
        assert result_b["status"] == "failed"
    
    @pytest.mark.asyncio
    async def test_trust_deposit_penalty_applied(self):
        """Test that trust deposit penalties are applied for misconduct"""
        service = MeetingSafetyService()
        db = await get_db()
        
        # Set up meeting with trust deposit
        scammer_id = ObjectId()
        victim_id = ObjectId()
        meeting_id = ObjectId()
        
        await db[Collections.USERS].insert_one({
            "_id": scammer_id,
            "username": "scammer",
            "authenticity_rating": 7.5,
            "created_at": datetime.utcnow()
        })
        
        await db[Collections.MEETINGS].insert_one({
            "_id": meeting_id,
            "user_a_id": scammer_id,
            "user_b_id": victim_id,
            "status": "completed",
            "created_at": datetime.utcnow()
        })
        
        # Create deposit
        deposit = await service.create_trust_deposit(
            user_a_id=str(scammer_id),
            user_b_id=str(victim_id),
            meeting_id=str(meeting_id)
        )
        
        # Victim reports severe misconduct
        result = await service.handle_post_meeting_report(
            meeting_id=str(meeting_id),
            reporter_id=str(victim_id),
            reported_user_id=str(scammer_id),
            report_type="severe",  # Harassment/threats
            details="Threatened and made me feel unsafe"
        )
        
        # Should apply PENALTY
        assert result["success"] == True
        assert result["action_taken"] == "penalty_applied"
        
        # Check scammer's rating decreased
        scammer = await db[Collections.USERS].find_one({"_id": scammer_id})
        assert scammer["authenticity_rating"] < 7.5  # Decreased
    
    @pytest.mark.asyncio
    async def test_assault_results_in_ban(self):
        """Test that assault report results in immediate ban"""
        service = MeetingSafetyService()
        db = await get_db()
        
        # Set up scenario
        assaulter_id = ObjectId()
        victim_id = ObjectId()
        meeting_id = ObjectId()
        
        await db[Collections.USERS].insert_one({
            "_id": assaulter_id,
            "username": "assaulter",
            "authenticity_rating": 8.0,
            "account_status": "active",
            "created_at": datetime.utcnow()
        })
        
        await db[Collections.MEETINGS].insert_one({
            "_id": meeting_id,
            "user_a_id": assaulter_id,
            "user_b_id": victim_id,
            "status": "completed",
            "created_at": datetime.utcnow()
        })
        
        # Create deposit
        await service.create_trust_deposit(
            user_a_id=str(assaulter_id),
            user_b_id=str(victim_id),
            meeting_id=str(meeting_id)
        )
        
        # Report assault
        result = await service.handle_post_meeting_report(
            meeting_id=str(meeting_id),
            reporter_id=str(victim_id),
            reported_user_id=str(assaulter_id),
            report_type="assault",
            details="Physical assault occurred"
        )
        
        # Should BAN immediately
        assert result["action_taken"] == "user_banned"
        
        # Check user is banned
        assaulter = await db[Collections.USERS].find_one({"_id": assaulter_id})
        assert assaulter["account_status"] == "banned"
    
    @pytest.mark.asyncio
    async def test_first_meeting_protocol_enforced(self):
        """Test that first meeting requires all safety protocols"""
        service = MeetingSafetyService()
        db = await get_db()
        
        # Users who have never met
        user_a_id = ObjectId()
        user_b_id = ObjectId()
        
        await db[Collections.USERS].insert_one({
            "_id": user_a_id,
            "username": "user_a",
            "created_at": datetime.utcnow() - timedelta(days=40),
            "emergency_contacts": []  # NO emergency contact configured
        })
        
        # Check requirements
        result = await service.validate_first_meeting_requirements(
            user_a_id=str(user_a_id),
            user_b_id=str(user_b_id),
            meeting_details={
                "location": "Private Home",  # NOT public place
                "time": datetime.strptime("22:00", "%H:%M"),  # Night time
                "location_sharing": False  # Location sharing OFF
            }
        )
        
        # Should FAIL multiple requirements
        assert result["allowed"] == False
        assert result["is_first_meeting"] == True
        assert "emergency_contact_configured" in result["missing_requirements"]
        assert "public_place_confirmed" in result["missing_requirements"]
        assert "daylight_meeting" in result["missing_requirements"]
        assert "location_sharing_enabled" in result["missing_requirements"]


# ==================== INTEGRATION TESTS ====================

class TestFullSecurityStack:
    """Test all 3 systems working together"""
    
    @pytest.mark.asyncio
    async def test_complete_scammer_lifecycle_blocked(self):
        """
        Test complete scammer attempt from signup to meeting:
        1. Fake profile with stolen identity -> LOW AI score
        2. Fake rating network -> Network flags
        3. Rapid progression attempt -> Meeting blocks
        
        Expected: BLOCKED at every stage
        """
        # Phase 1: AI Verification
        verification_service = VerificationService()
        
        ai_score = await verification_service.calculate_final_ai_score(
            user_id="complete_scammer"
        )
        
        # Should have LOW AI score
        assert ai_score["total_score"] < 5.0  # Out of 10
        assert len(ai_score["warnings"]) > 0
        
        # Phase 2: Network Analysis
        network_service = NetworkAnalysisService()
        
        network_score = await network_service.calculate_network_trust_score(
            user_id="complete_scammer"
        )
        
        # Should have NEGATIVE penalties
        assert network_score["total_penalty"] < 0
        assert network_score["trust_level"] == "Suspicious"
        
        # Phase 3: Meeting Safety
        meeting_service = MeetingSafetyService()
        
        meeting_check = await meeting_service.check_level_progression(
            user_id="complete_scammer",
            target_user_id="victim",
            current_level=1,
            target_level=4
        )
        
        # Should be BLOCKED
        assert meeting_check["allowed"] == False
    
    @pytest.mark.asyncio
    async def test_legitimate_user_full_journey_succeeds(self):
        """
        Test legitimate user can complete full journey:
        1. Real verified profile -> HIGH AI score
        2. Organic network -> No flags
        3. Proper progression -> Meeting allowed
        
        Expected: SUCCESS at every stage
        """
        # Create legitimate user
        db = await get_db()
        legit_user_id = ObjectId()
        
        await db[Collections.USERS].insert_one({
            "_id": legit_user_id,
            "username": "legitimate_user",
            "email": "real@user.com",
            "created_at": datetime.utcnow() - timedelta(days=90),  # 3 months old
            "linkedin_verified": True,
            "instagram_verified": True,
            "live_video_verified": True,
            "authenticity_rating": 8.5,
            "emergency_contacts": ["friend_1", "friend_2"]
        })
        
        # Phase 1: AI Verification
        verification_service = VerificationService()
        ai_score = await verification_service.calculate_final_ai_score(
            user_id=str(legit_user_id)
        )
        
        # Should have HIGH score
        assert ai_score["total_score"] >= 7.0
        
        # Phase 2: Network Analysis
        network_service = NetworkAnalysisService()
        network_score = await network_service.calculate_network_trust_score(
            user_id=str(legit_user_id)
        )
        
        # Should have NO penalties
        assert network_score["total_penalty"] == 0
        assert network_score["trust_level"] == "High"
        
        # Phase 3: Meeting Safety (after proper progression)
        meeting_service = MeetingSafetyService()
        
        # Simulate proper progression with another legitimate user
        other_user_id = ObjectId()
        
        await db[Collections.USERS].insert_one({
            "_id": other_user_id,
            "username": "other_legit_user",
            "created_at": datetime.utcnow() - timedelta(days=100)
        })
        
        # Connection exists for 30+ days
        await db[Collections.CONNECTIONS].insert_one({
            "sender_id": legit_user_id,
            "receiver_id": other_user_id,
            "status": "accepted",
            "created_at": datetime.utcnow() - timedelta(days=40)
        })
        
        # 3+ video calls completed
        for i in range(3):
            await db[Collections.CALLS].insert_one({
                "caller_id": legit_user_id,
                "receiver_id": other_user_id,
                "call_type": "video",
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(days=35 - i*5)
            })
        
        # Check meeting progression
        meeting_check = await meeting_service.check_level_progression(
            user_id=str(legit_user_id),
            target_user_id=str(other_user_id),
            current_level=3,
            target_level=4
        )
        
        # Should be ALLOWED
        assert meeting_check["allowed"] == True
        assert meeting_check["waiting_required"] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
