"""
BLE Security Dashboard — Flask Backend
Authors: manasvi-0523, Mithun Gowda B (@mithun50)
"""
"""

from flask import Flask, jsonify, render_template
import pandas as pd
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

app = Flask(__name__)

BASE = r'C:\Users\Lenovo\Desktop\ble_claude'
BLE_CSV    = os.path.join(BASE, 'dataset', 'ble_data.csv')
ALERTS_CSV = os.path.join(BASE, 'dataset', 'alerts.csv')
CHAIN_JSON = os.path.join(BASE, 'blockchain', 'chain.json')

def safe_read_csv(path, fallback_cols):
    if not os.path.exists(path):
        return pd.DataFrame(columns=fallback_cols)
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame(columns=fallback_cols)

# ── API Routes ────────────────────────────────────────────────

@app.route('/api/summary')
def summary():
    ble    = safe_read_csv(BLE_CSV,    ['mac','name','rssi','service_count','payload_size','timestamp'])
    alerts = safe_read_csv(ALERTS_CSV, ['mac','device_name','status','score','timestamp','action'])

    total_devices   = ble['mac'].nunique() if not ble.empty else 0
    total_scans     = len(ble)
    total_anomalies = len(alerts[alerts['status'] == 'ANOMALY']) if not alerts.empty else 0
    total_normal    = len(alerts[alerts['status'] == 'NORMAL'])  if not alerts.empty else 0

    chain_blocks = 0
    if os.path.exists(CHAIN_JSON):
        with open(CHAIN_JSON) as f:
            chain_blocks = len(json.load(f))

    return jsonify({
        'total_devices':   total_devices,
        'total_scans':     total_scans,
        'total_anomalies': total_anomalies,
        'total_normal':    total_normal,
        'chain_blocks':    chain_blocks,
    })

@app.route('/api/devices')
def devices():
    ble = safe_read_csv(BLE_CSV, ['mac','name','rssi','service_count','payload_size','timestamp'])
    if ble.empty:
        return jsonify([])
    latest = ble.sort_values('timestamp').groupby('mac').last().reset_index()
    return jsonify(latest[['mac','name','rssi','service_count','payload_size','timestamp']].to_dict(orient='records'))

@app.route('/api/alerts')
def alerts():
    df = safe_read_csv(ALERTS_CSV, ['mac','device_name','status','score','timestamp','action'])
    if df.empty:
        return jsonify([])
    df = df.sort_values('timestamp', ascending=False).head(50)
    return jsonify(df.to_dict(orient='records'))

@app.route('/api/rssi_trend')
def rssi_trend():
    ble = safe_read_csv(BLE_CSV, ['mac','name','rssi','timestamp'])
    if ble.empty:
        return jsonify([])
    ble['timestamp'] = pd.to_datetime(ble['timestamp'])
    ble = ble.sort_values('timestamp')
    # Return last 60 scan points across all devices
    recent = ble.tail(60)
    return jsonify(recent[['timestamp','mac','name','rssi']].assign(
        timestamp=recent['timestamp'].astype(str)
    ).to_dict(orient='records'))

@app.route('/api/blockchain')
def blockchain():
    if not os.path.exists(CHAIN_JSON):
        return jsonify([])
    with open(CHAIN_JSON) as f:
        chain = json.load(f)
    return jsonify(chain[-20:])  # last 20 blocks

@app.route('/api/anomaly_stats')
def anomaly_stats():
    df = safe_read_csv(ALERTS_CSV, ['mac','device_name','status','score','timestamp'])
    if df.empty:
        return jsonify({'labels': ['Normal', 'Anomaly'], 'values': [0, 0]})
    counts = df['status'].value_counts()
    return jsonify({
        'labels': counts.index.tolist(),
        'values': counts.values.tolist()
    })

# ── Frontend ──────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    print("\n🚀 BLE Dashboard running at http://localhost:5000\n")
    app.run(debug=True, port=5000)