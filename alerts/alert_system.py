import time
import csv
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ALERTS_PATH, ALERT_CRITICALITY_HIGH, ALERT_CRITICALITY_MEDIUM

def trigger_alert(mac, device_name, score, write_to_log=True):
    """
    Triggers a visual (and programmatic console) alert when an anomaly is detected.
    
    Args:
        mac: MAC address of the anomalous device
        device_name: Name of the device
        score: Anomaly score from the model (more negative = more anomalous)
        write_to_log: If True, write alert to CSV log file
    """
    # Determine criticality level
    if score < ALERT_CRITICALITY_HIGH:
        criticality = "HIGH"
    elif score < ALERT_CRITICALITY_MEDIUM:
        criticality = "MEDIUM"
    else:
        criticality = "LOW"
    
    print("\n" + "="*50)
    print("! SECURITY ALERT: ANOMALOUS DEVICE DETECTED !".center(50))
    print("="*50)
    print(f"Time          : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Device Name   : {device_name}")
    print(f"MAC Address   : {mac}")
    print(f"Anomaly Score : {score:.3f}")
    print(f"Criticality   : {criticality}")
    print("="*50)
    print("ACTION: Device blocked from Blockchain Identity Registry.\n")
    
    # Write to persistent alert log
    if write_to_log:
        _write_alert_to_log(mac, device_name, score, criticality)
    
    return criticality

def _write_alert_to_log(mac, device_name, score, criticality):
    """
    Write alert information to a CSV log file for historical tracking.
    
    Args:
        mac: MAC address
        device_name: Device name
        score: Anomaly score
        criticality: Criticality level (LOW/MEDIUM/HIGH)
    """
    try:
        alerts_file = str(ALERTS_PATH)
        os.makedirs(os.path.dirname(alerts_file), exist_ok=True)
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(alerts_file)
        
        with open(alerts_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'mac_address', 'device_name', 'anomaly_score', 'criticality'])
            
            writer.writerow([
                time.strftime('%Y-%m-%d %H:%M:%S'),
                mac,
                device_name,
                f"{score:.3f}",
                criticality
            ])
    except Exception as e:
        print(f"[Alert] Warning: Failed to write to alert log: {e}")

def get_alert_history(limit=None):
    """
    Retrieve alert history from the log file.
    
    Args:
        limit: Maximum number of recent alerts to return (None for all)
        
    Returns:
        list: List of alert dictionaries, or empty list if no alerts
    """
    alerts_file = str(ALERTS_PATH)
    
    if not os.path.exists(alerts_file):
        return []
    
    try:
        import pandas as pd
        df = pd.read_csv(alerts_file)
        
        if limit:
            df = df.tail(limit)
        
        return df.to_dict('records')
    except Exception as e:
        print(f"[Alert] Error reading alert history: {e}")
        return []

if __name__ == "__main__":
    # Test Alert
    print("Testing alert system...\n")
    trigger_alert("00:11:22:33:44:55", "Spoofed_JioSTB", -0.452)
    trigger_alert("AA:BB:CC:DD:EE:FF", "Unknown_Device", -0.156)
    trigger_alert("11:22:33:44:55:66", "Suspicious_Phone", -0.089)
    
    print("\n--- Alert History ---")
    history = get_alert_history()
    for alert in history:
        print(alert)
