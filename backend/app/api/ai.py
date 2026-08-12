import os
import glob
import json
import pandas as pd
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import UserModel
from app.core.database import get_db

try:
    from ai.model_manager import ModelManager
    from ai.train import train_and_select_best_model
    from ai.retrain import execute_continuous_learning_retrain
    from ai.export_dataset import export_communication_logs_to_csv
    from ai.utils import file_to_base64, METRICS_DIR, MODELS_DIR, DATASETS_DIR
except ImportError:
    from backend.ai.model_manager import ModelManager
    from backend.ai.train import train_and_select_best_model
    from backend.ai.retrain import execute_continuous_learning_retrain
    from backend.ai.export_dataset import export_communication_logs_to_csv
    from backend.ai.utils import file_to_base64, METRICS_DIR, MODELS_DIR, DATASETS_DIR

import logging

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__)

CIC_IDS2017_DIR = os.path.join(DATASETS_DIR, 'CIC-IDS2017')
os.makedirs(CIC_IDS2017_DIR, exist_ok=True)

@ai_bp.route('/import-dataset', methods=['POST'])
@jwt_required()
def import_dataset():
    """
    Admin endpoint to upload/import a CIC-IDS2017 CSV file.
    Validates CSV, calculates row count, column count, label distribution, and records metadata.
    NO SYNTHETIC BASELINE DATA IS EVER GENERATED.
    """
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No CSV file provided in upload request."}), 400

    file = request.files['file']
    if not file or not file.filename.endswith('.csv'):
        return jsonify({"error": "Only valid .csv files are supported."}), 400

    filename = file.filename
    save_path = os.path.join(CIC_IDS2017_DIR, filename)

    try:
        file.save(save_path)
        df = pd.read_csv(save_path, low_memory=False)
        df.columns = df.columns.str.strip()

        row_count = len(df)
        col_count = len(df.columns)
        missing_values = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        # Determine label column and class counts
        label_col = None
        for col in ['Label', 'label', 'Attack', 'Label_Clean']:
            if col in df.columns:
                label_col = col
                break

        class_distribution = {}
        if label_col:
            class_distribution = df[label_col].value_counts().to_dict()
            class_distribution = {str(k): int(v) for k, v in class_distribution.items()}

        import_meta = {
            "filename": filename,
            "filepath": save_path,
            "rowCount": row_count,
            "columnCount": col_count,
            "missingValues": missing_values,
            "duplicateRows": duplicate_rows,
            "classDistribution": class_distribution,
            "importedBy": current_user['username'],
            "importedAt": datetime.now(timezone.utc).isoformat()
        }

        # Store metadata in MongoDB DatasetImports collection
        get_db().get_collection("DatasetImports").update_one(
            {"filename": filename},
            {"$set": import_meta},
            upsert=True
        )

        return jsonify({
            "message": f"Successfully imported {filename} ({row_count} rows, {col_count} columns).",
            "metadata": import_meta
        }), 200
    except Exception as e:
        logger.error(f"Failed to import dataset: {e}")
        return jsonify({"error": f"Dataset import failed: {str(e)}"}), 500


@ai_bp.route('/datasets', methods=['GET'])
@jwt_required()
def get_imported_datasets():
    """
    Returns metadata for all manually imported CIC-IDS2017 datasets.
    """
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    datasets = list(get_db().get_collection("DatasetImports").find({}, {"_id": 0}))
    return jsonify(datasets), 200


@ai_bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_ai_metrics():
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    active_version = ModelManager.get_current_active_version()
    all_versions = ModelManager.get_all_versions()
    
    # Read latest evaluation report file
    report_path = os.path.join(MODELS_DIR, 'latest_evaluation_report.json')
    evaluation_report = {}
    if os.path.exists(report_path):
        try:
            with open(report_path, 'r') as f:
                evaluation_report = json.load(f)
        except Exception as e:
            logger.error(f"Error reading evaluation report: {e}")
            
    cm_base64 = file_to_base64(os.path.join(METRICS_DIR, 'confusion_matrix.png'))
    roc_base64 = file_to_base64(os.path.join(METRICS_DIR, 'roc_curve.png'))
    
    # Check model-specific feature importance image
    best_model_name = evaluation_report.get('best_model_name', 'Best Model')
    fi_filename = f"feature_importance_{best_model_name.replace(' ', '_')}.png"
    fi_base64 = file_to_base64(os.path.join(METRICS_DIR, fi_filename)) or file_to_base64(os.path.join(METRICS_DIR, 'feature_importance.png'))

    from app.models.communication_log import CommunicationLogModel
    total_logs = CommunicationLogModel.get_log_count()
    imported_datasets = list(get_db().get_collection("DatasetImports").find({}, {"_id": 0}))
    
    return jsonify({
        "activeVersion": active_version,
        "versionsHistory": all_versions,
        "evaluationReport": evaluation_report,
        "totalCommunicationLogs": total_logs,
        "importedDatasets": imported_datasets,
        "images": {
            "confusionMatrix": cm_base64,
            "rocCurve": roc_base64,
            "featureImportance": fi_base64
        }
    }), 200


@ai_bp.route('/train', methods=['POST'])
@jwt_required()
def trigger_training():
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    try:
        report = train_and_select_best_model()
        if "error" in report:
            return jsonify({"error": report["error"]}), 400

        # Record model version in MongoDB
        version_doc = ModelManager.record_new_version(
            model_type=report.get("best_model_name"),
            metrics=report.get("metrics", {}),
            dataset_size=report.get("dataset_size", 0),
            feature_count=report.get("feature_count", 0),
            dataset_sources=["CIC-IDS2017", "CommunicationLogs"],
            is_active=True
        )
        return jsonify({
            "message": f"Successfully trained 4 classifiers on real data. Best selected model: {report.get('best_model_name')}.",
            "version": version_doc.get("version"),
            "report": report
        }), 200
    except Exception as e:
        logger.error(f"Training failed: {e}")
        return jsonify({"error": f"Training failed: {str(e)}"}), 500


@ai_bp.route('/retrain', methods=['POST'])
@jwt_required()
def trigger_retraining():
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    try:
        result = execute_continuous_learning_retrain()
        if "error" in result:
            return jsonify({"error": result["error"]}), 400
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Retraining failed: {e}")
        return jsonify({"error": f"Retraining failed: {str(e)}"}), 500


@ai_bp.route('/export-dataset', methods=['POST'])
@jwt_required()
def export_dataset():
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    result = export_communication_logs_to_csv()
    if not result.get("success"):
        return jsonify(result), 400
    return jsonify(result), 200
