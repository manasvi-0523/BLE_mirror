"""
BLE Device Trust Registry - Main Entry Point
Enhanced with baseline/monitor mode separation for proper anomaly detection
"""
import asyncio
import os
import argparse
import time
import pandas as pd

from scanner.ble_scanner import SignatureScanner
from feature_engine.feature_extract import extract_features
from ai_model.anomaly_detector import BehaviorAnomalyDetector
from blockchain.blockchain import SimpleBlockchain
from alerts.alert_system import trigger_alert
from config import (
    BLE_DATA_PATH, 
    SCAN_DURATION, 
    SCAN_CYCLES_BASELINE, 
    SCAN_CYCLES_MONITOR,
    MAX_BLOCKS_DISPLAY
)

async def run_security_cycle(scanner, ai_model, blockchain, scan_duration, mode):
    """
    Execute one security monitoring cycle.
    
    Args:
        scanner: SignatureScanner instance
        ai_model: BehaviorAnomalyDetector instance
        blockchain: SimpleBlockchain instance
        scan_duration: Duration of scan in seconds
        mode: 'baseline' or 'monitor'
        
    Returns:
        list: List of anomaly dictionaries detected in this cycle
    """
    print("\n" + "#"*60)
    print(f"--- [PHASE 1] Starting Data Capture ({scan_duration}s, mode={mode}) ---")
    await scanner.run(scan_time=scan_duration)
    
    print(f"\n--- [PHASE 2] Extracting Behavioral Features ---")
    df = extract_features()
    
    if df is None or df.empty:
        print("Wait: No devices found in this cycle. Restarting...")
        return []
    
    anomalies_detected = []
    
    if mode == 'baseline':
        # BASELINE MODE: Just learn and store
        print(f"\n--- [PHASE 3] Baseline Learning Mode ---")
        print(f"Learning normal behavior from {len(df)} devices...")
        
        for index, row in df.iterrows():
            mac = row['mac_address']
            name = row['name']
            
            behavior_payload = {
                "mean_rssi": row['mean_rssi'],
                "mean_interval_ms": row['mean_interval'],
                "packet_count": row['packet_count']
            }
            
            # Add all devices to blockchain as trusted baseline
            blockchain.add_block(device_id=mac, behavior_data=behavior_payload)
            print(f"[Baseline] Device {mac} ({name}) registered as TRUSTED")
    
    elif mode == 'monitor':
        # MONITOR MODE: Detect anomalies using trained model
        if not ai_model.is_trained:
            print("[ERROR] AI model is not trained. Please run in baseline mode first!")
            return []
        
        print(f"\n--- [PHASE 3] Active Monitoring & Anomaly Detection ---")
        
        for index, row in df.iterrows():
            fingerprint_row = pd.DataFrame([row])
            mac = row['mac_address']
            name = row['name']
            
            # AI Detection
            is_anomaly = ai_model.detect(fingerprint_row, name, mac)
            
            behavior_payload = {
                "mean_rssi": row['mean_rssi'],
                "mean_interval_ms": row['mean_interval'],
                "packet_count": row['packet_count']
            }
            
            if is_anomaly:
                # PHASE 4: Trigger alerts for anomalies
                score = ai_model.get_anomaly_score(fingerprint_row)
                criticality = trigger_alert(mac, name, score)
                
                anomalies_detected.append({
                    "mac": mac,
                    "name": name,
                    "score": score,
                    "criticality": criticality
                })
            else:
                # Add normal devices to blockchain
                existing = blockchain.get_device_history(mac)
                if not existing:
                    blockchain.add_block(device_id=mac, behavior_data=behavior_payload)
                else:
                    print(f"[Blockchain] Device {mac} already verified in ledger.")
    
    print("\n[Cycle Complete] Next cycle starting in 3 seconds...")
    time.sleep(3)
    return anomalies_detected

async def baseline_mode(cycles=None):
    """
    Run in BASELINE mode: Learn what normal looks like.
    
    Args:
        cycles: Number of scan cycles (uses config default if None)
    """
    if cycles is None:
        cycles = SCAN_CYCLES_BASELINE
    
    print("="*60)
    print("   BASELINE LEARNING MODE".center(60))
    print("="*60)
    print(f"The system will scan for {cycles} cycles to establish")
    print("a trusted baseline of normal BLE device behavior.")
    print("="*60 + "\n")
    
    # Clean previous data to establish fresh baseline
    if os.path.exists(BLE_DATA_PATH):
        os.remove(BLE_DATA_PATH)
        print("[Baseline] Removed old dataset to start fresh.\n")
    
    # Initialize modules
    blockchain = SimpleBlockchain(load_from_disk=False)
    ai_model = BehaviorAnomalyDetector()
    
    # Run baseline scanning cycles
    for cycle in range(cycles):
        print(f"\n{'='*60}")
        print(f"   BASELINE CYCLE {cycle + 1}/{cycles}".center(60))
        print(f"{'='*60}")
        
        scanner = SignatureScanner()
        await run_security_cycle(scanner, ai_model, blockchain, SCAN_DURATION, mode='baseline')
    
    # Train the AI model on collected baseline data
    print("\n" + "="*60)
    print("   TRAINING AI MODEL ON BASELINE DATA".center(60))
    print("="*60)
    
    df_baseline = extract_features()
    if df_baseline is not None and not df_baseline.empty:
        success = ai_model.train(df_baseline)
        if success:
            print("\n[SUCCESS] Baseline established and model trained!")
            print(f"[SUCCESS] {len(df_baseline)} trusted devices learned.")
            print(f"[SUCCESS] Blockchain contains {len(blockchain.chain)} blocks.")
            print("\nYou can now run in MONITOR mode to detect anomalies.")
        else:
            print("\n[ERROR] Failed to train model on baseline data.")
    else:
        print("\n[ERROR] No baseline data collected. Try scanning again.")
    
    # Display blockchain summary
    print("\n--- Blockchain Trust Registry (First 5 blocks) ---")
    for block in blockchain.chain[:5]:
        print(f"Block {block.index:2} | MAC {block.device_id[:17]:17} | Hash: {block.hash[:20]}...")

