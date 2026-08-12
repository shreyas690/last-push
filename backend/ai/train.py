import os
import time
import json
import joblib
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)

try:
    from ai.dataset_loader import load_cic_ids2017_dataset
    from ai.feature_engineering import adapt_cic_ids2017_df
    from ai.preprocess import preprocess_and_save_artifacts
    from ai.utils import (
        MODELS_DIR, METRICS_DIR, plot_confusion_matrix, plot_roc_curve, plot_feature_importance
    )
    from ai.label_mapping import TARGET_CLASSES
except ImportError:
    from backend.ai.dataset_loader import load_cic_ids2017_dataset
    from backend.ai.feature_engineering import adapt_cic_ids2017_df
    from backend.ai.preprocess import preprocess_and_save_artifacts
    from backend.ai.utils import (
        MODELS_DIR, METRICS_DIR, plot_confusion_matrix, plot_roc_curve, plot_feature_importance
    )
    from backend.ai.label_mapping import TARGET_CLASSES

logger = logging.getLogger(__name__)

def train_and_select_best_model():
    """
    Trains and compares EXACTLY 4 Machine Learning Classifiers:
    1. Random Forest
    2. XGBoost
    3. LightGBM
    4. Extra Trees
    Evaluates real metrics on an 80/20 train/test split.
    Selects best model based on F1 Score & Recall.
    Saves models, versioning metadata, and real visualization plots.
    NO SYNTHETIC BASELINE OR HARDCODED DATA IS EVER USED.
    """
    df = load_cic_ids2017_dataset()
    if df is None or len(df) == 0:
        logger.info("No training dataset available. Please provide CIC-IDS2017 data.")
        return {
            "error": "No training dataset available. Please provide CIC-IDS2017 data.",
            "status": "Failed"
        }
        
    df_adapted = adapt_cic_ids2017_df(df)
    if len(df_adapted) < 10:
        return {
            "error": "Insufficient dataset records for training.",
            "status": "Failed"
        }

    X_train, X_test, y_train, y_test, scaler, label_encoder, feature_cols = preprocess_and_save_artifacts(df_adapted)
    
    # Train EXACTLY the 4 requested classifiers
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        'XGBoost': XGBClassifier(random_state=42, n_jobs=-1, eval_metric='mlogloss'),
        'LightGBM': LGBMClassifier(random_state=42, n_jobs=-1, verbose=-1),
        'Extra Trees': ExtraTreesClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    }
    
    comparison_results = {}
    trained_models = {}
    best_score = -1.0
    best_model_name = None
    
    # Track class names present
    present_classes = list(label_encoder.classes_)
    
    for name, model in models.items():
        logger.info(f"Training model: {name}...")
        start_train = time.time()
        model.fit(X_train, y_train)
        train_time = round(time.time() - start_train, 4)
        
        start_pred = time.time()
        y_pred = model.predict(X_test)
        pred_time = round(time.time() - start_pred, 4)
        
        y_proba = None
        if hasattr(model, "predict_proba"):
            try:
                y_proba = model.predict_proba(X_test)
            except Exception:
                y_proba = None

        acc = round(accuracy_score(y_test, y_pred), 4)
        prec = round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4)
        rec = round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4)
        f1 = round(f1_score(y_test, y_pred, average='macro', zero_division=0), 4)
        
        roc_auc = 0.5
        if y_proba is not None and len(np.unique(y_test)) > 1:
            try:
                roc_auc = round(roc_auc_score(y_test, y_proba, multi_class='ovr', average='weighted'), 4)
            except Exception as e:
                logger.warning(f"ROC-AUC calculation notice for {name}: {e}")
                roc_auc = 0.5
            
        metrics = {
            'accuracy': acc,
            'precision': prec,
            'recall': rec,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'train_time_sec': train_time,
            'prediction_time_sec': pred_time
        }
        comparison_results[name] = metrics
        trained_models[name] = (model, y_pred, y_proba)
        
        # Plot feature importance for each individual model
        if hasattr(model, 'feature_importances_'):
            plot_feature_importance(feature_cols, model.feature_importances_, model_name=name)
        
        # Primary selection: F1 score + Weighted Recall
        score = f1 + (0.1 * rec)
        if score > best_score:
            best_score = score
            best_model_name = name

    logger.info(f"Best selected model: {best_model_name} with F1: {comparison_results[best_model_name]['f1_score']}")
    best_model, best_pred, best_proba = trained_models[best_model_name]
    
    # Save best model to disk
    joblib.dump(best_model, os.path.join(MODELS_DIR, 'best_model.pkl'))
    joblib.dump(best_model, os.path.join(MODELS_DIR, 'trained_model.pkl')) # Compatibility
    
    # Generate real plots
    cm_path, cm_values = plot_confusion_matrix(y_test, best_pred, class_names=present_classes)
    plot_roc_curve(y_test, best_proba, class_names=present_classes)
    
    evaluation_report = {
        'best_model_name': best_model_name,
        'dataset_size': len(df_adapted),
        'feature_count': len(feature_cols),
        'metrics': comparison_results[best_model_name],
        'comparison': comparison_results,
        'classes': [str(c) for c in present_classes],
        'confusion_matrix': cm_values,
        'trained_at': datetime.now(timezone.utc).isoformat()
    }
    
    report_path = os.path.join(MODELS_DIR, 'latest_evaluation_report.json')
    with open(report_path, 'w') as f:
        json.dump(evaluation_report, f, indent=2)

    # Record model version in MongoDB ModelVersions collection
    try:
        from ai.model_manager import ModelManager
        ModelManager.record_new_version(
            model_type=best_model_name,
            metrics=comparison_results[best_model_name],
            dataset_sources=["CIC-IDS2017", "CommunicationLogs"],
            is_active=True
        )
    except Exception as e:
        logger.warning(f"Could not record model version in MongoDB: {e}")
        
    return evaluation_report
