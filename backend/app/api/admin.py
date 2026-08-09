from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import UserModel
from app.models.logs import SystemEventLogModel
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

    users = list(UserModel.get_collection().find({"status": "Pending"}, {"password": 0}))
    for user in users:
        user['_id'] = str(user['_id'])
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
    except:
        return jsonify({"error": "Invalid user ID"}), 400

    target_user = UserModel.get_collection().find_one({"_id": obj_id})
    if not target_user:
        return jsonify({"error": "User not found"}), 404

    if target_user['status'] == 'Approved':
        return jsonify({"error": "User is already approved"}), 400

    UserModel.update_status(target_user['username'], "Approved", True, current_user['username'])
    
    SystemEventLogModel.log_event(target_user['username'], target_user['role'], request.remote_addr, "User Approved", f"Approved by {current_user['username']}", "Success")
    socketio.emit('dashboard_update', {'type': 'USER_APPROVED', 'username': target_user['username']})
    
    return jsonify({"message": f"User {target_user['username']} approved for terminal access."}), 200

@admin_bp.route('/reject/<user_id>', methods=['PUT'])
@jwt_required()
def reject_user(user_id):
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    try:
        obj_id = ObjectId(user_id)
    except:
        return jsonify({"error": "Invalid user ID"}), 400

    target_user = UserModel.get_collection().find_one({"_id": obj_id})
    if not target_user:
        return jsonify({"error": "User not found"}), 404

    if target_user['status'] == 'Rejected':
        return jsonify({"error": "User is already rejected"}), 400

    UserModel.update_status(target_user['username'], "Rejected", False, current_user['username'])
    
    SystemEventLogModel.log_event(target_user['username'], target_user['role'], request.remote_addr, "User Rejected", f"Rejected by {current_user['username']}", "Success")
    socketio.emit('dashboard_update', {'type': 'USER_REJECTED', 'username': target_user['username']})
    
    return jsonify({"message": f"User {target_user['username']} rejected."}), 200
