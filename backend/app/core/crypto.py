import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from app.core.config import Config
import base64
import time

class CryptoEngine:
    
    @staticmethod
    def generate_nonce():
        """Generates a secure 96-bit nonce for AES-GCM"""
        return os.urandom(Config.NONCE_SIZE)

    @staticmethod
    def hash_sha3_512(data: bytes) -> bytes:
        """Hashes data using SHA3-512"""
        digest = hashes.Hash(hashes.SHA3_512())
        digest.update(data)
        return digest.finalize()

    @staticmethod
    def encrypt_aes_gcm(key: bytes, plaintext: bytes, associated_data: bytes = None) -> tuple:
        """
        Encrypts plaintext using AES-256-GCM.
        Returns (ciphertext, nonce, auth_tag, encryption_time)
        """
        start_time = time.time()
        aesgcm = AESGCM(key)
        nonce = CryptoEngine.generate_nonce()
        # AESGCM in cryptography appends the tag to the ciphertext
        encrypted_data = aesgcm.encrypt(nonce, plaintext, associated_data)
        enc_time = (time.time() - start_time) * 1000 # ms
        
        # Split ciphertext and tag
        ciphertext = encrypted_data[:-16]
        auth_tag = encrypted_data[-16:]
        
        return ciphertext, nonce, auth_tag, enc_time

    @staticmethod
    def decrypt_aes_gcm(key: bytes, nonce: bytes, ciphertext: bytes, auth_tag: bytes, associated_data: bytes = None) -> tuple:
        """
        Decrypts ciphertext using AES-256-GCM and verifies the auth tag.
        Returns (plaintext, decryption_time)
        """
        start_time = time.time()
        aesgcm = AESGCM(key)
        # Reconstruct the payload as required by the library (ciphertext + tag)
        payload = ciphertext + auth_tag
        plaintext = aesgcm.decrypt(nonce, payload, associated_data)
        dec_time = (time.time() - start_time) * 1000 # ms
        return plaintext, dec_time

    @staticmethod
    def generate_x25519_keypair():
        """Generates an X25519 keypair for ECDH"""
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()
        return private_key, public_key

    @staticmethod
    def derive_shared_key(private_key, peer_public_key, salt=None) -> bytes:
        """Derives a shared key using X25519 ECDH and HKDF"""
        shared_key = private_key.exchange(peer_public_key)
        
        # Derive a 256-bit key using HKDF
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b'handshake data',
        ).derive(shared_key)
        
        return derived_key

    # PQC (Post-Quantum Cryptography) Stubs
    # In a full production system, we would use liboqs-python.
    # Due to cross-platform compatibility issues with liboqs, this acts as a functional simulation 
    # of Key Encapsulation Mechanism (KEM) to demonstrate the architecture.
    
    @staticmethod
    def generate_kyber_keypair():
        """Stubs Kyber keypair generation"""
        # Simulated by generating random bytes representing keys
        public_key = os.urandom(800) # Approx Kyber512 public key size
        private_key = os.urandom(1632) # Approx Kyber512 private key size
        return private_key, public_key
        
    @staticmethod
    def encapsulate_kyber_secret(public_key: bytes):
        """Stubs Kyber encapsulation"""
        shared_secret = os.urandom(32)
        ciphertext = os.urandom(768) # Approx Kyber512 ciphertext size
        return ciphertext, shared_secret
        
    @staticmethod
    def decapsulate_kyber_secret(ciphertext: bytes, private_key: bytes):
        """Stubs Kyber decapsulation"""
        # In a real scenario, this would derive the same secret. 
        # For the mock, we assume the shared secret is somehow synchronized or we rely on X25519
        # For the sake of the conference project demo, the X25519 handles actual secrecy, 
        # and Kyber is a simulated layer.
        return b'mock_kyber_secret_32bytes_long!' 

