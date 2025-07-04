# Enhanced PIN Connection Endpoints
# These endpoints will be added to server.py

from fastapi import HTTPException
from enhanced_pin_system import EnhancedPINSystem
import json

# Enhanced PIN Management Endpoints

@api_router.post("/pin/regenerate")
async def regenerate_user_pin(current_user = Depends(get_current_user)):
    """Regenerate user's connection PIN"""
    try:
        new_pin = EnhancedPINSystem.generate_smart_pin(current_user)
        
        # Ensure PIN is unique
        while await db.users.find_one({"connection_pin": new_pin}):
            new_pin = EnhancedPINSystem.generate_smart_pin(current_user)
        
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

@api_router.get("/pin/qr-enhanced")
async def get_enhanced_qr_code(current_user = Depends(get_current_user)):
    """Get enhanced QR code with metadata"""
    try:
        pin = current_user.get("connection_pin")
        if not pin:
            # Generate new PIN if doesn't exist
            pin = EnhancedPINSystem.generate_smart_pin(current_user)
            await db.users.update_one(
                {"user_id": current_user["user_id"]},
                {"$set": {"connection_pin": pin}}
            )
        
        qr_code = EnhancedPINSystem.generate_enhanced_qr_code(pin, current_user)
        
        return {
            "qr_code": qr_code,
            "connection_pin": pin,
            "display_name": current_user.get("display_name"),
            "invite_link": f"https://authentic-connections.app/connect?pin={pin}",
            "qr_format": "enhanced"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate QR code")

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
            if not EnhancedPINSystem.validate_pin_format(search_query):
                raise HTTPException(status_code=400, detail="Invalid PIN format")
            
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

@api_router.post("/connections/request-enhanced")
async def send_enhanced_connection_request(request_data: dict, current_user = Depends(get_current_user)):
    """Send enhanced connection request with more options"""
    target_id = request_data.get("target_user_id")
    target_pin = request_data.get("target_pin")
    message = request_data.get("message", "")
    connection_type = request_data.get("connection_type", "general")  # general, professional, friendship, etc.
    
    if not target_id and not target_pin:
        raise HTTPException(status_code=400, detail="Target user ID or PIN required")
    
    try:
        # Find target user
        if target_pin:
            if not EnhancedPINSystem.validate_pin_format(target_pin):
                raise HTTPException(status_code=400, detail="Invalid PIN format")
            target_user = await db.users.find_one({"connection_pin": target_pin})
        else:
            target_user = await db.users.find_one({"user_id": target_id})
        
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
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
                raise HTTPException(status_code=400, detail="Connection request already sent")
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
        await manager.send_personal_message(
            json.dumps({
                "type": "connection_request",
                "data": {
                    "request_id": connection_request["request_id"],
                    "sender": connection_request["sender_info"],
                    "message": message,
                    "connection_type": connection_type
                }
            }),
            target_user["user_id"]
        )
        
        return {
            "message": "Connection request sent successfully",
            "request_id": connection_request["request_id"],
            "target_user": {
                "display_name": target_user.get("display_name"),
                "username": target_user["username"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send connection request")

@api_router.put("/connections/requests/{request_id}/respond")
async def respond_to_connection_request(request_id: str, response_data: dict, current_user = Depends(get_current_user)):
    """Respond to connection request with enhanced options"""
    action = response_data.get("action")  # accept, decline, block
    message = response_data.get("message", "")
    
    if action not in ["accept", "decline", "block"]:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    try:
        # Find the connection request
        request = await db.connection_requests.find_one({
            "request_id": request_id,
            "receiver_id": current_user["user_id"],
            "status": "pending"
        })
        
        if not request:
            raise HTTPException(status_code=404, detail="Connection request not found")
        
        # Update request status
        await db.connection_requests.update_one(
            {"request_id": request_id},
            {"$set": {
                "status": action + "ed",
                "response_message": message,
                "responded_at": datetime.utcnow()
            }}
        )
        
        if action == "accept":
            # Create mutual connection
            connection = {
                "connection_id": str(uuid.uuid4()),
                "user_id": current_user["user_id"],
                "connected_user_id": request["sender_id"],
                "status": "connected",
                "trust_level": 1,  # Start at trust level 1
                "created_at": datetime.utcnow(),
                "connection_type": request.get("connection_type", "general")
            }
            
            await db.connections.insert_one(connection)
            
            # Create reverse connection
            reverse_connection = {
                "connection_id": str(uuid.uuid4()),
                "user_id": request["sender_id"],
                "connected_user_id": current_user["user_id"],
                "status": "connected",
                "trust_level": 1,
                "created_at": datetime.utcnow(),
                "connection_type": request.get("connection_type", "general")
            }
            
            await db.connections.insert_one(reverse_connection)
            
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
            
            # Send notification to sender
            await manager.send_personal_message(
                json.dumps({
                    "type": "connection_accepted",
                    "data": {
                        "request_id": request_id,
                        "accepter": {
                            "display_name": current_user.get("display_name"),
                            "username": current_user["username"]
                        },
                        "chat_id": chat["chat_id"],
                        "message": message
                    }
                }),
                request["sender_id"]
            )
            
        elif action == "block":
            # Add to blocked users
            await db.blocked_users.insert_one({
                "blocker_id": current_user["user_id"],
                "blocked_id": request["sender_id"],
                "created_at": datetime.utcnow(),
                "reason": "Connection request blocked"
            })
        
        return {
            "message": f"Connection request {action}ed successfully",
            "action": action,
            "request_id": request_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to respond to connection request")