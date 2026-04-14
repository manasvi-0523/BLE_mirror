import os
import csv
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'alerts.csv')

ALERT_FIELDS = ['timestamp', 'mac', 'device_name', 'status', 'score', 'action']

def ensure_log():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=ALERT_FIELDS)
            writer.writeheader()

def trigger(mac: str, device_name: str, prediction: int, score: float):
    ensure_log()
    is_anomaly = prediction == -1
    status = "ANOMALY" if is_anomaly else "NORMAL"
    action = "BLOCK" if is_anomaly else "ALLOW"

    record = {
        'timestamp': datetime.now().isoformat(),
        'mac': mac,
        'device_name': device_name,
        'status': status,
        'score': round(score, 4),
        'action': action
    }

    with open(LOG_PATH, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=ALERT_FIELDS)
        writer.writerow(record)

    if is_anomaly:
        print(f"\n🚨 ALERT TRIGGERED")
        print(f"   Device  : {device_name} ({mac})")
        print(f"   Status  : {status}")
        print(f"   Score   : {score:.4f}")
        print(f"   Action  : {action}")
        print(f"   Time    : {record['timestamp']}\n")
    else:
        print(f"✅ {device_name} ({mac}) — {status} | Score: {score:.4f}")

    return record