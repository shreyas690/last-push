import os
from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import UserModel
from app.models.security_test_result import SecurityTestResultModel
try:
    from security_tests.evaluator import execute_full_security_evaluation
    from security_tests.report_generator import REPORTS_DIR
except ImportError:
    from backend.security_tests.evaluator import execute_full_security_evaluation
    from backend.security_tests.report_generator import REPORTS_DIR
from app import socketio
import logging

logger = logging.getLogger(__name__)

security_tests_bp = Blueprint('security_tests', __name__)

@security_tests_bp.route('/run', methods=['POST'])
@jwt_required()
def run_security_test():
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json() or {}
    scale = int(data.get('scale', 100))
    if scale not in [10, 50, 100, 500, 1000]:
        scale = 100

    try:
        summary = execute_full_security_evaluation(scale=scale, socketio=socketio)
        return jsonify({
            "message": "Formal Security Evaluation executed successfully.",
            "summary": summary
        }), 200
    except Exception as e:
        logger.error(f"Security Evaluation failed: {e}")
        return jsonify({"error": f"Security Evaluation failed: {str(e)}"}), 500

@security_tests_bp.route('/results', methods=['GET'])
@jwt_required()
def get_security_results():
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    results = SecurityTestResultModel.get_all_results()
    for r in results:
        if 'timestamp' in r and hasattr(r['timestamp'], 'isoformat'):
            r['timestamp'] = r['timestamp'].isoformat()
    return jsonify(results), 200

@security_tests_bp.route('/report/<exp_id>', methods=['GET'])
@jwt_required()
def download_report(exp_id):
    current_username = get_jwt_identity()
    current_user = UserModel.find_by_username(current_username)
    if not current_user or current_user['role'] != 'Admin':
        return jsonify({"error": "Unauthorized"}), 403

    format_type = request.args.get('format', 'json')
    filename = f"security_report_{exp_id}.{format_type}"
    filepath = os.path.join(REPORTS_DIR, filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "Report file not found."}), 404

    return send_file(filepath, as_attachment=True, download_name=filename)
