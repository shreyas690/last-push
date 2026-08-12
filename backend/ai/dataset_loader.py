import os
import glob
import pandas as pd
import numpy as np
import logging
from app.models.communication_log import CommunicationLogModel
from app.models.security_test_result import SecurityTestResultModel
try:
    from ai.utils import DATASETS_DIR
    from ai.label_mapping import map_raw_label_to_target
except ImportError:
    from backend.ai.utils import DATASETS_DIR
    from backend.ai.label_mapping import map_raw_label_to_target

logger = logging.getLogger(__name__)

CIC_IDS2017_DIR = os.path.join(DATASETS_DIR, 'CIC-IDS2017')
GENERATED_DIR = os.path.join(DATASETS_DIR, 'generated')

os.makedirs(CIC_IDS2017_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

def load_cic_ids2017_dataset(max_sample_per_file=20000):
    """
    Loads manually imported CSV files in datasets/CIC-IDS2017/
    Combines them with real MongoDB CommunicationLogs and controlled Security Evaluation events.
    NO AUTOMATIC SYNTHETIC BASELINE DATA IS EVER GENERATED.
    """
    csv_files = glob.glob(os.path.join(CIC_IDS2017_DIR, "*.csv"))
    dfs = []

    # 1. Load manually imported CIC-IDS2017 CSV files
    if csv_files:
        logger.info(f"Found {len(csv_files)} imported CSV files: {[os.path.basename(f) for f in csv_files]}")
        for filepath in csv_files:
            try:
                df = pd.read_csv(filepath, low_memory=False)
                df.columns = df.columns.str.strip()
                df = df.replace([np.inf, -np.inf], np.nan).dropna().drop_duplicates()
                
                # Identify label column
                label_col = None
                for col in ['Label', 'label', 'Attack', 'Label_Clean']:
                    if col in df.columns:
                        label_col = col
                        break

                if label_col:
                    mapped_labels = []
                    for val in df[label_col]:
                        target_cls, _ = map_raw_label_to_target(val, {"data_source": "CIC-IDS2017"})
                        mapped_labels.append(target_cls)
                    df['Target_Label'] = mapped_labels
                    df['data_source'] = "CIC-IDS2017"

                    if len(df) > max_sample_per_file:
                        df = df.sample(n=max_sample_per_file, random_state=42)

                    dfs.append(df)
                    logger.info(f"Loaded {len(df)} records from {os.path.basename(filepath)}")
            except Exception as e:
                logger.error(f"Error loading {filepath}: {e}")

    # 2. Merge real MongoDB live communication logs
    try:
        comm_logs = list(CommunicationLogModel.get_collection().find({}, {"_id": 0}))
        if comm_logs:
            comm_df = pd.DataFrame(comm_logs)
            mapped_labels = []
            for _, row in comm_df.iterrows():
                target_cls, _ = map_raw_label_to_target("benign", {
                    "data_source": "Live Application",
                    "packetModified": row.get("packetModified", False),
                    "nonceReused": row.get("nonceReused", False),
                    "replayCount": row.get("replayCount", 0),
                    "authTagValidation": row.get("authTagValidation", True),
                    "sha3Verification": row.get("sha3Verification", True)
                })
                mapped_labels.append(target_cls)
            comm_df['Target_Label'] = mapped_labels
            comm_df['data_source'] = "Live Application"
            dfs.append(comm_df)
            logger.info(f"Merged {len(comm_df)} real live application communication logs.")
    except Exception as e:
        logger.warning(f"Could not load live communication logs: {e}")

    # 3. Merge real MongoDB security test evaluation events
    try:
        sec_logs = list(SecurityTestResultModel.get_collection().find({}, {"_id": 0}))
        if sec_logs:
            sec_df = pd.DataFrame(sec_logs)
            mapped_labels = []
            for _, row in sec_df.iterrows():
                attack_type = row.get("attackType", "")
                target_cls, _ = map_raw_label_to_target(attack_type, {"data_source": "Security Evaluation"})
                mapped_labels.append(target_cls)
            sec_df['Target_Label'] = mapped_labels
            sec_df['data_source'] = "Security Evaluation"
            dfs.append(sec_df)
            logger.info(f"Merged {len(sec_df)} real security evaluation test events.")
    except Exception as e:
        logger.warning(f"Could not load security evaluation test events: {e}")

    if not dfs:
        logger.info("No CSV datasets or live application records found.")
        return None

    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df = combined_df.replace([np.inf, -np.inf], np.nan).dropna(subset=['Target_Label']).drop_duplicates()
    logger.info(f"Combined total real dataset shape: {combined_df.shape}")
    return combined_df
