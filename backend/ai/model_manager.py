from datetime import datetime, timezone
from app.core.database import get_db
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    COLLECTION_NAME = "ModelVersions"

    @classmethod
    def get_collection(cls):
        return get_db().get_collection(cls.COLLECTION_NAME)

    @classmethod
    def get_all_versions(cls):
        return list(cls.get_collection().find({}, {"_id": 0}).sort("version_number", -1))

    @classmethod
    def get_current_active_version(cls):
        versions = list(cls.get_collection().find({"is_active": True}, {"_id": 0}))
        if versions:
            return versions[0]
        # Return latest recorded version if active flag is not set
        all_v = cls.get_all_versions()
        return all_v[0] if all_v else None

    @classmethod
    def record_new_version(cls, model_type, metrics, dataset_size, feature_count, dataset_sources, is_active=True):
        """
        Creates a new model version record (v1, v2, v3...) in MongoDB ModelVersions collection.
        Never deletes previous versions.
        """
        all_v = cls.get_all_versions()
        next_ver_num = (all_v[0].get("version_number", 0) + 1) if all_v else 1
        version_str = f"v{next_ver_num}"
        
        if is_active:
            # Set previous versions active = False
            cls.get_collection().update_many({}, {"$set": {"is_active": False}})

        doc = {
            "version": version_str,
            "version_number": next_ver_num,
            "model_type": model_type,
            "training_date": datetime.now(timezone.utc).isoformat(),
            "dataset_size": dataset_size,
            "feature_count": feature_count,
            "accuracy": metrics.get("accuracy", 0.0),
            "precision": metrics.get("precision", 0.0),
            "recall": metrics.get("recall", 0.0),
            "f1_score": metrics.get("f1_score", 0.0),
            "roc_auc": metrics.get("roc_auc", 0.0),
            "training_time_sec": metrics.get("train_time_sec", 0.0),
            "prediction_time_sec": metrics.get("prediction_time_sec", 0.0),
            "dataset_sources": dataset_sources,
            "is_active": is_active,
            "createdAt": datetime.now(timezone.utc)
        }
        cls.get_collection().insert_one(doc)
        logger.info(f"Recorded new model version {version_str} in MongoDB.")
        return doc
