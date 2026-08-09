from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import UserModel
from app.models.logs import SystemEventLogModel
from app import socketio # For live dashboard emits
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

def get_client_info(req):
    ip = req.remote_addr
    ua = req.user_agent
    browser = ua.browser if ua.browser else "Unknown"
    os_name = ua.platform if ua.platform else "Unknown"
    return ip, browser, os_name

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({"error": "Username and password are required"}), 400

        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'User') 
        email = data.get('email')
        
        # Prevent Admin registration
        if role != 'User':
            return jsonify({"error": "Invalid role"}), 400

        if UserModel.find_by_username(username):
            return jsonify({"error": "Username already exists"}), 409

        hashed_password = generate_password_hash(password)
        UserModel.create_user(username, hashed_password, role, email)

        ip, _, _ = get_client_info(request)
        SystemEventLogModel.log_event(username, role, ip, "User Registered", "Account created and pending approval.", "Success")

        # Notify dashboard of new pending user
        socketio.emit('dashboard_update', {'type': 'NEW_PENDING_USER'})

        return jsonify({"message": "User registered successfully. Pending Admin approval."}), 201

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({"error": "Username and password are required"}), 400

        username = data.get('username')
        password = data.get('password')
        is_admin_route = request.path.endswith('/admin/login')

        user = UserModel.find_by_username(username)
        if not user or not check_password_hash(user['password'], password):
            return jsonify({"error": "Invalid username or password"}), 401

        if is_admin_route and user['role'] != 'Admin':
            ip, _, _ = get_client_info(request)
            SystemEventLogModel.log_event(username, user['role'], ip, "Unauthorized Access Attempt", "Attempted to login via Admin portal.", "Failed")
            return jsonify({"error": "Unauthorized"}), 403
            
        if not is_admin_route and user['role'] == 'Admin':
            return jsonify({"error": "Admins must use the admin portal"}), 403

        # Log login event
        ip, _, _ = get_client_info(request)
        SystemEventLogModel.log_event(username, user['role'], ip, "User Login", "Terminal access granted.", "Success")

        # Notify dashboard
        socketio.emit('dashboard_update', {'type': 'USER_LOGIN', 'username': username})

        access_token = create_access_token(identity=user['username'])
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "username": user['username'],
                "role": user['role'],
                "status": user['status'],
                "terminalAccess": user.get('terminalAccess', False)
            }
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    # Reuse login logic
    return login()

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_username = get_jwt_identity()
    user = UserModel.find_by_username(current_username)
    
    if user:
        ip, _, _ = get_client_info(request)
        SystemEventLogModel.log_event(user['username'], user['role'], ip, "User Logout", "User disconnected from session.", "Success")
        socketio.emit('dashboard_update', {'type': 'USER_LOGOUT', 'username': user['username']})
        
    return jsonify({"message": "Logged out"}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_username = get_jwt_identity()
    user = UserModel.find_by_username(current_username)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify({
        "username": user['username'],
        "role": user['role'],
        "status": user['status'],
        "terminalAccess": user['terminalAccess']
    }), 200

@auth_bp.route('/messages', methods=['GET'])
@jwt_required()
def get_messages():
    current_username = get_jwt_identity()
    user = UserModel.find_by_username(current_username)
    
    if not user or not user.get('terminalAccess'):
        return jsonify({"error": "Unauthorized"}), 403

    from app.models.message import MessageModel
    messages = MessageModel.get_messages_for_user(current_username)
    
    for msg in messages:
        msg['_id'] = str(msg['_id'])
        if msg.get('createdAt'):
            msg['createdAt'] = msg['createdAt'].isoformat()
        if msg.get('deliveredAt'):
            msg['deliveredAt'] = msg['deliveredAt'].isoformat()
        if msg.get('readAt'):
            msg['readAt'] = msg['readAt'].isoformat()
            
    return jsonify(messages), 200

@auth_bp.route('/validate-recipient', methods=['POST'])
@jwt_required()
def validate_recipient():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request"}), 400
        
    receiver_username = data.get('receiver', '').strip()
    receiver_email = data.get('email', '').strip()
    
    # 2. Search the MongoDB Users collection
    user = None
    if receiver_username:
        user = UserModel.find_by_username(receiver_username)
    
    if not user and receiver_email:
        user = UserModel.find_by_email(receiver_email)
        
    # 3. If user does NOT exist
    if not user:
        return jsonify({"error": "This email address is not registered with Secure Morse Communication. Please verify the recipient's email address and try again."}), 404
        
    # 4. If exists but not approved
    if user.get('status') != 'Approved':
        return jsonify({"error": "The recipient's account has not yet been approved by the System Administrator."}), 403
        
    # 5. If exists but terminal access is disabled
    if not user.get('terminalAccess'):
        return jsonify({"error": "The recipient does not currently have permission to use the Secure Communication Terminal."}), 403
        
    return jsonify({"message": "Valid"}), 200
