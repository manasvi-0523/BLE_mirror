import asyncio
import csv
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from bleak import BleakScanner

DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'ble_data.csv')

FIELDNAMES = ['timestamp', 'mac', 'name', 'rssi', 'interval_ms', 'payload_size', 'service_count', 'raw_services', 'scan_type']

def ensure_dataset():
    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    if not os.path.exists(DATASET_PATH):
        with open(DATASET_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def save_device(record: dict):
    with open(DATASET_PATH, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(record)

def parse_device(device, advertisement_data) -> dict:
    services = advertisement_data.service_uuids or []
    interval = getattr(advertisement_data, 'tx_power', None)
    payload = advertisement_data.manufacturer_data
    payload_size = sum(len(v) for v in payload.values()) if payload else 0

    return {
        'timestamp': datetime.now().isoformat(),
        'mac': device.address,
        'name': device.name or 'Unknown',
        'rssi': advertisement_data.rssi,
        'interval_ms': interval if interval else -1,
        'payload_size': payload_size,
        'service_count': len(services),
        'raw_services': '|'.join(services),
        'scan_type': 'BLE'
    }

import re

# ── Classic Bluetooth Scanning (Windows PowerShell) ───────────

# System-level BT components that aren't real devices
_SYSTEM_KEYWORDS = {'enumerator', 'rfcomm', 'protocol tdi', 'radio', 'adapter'}

def _extract_mac(instance_id: str) -> str | None:
    """Extract and format a MAC address from a Windows PnP InstanceId."""
    # Look for a 12-char hex string (the MAC) in the InstanceId
    match = re.search(r'(?<![0-9A-Fa-f])([0-9A-Fa-f]{12})(?![0-9A-Fa-f])', instance_id)
    if match:
        raw = match.group(1).upper()
        return ':'.join(raw[i:i+2] for i in range(0, 12, 2))
    return None

def scan_classic(verbose: bool = True) -> list[dict]:
    """Discover nearby Classic Bluetooth devices using Windows APIs."""
    if platform.system() != 'Windows':
        print("[WARN] Classic BT scan is only supported on Windows. Skipping.")
        return []

    print("[SCAN] Discovering Classic Bluetooth devices...\n")
    ps_script = (
        "Get-PnpDevice -Class Bluetooth | "
        "Where-Object { $_.Status -eq 'OK' -and $_.FriendlyName -ne '' } | "
        "Select-Object InstanceId, FriendlyName, Status | "
        "ConvertTo-Json -Compress"
    )
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            print(f"[ERROR] Classic BT scan failed: {result.stderr.strip()}")
            return []

        output = result.stdout.strip()
        if not output:
            print("[OK] Classic scan complete. 0 device(s) found.")
            return []

        data = json.loads(output)
        if isinstance(data, dict):
            data = [data]

    except subprocess.TimeoutExpired:
        print("[ERROR] Classic BT scan timed out.")
        return []
    except (json.JSONDecodeError, Exception) as e:
        print(f"[ERROR] Classic BT scan failed: {e}")
        return []

    records = []
    for dev in data:
        instance_id = dev.get('InstanceId', '')
        name = dev.get('FriendlyName', 'Unknown')
        # Skip system-level Bluetooth components
        name_lower = name.lower()
        if any(kw in name_lower for kw in _SYSTEM_KEYWORDS):
            continue
        # Extract real MAC address from InstanceId
        mac = _extract_mac(instance_id)
        if not mac:
            continue
        record = {
            'timestamp': datetime.now().isoformat(),
            'mac': mac,
            'name': name,
            'rssi': -1,
            'interval_ms': -1,
            'payload_size': 0,
            'service_count': 0,
            'raw_services': '',
            'scan_type': 'CLASSIC'
        }
        records.append(record)
        if verbose:
            print(f"[{record['timestamp']}] {mac} | {name:<20} | CLASSIC")

    print(f"\n[OK] Classic scan complete. {len(records)} device(s) found.")
    return records

# ── BLE Scanning ──────────────────────────────────────────────

async def scan_ble(duration: int = 10, verbose: bool = True) -> list[dict]:
    """Scan for BLE (Bluetooth Low Energy) advertising devices."""
    seen = {}

    def callback(device, advertisement_data):
        record = parse_device(device, advertisement_data)
        seen[device.address] = record
        if verbose:
            print(f"[{record['timestamp']}] {record['mac']} | {record['name']:<20} | RSSI: {record['rssi']} dBm | Services: {record['service_count']} | BLE")

    print(f"[SCAN] Scanning for BLE devices ({duration}s)...\n")
    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()
    await asyncio.sleep(duration)
    await scanner.stop()

    print(f"\n[OK] BLE scan complete. {len(seen)} unique device(s) found.")
    return list(seen.values())

# ── Combined Scan ─────────────────────────────────────────────

async def scan(duration: int = 10, verbose: bool = True) -> list[dict]:
    """Run both BLE and Classic Bluetooth scans, merge and save results."""
    ensure_dataset()

    # BLE scan
    print(f"\n[SCAN] Starting Bluetooth scan (BLE + Classic)...\n")
    ble_devices = await scan_ble(duration=duration, verbose=verbose)

    # Classic BT scan
    classic_devices = scan_classic(verbose=verbose)

    # Merge (deduplicate by MAC, BLE takes priority)
    all_devices = {}
    for dev in classic_devices:
        all_devices[dev['mac']] = dev
    for dev in ble_devices:
        all_devices[dev['mac']] = dev  # BLE overwrites classic if same MAC

    # Save all
    for record in all_devices.values():
        save_device(record)

    total = len(all_devices)
    ble_count = sum(1 for d in all_devices.values() if d['scan_type'] == 'BLE')
    classic_count = sum(1 for d in all_devices.values() if d['scan_type'] == 'CLASSIC')
    print(f"\n[OK] Total: {total} device(s) — {ble_count} BLE, {classic_count} Classic")
    print(f"[SAVE] Data saved to: {os.path.abspath(DATASET_PATH)}\n")
    return list(all_devices.values())

if __name__ == '__main__':
    asyncio.run(scan(duration=15))