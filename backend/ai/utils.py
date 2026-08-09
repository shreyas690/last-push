import os
import json
import base64
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, auc

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
DATASETS_DIR = os.path.join(BASE_DIR, 'datasets')
METRICS_DIR = os.path.join(BASE_DIR, 'metrics')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATASETS_DIR, exist_ok=True)
os.makedirs(METRICS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

def plot_confusion_matrix(y_true, y_pred, labels, save_path=None):
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    
    path = save_path or os.path.join(METRICS_DIR, 'confusion_matrix.png')
    plt.savefig(path)
    plt.close()
    return path

def plot_roc_curve(y_true_binary, y_score, save_path=None):
    fpr, tpr, _ = roc_curve(y_true_binary, y_score)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC)')
    plt.legend(loc="lower right")
    plt.tight_layout()
    
    path = save_path or os.path.join(METRICS_DIR, 'roc_curve.png')
    plt.savefig(path)
    plt.close()
    return path

def plot_feature_importance(feature_names, importances, save_path=None):
    indices = np.argsort(importances)[::-1][:15] # Top 15 features
    top_names = [feature_names[i] for i in indices]
    top_importances = importances[indices]
    
    plt.figure(figsize=(8, 5))
    plt.barh(range(len(indices)), top_importances[::-1], align='center', color='#10b981')
    plt.yticks(range(len(indices)), top_names[::-1])
    plt.xlabel('Relative Importance')
    plt.title('Top Feature Importances')
    plt.tight_layout()
    
    path = save_path or os.path.join(METRICS_DIR, 'feature_importance.png')
    plt.savefig(path)
    plt.close()
    return path

def file_to_base64(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')
