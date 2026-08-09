from datetime import datetime, timezone
from app.core.database import get_db

class SecurityTestResultModel:
    COLLECTION_NAME = "SecurityTestResults"

    @classmethod
    def get_collection(cls):
        return get_db().get_collection(cls.COLLECTION_NAME)

    @classmethod
    def save_experiment_results(cls, experiment_id, attack_type, total_attempts,
                                detected_attempts, missed_attempts, false_positives,
                                detection_rate, false_positive_rate, false_negative_rate,
                                avg_latency_ms, min_latency_ms, max_latency_ms,
                                encryption_overhead_ms, cpu_usage_pct, memory_usage_mb,
                                system_version="1.0.0", ai_model_version="v1"):
        """
        Saves security evaluation experiment metrics to MongoDB SecurityTestResults collection.
        """
        doc = {
            "experimentId": experiment_id,
            "attackType": attack_type,
            "totalAttempts": total_attempts,
            "detectedAttempts": detected_attempts,
            "missedAttempts": missed_attempts,
            "falsePositives": false_positives,
            "detectionRate": detection_rate,
            "falsePositiveRate": false_positive_rate,
            "falseNegativeRate": false_negative_rate,
            "avgDetectionLatencyMs": avg_latency_ms,
            "minDetectionLatencyMs": min_latency_ms,
            "maxDetectionLatencyMs": max_latency_ms,
            "encryptionOverheadMs": encryption_overhead_ms,
            "cpuUsagePct": cpu_usage_pct,
            "memoryUsageMb": memory_usage_mb,
            "timestamp": datetime.now(timezone.utc),
            "systemVersion": system_version,
            "aiModelVersion": ai_model_version
        }
        result = cls.get_collection().insert_one(doc)
        return result.inserted_id

    @classmethod
    def get_all_results(cls):
        return list(cls.get_collection().find({}, {"_id": 0}).sort("timestamp", -1))
