import logging
try:
    from ai.export_dataset import export_communication_logs_to_csv
    from ai.train import train_and_select_best_model
    from ai.model_manager import ModelManager
    from ai.predict import reload_prediction_assets
except ImportError:
    from backend.ai.export_dataset import export_communication_logs_to_csv
    from backend.ai.train import train_and_select_best_model
    from backend.ai.model_manager import ModelManager
    from backend.ai.predict import reload_prediction_assets

logger = logging.getLogger(__name__)

def execute_continuous_learning_retrain():
    """
    Executes continuous learning workflow:
    1. Export REAL communication logs from MongoDB.
    2. Retrain multi-model suite on combined dataset.
    3. Compare new model performance against active production model.
    4. Deploy ONLY if performance improves.
    """
    # 1. Export real communication logs
    export_result = export_communication_logs_to_csv()
    logger.info(f"Dataset export result: {export_result}")
    
    # 2. Train & select candidate model
    new_report = train_and_select_best_model()
    if "error" in new_report:
        return {"error": new_report["error"], "status": "Failed"}

    current_active = ModelManager.get_current_active_version()
    current_f1 = current_active.get("f1_score", 0.0) if current_active else 0.0
    
    new_metrics = new_report.get("metrics", {})
    new_f1 = new_metrics.get("f1_score", 0.0)
    
    # 3. Compare performance
    is_improved = (new_f1 >= current_f1) or (current_active is None)
    
    if is_improved:
        logger.info(f"Performance improved (New F1: {new_f1} >= Current F1: {current_f1}). Deploying new model version.")
        version_doc = ModelManager.record_new_version(
            model_type=new_report.get("best_model_name"),
            metrics=new_metrics,
            dataset_size=new_report.get("dataset_size", 0),
            feature_count=new_report.get("feature_count", 0),
            dataset_sources=["CIC-IDS2017", "CommunicationLogs"],
            is_active=True
        )
        reload_prediction_assets()
        return {
            "status": "Deployed",
            "message": f"New model version {version_doc.get('version')} deployed successfully (F1: {new_f1}).",
            "version": version_doc.get("version"),
            "improved": True,
            "metrics": new_metrics,
            "comparison": new_report.get("comparison")
        }
    else:
        logger.info(f"Performance did not improve (New F1: {new_f1} < Current F1: {current_f1}). Keeping existing production model.")
        return {
            "status": "Retained Previous Model",
            "message": f"Retrained model (F1: {new_f1}) performed lower than active production model (F1: {current_f1}). Existing model retained.",
            "current_version": current_active.get("version"),
            "improved": False,
            "candidate_metrics": new_metrics,
            "active_metrics": current_active
        }
