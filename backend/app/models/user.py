from datetime import datetime, timezone
from app.core.database import get_db

class UserModel:
    COLLECTION_NAME = "users"

    @classmethod
    def get_collection(cls):
        return get_db().get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create_user(cls, username, password_hash, role="User", email=None, face_embedding=None):
        """
        Creates a new user document with secure biometric template storage and Gmail address.
        """
        user_data = {
            "username": username,
            "email": email or f"{username}@gmail.com",
            "password": password_hash,
            "role": role,
            "status": "Approved" if role == "Admin" else "Pending",
            "terminalAccess": True if role == "Admin" else False,
            "approvedBy": None,
            "approvedAt": None,
            "faceEmbedding": face_embedding, # 128-float vector template
            "faceRegistered": True if (face_embedding or role == "Admin") else False,
            "faceRegisteredAt": datetime.now(timezone.utc) if face_embedding else None,
            "faceVerifiedAt": None,
            "emailNotificationStatus": "Pending",
            "createdAt": datetime.now(timezone.utc),
            "lastLoginAt": None,
            "lastLogoutAt": None
        }
        result = cls.get_collection().insert_one(user_data)
        return result.inserted_id

    @classmethod
    def update_status(cls, username, status, terminal_access, admin_username, email_status=None):
        update_fields = {
            "status": status,
            "terminalAccess": terminal_access
        }
        
        if email_status:
            update_fields["emailNotificationStatus"] = email_status
            
        if status == "Approved":
            update_fields["approvedBy"] = admin_username
            update_fields["approvedAt"] = datetime.now(timezone.utc)
        elif status == "Rejected":
            update_fields["rejectedBy"] = admin_username
            update_fields["rejectedAt"] = datetime.now(timezone.utc)
            
        cls.get_collection().update_one(
            {"username": username},
            {"$set": update_fields}
        )

    @classmethod
    def update_face_verification_time(cls, username):
        cls.get_collection().update_one(
            {"username": username},
            {"$set": {"faceVerifiedAt": datetime.now(timezone.utc), "lastLoginAt": datetime.now(timezone.utc)}}
        )

    @classmethod
    def find_by_username(cls, username):
        import re
        return cls.get_collection().find_one({"username": re.compile(f"^{username}$", re.IGNORECASE)})

    @classmethod
    def find_by_email(cls, email):
        import re
        return cls.get_collection().find_one({"email": re.compile(f"^{email}$", re.IGNORECASE)})

    @classmethod
    def get_all_users(cls):
        # Exclude password hash and raw faceEmbedding for security
        return list(cls.get_collection().find({}, {"password": 0, "faceEmbedding": 0}))
