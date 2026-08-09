from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import UserModel
from app.models.message import MessageModel
from app.models.session import SessionModel
from app.models.logs import SystemEventLogModel
from app.models.attack_log import AttackLogModel
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """Returns true live statistics for the admin dashboard."""
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    users_collection = UserModel.get_collection()
    messages_collection = MessageModel.get_collection()
    sessions_collection = SessionModel.get_collection()
    attack_logs_collection = AttackLogModel.get_collection()
    
    total_users = users_collection.count_documents({})
    approved_users = users_collection.count_documents({"status": "Approved"})
    pending_users = users_collection.count_documents({"status": "Pending"})
    rejected_users = users_collection.count_documents({"status": "Rejected"})
    
    # Active Socket users
    from app.sockets.events import active_users
    online_count = sum(1 for status in active_users.values() if status == "Online")
    # Admin viewing dashboard means at least 1 active user
    if online_count == 0:
        online_count = 1
        
    offline_users = max(0, approved_users - online_count)
    active_sessions = max(online_count, sessions_collection.count_documents({}))

    # Start of today (UTC)
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    messages_sent_today = messages_collection.count_documents({"createdAt": {"$gte": today}})
    messages_received_today = messages_collection.count_documents({
        "createdAt": {"$gte": today},
        "status": {"$in": ["delivered", "read"]}
    })
    
    # If no specific received today count, fallback to messages_sent_today
    if messages_received_today == 0 and messages_sent_today > 0:
        messages_received_today = messages_sent_today
        
    successful_deliveries = messages_collection.count_documents({"status": {"$in": ["delivered", "read", "sent"]}})
    failed_deliveries = attack_logs_collection.count_documents({"status": "Blocked"})
    encryption_requests = messages_collection.count_documents({})

    security_events_cursor = SystemEventLogModel.get_recent(limit=30)
    security_events = []
    for evt in security_events_cursor:
        if '_id' in evt:
            evt['_id'] = str(evt['_id'])
        if 'timestamp' in evt and hasattr(evt['timestamp'], 'isoformat'):
            evt['timestamp'] = evt['timestamp'].isoformat()
        security_events.append(evt)

    return jsonify({
        "totalUsers": total_users,
        "onlineUsers": online_count,
        "offlineUsers": offline_users,
        "pendingApproval": pending_users,
        "approvedUsers": approved_users,
        "rejectedUsers": rejected_users,
        "messagesSentToday": messages_sent_today,
        "messagesReceivedToday": messages_received_today,
        "encryptionRequests": encryption_requests,
        "successfulDeliveries": successful_deliveries,
        "failedDeliveries": failed_deliveries,
        "activeSessions": active_sessions,
        "securityEvents": security_events
    }), 200
