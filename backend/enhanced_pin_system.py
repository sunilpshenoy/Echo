# Enhanced PIN Connection System
# This file contains the enhanced PIN system logic to be integrated into server.py

import uuid
import qrcode
import random
import string
from datetime import datetime, timedelta
from io import BytesIO
import base64

class EnhancedPINSystem:
    """Enhanced PIN system for secure and user-friendly connections"""
    
    @staticmethod
    def generate_smart_pin(user_data: dict) -> str:
        """Generate a smart PIN based on user data for easier memorization"""
        # Get first 3 letters of display name or username
        name = user_data.get("display_name") or user_data.get("username", "USER")
        name_part = ''.join(c.upper() for c in name if c.isalpha())[:3]
        
        # Fill with random letters if needed
        while len(name_part) < 3:
            name_part += random.choice(string.ascii_uppercase)
        
        # Add 3 random numbers
        number_part = ''.join(random.choices(string.digits, k=3))
        
        return f"PIN-{name_part}{number_part}"
    
    @staticmethod
    def generate_enhanced_qr_code(pin: str, user_data: dict) -> str:
        """Generate enhanced QR code with connection metadata"""
        qr_data = {
            "type": "authentic_connection",
            "pin": pin,
            "display_name": user_data.get("display_name"),
            "timestamp": datetime.utcnow().isoformat(),
            "app_version": "1.0"
        }
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return base64.b64encode(img_buffer.getvalue()).decode()
    
    @staticmethod
    def validate_pin_format(pin: str) -> bool:
        """Validate PIN format"""
        if not pin or not isinstance(pin, str):
            return False
        
        # Check if PIN starts with "PIN-" and has 6 characters after
        if not pin.startswith("PIN-"):
            return False
        
        pin_code = pin[4:]  # Remove "PIN-" prefix
        return len(pin_code) == 6 and pin_code.isalnum()
    
    @staticmethod
    def generate_connection_invite_link(pin: str, base_url: str) -> str:
        """Generate a shareable connection invite link"""
        return f"{base_url}/connect?pin={pin}"

# Enhanced API endpoints to be added to server.py

async def regenerate_pin(current_user):
    """Regenerate user's PIN"""
    new_pin = EnhancedPINSystem.generate_smart_pin(current_user)
    
    # Ensure PIN is unique
    while await db.users.find_one({"connection_pin": new_pin}):
        new_pin = EnhancedPINSystem.generate_smart_pin(current_user)
    
    await db.users.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": {"connection_pin": new_pin, "pin_updated_at": datetime.utcnow()}}
    )
    
    return new_pin

async def get_enhanced_qr_code(current_user):
    """Get enhanced QR code with metadata"""
    pin = current_user.get("connection_pin")
    if not pin:
        pin = await regenerate_pin(current_user)
    
    qr_code = EnhancedPINSystem.generate_enhanced_qr_code(pin, current_user)
    
    return {
        "qr_code": qr_code,
        "connection_pin": pin,
        "display_name": current_user.get("display_name"),
        "invite_link": EnhancedPINSystem.generate_connection_invite_link(
            pin, 
            "https://authentic-connections.app"  # Replace with actual app URL
        )
    }

async def search_users_by_criteria(search_query: str, current_user_id: str):
    """Enhanced user search with multiple criteria"""
    search_results = []
    
    # Search by PIN
    if search_query.startswith("PIN-"):
        user = await db.users.find_one({"connection_pin": search_query})
        if user and user["user_id"] != current_user_id:
            search_results.append({
                "user_id": user["user_id"],
                "display_name": user.get("display_name"),
                "username": user["username"],
                "avatar": user.get("avatar"),
                "search_type": "pin"
            })
    
    # Search by email
    elif "@" in search_query:
        user = await db.users.find_one({"email": search_query})
        if user and user["user_id"] != current_user_id:
            search_results.append({
                "user_id": user["user_id"],
                "display_name": user.get("display_name"),
                "username": user["username"],
                "avatar": user.get("avatar"),
                "search_type": "email"
            })
    
    # Search by username or display name
    else:
        users = await db.users.find({
            "$and": [
                {"user_id": {"$ne": current_user_id}},
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
                "search_type": "name"
            })
    
    return search_results

async def get_connection_statistics(current_user_id: str):
    """Get connection statistics for user"""
    stats = {}
    
    # Total connections
    stats["total_connections"] = await db.connections.count_documents({
        "$or": [
            {"user_id": current_user_id},
            {"connected_user_id": current_user_id}
        ],
        "status": "connected"
    })
    
    # Pending requests (sent)
    stats["pending_sent"] = await db.connection_requests.count_documents({
        "sender_id": current_user_id,
        "status": "pending"
    })
    
    # Pending requests (received)
    stats["pending_received"] = await db.connection_requests.count_documents({
        "receiver_id": current_user_id,
        "status": "pending"
    })
    
    # Recent connections (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    stats["recent_connections"] = await db.connections.count_documents({
        "$or": [
            {"user_id": current_user_id},
            {"connected_user_id": current_user_id}
        ],
        "status": "connected",
        "created_at": {"$gte": week_ago}
    })
    
    return stats