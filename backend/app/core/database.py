from pymongo import MongoClient
from app.core.config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    client = None
    db = None

    @classmethod
    def initialize(cls):
        try:
            cls.client = MongoClient(Config.MONGO_URI)
            # Explicitly specify the database name since the URI might not have one
            cls.db = cls.client.get_database("morse_secure_comm")
            logger.info("Connected to MongoDB successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    def get_collection(cls, collection_name):
        if cls.db is None:
            raise Exception("Database not initialized.")
        return cls.db[collection_name]

# Helper to get db instance
def get_db():
    return Database
