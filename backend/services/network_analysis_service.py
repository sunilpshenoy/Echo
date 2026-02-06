"""
Pulse Backend - Network Analysis Service
Detects fake rating networks and coordinated fraud attempts

CONFIDENTIAL: Detection algorithms not exposed to users
Users only see: adjusted ratings and risk warnings
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class NetworkAnalysisService:
    """
    Analyzes user networks to detect suspicious patterns:
    1. Circular rating patterns (users only rate each other)
    2. Account creation clusters (created same time, rate each other)
    3. Shared devices (multiple accounts from same device)
    4. Isolated networks (no external connections)
    5. Rating velocity (too many ratings too quickly)
    
    CONFIDENTIAL: Detection logic is proprietary
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users = db.users
        self.connections = db.connections
        self.ratings = db.ratings
        self.device_logs = db.device_logs
    
    
    # ==================== CIRCULAR RATING DETECTION ====================
    
    async def detect_circular_ratings(self, user_id: str) -> Dict:
        """
        Detect if user is part of circular rating pattern
        
        Suspicious: User A rates B, B rates A, A rates C, C rates A...
        Real networks: Ratings flow in many directions
        
        Returns:
            Detection result with penalty if suspicious
        """
        # Get all users who rated this user
        raters = await self._get_users_who_rated(user_id)
        
        # Get all users this user rated
        rated_by_user = await self._get_users_rated_by(user_id)
        
        if len(raters) == 0:
            return {"suspicious": False, "reason": "No ratings yet"}
        
        # Check for circular patterns (mutual ratings)
        circle_count = 0
        circular_pairs = []
        
        for rater in raters:
            if rater in rated_by_user:
                # User A rated B, and B rated A back (circular)
                circle_count += 1
                circular_pairs.append(rater)
        
        # Calculate circle ratio
        circle_ratio = circle_count / len(raters)
        
        # Suspicious if more than 70% are circular and have 5+ raters
        if circle_ratio > 0.7 and len(raters) >= 5:
            penalty = -2.0
            
            logger.warning(
                f"Circular rating pattern detected for {user_id}: "
                f"{circle_count}/{len(raters)} circular ({circle_ratio:.0%})"
            )
            
            return {
                "suspicious": True,
                "flag": "High circular rating pattern",
                "circle_ratio": round(circle_ratio, 2),
                "penalty": penalty,
                "details": f"{circle_count} of {len(raters)} ratings are circular"
            }
        
        return {"suspicious": False}
    
    
    async def _get_users_who_rated(self, user_id: str) -> List[str]:
        """Get list of user IDs who rated this user"""
        ratings = await self.ratings.find({
            "rated_user_id": user_id
        }).to_list(length=None)
        
        return [r["rater_user_id"] for r in ratings]
    
    
    async def _get_users_rated_by(self, user_id: str) -> List[str]:
        """Get list of user IDs this user rated"""
        ratings = await self.ratings.find({
            "rater_user_id": user_id
        }).to_list(length=None)
        
        return [r["rated_user_id"] for r in ratings]
    
    
    # ==================== ACCOUNT CLUSTER DETECTION ====================
    
    async def detect_account_clusters(self, user_id: str) -> Dict:
        """
        Detect if user's connections were all created around same time
        
        Suspicious: 10 accounts created same week, all connect with each other
        Real: Friends join at different times
        
        Returns:
            Detection result with penalty if suspicious
        """
        # Get user's creation date
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            return {"suspicious": False, "reason": "User not found"}
        
        user_created = user.get("created_at")
        if not user_created:
            return {"suspicious": False, "reason": "No creation date"}
        
        # Get all connections
        connections = await self._get_user_connections(user_id)
        
        if len(connections) < 5:
            return {"suspicious": False, "reason": "Too few connections"}
        
        # Check how many were created within 7 days
        same_week_count = 0
        same_week_users = []
        
        for conn_id in connections:
            conn = await self.users.find_one({"user_id": conn_id})
            if not conn:
                continue
            
            conn_created = conn.get("created_at")
            if not conn_created:
                continue
            
            days_diff = abs((user_created - conn_created).days)
            
            if days_diff <= 7:
                same_week_count += 1
                same_week_users.append(conn_id)
        
        # Calculate cluster ratio
        cluster_ratio = same_week_count / len(connections)
        
        # Suspicious if more than 60% created same week
        if cluster_ratio > 0.6 and len(connections) >= 5:
            penalty = -1.5
            
            logger.warning(
                f"Account cluster detected for {user_id}: "
                f"{same_week_count}/{len(connections)} created same week ({cluster_ratio:.0%})"
            )
            
            return {
                "suspicious": True,
                "flag": "Account creation cluster detected",
                "cluster_ratio": round(cluster_ratio, 2),
                "penalty": penalty,
                "details": f"{same_week_count} connections created within 7 days"
            }
        
        return {"suspicious": False}
    
    
    async def _get_user_connections(self, user_id: str) -> List[str]:
        """Get list of user's connection IDs"""
        connections = await self.connections.find({
            "$or": [
                {"user1_id": user_id, "status": "connected"},
                {"user2_id": user_id, "status": "connected"}
            ]
        }).to_list(length=None)
        
        conn_ids = []
        for conn in connections:
            if conn["user1_id"] == user_id:
                conn_ids.append(conn["user2_id"])
            else:
                conn_ids.append(conn["user1_id"])
        
        return conn_ids
    
    
    # ==================== SHARED DEVICE DETECTION ====================
    
    async def detect_shared_devices(self, user_id: str) -> Dict:
        """
        Detect if user shares device/IP with their connections
        
        Families may share WiFi (IP), but NOT device fingerprint
        Multiple accounts from same device = coordinated fake accounts
        
        Returns:
            Detection result with heavy penalty if detected
        """
        # Get user's device fingerprints
        user_devices = await self._get_user_device_fingerprints(user_id)
        
        if len(user_devices) == 0:
            return {"suspicious": False, "reason": "No device data"}
        
        # Get connections
        connections = await self._get_user_connections(user_id)
        
        if len(connections) == 0:
            return {"suspicious": False, "reason": "No connections"}
        
        # Check for device overlap
        shared_device_count = 0
        shared_with_users = []
        
        for conn_id in connections:
            conn_devices = await self._get_user_device_fingerprints(conn_id)
            
            # Check if any device fingerprints match
            overlap = set(user_devices) & set(conn_devices)
            
            if len(overlap) > 0:
                shared_device_count += 1
                shared_with_users.append(conn_id)
        
        # More than 2 connections on same device = VERY suspicious
        if shared_device_count >= 2:
            penalty = -3.0  # Heavy penalty
            
            logger.error(
                f"CRITICAL: Shared device detected for {user_id}: "
                f"Shares device with {shared_device_count} connections"
            )
            
            return {
                "suspicious": True,
                "flag": f"Shares device with {shared_device_count} connections",
                "penalty": penalty,
                "severity": "critical",
                "details": "Multiple accounts from same device",
                "action_required": True  # May warrant immediate review
            }
        
        return {"suspicious": False}
    
    
    async def _get_user_device_fingerprints(self, user_id: str) -> List[str]:
        """
        Get unique device fingerprints for user
        
        Device fingerprint includes:
        - Browser version
        - Screen resolution
        - Timezone
        - Installed plugins
        - Canvas fingerprint
        etc.
        """
        # Get recent device logs (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        logs = await self.device_logs.find({
            "user_id": user_id,
            "timestamp": {"$gte": thirty_days_ago}
        }).to_list(length=None)
        
        # Extract unique device fingerprints
        fingerprints = list(set([log.get("device_fingerprint") for log in logs if log.get("device_fingerprint")]))
        
        return fingerprints
    
    
    # ==================== ISOLATED NETWORK DETECTION ====================
    
    async def detect_isolated_networks(self, user_id: str) -> Dict:
        """
        Detect if user is part of isolated group
        
        Suspicious: Group of 10 users who only connect with each other
        Real: Networks expand exponentially (friends of friends)
        
        Uses graph analysis to detect islands
        
        Returns:
            Detection result with penalty if isolated
        """
        # Get immediate connections (1st degree)
        immediate_connections = await self._get_user_connections(user_id)
        
        if len(immediate_connections) < 5:
            return {"suspicious": False, "reason": "Too few connections"}
        
        # Get extended network (2nd degree - friends of friends)
        extended_network = set()
        
        for conn_id in immediate_connections:
            conn_friends = await self._get_user_connections(conn_id)
            extended_network.update(conn_friends)
        
        # Remove self and immediate connections from extended network
        extended_network.discard(user_id)
        extended_network = extended_network - set(immediate_connections)
        
        # Calculate network expansion
        immediate_count = len(immediate_connections)
        extended_count = len(extended_network)
        
        # Real networks expand (10 friends should have 50-100 other friends combined)
        expected_extended = immediate_count * 5
        
        if extended_count < expected_extended:
            isolation_score = extended_count / expected_extended if expected_extended > 0 else 0
            
            # If less than 30% of expected expansion, it's isolated
            if isolation_score < 0.3:
                penalty = -1.5
                
                logger.warning(
                    f"Isolated network detected for {user_id}: "
                    f"{extended_count} extended connections (expected {expected_extended})"
                )
                
                return {
                    "suspicious": True,
                    "flag": "Isolated network - no external connections",
                    "isolation_score": round(isolation_score, 2),
                    "penalty": penalty,
                    "details": f"Network doesn't expand naturally"
                }
        
        return {"suspicious": False}
    
    
    # ==================== RATING VELOCITY DETECTION ====================
    
    async def detect_rating_velocity(self, user_id: str) -> Dict:
        """
        Detect if user is getting ratings too quickly
        
        Suspicious: 10 ratings in first week
        Real: Trust builds slowly over time
        
        Returns:
            Detection result with penalty if too fast
        """
        # Get user's account age
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            return {"suspicious": False, "reason": "User not found"}
        
        created_at = user.get("created_at")
        if not created_at:
            return {"suspicious": False, "reason": "No creation date"}
        
        account_age_days = (datetime.utcnow() - created_at).days
        
        # Get rating count
        ratings = await self.ratings.count_documents({
            "rated_user_id": user_id
        })
        
        if ratings == 0:
            return {"suspicious": False, "reason": "No ratings yet"}
        
        # Calculate velocity (ratings per day)
        velocity = ratings / max(account_age_days, 1)
        
        # Check suspicious thresholds
        if account_age_days <= 7 and velocity > 2:
            # More than 2 ratings per day in first week
            penalty = -2.0
            
            logger.warning(
                f"High rating velocity detected for {user_id}: "
                f"{velocity:.1f} ratings/day in first week"
            )
            
            return {
                "suspicious": True,
                "flag": "Too many ratings too quickly (first week)",
                "velocity": round(velocity, 2),
                "penalty": penalty,
                "details": f"{ratings} ratings in {account_age_days} days"
            }
        
        if account_age_days <= 30 and velocity > 1:
            # More than 1 rating per day in first month
            penalty = -1.0
            
            logger.warning(
                f"High rating velocity detected for {user_id}: "
                f"{velocity:.1f} ratings/day in first month"
            )
            
            return {
                "suspicious": True,
                "flag": "High rating velocity (first month)",
                "velocity": round(velocity, 2),
                "penalty": penalty,
                "details": f"{ratings} ratings in {account_age_days} days"
            }
        
        return {"suspicious": False}
    
    
    # ==================== COMPREHENSIVE NETWORK ANALYSIS ====================
    
    async def calculate_network_trust_score(self, user_id: str) -> Dict:
        """
        Run all detection methods and calculate adjusted trust score
        
        Combines:
        1. Circular ratings
        2. Account clusters
        3. Shared devices
        4. Isolated networks
        5. Rating velocity
        
        CONFIDENTIAL: Users see adjusted score, not detection details
        
        Returns:
            Adjusted rating with risk level
        """
        # Get base user rating (from connections)
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            return {"score": 0.0, "risk_level": "unknown"}
        
        base_rating = user.get("user_rating", 0.0)  # 0-5 scale from connections
        
        total_penalty = 0.0
        flags = []
        critical_flags = []
        
        # Run all detection methods
        
        # 1. Circular ratings
        circular = await self.detect_circular_ratings(user_id)
        if circular.get("suspicious"):
            total_penalty += circular["penalty"]
            flags.append(circular["flag"])
        
        # 2. Account clusters
        cluster = await self.detect_account_clusters(user_id)
        if cluster.get("suspicious"):
            total_penalty += cluster["penalty"]
            flags.append(cluster["flag"])
        
        # 3. Shared devices (CRITICAL)
        devices = await self.detect_shared_devices(user_id)
        if devices.get("suspicious"):
            total_penalty += devices["penalty"]
            flags.append(devices["flag"])
            if devices.get("severity") == "critical":
                critical_flags.append(devices["flag"])
        
        # 4. Isolated network
        isolated = await self.detect_isolated_networks(user_id)
        if isolated.get("suspicious"):
            total_penalty += isolated["penalty"]
            flags.append(isolated["flag"])
        
        # 5. Rating velocity
        velocity = await self.detect_rating_velocity(user_id)
        if velocity.get("suspicious"):
            total_penalty += velocity["penalty"]
            flags.append(velocity["flag"])
        
        # Convert base rating from 5-star to 10-point scale
        base_rating_10 = base_rating * 2
        
        # Apply penalties
        adjusted_rating = base_rating_10 + total_penalty
        adjusted_rating = max(0, min(10, adjusted_rating))  # Cap 0-10
        
        # Determine risk level
        risk_level = "low"
        if len(flags) >= 3 or len(critical_flags) > 0:
            risk_level = "high"
        elif len(flags) >= 1:
            risk_level = "medium"
        
        # Determine action needed
        action_required = risk_level == "high" or len(critical_flags) > 0
        
        # Update user's network analysis results
        await self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "network_trust_score": round(adjusted_rating, 1),
                    "network_risk_level": risk_level,
                    "network_flags": flags,
                    "network_penalty_applied": round(total_penalty, 1),
                    "network_analyzed_at": datetime.utcnow(),
                    "action_required": action_required
                }
            }
        )
        
        logger.info(
            f"Network analysis for {user_id}: "
            f"{base_rating_10:.1f} -> {adjusted_rating:.1f} "
            f"(penalty: {total_penalty:.1f}, risk: {risk_level})"
        )
        
        # Log critical issues
        if action_required:
            logger.error(
                f"ACTION REQUIRED for {user_id}: "
                f"Critical flags: {critical_flags}, All flags: {flags}"
            )
        
        return {
            "original_rating": round(base_rating, 1),
            "original_rating_10": round(base_rating_10, 1),
            "adjusted_rating": round(adjusted_rating, 1),
            "penalty_applied": round(total_penalty, 1),
            "flags": flags,
            "critical_flags": critical_flags,
            "risk_level": risk_level,
            "action_required": action_required,
            "trust_status": "High" if len(flags) == 0 else "Suspicious"
        }


def get_network_analysis_service(db: AsyncIOMotorDatabase) -> NetworkAnalysisService:
    """Dependency for getting NetworkAnalysisService"""
    return NetworkAnalysisService(db)
