from datetime import datetime, timezone
from app.core.database import get_db

class MessageModel:
    COLLECTION_NAME = "messages"

    @classmethod
    def get_collection(cls):
        return get_db().get_collection(cls.COLLECTION_NAME)

    @classmethod
    def save_message(cls, sender_id, sender_username, sender_email, receiver_id, receiver_username, receiver_email, subject, plaintext, morse_code, ciphertext, nonce, authentication_tag, sha3_hash, encryption_status="AES-256-GCM", verification_status="SHA3-512 Verified", status="sent", **kwargs):
        """
        Saves an encrypted message to the database.
        """
        message_data = {
            "senderId": sender_id,
            "senderUsername": sender_username,
            "senderEmail": sender_email,
            "receiverId": receiver_id,
            "receiverUsername": receiver_username,
            "receiverEmail": receiver_email,
            "subject": subject,
            "plaintext": plaintext, 
            "morseCode": morse_code,
            "ciphertext": ciphertext,
            "nonce": nonce,
            "authenticationTag": authentication_tag,
            "sha3Hash": sha3_hash,
            "encryptionStatus": encryption_status,
            "verificationStatus": verification_status,
            "status": status,
            "createdAt": datetime.now(timezone.utc),
            "deliveredAt": datetime.now(timezone.utc) if status == "delivered" else None,
            "readAt": None
        }
        result = cls.get_collection().insert_one(message_data)
        return result.inserted_id

    @classmethod
    def mark_as_read(cls, message_id):
        from bson import ObjectId
        cls.get_collection().update_one(
            {"_id": ObjectId(message_id)}, 
            {"$set": {
                "isRead": True, 
                "status": "read",
                "readAt": datetime.now(timezone.utc)
            }}
        )

    @classmethod
    def get_messages_for_user(cls, username):
        return list(cls.get_collection().find({
            "$or": [{"senderUsername": username}, {"receiverUsername": username}]
        }).sort("createdAt", -1))
