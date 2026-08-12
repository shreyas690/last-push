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

def plot_confusion_matrix(y_true, y_pred, class_names, save_path=None):
    """
    Generates a dynamic Confusion Matrix plot from actual predictions across the 4 threat classes.
    """
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(7, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Greens', xticklabels=class_names, yticklabels=class_names)
    plt.title('Real Confusion Matrix (Threat Classification)')
    plt.ylabel('Actual Class')
    plt.xlabel('Predicted Class')
    plt.xticks(rotation=30, ha='right', fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    
    path = save_path or os.path.join(METRICS_DIR, 'confusion_matrix.png')
    plt.savefig(path, dpi=150)
    plt.close()
    return path, cm.tolist()

def plot_roc_curve(y_true, y_proba, class_names, save_path=None):
    """
    Generates a multi-class One-vs-Rest (OvR) ROC curve plot from actual model probability outputs.
    """
    plt.figure(figsize=(7, 5))
    colors = ['#00ff66', '#00f3ff', '#ff0055', '#eab308']
    
    # One-vs-Rest ROC curve for each class
    for i, class_name in enumerate(class_names):
        y_true_binary = (np.array(y_true) == i).astype(int)
        if len(np.unique(y_true_binary)) > 1 and y_proba is not None and y_proba.shape[1] > i:
            fpr, tpr, _ = roc_curve(y_true_binary, y_proba[:, i])
            roc_auc = auc(fpr, tpr)
            plt.plot(fpr, tpr, color=colors[i % len(colors)], lw=2, label=f'{class_name} (AUC = {roc_auc:.2f})')

    plt.plot([0, 1], [0, 1], color='gray', lw=1.5, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Multi-Class ROC Curve Analysis (One-vs-Rest)')
    plt.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    
    path = save_path or os.path.join(METRICS_DIR, 'roc_curve.png')
    plt.savefig(path, dpi=150)
    plt.close()
    return path

def plot_feature_importance(feature_names, importances, model_name="Best Model", save_path=None):
    """
    Generates a dynamic feature importance bar chart for the specified trained classifier.
    """
    indices = np.argsort(importances)[::-1][:15] # Top 15 features
    top_names = [feature_names[i] for i in indices]
    top_importances = importances[indices]
    
    plt.figure(figsize=(8, 5))
    plt.barh(range(len(indices)), top_importances[::-1], align='center', color='#00ff66')
    plt.yticks(range(len(indices)), top_names[::-1], fontsize=9)
    plt.xlabel('Relative Feature Importance')
    plt.title(f'Top Feature Importances — {model_name}')
    plt.tight_layout()
    
    filename = f"feature_importance_{model_name.replace(' ', '_')}.png"
    path = save_path or os.path.join(METRICS_DIR, filename)
    plt.savefig(path, dpi=150)
    plt.close()
    return path

def file_to_base64(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')
