from datetime import datetime, timezone
from app.core.database import get_db

class CommunicationLogModel:
    COLLECTION_NAME = "CommunicationLogs"

    @classmethod
    def get_collection(cls):
        return get_db().get_collection(cls.COLLECTION_NAME)

    @classmethod
    def log_communication(cls, sender, receiver, packet_size, message_length,
                          encryption_time=0.5, decryption_time=0.5, sha3_verification=True,
                          auth_tag_validation=True, nonce_reused=False, replay_count=0,
                          packet_modified=False, authentication_result="Success",
                          delivery_status="delivered", read_status=False, packet_interval=100.0,
                          connection_duration=10.0, failed_login_attempts=0,
                          threat_prediction="BENIGN / Normal", confidence_score=99.0, risk_level="Low"):
        """
        Logs real communication events with security features into MongoDB CommunicationLogs collection.
        """
        doc = {
            "sender": sender,
            "receiver": receiver,
            "timestamp": datetime.now(timezone.utc),
            "packetSize": packet_size,
            "messageLength": message_length,
            "encryptionTime": encryption_time,
            "decryptionTime": decryption_time,
            "sha3Verification": sha3_verification,
            "authTagValidation": auth_tag_validation,
            "nonceReused": nonce_reused,
            "replayCount": replay_count,
            "packetModified": packet_modified,
            "authenticationResult": authentication_result,
            "deliveryStatus": delivery_status,
            "readStatus": read_status,
            "packetInterval": packet_interval,
            "connectionDuration": connection_duration,
            "failedLoginAttempts": failed_login_attempts,
            "threatPrediction": threat_prediction,
            "confidenceScore": confidence_score,
            "riskLevel": risk_level
        }
        result = cls.get_collection().insert_one(doc)
        return result.inserted_id

    @classmethod
    def get_all_logs(cls):
        return list(cls.get_collection().find({}, {"_id": 0}).sort("timestamp", -1))

    @classmethod
    def get_log_count(cls):
        return cls.get_collection().count_documents({})
