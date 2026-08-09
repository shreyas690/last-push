import os
import csv
import logging
from datetime import datetime, timezone
try:
    from ai.utils import DATASETS_DIR
except ImportError:
    from backend.ai.utils import DATASETS_DIR

logger = logging.getLogger(__name__)

GENERATED_DIR = os.path.join(DATASETS_DIR, 'generated')

def export_communication_logs_to_csv():
    """
    Exports REAL MongoDB CommunicationLogs collection records into datasets/generated/ communication_logs_YYYY.csv.
    If no communication data exists, returns appropriate message.
    """
    from app.models.communication_log import CommunicationLogModel
    
    logs = CommunicationLogModel.get_all_logs()
    if not logs:
        return {"success": False, "message": "No communication data available."}
        
    os.makedirs(GENERATED_DIR, exist_ok=True)
    filename = f"communication_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(GENERATED_DIR, filename)
    
    fieldnames = [
        "sender", "receiver", "timestamp", "packetSize", "messageLength",
        "encryptionTime", "decryptionTime", "sha3Verification", "authTagValidation",
        "nonceReused", "replayCount", "packetModified", "authenticationResult",
        "deliveryStatus", "readStatus", "packetInterval", "connectionDuration",
        "failedLoginAttempts", "threatPrediction", "confidenceScore", "riskLevel"
    ]
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for log in logs:
                row = {k: log.get(k, '') for k in fieldnames}
                writer.writerow(row)
                
        logger.info(f"Exported {len(logs)} communication log records to {filepath}")
        return {
            "success": True,
            "filename": filename,
            "filepath": filepath,
            "recordCount": len(logs),
            "message": f"Successfully exported {len(logs)} communication records to datasets/generated/{filename}"
        }
    except Exception as e:
        logger.error(f"Error exporting communication logs: {e}")
        return {"success": False, "error": str(e)}
