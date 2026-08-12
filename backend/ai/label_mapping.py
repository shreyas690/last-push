"""
Label Mapping Layer & Data Provenance Tracking
Maps raw dataset labels (CIC-IDS2017, live application logs, controlled security evaluation events)
to the 4 required application threat categories:
1. BENIGN / Normal
2. Suspicious Anomaly
3. Replay Attack
4. Tampering Attempt
"""

TARGET_CLASSES = [
    "BENIGN / Normal",
    "Suspicious Anomaly",
    "Replay Attack",
    "Tampering Attempt"
]

# Configurable label mapping strategy
CIC_IDS2017_BENIGN_LABELS = {"benign", "normal"}

def map_raw_label_to_target(raw_label, provenance=None):
    """
    Transparently maps a raw label string or metadata dictionary to one of the 4 target classes.
    """
    if provenance is None:
        provenance = {}

    data_source = provenance.get("data_source", "CIC-IDS2017")
    
    # 1. Controlled Security Evaluation / Live App Logs with explicit tampering indicators
    if provenance.get("packetModified") or provenance.get("authTagValidation") == False or provenance.get("sha3Verification") == False or str(raw_label).lower() in ["tampering", "tampering attempt"]:
        return "Tampering Attempt", {
            "data_source": data_source,
            "dataset_type": "Security Test" if data_source == "Security Evaluation" else "Communication Log",
            "label_source": "Application Integrity Check"
        }

    # 2. Controlled Security Evaluation / Live App Logs with explicit replay indicators
    if provenance.get("nonceReused") or provenance.get("replayCount", 0) > 0 or str(raw_label).lower() in ["replay", "replay attack"]:
        return "Replay Attack", {
            "data_source": data_source,
            "dataset_type": "Security Test" if data_source == "Security Evaluation" else "Communication Log",
            "label_source": "Replay Detector Flag"
        }

    # 3. CIC-IDS2017 Network Dataset mapping
    raw_str = str(raw_label).strip().lower()
    if raw_str in CIC_IDS2017_BENIGN_LABELS or raw_str == "benign / normal":
        return "BENIGN / Normal", {
            "data_source": data_source,
            "dataset_type": "Public Dataset" if data_source == "CIC-IDS2017" else "Communication Log",
            "label_source": "Dataset Label"
        }
    else:
        # Network attack categories (DoS, PortScan, BruteForce, Botnet, Infiltration, etc.)
        return "Suspicious Anomaly", {
            "data_source": data_source,
            "dataset_type": "Public Dataset" if data_source == "CIC-IDS2017" else "Communication Log",
            "label_source": "Dataset Attack Category"
        }
