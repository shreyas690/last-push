import re
import logging
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import UserModel
from app.models.logs import SystemEventLogModel
from services.face_service import FaceService
from app import socketio

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
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', 'User')
        face_data = data.get('faceData') or data.get('face_data')

        if not username or not password or not email:
            return jsonify({"error": "Username, password, and Gmail address are required."}), 400

        # Validate Gmail format
        if not re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", email, re.IGNORECASE):
            return jsonify({"error": "A valid Gmail address (@gmail.com) is required for registration."}), 400

        # Prevent non-User registrations
        if role != 'User':
            return jsonify({"error": "Invalid role"}), 400

        if UserModel.find_by_username(username):
            return jsonify({"error": "Username already exists."}), 409

        if UserModel.find_by_email(email):
            return jsonify({"error": "Gmail address is already registered."}), 409

        # Validate Biometric Face Registration
        is_valid_face, face_err_msg = FaceService.validate_face_quality(face_data)
        if not is_valid_face:
            return jsonify({"error": face_err_msg}), 400

        face_embedding = face_data.get('embedding')
        hashed_password = generate_password_hash(password)

        # Store protected biometric template vector in MongoDB
        UserModel.create_user(
            username=username,
            password_hash=hashed_password,
            role=role,
            email=email,
            face_embedding=face_embedding
        )

        ip, _, _ = get_client_info(request)
        SystemEventLogModel.log_event(username, role, ip, "User Registered", "Account created with face template and pending approval.", "Success")

        # Notify dashboard of new pending user
        socketio.emit('dashboard_update', {'type': 'NEW_PENDING_USER', 'username': username})

        return jsonify({
            "message": "User registered successfully. Pending Admin approval."
        }), 201

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        is_admin_route = request.path.endswith('/admin/login')

        if not username or not password:
            return jsonify({"error": "Username and password are required."}), 400

        user = UserModel.find_by_username(username)
        if not user or not check_password_hash(user['password'], password):
            return jsonify({"error": "Invalid username or password."}), 401

        if is_admin_route and user['role'] != 'Admin':
            ip, _, _ = get_client_info(request)
            SystemEventLogModel.log_event(username, user['role'], ip, "Unauthorized Access Attempt", "Attempted login via Admin portal.", "Failed")
            return jsonify({"error": "Unauthorized"}), 403

        if not is_admin_route and user['role'] == 'Admin':
            return jsonify({"error": "Admins must use the admin portal."}), 403

        # Check approval status for regular users
        if not is_admin_route:
            if user.get('status') == 'Pending':
                return jsonify({"error": "Your account is pending System Admin approval."}), 403
            elif user.get('status') == 'Rejected':
                return jsonify({"error": "Your account registration was not approved."}), 403

        # If Admin, issue token directly
        if is_admin_route or user['role'] == 'Admin':
            ip, _, _ = get_client_info(request)
            SystemEventLogModel.log_event(username, user['role'], ip, "Admin Login", "Admin dashboard access granted.", "Success")
            socketio.emit('dashboard_update', {'type': 'USER_LOGIN', 'username': username})
            access_token = create_access_token(identity=user['username'])
            return jsonify({
                "message": "Login successful",
                "access_token": access_token,
                "user": {
                    "username": user['username'],
                    "role": user['role'],
                    "status": user['status'],
                    "terminalAccess": user.get('terminalAccess', True)
                }
            }), 200

        # For regular users, require Step 2: Face Verification
        return jsonify({
            "message": "Password verified. Please complete face authentication.",
            "requiresFaceVerification": True,
            "username": user['username']
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/verify-face', methods=['POST'])
def verify_face():
    """
    Step 2: Biometric Face Verification login handler.
    Compares live webcam embedding against registered template in MongoDB.
    """
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        face_data = data.get('faceData') or data.get('face_data')
        ip, _, user_agent = get_client_info(request)

        if not username or not face_data:
            return jsonify({"error": "Username and face verification data are required."}), 400

        user = UserModel.find_by_username(username)
        if not user:
            FaceService.log_face_auth(None, username, "Failed", "User not found", 0.0, ip, str(user_agent))
            return jsonify({"error": "User not found."}), 404

        if user.get('status') != 'Approved' or not user.get('terminalAccess'):
            FaceService.log_face_auth(str(user['_id']), username, "Failed", "Account not approved", 0.0, ip, str(user_agent))
            return jsonify({"error": "Your account does not have clearance for terminal access."}), 403

        registered_embedding = user.get('faceEmbedding')
        if not registered_embedding:
            FaceService.log_face_auth(str(user['_id']), username, "Failed", "No registered face template", 0.0, ip, str(user_agent))
            return jsonify({"error": "No registered face template found for this account."}), 400

        input_embedding = face_data.get('embedding')
        face_count = face_data.get('faceCount', 1)

        if face_count == 0 or not input_embedding:
            FaceService.log_face_auth(str(user['_id']), username, "Failed", "No face detected", 0.0, ip, str(user_agent))
            return jsonify({"error": "No face was detected. Please position your face inside the frame."}), 400

        if face_count > 1:
            FaceService.log_face_auth(str(user['_id']), username, "Failed", "Multiple faces detected", 0.0, ip, str(user_agent))
            return jsonify({"error": "Multiple faces detected. Please ensure that only one person is visible."}), 400

        # Perform Euclidean & Cosine Biometric Template Matching
        is_match, similarity_pct, distance, reason = FaceService.verify_face(input_embedding, registered_embedding)

        if not is_match:
            FaceService.log_face_auth(str(user['_id']), username, "Failed", reason, similarity_pct, ip, str(user_agent))
            return jsonify({"error": "Face verification does not match the registered account."}), 401

        # Successful Biometric Verification
        FaceService.log_face_auth(str(user['_id']), username, "Success", None, similarity_pct, ip, str(user_agent))
        UserModel.update_face_verification_time(username)
        SystemEventLogModel.log_event(username, user['role'], ip, "Biometric Verification Success", f"Face matched ({similarity_pct}% similarity). Terminal access granted.", "Success")
        socketio.emit('dashboard_update', {'type': 'USER_LOGIN', 'username': username})

        access_token = create_access_token(identity=user['username'])
        return jsonify({
            "message": "Face verification successful. Terminal access granted.",
            "access_token": access_token,
            "user": {
                "username": user['username'],
                "role": user['role'],
                "status": user['status'],
                "terminalAccess": user.get('terminalAccess', True)
            }
        }), 200

    except Exception as e:
        logger.error(f"Face verification error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    return login()


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_username = get_jwt_identity()
    user = UserModel.find_by_username(current_username)
    if user:
        ip, _, _ = get_client_info(request)
        SystemEventLogModel.log_event(user['username'], user['role'], ip, "User Logout", "User disconnected session.", "Success")
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
        "email": user.get('email'),
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
    data = request.get_json() or {}
    receiver_username = data.get('receiver', '').strip()
    receiver_email = data.get('email', '').strip()

    user = None
    if receiver_username:
        user = UserModel.find_by_username(receiver_username)
    if not user and receiver_email:
        user = UserModel.find_by_email(receiver_email)

    if not user:
        return jsonify({"error": "This address is not registered with Secure Morse Communication."}), 404
    if user.get('status') != 'Approved':
        return jsonify({"error": "The recipient's account has not yet been approved by the System Administrator."}), 403
    if not user.get('terminalAccess'):
        return jsonify({"error": "The recipient does not currently have permission to use the Secure Communication Terminal."}), 403

    return jsonify({"message": "Valid"}), 200
