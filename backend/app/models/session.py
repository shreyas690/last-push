from datetime import datetime, timezone
from app.core.database import get_db
import uuid

class SessionModel:
    COLLECTION_NAME = "sessions"

    @classmethod
    def get_collection(cls):
        return get_db().get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create_session(cls, sender, receiver, session_key):
        """
        Creates a new encrypted session record.
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "sessionId": session_id,
            "sender": sender,
            "receiver": receiver,
            "sessionKey": session_key, # In production this would be handled delicately
            "createdAt": datetime.now(timezone.utc)
        }
        cls.get_collection().insert_one(session_data)
        return session_id

    @classmethod
    def get_active_sessions(cls):
        return list(cls.get_collection().find({}, {"_id": 0}))

    @classmethod
    def end_session(cls, session_id):
        return cls.get_collection().delete_one({"sessionId": session_id})
