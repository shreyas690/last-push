import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Feature Definition Mapping Layer
PUBLIC_DATASET_FEATURES = [
    'Destination Port', 'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
    'Total Length of Fwd Packets', 'Total Length of Bwd Packets', 'Fwd Packet Length Max',
    'Fwd Packet Length Min', 'Flow Bytes/s', 'Flow Packets/s', 'Flow IAT Mean',
    'Fwd IAT Mean', 'Bwd IAT Mean', 'Active Mean', 'Idle Mean'
]

APPLICATION_FEATURES = [
    'packetSize', 'messageLength', 'encryptionTime', 'decryptionTime',
    'sha3Verification', 'authTagValidation', 'nonceReused', 'replayCount',
    'packetModified', 'failedLoginAttempts', 'packetInterval', 'connectionDuration'
]

COMMON_FEATURES = [
    'packetSize', 'packetInterval', 'failedLoginAttempts', 'authFailures', 'sequenceDiff'
]

def extract_features_from_packet(packet_data):
    """
    Extracts numerical feature vector from a real live communication event dictionary.
    """
    packet_size = int(packet_data.get('packetSize', 0))
    message_length = int(packet_data.get('messageLength', len(packet_data.get('plaintext', '')) or 1))
    encryption_time = float(packet_data.get('encryptionTime', 0.5))
    decryption_time = float(packet_data.get('decryptionTime', 0.5))
    sha3_verification = 1 if packet_data.get('sha3Verification', True) else 0
    auth_tag_validation = 1 if packet_data.get('authTagValidation', True) else 0
    nonce_reused = 1 if packet_data.get('nonceReused', False) else 0
    replay_count = int(packet_data.get('replayCount', 0))
    packet_modified = 1 if packet_data.get('packetModified', False) else 0
    failed_login_attempts = int(packet_data.get('failedLoginAttempts', 0))
    packet_interval = float(packet_data.get('packetInterval', 100.0))
    connection_duration = float(packet_data.get('connectionDuration', 10.0))
    
    feature_dict = {
        'packetSize': packet_size,
        'messageLength': message_length,
        'encryptionTime': encryption_time,
        'decryptionTime': decryption_time,
        'sha3Verification': sha3_verification,
        'authTagValidation': auth_tag_validation,
        'nonceReused': nonce_reused,
        'replayCount': replay_count,
        'packetModified': packet_modified,
        'failedLoginAttempts': failed_login_attempts,
        'packetInterval': packet_interval,
        'connectionDuration': connection_duration
    }
    return feature_dict

def adapt_cic_ids2017_df(df):
    """
    Adapts CIC-IDS2017 DataFrame columns to standard names and label targets.
    """
    df = df.copy()
    label_col = None
    for col in df.columns:
        if col.lower() == 'label':
            label_col = col
            break
            
    if label_col is None:
        raise ValueError("No 'Label' column found in dataset.")
        
    # Standardize label values
    df['Label_Clean'] = df[label_col].astype(str).str.strip().apply(
        lambda x: 'BENIGN' if 'benign' in x.lower() else 'ATTACK'
    )
    return df
