from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import UserModel
from app.models.logs import SystemEventLogModel
from services.email_service import EmailService
from app import socketio
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/pending-users', methods=['GET'])
@jwt_required()
def get_pending_users():
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    users = list(UserModel.get_collection().find({"status": "Pending"}, {"password": 0, "faceEmbedding": 0}))
    for user in users:
        user['_id'] = str(user['_id'])
        user['faceRegistered'] = bool(user.get('faceRegistered', False))
    return jsonify(users), 200


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    users = list(UserModel.get_collection().find({}, {"password": 0, "faceEmbedding": 0}))
    for user in users:
        user['_id'] = str(user['_id'])
        user['faceRegistered'] = bool(user.get('faceRegistered', False))
    return jsonify(users), 200


@admin_bp.route('/approve/<user_id>', methods=['PUT'])
@jwt_required()
def approve_user(user_id):
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    try:
        obj_id = ObjectId(user_id)
    except Exception:
        return jsonify({"error": "Invalid user ID"}), 400

    target_user = UserModel.get_collection().find_one({"_id": obj_id})
    if not target_user:
        return jsonify({"error": "User not found"}), 404

    if target_user['status'] == 'Approved':
        return jsonify({"error": "User is already approved"}), 400

    # 1. Immediately trigger Gmail Approval Email Notification
    email_success, email_msg = EmailService.send_approval_email(
        recipient_email=target_user.get('email'),
        username=target_user['username'],
        user_id=str(target_user['_id'])
    )

    email_status = "Sent" if email_success else "Failed"

    # 2. Update user approval status in MongoDB
    UserModel.update_status(target_user['username'], "Approved", True, current_user['username'], email_status=email_status)

    # 3. Log security event & broadcast real-time update
    SystemEventLogModel.log_event(target_user['username'], target_user['role'], request.remote_addr, "User Approved", f"Approved by {current_user['username']} (Email: {email_status})", "Success")
    socketio.emit('dashboard_update', {'type': 'USER_APPROVED', 'username': target_user['username'], 'emailStatus': email_status})

    if email_success:
        return jsonify({"message": f"User {target_user['username']} approved. Notification email sent to {target_user.get('email')}."}), 200
    else:
        return jsonify({"message": f"User {target_user['username']} approved, but notification email could not be delivered: {email_msg}"}), 200


@admin_bp.route('/reject/<user_id>', methods=['PUT'])
@jwt_required()
def reject_user(user_id):
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    try:
        obj_id = ObjectId(user_id)
    except Exception:
        return jsonify({"error": "Invalid user ID"}), 400

    target_user = UserModel.get_collection().find_one({"_id": obj_id})
    if not target_user:
        return jsonify({"error": "User not found"}), 404

    if target_user['status'] == 'Rejected':
        return jsonify({"error": "User is already rejected"}), 400

    # 1. Immediately trigger Gmail Rejection Email Notification
    email_success, email_msg = EmailService.send_rejection_email(
        recipient_email=target_user.get('email'),
        username=target_user['username'],
        user_id=str(target_user['_id'])
    )

    email_status = "Sent" if email_success else "Failed"

    # 2. Update user rejection status in MongoDB
    UserModel.update_status(target_user['username'], "Rejected", False, current_user['username'], email_status=email_status)

    # 3. Log security event & broadcast real-time update
    SystemEventLogModel.log_event(target_user['username'], target_user['role'], request.remote_addr, "User Rejected", f"Rejected by {current_user['username']} (Email: {email_status})", "Success")
    socketio.emit('dashboard_update', {'type': 'USER_REJECTED', 'username': target_user['username'], 'emailStatus': email_status})

    if email_success:
        return jsonify({"message": f"User {target_user['username']} rejected. Notification email sent to {target_user.get('email')}."}), 200
    else:
        return jsonify({"message": f"User {target_user['username']} rejected, but notification email could not be delivered: {email_msg}"}), 200
