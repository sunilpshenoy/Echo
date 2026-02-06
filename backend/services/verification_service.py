"""
Pulse Backend - Verification Service
AI-powered verification system for social media profiles and user authenticity

CONFIDENTIAL: Algorithm details not exposed to users
Users only see: verification status and trust scores
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class VerificationService:
    """
    Handles multi-factor verification of user authenticity
    
    Components:
    1. Social media ownership verification (codes)
    2. Account age analysis
    3. Profile activity analysis
    4. Live video challenge verification
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = db.users
        self.verification_codes = db.verification_codes
        self.video_verifications = db.video_verifications
    
    
    # ==================== SOCIAL MEDIA VERIFICATION ====================
    
    async def generate_verification_code(self, user_id: str, platform: str) -> str:
        """
        Generate unique verification code for social media ownership proof
        
        Args:
            user_id: User's ID
            platform: 'linkedin', 'instagram', or 'facebook'
            
        Returns:
            Unique verification code (e.g., "PULSE-A7K9M2")
        """
        # Generate random 6-character code
        code_suffix = str(uuid.uuid4())[:6].upper()
        code = f"PULSE-{code_suffix}"
        
        # Store in database with expiry
        await self.verification_codes.insert_one({
            "user_id": user_id,
            "platform": platform,
            "code": code,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "verified": False
        })
        
        logger.info(f"Generated verification code for user {user_id} - {platform}")
        
        return code
    
    
    async def verify_social_media_code(
        self, 
        user_id: str, 
        platform: str, 
        profile_url: str
    ) -> Dict:
        """
        Verify that user posted the code on their social media profile
        
        NOTE: In production, this would scrape the actual profile.
        For now, we'll simulate with a flag.
        
        Args:
            user_id: User's ID
            platform: Social media platform
            profile_url: URL of the profile to check
            
        Returns:
            Verification result with status and score impact
        """
        # Get the pending verification code
        verification = await self.verification_codes.find_one({
            "user_id": user_id,
            "platform": platform,
            "status": "pending",
            "expires_at": {"$gte": datetime.utcnow()}
        })
        
        if not verification:
            return {
                "success": False,
                "reason": "No pending verification found or code expired",
                "score_change": 0.0
            }
        
        code = verification["code"]
        
        # TODO: In production, implement actual scraping
        # For now, we simulate success if profile_url is provided
        code_found = await self._check_code_on_profile(profile_url, code, platform)
        
        if code_found:
            # Mark as verified
            await self.verification_codes.update_one(
                {"_id": verification["_id"]},
                {
                    "$set": {
                        "status": "verified",
                        "verified": True,
                        "verified_at": datetime.utcnow(),
                        "profile_url": profile_url
                    }
                }
            )
            
            # Update user's verification status
            score_bonus = self._get_platform_score_bonus(platform)
            
            await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        f"verified_platforms.{platform}": True,
                        f"verified_platforms.{platform}_url": profile_url,
                        f"verified_platforms.{platform}_verified_at": datetime.utcnow()
                    },
                    "$inc": {
                        "ai_verification_score": score_bonus
                    }
                }
            )
            
            logger.info(f"User {user_id} verified {platform} (+{score_bonus} points)")
            
            return {
                "success": True,
                "platform": platform,
                "score_change": score_bonus,
                "message": f"{platform.title()} verified successfully!"
            }
        else:
            return {
                "success": False,
                "reason": f"Verification code not found on {platform} profile",
                "score_change": 0.0
            }
    
    
    async def _check_code_on_profile(
        self, 
        profile_url: str, 
        code: str, 
        platform: str
    ) -> bool:
        """
        Check if verification code exists on social media profile
        
        PRODUCTION IMPLEMENTATION NEEDED:
        - LinkedIn: Use LinkedIn API or scraping
        - Instagram: Use Instagram Graph API
        - Facebook: Use Facebook Graph API
        
        For testing: Returns True if profile_url is provided
        """
        # TODO: Implement actual profile scraping
        # This is a placeholder that returns True for testing
        
        if not profile_url:
            return False
        
        # In production, would scrape profile and search for code
        # For now, simulate success
        logger.info(f"Simulated code check on {platform}: {profile_url}")
        return True
    
    
    def _get_platform_score_bonus(self, platform: str) -> float:
        """Get score bonus for verifying a platform"""
        bonuses = {
            "linkedin": 2.0,  # Most trustworthy
            "instagram": 1.0,
            "facebook": 1.0
        }
        return bonuses.get(platform, 0.5)
    
    
    # ==================== ACCOUNT AGE ANALYSIS ====================
    
    async def analyze_account_age(self, user_id: str) -> Dict:
        """
        Analyze social media account ages
        Newer accounts = lower trust (possible fakes)
        
        Returns:
            Score adjustment and flags
        """
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            return {"score": 0.0, "flags": ["User not found"]}
        
        verified_platforms = user.get("verified_platforms", {})
        
        score = 0.0
        flags = []
        
        # Check LinkedIn age
        if verified_platforms.get("linkedin"):
            linkedin_age = await self._get_account_age_days(
                verified_platforms.get("linkedin_url"),
                "linkedin"
            )
            
            if linkedin_age >= 365:  # 1+ year
                score += 1.0
                flags.append("✅ Established LinkedIn (1+ year)")
            elif linkedin_age >= 180:  # 6+ months
                score += 0.5
                flags.append("⚠️ LinkedIn account 6+ months old")
            else:
                score += 0.0
                flags.append("🚩 LinkedIn account less than 6 months old")
        
        # Check Instagram age
        if verified_platforms.get("instagram"):
            instagram_age = await self._get_account_age_days(
                verified_platforms.get("instagram_url"),
                "instagram"
            )
            
            if instagram_age >= 365:
                score += 0.5
                flags.append("✅ Active Instagram (1+ year)")
            elif instagram_age >= 90:
                score += 0.25
                flags.append("⚠️ Instagram account 3+ months old")
            else:
                score += 0.0
                flags.append("🚩 New Instagram account")
        
        # Check Facebook age
        if verified_platforms.get("facebook"):
            facebook_age = await self._get_account_age_days(
                verified_platforms.get("facebook_url"),
                "facebook"
            )
            
            if facebook_age >= 365:
                score += 0.5
                flags.append("✅ Established Facebook (1+ year)")
            elif facebook_age >= 180:
                score += 0.25
                flags.append("⚠️ Facebook account 6+ months old")
            else:
                score += 0.0
                flags.append("🚩 New Facebook account")
        
        # Update user's account age score
        await self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "account_age_score": round(score, 2),
                    "account_age_flags": flags,
                    "account_age_analyzed_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Account age analysis for {user_id}: {score}/2.0")
        
        return {
            "score": round(score, 2),
            "max_score": 2.0,
            "flags": flags
        }
    
    
    async def _get_account_age_days(self, profile_url: str, platform: str) -> int:
        """
        Get account creation age in days
        
        PRODUCTION: Use platform APIs
        TESTING: Simulate with random ages
        """
        # TODO: Implement actual API calls
        # For testing, return simulated ages
        
        import random
        
        # Simulate different account ages for testing
        age_ranges = {
            "old": random.randint(400, 2000),    # 1-5 years
            "medium": random.randint(100, 365),  # 3-12 months
            "new": random.randint(1, 90)         # 0-3 months
        }
        
        # For testing, 60% old, 30% medium, 10% new
        choice = random.choices(
            ["old", "medium", "new"], 
            weights=[0.6, 0.3, 0.1]
        )[0]
        
        return age_ranges[choice]
    
    
    # ==================== ACTIVITY ANALYSIS ====================
    
    async def analyze_profile_activity(self, user_id: str) -> Dict:
        """
        Analyze social media profile activity
        Real accounts are active; fake accounts are dormant
        
        Returns:
            Score adjustment and flags
        """
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            return {"score": 0.0, "flags": ["User not found"]}
        
        verified_platforms = user.get("verified_platforms", {})
        
        score = 0.0
        flags = []
        
        # Check LinkedIn activity
        if verified_platforms.get("linkedin"):
            linkedin_activity = await self._get_profile_activity(
                verified_platforms.get("linkedin_url"),
                "linkedin"
            )
            
            posts = linkedin_activity.get("posts_6mo", 0)
            connections = linkedin_activity.get("connections", 0)
            
            if posts >= 5 and connections >= 100:
                score += 1.0
                flags.append(f"✅ Active LinkedIn ({connections} connections)")
            elif posts >= 2 or connections >= 50:
                score += 0.5
                flags.append("⚠️ Some LinkedIn activity")
            else:
                score += 0.0
                flags.append("🚩 Inactive LinkedIn")
        
        # Check Instagram activity
        if verified_platforms.get("instagram"):
            instagram_activity = await self._get_profile_activity(
                verified_platforms.get("instagram_url"),
                "instagram"
            )
            
            posts = instagram_activity.get("posts_count", 0)
            followers = instagram_activity.get("followers", 0)
            
            if posts >= 20 and followers >= 100:
                score += 0.5
                flags.append(f"✅ Active Instagram ({followers} followers)")
            elif posts >= 5 or followers >= 50:
                score += 0.25
                flags.append("⚠️ Some Instagram activity")
            else:
                score += 0.0
                flags.append("🚩 Inactive Instagram")
        
        # Check Facebook activity
        if verified_platforms.get("facebook"):
            facebook_activity = await self._get_profile_activity(
                verified_platforms.get("facebook_url"),
                "facebook"
            )
            
            friends = facebook_activity.get("friends", 0)
            posts_year = facebook_activity.get("posts_year", 0)
            
            if friends >= 100 and posts_year >= 10:
                score += 0.5
                flags.append(f"✅ Active Facebook ({friends} friends)")
            elif friends >= 50 or posts_year >= 5:
                score += 0.25
                flags.append("⚠️ Some Facebook activity")
            else:
                score += 0.0
                flags.append("🚩 Inactive Facebook")
        
        # Update user's activity score
        await self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "activity_score": round(score, 2),
                    "activity_flags": flags,
                    "activity_analyzed_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Activity analysis for {user_id}: {score}/2.0")
        
        return {
            "score": round(score, 2),
            "max_score": 2.0,
            "flags": flags
        }
    
    
    async def _get_profile_activity(self, profile_url: str, platform: str) -> Dict:
        """
        Get profile activity metrics
        
        PRODUCTION: Use platform APIs
        TESTING: Simulate with random data
        """
        # TODO: Implement actual API calls
        # For testing, return simulated activity
        
        import random
        
        activity_profiles = {
            "active": {
                "posts_6mo": random.randint(10, 50),
                "posts_count": random.randint(50, 500),
                "posts_year": random.randint(20, 100),
                "connections": random.randint(150, 1000),
                "followers": random.randint(200, 2000),
                "friends": random.randint(150, 800)
            },
            "moderate": {
                "posts_6mo": random.randint(2, 9),
                "posts_count": random.randint(10, 49),
                "posts_year": random.randint(5, 19),
                "connections": random.randint(50, 149),
                "followers": random.randint(50, 199),
                "friends": random.randint(50, 149)
            },
            "inactive": {
                "posts_6mo": random.randint(0, 1),
                "posts_count": random.randint(0, 9),
                "posts_year": random.randint(0, 4),
                "connections": random.randint(0, 49),
                "followers": random.randint(0, 49),
                "friends": random.randint(0, 49)
            }
        }
        
        # For testing, 50% active, 30% moderate, 20% inactive
        choice = random.choices(
            ["active", "moderate", "inactive"],
            weights=[0.5, 0.3, 0.2]
        )[0]
        
        return activity_profiles[choice]
    
    
    # ==================== LIVE VIDEO VERIFICATION ====================
    
    async def generate_video_challenges(self, user_id: str) -> List[str]:
        """
        Generate random challenges for live video verification
        Prevents use of pre-recorded videos
        
        Returns:
            List of 4 random challenges
        """
        import random
        
        all_challenges = [
            # Basic actions
            "Say your first name",
            "Say today's date",
            "Smile at the camera",
            "Turn your head to the left",
            "Turn your head to the right",
            
            # Hand gestures
            "Hold up 1 finger",
            "Hold up 2 fingers",
            "Hold up 3 fingers",
            "Make a peace sign",
            "Give a thumbs up",
            "Touch your nose",
            "Wave at the camera",
            
            # Facial expressions
            "Blink twice",
            "Raise your eyebrows",
            "Open your mouth wide",
            
            # Movement
            "Nod your head yes",
            "Shake your head no",
            "Look up at the ceiling",
            "Look down at the floor"
        ]
        
        # Select 4 random challenges
        challenges = random.sample(all_challenges, 4)
        
        # Store challenges for verification
        await self.video_verifications.insert_one({
            "user_id": user_id,
            "challenges": challenges,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10),
            "status": "pending",
            "completed": False
        })
        
        logger.info(f"Generated video challenges for {user_id}")
        
        return challenges
    
    
    async def verify_video_submission(
        self, 
        user_id: str, 
        video_url: str
    ) -> Dict:
        """
        Verify live video submission
        
        PRODUCTION: Use AI/ML models for:
        - Face detection
        - Liveness detection
        - Challenge completion verification
        - Face matching with social media photos
        
        TESTING: Simulate verification result
        
        Returns:
            Verification result with score impact
        """
        # Get pending verification
        verification = await self.video_verifications.find_one({
            "user_id": user_id,
            "status": "pending",
            "expires_at": {"$gte": datetime.utcnow()}
        })
        
        if not verification:
            return {
                "success": False,
                "reason": "No pending verification or expired",
                "score_change": 0.0
            }
        
        # TODO: Implement actual AI/ML verification
        # For testing, simulate verification result
        
        verification_result = await self._simulate_video_verification(
            video_url, 
            verification["challenges"]
        )
        
        if verification_result["passed"]:
            # Mark as completed
            await self.video_verifications.update_one(
                {"_id": verification["_id"]},
                {
                    "$set": {
                        "status": "completed",
                        "completed": True,
                        "completed_at": datetime.utcnow(),
                        "video_url": video_url,
                        "liveness_score": verification_result["liveness_score"],
                        "challenges_completed": verification_result["challenges_completed"]
                    }
                }
            )
            
            # Update user's video verification status
            score_bonus = 2.0  # Video verification bonus
            
            await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "video_verified": True,
                        "video_verified_at": datetime.utcnow(),
                        "video_liveness_score": verification_result["liveness_score"]
                    },
                    "$inc": {
                        "ai_verification_score": score_bonus
                    }
                }
            )
            
            logger.info(f"User {user_id} passed video verification (+{score_bonus} points)")
            
            return {
                "success": True,
                "score_change": score_bonus,
                "liveness_score": verification_result["liveness_score"],
                "message": "Video verification successful!"
            }
        else:
            return {
                "success": False,
                "reason": verification_result["reason"],
                "flags": verification_result.get("flags", []),
                "score_change": 0.0
            }
    
    
    async def _simulate_video_verification(
        self, 
        video_url: str, 
        challenges: List[str]
    ) -> Dict:
        """
        Simulate video verification for testing
        
        PRODUCTION: Replace with actual AI/ML models
        """
        import random
        
        # For testing, 80% pass rate
        passed = random.random() < 0.8
        
        if passed:
            return {
                "passed": True,
                "liveness_score": round(random.uniform(0.75, 0.95), 2),
                "challenges_completed": challenges,
                "face_match_score": round(random.uniform(0.80, 0.95), 2)
            }
        else:
            # Simulate various failure reasons
            failure_reasons = [
                "Low liveness score - possible fake",
                "Not all challenges completed",
                "Face doesn't match social media photos",
                "Multiple faces detected",
                "No face detected"
            ]
            
            return {
                "passed": False,
                "reason": random.choice(failure_reasons),
                "flags": ["verification_failed"],
                "liveness_score": round(random.uniform(0.3, 0.69), 2)
            }
    
    
    # ==================== COMPREHENSIVE SCORE ====================
    
    async def calculate_comprehensive_ai_score(self, user_id: str) -> Dict:
        """
        Calculate final AI verification score from all components
        
        Components:
        1. Verification codes (max 4.0)
        2. Account age (max 2.0)
        3. Activity (max 2.0)
        4. Video verification (max 2.0)
        
        Total: 10.0 points
        
        CONFIDENTIAL: Users see final score, not breakdown calculation
        """
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            return {"score": 0.0, "breakdown": {}}
        
        total_score = 0.0
        breakdown = {}
        flags = []
        
        # 1. Verification codes
        verified_platforms = user.get("verified_platforms", {})
        verification_score = 0.0
        
        if verified_platforms.get("linkedin"):
            verification_score += 2.0
            breakdown["LinkedIn Verified"] = "+2.0"
        else:
            flags.append("LinkedIn not verified")
        
        if verified_platforms.get("instagram"):
            verification_score += 1.0
            breakdown["Instagram Verified"] = "+1.0"
        else:
            flags.append("Instagram not verified")
        
        if verified_platforms.get("facebook"):
            verification_score += 1.0
            breakdown["Facebook Verified"] = "+1.0"
        else:
            flags.append("Facebook not verified")
        
        total_score += verification_score
        
        # 2. Account age
        account_age_score = user.get("account_age_score", 0.0)
        account_age_flags = user.get("account_age_flags", [])
        
        total_score += account_age_score
        breakdown["Account Age"] = f"+{account_age_score}"
        flags.extend(account_age_flags)
        
        # 3. Activity
        activity_score = user.get("activity_score", 0.0)
        activity_flags = user.get("activity_flags", [])
        
        total_score += activity_score
        breakdown["Profile Activity"] = f"+{activity_score}"
        flags.extend(activity_flags)
        
        # 4. Video verification
        if user.get("video_verified"):
            video_score = 2.0
            total_score += video_score
            breakdown["Live Video Verified"] = "+2.0"
        else:
            breakdown["Live Video Verified"] = "+0.0 (not completed)"
            flags.append("Video verification pending")
        
        # Cap at 10.0
        final_score = min(total_score, 10.0)
        
        # Update user's final AI score
        await self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "ai_verification_score": round(final_score, 1),
                    "ai_score_breakdown": breakdown,
                    "ai_score_flags": flags,
                    "ai_score_updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Final AI score for {user_id}: {final_score}/10.0")
        
        return {
            "score": round(final_score, 1),
            "breakdown": breakdown,
            "flags": flags,
            "max_possible": 10.0
        }


def get_verification_service(db: AsyncIOMotorDatabase) -> VerificationService:
    """Dependency for getting VerificationService"""
    return VerificationService(db)
