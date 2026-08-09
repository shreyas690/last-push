from datetime import datetime, timezone
from app.core.database import get_db

class PerformanceModel:
    COLLECTION_NAME = "performance_metrics"

    @classmethod
    def get_collection(cls):
        return get_db().get_collection(cls.COLLECTION_NAME)

    @classmethod
    def log_metrics(cls, cpu, memory, latency, packet_loss, key_gen_time):
        """
        Logs system performance metrics.
        """
        metrics_data = {
            "cpuUsage": cpu,
            "memoryUsage": memory,
            "latency": latency,
            "packetLoss": packet_loss,
            "keyGenerationTime": key_gen_time,
            "timestamp": datetime.now(timezone.utc)
        }
        result = cls.get_collection().insert_one(metrics_data)
        return result.inserted_id

    @classmethod
    def get_latest_metrics(cls, limit=100):
        return list(cls.get_collection().find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
