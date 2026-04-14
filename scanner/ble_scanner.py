import asyncio
import csv
import os
from datetime import datetime
from bleak import BleakScanner

DATASET_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'ble_data.csv')

FIELDNAMES = ['timestamp', 'mac', 'name', 'rssi', 'interval_ms', 'payload_size', 'service_count', 'raw_services']

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
    # Estimate advertisement interval from metadata if available, else default
    interval = getattr(advertisement_data, 'tx_power', None)  # placeholder; real interval needs multi-scan
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
        'raw_services': '|'.join(services)
    }

async def scan(duration: int = 10, verbose: bool = True):
    ensure_dataset()
    seen = {}

    def callback(device, advertisement_data):
        record = parse_device(device, advertisement_data)
        seen[device.address] = record
        if verbose:
            print(f"[{record['timestamp']}] {record['mac']} | {record['name']:<20} | RSSI: {record['rssi']} dBm | Services: {record['service_count']}")

    print(f"\n🔍 Scanning for BLE devices ({duration}s)...\n")
    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()
    await asyncio.sleep(duration)
    await scanner.stop()

    print(f"\n✅ Scan complete. {len(seen)} unique device(s) found.")
    for record in seen.values():
        save_device(record)
    print(f"💾 Data saved to: {os.path.abspath(DATASET_PATH)}\n")
    return list(seen.values())

if __name__ == '__main__':
    asyncio.run(scan(duration=15))