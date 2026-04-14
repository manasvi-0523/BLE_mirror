import asyncio
import os
import pandas as pd
import time

from scanner.ble_scanner import SignatureScanner
from feature_engine.feature_extract import extract_features
from ai_model.anomaly_detector import BehaviorAnomalyDetector
from blockchain.blockchain import SimpleBlockchain
from alerts.alert_system import trigger_alert

async def run_security_cycle(scanner, ai_model, blockchain, scan_duration=10):
    print("\n" + "#"*60)
    print(f"--- [PHASE 1] Starting Data Capture Cycle ({scan_duration}s) ---")
    await scanner.run(scan_time=scan_duration)
    
    print(f"\n--- [PHASE 2] Extracting Behavioral Features ---")
    dataset_path = os.path.join(os.path.dirname(__file__), 'dataset', 'ble_data.csv')
    df = extract_features(dataset_path)
    
    if df is None or df.empty:
        print("Wait: No devices found in this cycle. Restarting...")
        return
        
    print(f"\n--- [PHASE 3 & 4] AI Detection & Blockchain Registry ---")
    
    anomalies_detected = []
    for index, row in df.iterrows():
        fingerprint_row = pd.DataFrame([row])
        mac = row['mac_address']
        name = row['name']
        
        # AI Detection
        is_anomaly = ai_model.detect(fingerprint_row, name, mac)
        
        # Extract the behavioral blueprint dict
        behavior_payload = {
            "mean_rssi": row['mean_rssi'],
            "mean_interval_ms": row['mean_interval'],
            "packet_count": row['packet_count']
        }
        
        if is_anomaly:
            # PHASE 5: Alerts
            score = ai_model.model.decision_function(fingerprint_row[ai_model.features])[0]
            trigger_alert(mac, name, score)
            
            # Categorize Criticality
            criticality = "LOW"
            if score < -0.2: criticality = "HIGH"
            elif score < -0.1: criticality = "MEDIUM"
            
            anomalies_detected.append({
                "mac": mac,
                "name": name,
                "score": score,
                "criticality": criticality
            })
        else:
            # Add to blockchain
            # Avoid re-adding if it's already in the chain
            existing = blockchain.get_device_history(mac)
            if not existing:
                blockchain.add_block(device_id=mac, behavior_data=behavior_payload)
            else:
                print(f"[Blockchain] Device {mac} already verified in ledger. Skipping.")
                
    print("\n[Cycle Complete] Next cycle starting in 5 seconds...")
    time.sleep(5)
    return anomalies_detected

async def main():
    print("==================================================")
    print("      BLE DEVICE TRUST REGISTRY STARTING...       ")
    print("==================================================")
    
    # Initialize Core Modules
    blockchain = SimpleBlockchain()
    ai_model = BehaviorAnomalyDetector(contamination=0.1)
    dataset_path = os.path.join(os.path.dirname(__file__), 'dataset', 'ble_data.csv')
    
    # We will use exactly one file to keep state within the demo lifecycle
    # Pre-train the AI if possible
    df_train = extract_features(dataset_path)
    if df_train is not None:
        ai_model.train(df_train)
    else:
        print("[WARNING] No previous dataset found. Real-time data will establish the baseline.")
        # Without data, anomaly detection crashes. So we need to train on cycle 1.
        
    # Main continuous loop
    # For prototype demo, we run it for 2 cycles
    all_anomalies = []
    for cycle in range(2):
        print(f"\n>>>> SECURITY CYCLE: {cycle + 1}/2 <<<<")
        scanner = SignatureScanner() # fresh scanner
        
        cycle_anomalies = await run_security_cycle(scanner, ai_model, blockchain, scan_duration=10)
        if cycle_anomalies:
            all_anomalies.extend(cycle_anomalies)
        
        # If AI wasn't trained because there was no data on boot, train it after cycle 1
        if not ai_model.is_trained:
            df_train = extract_features(dataset_path)
            if df_train is not None:
               ai_model.train(df_train)
        
    print("\n==================================================")
    print("      BLE TRUST REGISTRY DEMO COMPLETED           ")
    print("==================================================")
    print("\nFinal Blockchain Ledger:")
    for b in blockchain.chain[:5]: # print first 5 to not spam the console
        print(f"Block {b.index:2} | MAC {b.device_id[:17]:17} | Hash: {b.hash[:20]}...")
    if len(blockchain.chain) > 5:
        print("... [Truncated]")

    print("\n╔══════════════════════════════════════════════════╗")
    print("║            FINAL SECURITY RESULT CORNER          ║")
    print("╠══════════════════════════════════════════════════╣")
    if not all_anomalies:
        print("║  OVERALL STATUS: SAFE [OK]                       ║")
        print("║  All devices passed behavioral verification.     ║")
    else:
        print("║  OVERALL STATUS: NOT SAFE [CRITICAL]             ║")
        print(f"║  Detected {len(all_anomalies)} Anomaly Event(s).                 ║")
        print("╠══════════════════════════════════════════════════╣")
        print("║  SPOOFING DEVICE LOG:                            ║")
        # Ensure we don't print duplicates of the same device found in different cycles
        unique_anomalies = {a['mac']: a for a in all_anomalies}.values()
        for dev in unique_anomalies:
            line = f"║  • {dev['name'][:10]} ({dev['mac']}) -> {dev['criticality']} ║"
            print(line.ljust(51) + "║")
    print("╚══════════════════════════════════════════════════╝\n")

if __name__ == "__main__":
    # Remove older dataset if it exists to make demo extremely clean
    dataset_path = os.path.join(os.path.dirname(__file__), 'dataset', 'ble_data.csv')
    if os.path.exists(dataset_path):
        os.remove(dataset_path)
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[System Guard] Process safely terminated by user.")
