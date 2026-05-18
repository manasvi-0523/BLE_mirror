"""
Feature extraction - now delegates to the SQLite device registry.
The CSV path is kept for legacy / offline analysis only.
"""

import pandas as pd
import numpy as np
import os

DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'ble_data.csv')

# 12 history-aware features (matches db.registry.FEATURE_ORDER)
FEATURE_COLS = [
    'scan_count', 'mean_rssi', 'std_rssi', 'min_rssi', 'max_rssi',
    'rssi_slope', 'mean_payload', 'std_payload', 'mean_services',
    'scan_frequency', 'uuid_change_rate', 'mac_rotation_count',
]


def load_data() -> pd.DataFrame:
    """Load raw scan CSV (legacy / offline use)."""
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(
            f"No dataset found at {DATASET_PATH}. Run the scanner first.")
    try:
        df = pd.read_csv(DATASET_PATH, encoding='utf-8',
                         encoding_errors='replace', on_bad_lines='skip')
    except UnicodeDecodeError:
        df = pd.read_csv(DATASET_PATH, encoding='cp1252',
                         encoding_errors='replace', on_bad_lines='skip')

    if 'scan_type' not in df.columns:
        df['scan_type'] = 'BLE'
    for col, default in [('tx_power', -1), ('company_id', -1), ('is_random_mac', 0)]:
        if col not in df.columns:
            df[col] = default

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Legacy CSV-based feature extraction (single-scan snapshot).
    Prefer db.registry.build_training_matrix() for reliable multi-scan features.
    """
    for col, default in [('tx_power', -1), ('company_id', -1), ('is_random_mac', 0)]:
        if col not in df.columns:
            df[col] = default

    grouped = df.groupby('mac').agg(
        device_name=('name', lambda x: x.mode()[0] if not x.empty else 'Unknown'),
        mean_rssi=('rssi', 'mean'),
        std_rssi=('rssi', 'std'),
        min_rssi=('rssi', 'min'),
        max_rssi=('rssi', 'max'),
        mean_payload=('payload_size', 'mean'),
        std_payload=('payload_size', 'std'),
        mean_services=('service_count', 'mean'),
        scan_count=('mac', 'count'),
        mean_interval=('interval_ms', 'mean'),
        mean_tx_power=('tx_power', 'mean'),
        has_company_id=('company_id', lambda x: int((x != -1).any())),
        random_mac_ratio=('is_random_mac', 'mean'),
    ).reset_index()

    grouped.fillna(0, inplace=True)
    print(f"[OK] Features extracted for {len(grouped)} device(s).\n")
    return grouped


def get_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    """Legacy: extract numeric matrix from a features DataFrame."""
    legacy_cols = ['mean_rssi', 'std_rssi', 'min_rssi', 'max_rssi',
                   'mean_payload', 'std_payload', 'mean_services',
                   'scan_count', 'mean_interval',
                   'mean_tx_power', 'has_company_id', 'random_mac_ratio']
    available = [c for c in legacy_cols if c in df.columns]
    return df[available].values


if __name__ == '__main__':
    raw      = load_data()
    features = extract_features(raw)
    print(features[['mac', 'device_name', 'mean_rssi',
                     'mean_payload', 'mean_services', 'scan_count']])
