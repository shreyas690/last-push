import os
import time
import json
import joblib
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, classification_report
)
try:
    from ai.dataset_loader import load_cic_ids2017_dataset
    from ai.feature_engineering import adapt_cic_ids2017_df
    from ai.preprocess import preprocess_and_save_artifacts
    from ai.utils import (
        MODELS_DIR, plot_confusion_matrix, plot_roc_curve, plot_feature_importance
    )
except ImportError:
    from backend.ai.dataset_loader import load_cic_ids2017_dataset
    from backend.ai.feature_engineering import adapt_cic_ids2017_df
    from backend.ai.preprocess import preprocess_and_save_artifacts
    from backend.ai.utils import (
        MODELS_DIR, plot_confusion_matrix, plot_roc_curve, plot_feature_importance
    )

logger = logging.getLogger(__name__)

def train_and_select_best_model():
    """
    Trains and compares Random Forest, XGBoost, Decision Tree, and Logistic Regression.
    Evaluates Accuracy, Precision, Recall, F1 Score, ROC-AUC, Training Time, and Prediction Time.
    Selects the best model based on F1 Score & Recall.
    Saves trained_model.pkl and updates model metrics.
    """
    df = load_cic_ids2017_dataset()
    if df is None or len(df) == 0:
        logger.info("No CIC-IDS2017 dataset CSVs found. Falling back to synthetic baseline model training.")
        return train_baseline_synthetic_model()
        
    df_adapted = adapt_cic_ids2017_df(df)
    X_train, X_test, y_train, y_test, scaler, label_encoder, feature_cols = preprocess_and_save_artifacts(df_adapted)
    
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        'XGBoost': XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42, n_jobs=-1),
        'Decision Tree': DecisionTreeClassifier(random_state=42),
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42)
    }
    
    comparison_results = {}
    trained_models = {}
    best_score = -1.0
    best_model_name = None
    
    for name, model in models.items():
        logger.info(f"Training model: {name}...")
        start_train = time.time()
        model.fit(X_train, y_train)
        train_time = round(time.time() - start_train, 4)
        
        start_pred = time.time()
        y_pred = model.predict(X_test)
        pred_time = round(time.time() - start_pred, 4)
        
        y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred
        
        acc = round(accuracy_score(y_test, y_pred), 4)
        prec = round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4)
        rec = round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4)
        f1 = round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4)
        
        try:
            roc_auc = round(roc_auc_score(y_test, y_proba), 4)
        except Exception:
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
        
        # Primary selection: F1 score (balanced with recall for security)
        score = f1 + (0.1 * rec)
        if score > best_score:
            best_score = score
            best_model_name = name
            
    logger.info(f"Best selected model: {best_model_name} with F1: {comparison_results[best_model_name]['f1_score']}")
    best_model, best_pred, best_proba = trained_models[best_model_name]
    
    # Save best trained model
    model_save_path = os.path.join(MODELS_DIR, 'trained_model.pkl')
    joblib.dump(best_model, model_save_path)
    
    # Generate visualization plots
    plot_confusion_matrix(y_test, best_pred, labels=list(range(len(label_encoder.classes_))))
    plot_roc_curve(y_test, best_proba)
    
    if hasattr(best_model, 'feature_importances_'):
        plot_feature_importance(feature_cols, best_model.feature_importances_)
    elif hasattr(best_model, 'coef_'):
        plot_feature_importance(feature_cols, np.abs(best_model.coef_[0]))
        
    evaluation_report = {
        'best_model_name': best_model_name,
        'dataset_size': len(df_adapted),
        'feature_count': len(feature_cols),
        'metrics': comparison_results[best_model_name],
        'comparison': comparison_results,
        'classes': [str(c) for c in label_encoder.classes_],
        'trained_at': datetime.now(timezone.utc).isoformat()
    }
    
    report_path = os.path.join(MODELS_DIR, 'latest_evaluation_report.json')
    with open(report_path, 'w') as f:
        json.dump(evaluation_report, f, indent=2)
        
    return evaluation_report

def train_baseline_synthetic_model():
    """
    Fallback baseline training on application feature space if CIC-IDS2017 files are not yet present.
    """
    feature_cols = [
        'packetSize', 'messageLength', 'encryptionTime', 'decryptionTime',
        'sha3Verification', 'authTagValidation', 'nonceReused', 'replayCount',
        'packetModified', 'failedLoginAttempts', 'packetInterval', 'connectionDuration'
    ]
    np.random.seed(42)
    n = 1000
    
    # Normal samples
    X_normal = np.column_stack([
        np.random.randint(100, 500, n), np.random.randint(10, 100, n),
        np.random.uniform(0.1, 0.5, n), np.random.uniform(0.1, 0.5, n),
        np.ones(n), np.ones(n), np.zeros(n), np.zeros(n),
        np.zeros(n), np.zeros(n), np.random.uniform(10, 500, n), np.random.uniform(1, 60, n)
    ])
    y_normal = np.array(['BENIGN'] * n)
    
    # Attack samples
    X_attack = np.column_stack([
        np.random.randint(50, 2000, n//2), np.random.randint(1, 200, n//2),
        np.random.uniform(0.5, 2.0, n//2), np.random.uniform(0.5, 2.0, n//2),
        np.random.choice([0, 1], n//2), np.random.choice([0, 1], n//2),
        np.random.choice([0, 1], n//2), np.random.randint(1, 5, n//2),
        np.random.choice([0, 1], n//2), np.random.randint(1, 10, n//2),
        np.random.uniform(0.1, 5.0, n//2), np.random.uniform(0.1, 10, n//2)
    ])
    y_attack = np.array(['ATTACK'] * (n//2))
    
    X = np.vstack([X_normal, X_attack])
    y = np.concatenate([y_normal, y_attack])
    
    df = pd.DataFrame(X, columns=feature_cols)
    df['Label_Clean'] = y
    
    X_train, X_test, y_train, y_test, scaler, label_encoder, feature_cols = preprocess_and_save_artifacts(df)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    start_t = time.time()
    model.fit(X_train, y_train)
    train_t = round(time.time() - start_t, 4)
    
    start_p = time.time()
    y_pred = model.predict(X_test)
    pred_t = round(time.time() - start_p, 4)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    acc = round(accuracy_score(y_test, y_pred), 4)
    prec = round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4)
    rec = round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4)
    f1 = round(f1_score(y_test, y_pred, average='weighted', zero_division=0), 4)
    roc_auc = round(roc_auc_score(y_test, y_proba), 4)
    
    joblib.dump(model, os.path.join(MODELS_DIR, 'trained_model.pkl'))
    
    plot_confusion_matrix(y_test, y_pred, labels=list(range(len(label_encoder.classes_))))
    plot_roc_curve(y_test, y_proba)
    plot_feature_importance(feature_cols, model.feature_importances_)
    
    metrics = {
        'accuracy': acc, 'precision': prec, 'recall': rec, 'f1_score': f1,
        'roc_auc': roc_auc, 'train_time_sec': train_t, 'prediction_time_sec': pred_t
    }
    evaluation_report = {
        'best_model_name': 'Random Forest (Baseline)',
        'dataset_size': len(df),
        'feature_count': len(feature_cols),
        'metrics': metrics,
        'comparison': {'Random Forest': metrics},
        'classes': [str(c) for c in label_encoder.classes_],
        'trained_at': datetime.now(timezone.utc).isoformat()
    }
    with open(os.path.join(MODELS_DIR, 'latest_evaluation_report.json'), 'w') as f:
        json.dump(evaluation_report, f, indent=2)
        
    return evaluation_report
