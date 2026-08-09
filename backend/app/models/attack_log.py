from datetime import datetime, timezone
from app.core.database import get_db

class AttackLogModel:
    COLLECTION_NAME = "attack_logs"

    @classmethod
    def get_collection(cls):
        return get_db().get_collection(cls.COLLECTION_NAME)

    @classmethod
    def log_attack(cls, attack_type, packet, status="Blocked"):
        """
        Logs a detected attack simulation.
        """
        log_data = {
            "attackType": attack_type,
            "packet": packet,
            "status": status,
            "time": datetime.now(timezone.utc)
        }
        result = cls.get_collection().insert_one(log_data)
        return result.inserted_id

    @classmethod
    def get_recent_attacks(cls, limit=50):
        return list(cls.get_collection().find({}, {"_id": 0}).sort("time", -1).limit(limit))
