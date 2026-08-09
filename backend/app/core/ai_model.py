import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import logging

logger = logging.getLogger(__name__)

class AIThreatDetector:
    MODEL_PATH = os.path.join(os.path.dirname(__file__), 'threat_model.pkl')
    
    def __init__(self):
        self.model = None
        self.load_or_train_model()
        
    def load_or_train_model(self):
        if os.path.exists(self.MODEL_PATH):
            try:
                self.model = joblib.load(self.MODEL_PATH)
                logger.info("AI Threat Model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self.train_synthetic_model()
        else:
            self.train_synthetic_model()
            
    def train_synthetic_model(self):
        """
        Trains a Random Forest model on synthetic packet data.
        Features: [packet_size, time_delta, auth_failures_recent, sequence_number_diff]
        Classes: 0: Normal, 1: Replay Attack, 2: Tampering, 3: Unknown
        """
        logger.info("Training new AI Threat Model on synthetic data...")
        
        # Synthetic Normal Data
        # [size (100-500), delta_ms (50-2000), auth_fails (0), seq_diff (1)]
        X_normal = np.column_stack((
            np.random.randint(100, 500, 500),
            np.random.randint(50, 2000, 500),
            np.zeros(500),
            np.ones(500)
        ))
        y_normal = np.zeros(500)
        
        # Synthetic Replay Attack Data
        # seq_diff <= 0 or time_delta < 5
        X_replay = np.column_stack((
            np.random.randint(100, 500, 200),
            np.random.randint(0, 10, 200),
            np.zeros(200),
            np.random.randint(-5, 1, 200)
        ))
        y_replay = np.ones(200)
        
        # Synthetic Tampering Data
        # Auth fails > 0, random size
        X_tamper = np.column_stack((
            np.random.randint(50, 1000, 200),
            np.random.randint(50, 2000, 200),
            np.random.randint(1, 5, 200),
            np.random.randint(1, 5, 200)
        ))
        y_tamper = np.full(200, 2)
        
        # Combine
        X = np.vstack((X_normal, X_replay, X_tamper))
        y = np.concatenate((y_normal, y_replay, y_tamper))
        
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, y)
        
        # Save model
        joblib.dump(self.model, self.MODEL_PATH)
        logger.info("AI Threat Model trained and saved.")
        
    def predict_packet(self, packet_size, time_delta_ms, recent_auth_fails, seq_diff):
        """
        Predicts if a packet is malicious.
        Returns: String label
        """
        if not self.model:
            return "Unknown"
            
        features = np.array([[packet_size, time_delta_ms, recent_auth_fails, seq_diff]])
        prediction = self.model.predict(features)[0]
        
        labels = {
            0: "Normal",
            1: "Replay Attack",
            2: "Tampering",
            3: "Unknown"
        }
        return labels.get(prediction, "Unknown")

# Singleton instance
threat_detector = AIThreatDetector()
