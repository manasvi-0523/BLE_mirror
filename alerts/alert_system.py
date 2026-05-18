"""
Alert engine for BLE Security System.

Output format matches the research paper:
  [TRUSTED] MAC | Name | RSSI       - device cleared all 3 gates
  ** ALERT: UNKNOWN DEVICE **       - not in Ethereum registry
  [!!ANOMALY!!] Duplicate MAC:      - MAC cloning detected
  [AI ALERT] Anomaly score: X.XXX  - AI behavioral outlier
"""
import os
import csv
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'alerts.csv')

ALERT_FIELDS = [
    'timestamp', 'mac', 'device_name', 'status',
    'score', 'risk_score', 'risk_level', 'reason', 'action'
]


def ensure_log():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    if not os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=ALERT_FIELDS)
            writer.writeheader()


def alert_unknown_device(mac: str, name: str, rssi: int):
    """
    Gate 1 (Ethereum registry) miss - device not in on-chain whitelist.
    Paper output format:
        ** ALERT: UNKNOWN DEVICE **
         MAC  : AA:BB:CC:DD:EE:FF
         Name : Unknown Device
         RSSI : -72 dBm
    """
    ensure_log()
    ts = datetime.now().isoformat()
    print(f"\n** ALERT: UNKNOWN DEVICE **")
    print(f"   MAC  : {mac}")
    print(f"   Name : {name or 'Unknown'}")
    print(f"   RSSI : {rssi} dBm" if rssi and rssi != -1 else "   RSSI : N/A")
    print()

    record = {
        'timestamp':   ts,
        'mac':         mac,
        'device_name': name or 'Unknown',
        'status':      'UNKNOWN',
        'score':       '',
        'risk_score':  '',
        'risk_level':  'HIGH',
        'reason':      'Not in Ethereum on-chain registry',
        'action':      'ALERT',
    }
    with open(LOG_PATH, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=ALERT_FIELDS)
        writer.writerow(record)
    return record


def alert_duplicate_mac(mac: str, rssi_list: list):
    """
    Gate 2 (Duplicate MAC detector) hit - paper output format:
        [!!ANOMALY!!] Duplicate MAC detected: AA:BB:CC:DD:EE:FF
         RSSI readings: [-42, -87]
         -> Possible MAC spoofing or relay attack
    """
    ensure_log()
    ts = datetime.now().isoformat()
    print(f"[!!ANOMALY!!] Duplicate MAC detected: {mac}")
    print(f"   RSSI readings: {rssi_list}")
    print(f"   -> Possible MAC spoofing or relay attack")

    record = {
        'timestamp':   ts,
        'mac':         mac,
        'device_name': '',
        'status':      'DUPLICATE_MAC',
        'score':       '',
        'risk_score':  1.0,
        'risk_level':  'HIGH',
        'reason':      f"Duplicate MAC: {len(rssi_list)} RSSI readings {rssi_list}",
        'action':      'BLOCK',
    }
    with open(LOG_PATH, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=ALERT_FIELDS)
        writer.writerow(record)
    return record


def alert_cleared(mac: str, name: str, rssi: int):
    """
    Device passed all 3 gates - paper output:
        [TRUSTED] AA:BB:CC:DD:EE:FF | Name | RSSI:-42
    """
    rssi_str = f"{rssi} dBm" if rssi and rssi != -1 else "N/A"
    print(f"[TRUSTED] {mac} | {name or 'Unknown'} | RSSI:{rssi_str}")


def trigger(mac: str, device_name: str, prediction: int, score: float,
            risk_score: float = None, reason: str = ''):
    """
    AI layer (Gate 3) result - anomaly or CLEARED.
    Paper output:
      Anomaly: [AI ALERT] Anomaly score: -0.123 -> Behavioral outlier detected!
      Normal:  [TRUSTED] MAC | Name | RSSI
    """
    ensure_log()
    is_anomaly = prediction == -1
    status = "ANOMALY" if is_anomaly else "NORMAL"
    action = "BLOCK" if is_anomaly else "ALLOW"

    if risk_score is not None:
        if risk_score >= 0.7:
            risk_level = "HIGH"
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
    else:
        risk_level = "N/A"

    record = {
        'timestamp':   datetime.now().isoformat(),
        'mac':         mac,
        'device_name': device_name,
        'status':      status,
        'score':       round(score, 4),
        'risk_score':  round(risk_score, 3) if risk_score is not None else '',
        'risk_level':  risk_level,
        'reason':      reason,
        'action':      action,
    }

    with open(LOG_PATH, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=ALERT_FIELDS)
        writer.writerow(record)

    if is_anomaly:
        print(f"\n[AI ALERT] Anomaly score: {score:.4f} -> Behavioral outlier detected!")
        print(f"   Device  : {device_name} ({mac})")
        print(f"   Risk    : {risk_level}" + (f" ({risk_score:.3f})" if risk_score is not None else ""))
        print(f"   Reason  : {reason}")
        print(f"   Action  : {action}\n")
    else:
        print(f"[OK] {device_name} ({mac}) | Score: {score:.4f} | Risk: {risk_level}")

    return record
