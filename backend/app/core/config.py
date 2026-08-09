import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/morse_secure_comm')
    
    # Cryptography configuration
    AES_KEY_SIZE = 32 # 256 bits
    NONCE_SIZE = 12 # 96 bits for GCM
    TAG_SIZE = 16 # 128 bits for GCM
