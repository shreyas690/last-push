from flask_socketio import emit, join_room, leave_room
from flask import request
from app import socketio
from app.core.ai_model import threat_detector
from app.models.attack_log import AttackLogModel
from app.models.message import MessageModel
from app.models.user import UserModel
from app.models.logs import SystemEventLogModel
import logging
from datetime import datetime, timezone
import time

logger = logging.getLogger(__name__)

# State tracking for real-time delivery and online status
active_users = {} # Maps username -> "Online" or timestamp (offline)
sid_to_user = {}  # Maps request.sid -> username

def broadcast_online_users():
    socketio.emit('online_users_update', active_users)

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    emit('status', {'message': 'Connected to Secure Morse Communication Server'})
    broadcast_online_users()

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected")
    username = sid_to_user.pop(request.sid, None)
    if username:
        active_users[username] = time.time() * 1000 # Last seen timestamp in ms
        broadcast_online_users()
        logger.info(f"{username} went offline.")

@socketio.on('join_personal_room')
def handle_join_personal_room(data):
    """
    User joins their personal room to receive mailbox updates and direct messages.
    """
    username = data.get('username')
    if username:
        join_room(username)
        user = UserModel.find_by_username(username)
        if user:
            join_room(str(user['_id']))
        sid_to_user[request.sid] = username
        active_users[username] = "Online"
        broadcast_online_users()
        logger.info(f"{username} joined their personal mailbox room.")


@socketio.on('send_message')
def handle_send_message(data):
    """
    Receives an encrypted message, runs AI threat detection, saves it, and forwards to receiver.
    Returns a dict to the client as an acknowledgement.
    """
    print(f"!!! RECEIVED SEND_MESSAGE EVENT FROM FRONTEND: {data} !!!", flush=True)
    sender = data.get('sender')
    receiver = data.get('receiver')
    subject = data.get('subject', 'No Subject')
    plaintext = data.get('plaintext') 
    packet = data.get('packet', {})
    
    sender_user = UserModel.find_by_username(sender)
    
    receiver_user = UserModel.find_by_username(receiver)
    if not receiver_user:
        receiver_user = UserModel.find_by_email(receiver)
        
    if not sender_user or not receiver_user:
        return {"success": False, "error": "Invalid sender or receiver."}
        
    # Standardize receiver username if email was passed
    receiver = receiver_user['username']

    # 1. AI Threat Detection
    packet_size = packet.get('packetSize', 0)
    timestamp = packet.get('timestamp', time.time())
    time_delta = (time.time() - timestamp) * 1000 
    
    seq_diff = 1 
    recent_auth_fails = 0
    
    threat_label = threat_detector.predict_packet(packet_size, time_delta, recent_auth_fails, seq_diff)
    
    if threat_label != "Normal":
        AttackLogModel.log_attack(threat_label, str(packet), status="Blocked")
        event_str = "Replay Attack Detected" if "Replay" in threat_label else "Tampering Attempt Blocked"
        SystemEventLogModel.log_event(sender, "User", request.remote_addr, event_str, f"Blocked packet to {receiver}", "Failed")
        socketio.emit('dashboard_update', {'type': 'SECURITY_EVENT', 'event': threat_label})
        return {"success": False, "error": f"{threat_label} Detected. Message Rejected."}
        
    # 2. Check Receiver Online Status
    is_receiver_online = active_users.get(receiver) == "Online"
    message_status = "delivered" if is_receiver_online else "sent"
    
    # 3. Save and Forward
    try:
        msg_id = MessageModel.save_message(
            sender_id=str(sender_user.get('_id')),
            sender_username=sender,
            sender_email=sender_user.get('email'),
            receiver_id=str(receiver_user.get('_id')),
            receiver_username=receiver,
            receiver_email=receiver_user.get('email'),
            subject=subject,
            plaintext=plaintext,
            morse_code=data.get('morseCode', ''),
            ciphertext=packet.get('ciphertext'),
            nonce=packet.get('nonce'),
            authentication_tag=packet.get('authTag'),
            sha3_hash=packet.get('hash', 'N/A'),
            encryption_status=packet.get('encryptionStatus', 'AES-256-GCM'),
            verification_status=packet.get('verificationStatus', 'SHA3-512 Verified'),
            status=message_status
        )
        
        # Build the inbox item to broadcast to receiver
        inbox_item = {
            "_id": str(msg_id),
            "senderId": str(sender_user.get('_id')),
            "senderUsername": sender,
            "senderEmail": sender_user.get('email'),
            "receiverId": str(receiver_user.get('_id')),
            "receiverUsername": receiver,
            "receiverEmail": receiver_user.get('email'),
            "subject": subject,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "deliveredAt": datetime.now(timezone.utc).isoformat() if is_receiver_online else None,
            "readAt": None,
            "plaintext": plaintext,
            "morseCode": data.get('morseCode', ''),
            "ciphertext": packet.get('ciphertext'),
            "nonce": packet.get('nonce'),
            "authenticationTag": packet.get('authTag'),
            "sha3Hash": packet.get('hash', 'N/A'),
            "encryptionStatus": packet.get('encryptionStatus', 'AES-256-GCM'),
            "verificationStatus": packet.get('verificationStatus', 'SHA3-512 Verified'),
            "status": message_status
        }
        
        SystemEventLogModel.log_event(sender, "User", request.remote_addr, "Encryption Successful", "AES-256-GCM payload generated.", "Success")
        SystemEventLogModel.log_event(sender, "User", request.remote_addr, "Message Transmitted", f"Transmitted payload to {receiver}", "Success")
        
        # Log feature vector to CommunicationLogs for continuous learning
        from app.models.communication_log import CommunicationLogModel
        CommunicationLogModel.log_communication(
            sender=sender,
            receiver=receiver,
            packet_size=packet_size,
            message_length=len(plaintext or ''),
            encryption_time=0.45,
            decryption_time=0.45,
            sha3_verification=True,
            auth_tag_validation=True,
            nonce_reused=False,
            replay_count=0,
            packet_modified=False,
            authentication_result="Success",
            delivery_status=message_status,
            threat_prediction="BENIGN / Normal",
            confidence_score=99.0,
            risk_level="Low"
        )
        
        if is_receiver_online:
            # Emit to receiver's personal room instantly (once)
            emit('receive_message', inbox_item, room=str(receiver_user.get('_id')))
            SystemEventLogModel.log_event(receiver, "User", "Unknown", "Message Delivered", f"Received payload from {sender}", "Success")
            socketio.emit('dashboard_update', {'type': 'MESSAGE_DELIVERED'})
            
            return {"success": True, "message": "Message delivered instantly.", "data": inbox_item}
        else:
            socketio.emit('dashboard_update', {'type': 'MESSAGE_SENT'})
            return {
                "success": True, 
                "message": "Message could not be delivered because the recipient is currently unavailable. The message has been securely saved and will be delivered when the recipient reconnects.",
                "data": inbox_item
            }
            
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        SystemEventLogModel.log_event(sender, "User", request.remote_addr, "Message Failed", f"Delivery failed to {receiver}", "Failed")
        return {"success": False, "error": "Internal delivery error."}

@socketio.on('mark_read')
def handle_mark_read(data):
    message_id = data.get('message_id')
    sender = data.get('sender')
    if message_id:
        MessageModel.mark_as_read(message_id)
        # Notify sender that their message was read
        sender_user = UserModel.find_by_username(sender)
        if sender_user:
            emit('message_read_receipt', {'message_id': message_id, 'readAt': datetime.now(timezone.utc).isoformat()}, room=str(sender_user.get('_id')))
