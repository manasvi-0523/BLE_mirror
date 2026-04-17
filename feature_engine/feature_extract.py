import pandas as pd
import numpy as np
import os

DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'ble_data.csv')

FEATURE_COLS = ['rssi', 'interval_ms', 'payload_size', 'service_count', 'scan_type']

def load_data() -> pd.DataFrame:
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"No dataset found at {DATASET_PATH}. Run the scanner first.")
    df = pd.read_csv(DATASET_PATH, encoding='utf-8')
    # Backwards compatibility: add scan_type if missing (old CSV format)
    if 'scan_type' not in df.columns:
        df['scan_type'] = 'BLE'
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate per-device behavioral signature from raw scan records.
    Each device gets a single feature vector.
    """
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
    ).reset_index()

    # Fill NaN std values (single scan devices)
    grouped.fillna(0, inplace=True)

    print(f"[OK] Features extracted for {len(grouped)} device(s).\n")
    return grouped

def get_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    """Returns numeric-only feature matrix for ML input."""
    numeric_cols = ['mean_rssi', 'std_rssi', 'min_rssi', 'max_rssi',
                    'mean_payload', 'std_payload', 'mean_services',
                    'scan_count', 'mean_interval']
    return df[numeric_cols].values

if __name__ == '__main__':
    raw = load_data()
    features = extract_features(raw)
    print(features[['mac', 'device_name', 'mean_rssi', 'mean_payload', 'mean_services', 'scan_count']])