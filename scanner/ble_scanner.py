import asyncio
import csv
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from bleak import BleakScanner

from scanner.distance import estimate_distance, get_proximity_zone, format_distance

DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'ble_data.csv')

FIELDNAMES = ['timestamp', 'mac', 'name', 'rssi', 'tx_power', 'interval_ms', 'payload_size',
              'service_count', 'raw_services', 'company_id', 'is_random_mac',
              'scan_type', 'distance_m', 'proximity_zone']

def ensure_dataset():
    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    needs_header = True
    if os.path.exists(DATASET_PATH):
        with open(DATASET_PATH, 'r', newline='') as f:
            first_line = f.readline().strip()
        # Rewrite header if the schema has changed
        existing_cols = set(first_line.split(','))
        needs_header = not existing_cols.issuperset({'tx_power', 'company_id', 'is_random_mac'})
    if needs_header:
        with open(DATASET_PATH, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def save_device(record: dict):
    with open(DATASET_PATH, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(record)

def parse_device(device, advertisement_data) -> dict:
    services = advertisement_data.service_uuids or []
    tx_power_val = getattr(advertisement_data, 'tx_power', None)
    mfr = advertisement_data.manufacturer_data or {}
    payload_size = sum(len(v) for v in mfr.values()) if mfr else 0
    company_id = list(mfr.keys())[0] if mfr else -1
    rssi = advertisement_data.rssi
    dist = estimate_distance(rssi)
    zone = get_proximity_zone(dist)
    # Locally administered bit (bit 1 of first byte) indicates a randomized MAC
    try:
        first_byte = int(device.address.split(':')[0], 16)
        is_random = int(bool(first_byte & 0x02))
    except (ValueError, IndexError):
        is_random = 0

    return {
        'timestamp': datetime.now().isoformat(),
        'mac': device.address,
        'name': device.name or 'Unknown',
        'rssi': rssi,
        'tx_power': tx_power_val if tx_power_val is not None else -1,
        'interval_ms': -1,
        'payload_size': payload_size,
        'service_count': len(services),
        'raw_services': '|'.join(services),
        'company_id': company_id,
        'is_random_mac': is_random,
        'scan_type': 'BLE',
        'distance_m': dist,
        'proximity_zone': zone
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
            'tx_power': -1,
            'interval_ms': -1,
            'payload_size': 0,
            'service_count': 0,
            'raw_services': '',
            'company_id': -1,
            'is_random_mac': 0,
            'scan_type': 'CLASSIC',
            'distance_m': None,
            'proximity_zone': 'N/A'
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
            dist_str = format_distance(record['rssi'])
            print(f"[{record['timestamp']}] {record['mac']} | {record['name']:<20} | RSSI: {record['rssi']} dBm | {dist_str} | Services: {record['service_count']} | BLE")

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

# ── Duplicate MAC Detection ───────────────────────────────────
# Paper section 3.2: same MAC appearing with two very different RSSI
# values in a single scan cycle is a strong MAC spoofing indicator.

_RSSI_SPOOF_THRESHOLD = 15  # dBm - difference that triggers a spoofing flag

def detect_duplicate_macs(devices: list[dict]) -> list[dict]:
    """
    Scan the device list for duplicate MACs with anomalous RSSI spread.

    Returns a list of spoofing signal dicts (same shape as check_spoofing()
    output in db/registry.py) so they can be appended to spoofing_hits in
    main.py without any special casing.

    A duplicate MAC entry means two different physical devices are advertising
    under the same address - a classic MAC spoofing / cloning attack.
    """
    from collections import defaultdict
    mac_groups: dict[str, list[int]] = defaultdict(list)
    for dev in devices:
        if dev.get('scan_type') == 'BLE' and dev.get('rssi') not in (None, -1):
            mac_groups[dev['mac']].append(int(dev['rssi']))

    signals = []
    for mac, rssi_list in mac_groups.items():
        if len(rssi_list) < 2:
            continue
        rssi_range = max(rssi_list) - min(rssi_list)
        if rssi_range >= _RSSI_SPOOF_THRESHOLD:
            signals.append({
                'mac': mac,
                'type': 'DUPLICATE_MAC',
                'detail': (
                    f"MAC seen {len(rssi_list)} times with RSSI spread "
                    f"{rssi_range} dBm ({min(rssi_list)} to {max(rssi_list)}) "
                    "in one scan - possible MAC cloning"
                ),
                'severity': 'HIGH',
            })
    return signals


if __name__ == '__main__':
    asyncio.run(scan(duration=15))