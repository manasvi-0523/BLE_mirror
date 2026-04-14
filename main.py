"""
BLE Behavioral Fingerprinting Security System
AI + Blockchain Prototype

Author: manasvi-0523
"""

import asyncio
import sys
import os

# Path setup
sys.path.insert(0, os.path.dirname(__file__))

from scanner.ble_scanner import scan
from feature_engine.feature_extract import load_data, extract_features, get_feature_matrix
from ai_model.anomaly_detector import train, predict, label
from blockchain.blockchain import Blockchain
from alerts.alert_system import trigger

SCAN_DURATION = 15  # seconds

async def run():
    print("=" * 60)
    print("  BLE SECURITY SYSTEM — AI + Blockchain Prototype")
    print("  github: manasvi-0523")
    print("=" * 60)

    # ── Phase 1: Scan ─────────────────────────────────────────
    print("\n[Phase 1] BLE Scanning...")
    devices = await scan(duration=SCAN_DURATION)

    if not devices:
        print("⚠️  No devices found. Make sure Bluetooth is enabled.")
        return

    # ── Phase 2: Feature Extraction ───────────────────────────
    print("[Phase 2] Extracting behavioral features...")
    raw_df = load_data()
    features_df = extract_features(raw_df)
    X = get_feature_matrix(features_df)

    if len(X) < 2:
        print("⚠️  Need at least 2 devices for anomaly detection. Scan again later.")
        return

    # ── Phase 3: AI Training + Prediction ─────────────────────
    print("[Phase 3] Training Isolation Forest model...")
    model, scaler = train(X)

    print("[Phase 3] Running anomaly detection...\n")
    predictions, scores = predict(X, model, scaler)

    # ── Phase 4: Blockchain + Alerts ──────────────────────────
    print("[Phase 4] Registering devices on blockchain...\n")
    bc = Blockchain()

    for i, row in features_df.iterrows():
        mac = row['mac']
        name = row['device_name']
        feature_vector = X[i].tolist()
        pred = predictions[i]
        score = float(scores[i])

        # Register on blockchain
        bc.add_device(mac, feature_vector)

        # Trigger alert
        trigger(mac, name, pred, score)

    # ── Verify Chain Integrity ────────────────────────────────
    print("\n[Blockchain] Verifying chain integrity...")
    bc.verify_chain()
    bc.print_chain()

    print("\n" + "=" * 60)
    print("  Scan complete. Check dataset/alerts.csv for full log.")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(run())