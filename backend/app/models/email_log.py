from datetime import datetime, timezone
from app.core.database import get_db

class EmailNotificationLogModel:
    COLLECTION_NAME = "EmailNotificationLogs"

    @classmethod
    def get_collection(cls):
        return get_db().get_collection(cls.COLLECTION_NAME)

    @classmethod
    def log_notification(cls, user_id, recipient_email, notification_type, status, error_message=None):
        """
        Logs notification email delivery status into MongoDB EmailNotificationLogs collection.
        """
        doc = {
            "userId": user_id,
            "recipientEmail": recipient_email,
            "notificationType": notification_type, # "Approval Notification" or "Rejection Notification"
            "timestamp": datetime.now(timezone.utc),
            "deliveryStatus": status, # "Sent" or "Failed"
            "errorMessage": error_message,
            "retryCount": 0
        }
        result_id = cls.get_collection().insert_one(doc)
        return result_id.inserted_id

    @classmethod
    def get_logs_for_email(cls, recipient_email, limit=20):
        return list(cls.get_collection().find({"recipientEmail": recipient_email}, {"_id": 0}).sort("timestamp", -1).limit(limit))
