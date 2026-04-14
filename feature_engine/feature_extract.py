import pandas as pd
import numpy as np
import os

def extract_features(csv_path="dataset/ble_data.csv"):
    if not os.path.exists(csv_path):
        print(f"Dataset not found at {csv_path}. Please run BLE scanner first.")
        return None
        
    df = pd.read_csv(csv_path)
    if df.empty:
        print("Dataset is empty.")
        return None
        
    print(f"Loaded {len(df)} raw data points.")
    
    # Handle possible NaN in interval (which might happen on the first detection packet)
    df['interval_ms'] = df['interval_ms'].fillna(0)
    
    features = []
    
    # Create Behavioral Fingerprint for each device
    for mac, group in df.groupby('mac_address'):
        mean_rssi = group['rssi'].mean()
        mean_interval = group['interval_ms'].mean()
        std_interval = group['interval_ms'].std()
        
        # If std is NaN (only 1 packet collected), fill with 0
        if np.isnan(std_interval):
            std_interval = 0
            
        packet_count = len(group)
        services = group['services_count'].max() # services typically static
        name = group['name'].iloc[0]
        
        features.append({
            'mac_address': mac,
            'mean_rssi': round(mean_rssi, 2),
            'mean_interval': round(mean_interval, 2),
            'std_interval': round(std_interval, 2),
            'packet_count': packet_count,
            'services_count': services,
            'name': name
        })
        
    features_df = pd.DataFrame(features)
    print(f"Extracted behavioral features for {len(features_df)} unique devices.")
    return features_df

if __name__ == "__main__":
    # Test path handling locally
    path = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'ble_data.csv')
    features_df = extract_features(path)
    if features_df is not None:
        print("\n--- Device Behavioral Fingerprints ---")
        # Display the formatted features
        print(features_df.to_string(index=False))
