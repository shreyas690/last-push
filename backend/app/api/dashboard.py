from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import UserModel
from app.models.message import MessageModel
from app.models.session import SessionModel
from app.models.logs import SystemEventLogModel
from datetime import datetime, timezone, timedelta

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
    
    total_users = users_collection.count_documents({})
    approved_users = users_collection.count_documents({"status": "Approved"})
    pending_users = users_collection.count_documents({"status": "Pending"})
    rejected_users = users_collection.count_documents({"status": "Rejected"})
    
    active_sessions = sessions_collection.count_documents({})
    online_users = len(sessions_collection.distinct("username"))
    offline_users = total_users - online_users

    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    messages_sent_today = messages_collection.count_documents({"timestamp": {"$gte": today}})
    messages_received_today = messages_sent_today # Same logical count for system level
    successful_deliveries = messages_collection.count_documents({"status": "delivered"})
    failed_deliveries = messages_collection.count_documents({"status": "failed"})
    encryption_requests = messages_collection.count_documents({}) # Every message sent is an encryption request

    security_events_cursor = SystemEventLogModel.get_recent(limit=20)
    security_events = []
    for evt in security_events_cursor:
        if '_id' in evt:
            evt['_id'] = str(evt['_id'])
        evt['timestamp'] = evt['timestamp'].isoformat()
        security_events.append(evt)

    return jsonify({
        "totalUsers": total_users,
        "onlineUsers": online_users,
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