async def monitor_mode(cycles=None):
    """
    Run in MONITOR mode: Detect anomalies using trained model.
    
    Args:
        cycles: Number of scan cycles (uses config default if None)
    """
    if cycles is None:
        cycles = SCAN_CYCLES_MONITOR
    
    print("="*60)
    print("   ACTIVE MONITORING MODE".center(60))
    print("="*60)
    print(f"The system will monitor for {cycles} cycles and detect")
    print("any devices behaving differently from the baseline.")
    print("="*60 + "\n")
    
    # Initialize modules
    blockchain = SimpleBlockchain(load_from_disk=True)
    ai_model = BehaviorAnomalyDetector()
    
    # Load pre-trained model
    if not ai_model.load_model():
        print("\n[ERROR] No trained model found!")
        print("Please run in BASELINE mode first to train the model:")
        print("  python main.py --mode baseline\n")
        return
    
    # Run monitoring cycles
    all_anomalies = []
    for cycle in range(cycles):
        print(f"\n{'='*60}")
        print(f"   MONITORING CYCLE {cycle + 1}/{cycles}".center(60))
        print(f"{'='*60}")
        
        scanner = SignatureScanner()
        cycle_anomalies = await run_security_cycle(scanner, ai_model, blockchain, SCAN_DURATION, mode='monitor')
        if cycle_anomalies:
            all_anomalies.extend(cycle_anomalies)
    
    # Final Security Report
    print("\n" + "="*60)
    print("   MONITORING SESSION COMPLETED".center(60))
    print("="*60)
    
    print("\n╔══════════════════════════════════════════════════╗")
    print("║            FINAL SECURITY RESULT CORNER          ║")
    print("╠══════════════════════════════════════════════════╣")
    
    if not all_anomalies:
        print("║  OVERALL STATUS: SAFE ✓                          ║")
        print("║  All devices passed behavioral verification.     ║")
    else:
        print("║  OVERALL STATUS: THREATS DETECTED ⚠               ║")
        print(f"║  Detected {len(all_anomalies)} Anomaly Event(s).                      ║")
        print("╠══════════════════════════════════════════════════╣")
        print("║  SPOOFING/ANOMALOUS DEVICE LOG:                  ║")
        
        # Remove duplicates (same MAC seen multiple times)
        unique_anomalies = {a['mac']: a for a in all_anomalies}.values()
        for dev in unique_anomalies:
            name_trunc = dev['name'][:12]
            mac_trunc = dev['mac'][:17]
            crit = dev['criticality']
            line = f"║  • {name_trunc:12} {mac_trunc:17} [{crit:6}] ║"
            print(line)
    
    print("╚══════════════════════════════════════════════════╝")
    
    # Blockchain summary
    print(f"\n--- Blockchain Ledger ({len(blockchain.chain)} blocks total) ---")
    display_count = min(MAX_BLOCKS_DISPLAY, len(blockchain.chain))
    for block in blockchain.chain[:display_count]:
        print(f"Block {block.index:2} | Device {block.device_id[:17]:17} | Hash: {block.hash[:20]}...")
    if len(blockchain.chain) > display_count:
        print(f"... [{len(blockchain.chain) - display_count} more blocks]")
    
    print(f"\nChain integrity: {'VALID ✓' if blockchain.is_chain_valid() else 'INVALID ✗'}")

def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description='BLE Device Trust Registry - AI-Powered Security System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Establish baseline (learn normal behavior)
  python main.py --mode baseline
  
  # Monitor for anomalies (requires trained model)
  python main.py --mode monitor
  
  # Custom cycle counts
  python main.py --mode baseline --cycles 3
  python main.py --mode monitor --cycles 10
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['baseline', 'monitor'],
        required=True,
        help='Operation mode: baseline (learn) or monitor (detect)'
    )
    
    parser.add_argument(
        '--cycles',
        type=int,
        default=None,
        help='Number of scan cycles (default: 2 for baseline, 5 for monitor)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'baseline':
            asyncio.run(baseline_mode(cycles=args.cycles))
        elif args.mode == 'monitor':
            asyncio.run(monitor_mode(cycles=args.cycles))
    except KeyboardInterrupt:
        print("\n\n[System Guard] Process safely terminated by user.")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
