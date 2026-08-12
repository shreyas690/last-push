import os
import math
import time
import logging
from datetime import datetime, timezone
from app.core.database import get_db

logger = logging.getLogger(__name__)

# Configurable face matching threshold (Euclidean distance threshold: 0.6)
FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.6"))

class FaceService:
    @staticmethod
    def validate_face_quality(face_data):
        """
        Validates face registration data provided by frontend webcam detection.
        Checks for:
        - Presence of face embedding descriptor vector (128 floats)
        - Face bounding box dimensions (ensuring face is close enough)
        - Single face verification flag
        """
        if not face_data:
            return False, "No face data provided. Please position your face inside the frame."
            
        embedding = face_data.get('embedding')
        if not embedding or not isinstance(embedding, list) or len(embedding) < 16:
            return False, "No face was detected. Please position your face inside the frame."
            
        face_count = face_data.get('faceCount', 1)
        if face_count == 0:
            return False, "No face was detected. Please position your face inside the frame."
        elif face_count > 1:
            return False, "Multiple faces detected. Please ensure that only one person is visible."
            
        face_box = face_data.get('box', {})
        width = face_box.get('width', 0)
        height = face_box.get('height', 0)
        
        # Quality check: box width/height threshold
        if width > 0 and height > 0 and (width < 60 or height < 60):
            return False, "Please move closer to the camera and try again."
            
        return True, "Valid face detected."

    @staticmethod
    def calculate_euclidean_distance(embedding1, embedding2):
        """
        Calculates the Euclidean distance between two biometric embedding vectors.
        """
        if not embedding1 or not embedding2 or len(embedding1) != len(embedding2):
            return 999.0
            
        sum_sq = sum((float(a) - float(b)) ** 2 for a, b in zip(embedding1, embedding2))
        return math.sqrt(sum_sq)

    @staticmethod
    def calculate_cosine_similarity(embedding1, embedding2):
        """
        Calculates Cosine Similarity score between two biometric vectors (range 0.0 to 1.0).
        """
        if not embedding1 or not embedding2 or len(embedding1) != len(embedding2):
            return 0.0
            
        dot_product = sum(float(a) * float(b) for a, b in zip(embedding1, embedding2))
        norm_a = math.sqrt(sum(float(a) ** 2 for a in embedding1))
        norm_b = math.sqrt(sum(float(b) ** 2 for b in embedding2))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return dot_product / (norm_a * norm_b)

    @classmethod
    def verify_face(cls, input_embedding, registered_embedding, threshold=None):
        """
        Compares input webcam embedding against registered user embedding template.
        Returns (is_match, similarity_score, distance, reason).
        """
        if threshold is None:
            threshold = FACE_MATCH_THRESHOLD
            
        if not input_embedding or not registered_embedding:
            return False, 0.0, 999.0, "Missing biometric template data."
            
        distance = cls.calculate_euclidean_distance(input_embedding, registered_embedding)
        similarity = cls.calculate_cosine_similarity(input_embedding, registered_embedding)
        similarity_pct = round(similarity * 100, 2)
        
        is_match = distance <= threshold or similarity >= 0.70
        
        if is_match:
            return True, similarity_pct, round(distance, 4), "Face verification successful."
        else:
            return False, similarity_pct, round(distance, 4), "Face verification does not match the registered account."

    @classmethod
    def log_face_auth(cls, user_id, username, result, failure_reason=None, similarity_score=0.0, ip_address=None, user_agent=None):
        """
        Logs biometric authentication attempts to MongoDB FaceAuthenticationLogs collection.
        NEVER stores raw face images or embeddings.
        """
        try:
            from app.models.face_log import FaceAuthLogModel
            FaceAuthLogModel.log_attempt(
                user_id=str(user_id) if user_id else "Unknown",
                username=username,
                result=result,
                failure_reason=failure_reason,
                similarity_score=similarity_score,
                ip_address=ip_address,
                user_agent=user_agent
            )
        except Exception as e:
            logger.error(f"Failed to log face authentication attempt: {e}")
