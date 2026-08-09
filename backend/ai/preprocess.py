import os
import json
import joblib
import pandas as pd
import numpy as np
import logging
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
try:
    from ai.utils import MODELS_DIR
except ImportError:
    from backend.ai.utils import MODELS_DIR

logger = logging.getLogger(__name__)

def preprocess_and_save_artifacts(df, target_col='Label_Clean', feature_cols=None):
    """
    Preprocesses data, scales features, encodes labels, and persists artifacts in models/
    """
    if feature_cols is None:
        # Auto-select numeric feature columns
        feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target_col]
        
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    # Handle infinite/nan
    X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
    
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    # Save artifacts
    scaler_path = os.path.join(MODELS_DIR, 'feature_scaler.pkl')
    encoder_path = os.path.join(MODELS_DIR, 'label_encoder.pkl')
    schema_path = os.path.join(MODELS_DIR, 'feature_schema.json')
    
    joblib.dump(scaler, scaler_path)
    joblib.dump(label_encoder, encoder_path)
    
    schema = {
        'features': feature_cols,
        'classes': [str(c) for c in label_encoder.classes_],
        'feature_count': len(feature_cols)
    }
    with open(schema_path, 'w') as f:
        json.dump(schema, f, indent=2)
        
    logger.info("Saved preprocessing artifacts: scaler, encoder, feature_schema.json")
    return X_train, X_test, y_train, y_test, scaler, label_encoder, feature_cols
