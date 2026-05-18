"""
BLE Device Trust Registry: A Blockchain-Based Approach to
Bluetooth Classic and Low Energy Security

Defense-in-depth pipeline (Paper Figure 5):
  Gate 1 - Ethereum on-chain trust registry  (Blockchain Registry Check)
  Gate 2 - Duplicate MAC detection           (Duplicate MAC Detector)
  Gate 3 - AI ensemble behavioral check      (AI IsolationForest Check)
  Final  - Device CLEARED

Authors: manasvi-0523, Mithun Gowda B (@mithun50)
"""

import asyncio
import sys
import os
import time
import uuid as _uuid

sys.path.insert(0, os.path.dirname(__file__))

from scanner.ble_scanner import scan, detect_duplicate_macs
from db.registry import (
    init_db, get_db, upsert_device, build_training_matrix,
    check_spoofing, update_anomaly_result, get_registry_stats,
)
from ai_model.anomaly_detector import (
    train, train_ocsvm, predict_ensemble,
    normalize_risk, risk_label,
)
from blockchain.blockchain import Blockchain
from blockchain.eth_registry import (
    eth_is_trusted_batch, eth_log_anomaly, eth_enabled,
)
from alerts.alert_system import (
    trigger, alert_unknown_device, alert_duplicate_mac, alert_cleared,
)

SCAN_DURATION = 15


