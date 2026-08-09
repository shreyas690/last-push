import os
import json
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import UserModel
try:
    from ai.model_manager import ModelManager
    from ai.train import train_and_select_best_model
    from ai.retrain import execute_continuous_learning_retrain
    from ai.export_dataset import export_communication_logs_to_csv
    from ai.utils import file_to_base64, METRICS_DIR, MODELS_DIR
except ImportError:
    from backend.ai.model_manager import ModelManager
    from backend.ai.train import train_and_select_best_model
    from backend.ai.retrain import execute_continuous_learning_retrain
    from backend.ai.export_dataset import export_communication_logs_to_csv
    from backend.ai.utils import file_to_base64, METRICS_DIR, MODELS_DIR
import logging

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__)

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
    fi_base64 = file_to_base64(os.path.join(METRICS_DIR, 'feature_importance.png'))
    
    from app.models.communication_log import CommunicationLogModel
    total_logs = CommunicationLogModel.get_log_count()
    
    return jsonify({
        "activeVersion": active_version,
        "versionsHistory": all_versions,
        "evaluationReport": evaluation_report,
        "totalCommunicationLogs": total_logs,
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
        # Record model version in MongoDB
        version_doc = ModelManager.record_new_version(
            model_type=report.get("best_model_name"),
            metrics=report.get("metrics", {}),
            dataset_size=report.get("dataset_size", 0),
            feature_count=report.get("feature_count", 0),
            dataset_sources=["CIC-IDS2017"],
            is_active=True
        )
        return jsonify({
            "message": "AI Model Training completed successfully.",
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
