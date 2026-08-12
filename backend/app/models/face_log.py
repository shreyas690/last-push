from datetime import datetime, timezone
from app.core.database import get_db

class FaceAuthLogModel:
    COLLECTION_NAME = "FaceAuthenticationLogs"

    @classmethod
    def get_collection(cls):
        return get_db().get_collection(cls.COLLECTION_NAME)

    @classmethod
    def log_attempt(cls, user_id, username, result, failure_reason=None, similarity_score=0.0, ip_address=None, user_agent=None):
        """
        Logs biometric face authentication attempt into MongoDB FaceAuthenticationLogs collection.
        NEVER stores raw face images or face embedding vectors.
        """
        doc = {
            "userId": user_id,
            "username": username,
            "timestamp": datetime.now(timezone.utc),
            "result": result, # "Success" or "Failed"
            "failureReason": failure_reason,
            "similarityScore": similarity_score,
            "ipAddress": ip_address,
            "userAgent": user_agent
        }
        result_id = cls.get_collection().insert_one(doc)
        return result_id.inserted_id

    @classmethod
    def get_logs_for_user(cls, username, limit=20):
        return list(cls.get_collection().find({"username": username}, {"_id": 0}).sort("timestamp", -1).limit(limit))
