from datetime import datetime, timezone
from app.core.database import get_db

class SystemEventLogModel:
    COLLECTION_NAME = "system_events"

    @classmethod
    def get_collection(cls):
        return get_db().get_collection(cls.COLLECTION_NAME)

    @classmethod
    def log_event(cls, username, role, ip_address, event_type, description, status):
        """
        Logs a universal system event into MongoDB.
        """
        log_data = {
            "timestamp": datetime.now(timezone.utc),
            "username": username,
            "role": role,
            "ipAddress": ip_address,
            "eventType": event_type,
            "description": description,
            "status": status
        }
        cls.get_collection().insert_one(log_data)

    @classmethod
    def get_recent(cls, limit=50):
        return list(cls.get_collection().find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
