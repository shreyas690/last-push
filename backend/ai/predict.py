import os
import json
import time
import joblib
import numpy as np
import logging

try:
    from ai.utils import MODELS_DIR
    from ai.feature_engineering import extract_features_from_packet
except ImportError:
    from backend.ai.utils import MODELS_DIR
    from backend.ai.feature_engineering import extract_features_from_packet

logger = logging.getLogger(__name__)

_model_cache = {}

def get_loaded_prediction_assets():
    """
    Lazy loads trained model, scaler, encoder, and schema.
    Returns None if no trained model exists.
    """
    if 'model' in _model_cache:
        return _model_cache['model'], _model_cache['scaler'], _model_cache['encoder'], _model_cache['schema']
        
    model_path = os.path.join(MODELS_DIR, 'best_model.pkl')
    if not os.path.exists(model_path):
        model_path = os.path.join(MODELS_DIR, 'trained_model.pkl')

    scaler_path = os.path.join(MODELS_DIR, 'feature_scaler.pkl')
    encoder_path = os.path.join(MODELS_DIR, 'label_encoder.pkl')
    schema_path = os.path.join(MODELS_DIR, 'feature_schema.json')
    
    if not (os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(encoder_path) and os.path.exists(schema_path)):
        return None, None, None, None
        
    try:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        encoder = joblib.load(encoder_path)
        with open(schema_path, 'r') as f:
            schema = json.load(f)
            
        _model_cache['model'] = model
        _model_cache['scaler'] = scaler
        _model_cache['encoder'] = encoder
        _model_cache['schema'] = schema
        return model, scaler, encoder, schema
    except Exception as e:
        logger.error(f"Error loading trained model assets: {e}")
        return None, None, None, None

def reload_prediction_assets():
    """
    Clears cache so newly retrained model artifacts are reloaded immediately.
    """
    _model_cache.clear()

def predict_threat(packet_data):
    """
    Performs real-time AI threat prediction on live packet or security test metadata.
    Outputs one of:
    - BENIGN / Normal (Low Risk)
    - Suspicious Anomaly (Medium Risk)
    - Replay Attack (High Risk)
    - Tampering Attempt (Critical Risk)
    If model is not trained yet, explicitly reports: 'Threat detection model is not trained yet.'
    """
    start_t = time.time()
    model, scaler, encoder, schema = get_loaded_prediction_assets()
    
    if model is None:
        return {
            "prediction": "Threat detection model is not trained yet.",
            "confidence": 0.0,
            "riskLevel": "None",
            "latencyMs": 0.0,
            "status": "Not Trained"
        }

    try:
        feature_dict = extract_features_from_packet(packet_data)
        
        # Align feature vector with trained schema
        schema_features = schema.get('features', [])
        feature_vector = [float(feature_dict.get(feat, 0)) for feat in schema_features]
            
        X = np.array([feature_vector], dtype=float)
        X_scaled = scaler.transform(X)
        
        pred_class_idx = model.predict(X_scaled)[0]
        confidence = 0.95
        
        if hasattr(model, 'predict_proba'):
            try:
                probas = model.predict_proba(X_scaled)[0]
                confidence = float(np.max(probas))
            except Exception:
                confidence = 0.90
            
        predicted_label = str(encoder.inverse_transform([pred_class_idx])[0])

        # Security risk level mapping
        risk_map = {
            "BENIGN / Normal": "Low",
            "Suspicious Anomaly": "Medium",
            "Replay Attack": "High",
            "Tampering Attempt": "Critical"
        }
        
        # Immediate rule checks for live packet anomalies
        if packet_data.get('packetModified') or packet_data.get('authTagValidation') == False:
            predicted_label = "Tampering Attempt"
        elif packet_data.get('nonceReused') or packet_data.get('replayCount', 0) > 0:
            predicted_label = "Replay Attack"

        risk_level = risk_map.get(predicted_label, "Medium")
        latency_ms = round((time.time() - start_t) * 1000, 2)
        
        return {
            "prediction": predicted_label,
            "confidence": round(confidence * 100, 2),
            "riskLevel": risk_level,
            "latencyMs": latency_ms,
            "featuresExtracted": feature_dict
        }
    except Exception as e:
        logger.error(f"Prediction execution error: {e}")
        return {
            "prediction": "Prediction Error",
            "confidence": 0.0,
            "riskLevel": "High",
            "latencyMs": 0.0,
            "error": str(e)
        }
