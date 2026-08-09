import os
import glob
import pandas as pd
import numpy as np
import logging
try:
    from ai.utils import DATASETS_DIR
except ImportError:
    from backend.ai.utils import DATASETS_DIR

logger = logging.getLogger(__name__)

CIC_IDS2017_DIR = os.path.join(DATASETS_DIR, 'CIC-IDS2017')
GENERATED_DIR = os.path.join(DATASETS_DIR, 'generated')

os.makedirs(CIC_IDS2017_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)

def load_cic_ids2017_dataset(max_sample_per_file=20000):
    """
    Automatically detects all CSV files in datasets/CIC-IDS2017/
    Preprocesses missing values, infinity, duplicates, and merges them into a single dataframe.
    """
    csv_files = glob.glob(os.path.join(CIC_IDS2017_DIR, "*.csv"))
    if not csv_files:
        logger.info(f"No CSV files found in {CIC_IDS2017_DIR}. Returning empty DataFrame.")
        return None

    dfs = []
    logger.info(f"Found {len(csv_files)} CSV files in {CIC_IDS2017_DIR}: {[os.path.basename(f) for f in csv_files]}")
    
    for filepath in csv_files:
        try:
            df = pd.read_csv(filepath, low_memory=False)
            df.columns = df.columns.str.strip()
            
            # Replace infinity values
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.dropna()
            df = df.drop_duplicates()
            
            if len(df) > max_sample_per_file:
                df = df.sample(n=max_sample_per_file, random_state=42)
                
            dfs.append(df)
            logger.info(f"Loaded {len(df)} records from {os.path.basename(filepath)}")
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            
    if not dfs:
        return None
        
    combined_df = pd.concat(dfs, ignore_index=True)
    combined_df = combined_df.replace([np.inf, -np.inf], np.nan).dropna()
    combined_df = combined_df.drop_duplicates()
    logger.info(f"Combined dataset total shape: {combined_df.shape}")
    return combined_df

def load_generated_application_dataset():
    """
    Loads the latest exported application communication logs CSV from datasets/generated/
    """
    csv_files = glob.glob(os.path.join(GENERATED_DIR, "*.csv"))
    if not csv_files:
        return None
    latest_file = max(csv_files, key=os.path.getctime)
    logger.info(f"Loading application dataset from {latest_file}")
    df = pd.read_csv(latest_file)
    df = df.replace([np.inf, -np.inf], np.nan).dropna().drop_duplicates()
    return df