async def run():
    t_start = time.time()

    print("=" * 60)
    print("  BLE Device Trust Registry")
    print("  AI + Blockchain Security System")
    print("  github: manasvi-0523 | mithun50")
    print("=" * 60)

    session_id = str(_uuid.uuid4())
    init_db()

    # ── Ethereum status banner ─────────────────────────────────
    if eth_enabled():
        print("\n[ETH] Ethereum trust registry: CONNECTED (Sepolia)")
    else:
        print("\n[ETH] Ethereum trust registry: OFFLINE")
        print("      Set ETH_RPC_URL + CONTRACT_ADDRESS to enable Gate 1.")

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 1: BLE + Classic Bluetooth Scan
    # ─────────────────────────────────────────────────────────────────────────
    t1 = time.time()
    print(f"\n{'─'*60}")
    print(f"[Phase 1] BLE + Classic Bluetooth Scan ({SCAN_DURATION}s)...")
    print(f"{'─'*60}")
    try:
        devices = await scan(duration=SCAN_DURATION)
    except Exception as e:
        err = str(e).lower()
        if 'bluetooth' in err or 'not powered' in err or 'not available' in err:
            print("[ERROR] Bluetooth is not available or powered off.")
            print("        Enable Bluetooth in Settings and try again.")
        else:
            print(f"[ERROR] BLE scan failed: {e}")
        return

    if not devices:
        print("[WARN] No devices found.")
        return

    ble_devices = [d for d in devices if d.get('scan_type') == 'BLE']
    t1_elapsed = time.time() - t1
    print(f"\n[Phase 1] Done in {t1_elapsed:.1f}s: "
          f"{len(devices)} total ({len(ble_devices)} BLE, "
          f"{len(devices)-len(ble_devices)} Classic)")

    # ─────────────────────────────────────────────────────────────────────────
    # GATE 1: Ethereum On-Chain Trust Registry (PRIMARY CHECK)
    # ─────────────────────────────────────────────────────────────────────────
    t2 = time.time()
    print(f"\n{'─'*60}")
    print("[Layer 1/3] Blockchain Registry Check (Ethereum Sepolia)")
    print(f"{'─'*60}")

    # Batch parallel isTrusted() calls for all BLE MACs
    ble_macs = [d['mac'] for d in ble_devices]
    trusted_map: dict[str, bool] = {}   # mac -> bool

    if eth_enabled() and ble_macs:
        print(f"  Querying on-chain registry for {len(ble_macs)} BLE device(s)...")
        trusted_map = eth_is_trusted_batch(ble_macs)
        unknown_ble = [mac for mac, ok in trusted_map.items() if not ok]
        print(f"  {len(ble_macs) - len(unknown_ble)} trusted | "
              f"{len(unknown_ble)} unknown (not whitelisted)")
    else:
        # ETH offline - all BLE devices pass Gate 1 by default
        trusted_map = {d['mac']: True for d in ble_devices}
        unknown_ble = []
        print("  [Gate 1 BYPASSED] Ethereum not configured - "
              "all devices pass by default.")

    # Trigger UNKNOWN DEVICE alerts immediately (paper format)
    for dev in ble_devices:
        mac = dev['mac']
        name = dev.get('name', 'Unknown')
        rssi = dev.get('rssi', -1)
        if trusted_map.get(mac, True):
            print(f"  [TRUSTED] {mac} | {name} | RSSI:{rssi} dBm")
        else:
            alert_unknown_device(mac, name, rssi)

    t2_elapsed = time.time() - t2
    print(f"[Layer 1/3] Done in {t2_elapsed:.1f}s")

    # ─────────────────────────────────────────────────────────────────────────
    # GATE 2: Duplicate MAC Detection
    # ─────────────────────────────────────────────────────────────────────────
    t3 = time.time()
    print(f"\n{'─'*60}")
    print("[Layer 2/3] Duplicate MAC Detector")
    print(f"{'─'*60}")

    dup_signals = detect_duplicate_macs(devices)
    dup_macs = {s['mac'] for s in dup_signals}

    if dup_signals:
        for sig in dup_signals:
            # Extract rssi_list from detail string for paper-style output
            alert_duplicate_mac(sig['mac'], [sig['detail']])
    else:
        print("  [OK] No duplicate MACs detected.")

    t3_elapsed = time.time() - t3
    print(f"[Layer 2/3] Done in {t3_elapsed:.1f}s: "
          f"{len(dup_signals)} duplicate MAC signal(s)")

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE: SQLite Registry upsert + rule-based spoofing signals
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("[Registry] Updating device behavioral history...")
    print(f"{'─'*60}")
    spoofing_hits = []

    with get_db() as conn:
        fp_map = {}
        for record in devices:
            fp_id = upsert_device(conn, record, session_id)
            fp_map[record['mac']] = fp_id
            signals = check_spoofing(conn, fp_id, record)
            for sig in signals:
                spoofing_hits.append((record['mac'], record.get('name', '?'), sig))
                print(f"  [SPOOF SIGNAL] {sig['type']} | {sig['detail']} "
                      f"({sig['severity']})")

        print(f"  Building feature matrix from scan history...")
        fp_ids, names, macs, X = build_training_matrix(conn)

    print(f"[Registry] {len(fp_ids)} device(s) with enough history for AI.")

    if len(X) < 2:
        print(f"\n[WARN] Need 2+ devices with scan history for AI layer.")
        print(f"       Run more scans to build up history.")
        with get_db() as conn:
            stats = get_registry_stats(conn)
        _print_summary(
            t_start, devices, unknown_ble, dup_signals, spoofing_hits,
            anomaly_count=0, eth_online=eth_enabled(),
            stats=stats, chain_len=0,
        )
        return

    # ─────────────────────────────────────────────────────────────────────────
    # GATE 3: AI Behavioral Anomaly Detection (IsolationForest + OCSVM)
    # ─────────────────────────────────────────────────────────────────────────
    t4 = time.time()
    print(f"\n{'─'*60}")
    print(f"[Layer 3/3] AI IsolationForest Check "
          f"(IF + OCSVM ensemble, {len(X)} device(s))")
    print(f"{'─'*60}")

    try:
        model, scaler  = train(X)
        train_ocsvm(X)
        predictions, scores = predict_ensemble(X, model, scaler)
        risks = normalize_risk(scores)
    except Exception as e:
        print(f"[ERROR] AI model failed: {e}")
        return

    t4_elapsed = time.time() - t4
    print(f"[Layer 3/3] Done in {t4_elapsed:.1f}s")

    # ─────────────────────────────────────────────────────────────────────────
    # Blockchain registration + Alerts + CLEARED
    # ─────────────────────────────────────────────────────────────────────────
    print(f"\n{'─'*60}")
    print("[Blockchain] Registering device signatures on local chain...")
    print(f"{'─'*60}")
    bc = Blockchain()
    anomaly_count = 0
    dev_lookup = {d['mac']: d for d in devices}

    with get_db() as conn:
        for i, fp_id in enumerate(fp_ids):
            mac        = macs[i]
            name       = names[i]
            pred       = int(predictions[i])
            score      = float(scores[i])
            risk       = float(risks[i])
            rlabel     = risk_label(risk)
            is_anomaly = pred == -1
            dev        = dev_lookup.get(mac, {})
            rssi       = dev.get('rssi', -1)

            # Escalate risk if ETH flagged device or dup MAC detected
            not_whitelisted = mac in unknown_ble
            is_dup_mac      = mac in dup_macs
            reason_parts = []
            if is_anomaly:
                reason_parts.append("IF+OCSVM both flagged behavioral anomaly")
            if not_whitelisted:
                reason_parts.append("not in ETH whitelist")
                if rlabel == 'LOW':
                    rlabel = 'MEDIUM'
                    risk   = max(risk, 0.4)
            if is_dup_mac:
                reason_parts.append("duplicate MAC (cloning suspected)")
                rlabel = 'HIGH'
                risk   = max(risk, 0.7)
            if not reason_parts:
                reason_parts.append("all gates passed")

            reason = "; ".join(reason_parts)

            try:
                bc.add_device(fp_id, X[i].tolist())
                trigger(mac, name, pred, score, risk_score=risk, reason=reason)
                update_anomaly_result(conn, fp_id, score, rlabel, is_anomaly)

                # Log high-risk events on-chain via logAnomaly()
                if (is_anomaly or not_whitelisted or is_dup_mac) and eth_enabled():
                    eth_log_anomaly(mac, rlabel, reason)

            except Exception as e:
                print(f"[ERROR] Failed to process {mac}: {e}")

            if is_anomaly:
                anomaly_count += 1
            elif not (not_whitelisted or is_dup_mac):
                # All 3 gates passed - CLEARED
                alert_cleared(mac, name, rssi)

    # ── Verify local chain ─────────────────────────────────────
    print(f"\n{'─'*60}")
    print("[Blockchain] Verifying chain integrity...")
    try:
        bc.verify_chain()
        bc.print_chain()
    except Exception as e:
        print(f"[ERROR] Blockchain verification failed: {e}")

    with get_db() as conn:
        stats = get_registry_stats(conn)

    _print_summary(
        t_start, devices, unknown_ble, dup_signals, spoofing_hits,
        anomaly_count=anomaly_count, eth_online=eth_enabled(),
        stats=stats, chain_len=len(bc.chain),
    )


def _print_summary(t_start, devices, unknown_ble, dup_signals,
                   spoofing_hits, anomaly_count, eth_online, stats, chain_len):
    elapsed = time.time() - t_start
    total   = len(devices)
    ble_cnt = sum(1 for d in devices if d.get('scan_type') == 'BLE')

    print("\n" + "=" * 60)
    print("  SCAN SUMMARY")
    print("=" * 60)
    print(f"  Total scan time       : {elapsed:.1f}s")
    print(f"  Devices found         : {total} ({ble_cnt} BLE, "
          f"{total - ble_cnt} Classic)")
    print(f"  [Gate 1] ETH unknown  : {len(unknown_ble)}"
          + (" (ETH offline)" if not eth_online else ""))
    print(f"  [Gate 2] Dup MAC      : {len(dup_signals)}")
    print(f"  [Gate 2] Spoof signals: {len(spoofing_hits)}")
    print(f"  [Gate 3] AI anomalies : {anomaly_count}")
    print(f"  Registry totals       : "
          f"{stats.get('total_devices', 0)} devices, "
          f"{stats.get('total_observations', 0)} observations")
    print(f"  Chain blocks          : {chain_len}")
    print(f"  Alerts log            : dataset/alerts.csv")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(run())
