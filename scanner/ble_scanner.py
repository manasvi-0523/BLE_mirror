import asyncio
from bleak import BleakScanner
import time
import csv
import os

class SignatureScanner:
    def __init__(self):
        # We will keep track of devices to compute intervals
        self.devices_data = {}
        
        # Setup dataset directory and CSV logger
        self.dataset_dir = os.path.join(os.path.dirname(__file__), '..', 'dataset')
        os.makedirs(self.dataset_dir, exist_ok=True)
        self.csv_file = os.path.join(self.dataset_dir, 'ble_data.csv')
        
        file_exists = os.path.exists(self.csv_file)
        self.f = open(self.csv_file, 'a', newline='', encoding='utf-8')
        self.writer = csv.writer(self.f)
        if not file_exists or os.path.getsize(self.csv_file) == 0:
            self.writer.writerow(['timestamp', 'mac_address', 'rssi', 'interval_ms', 'services_count', 'name'])

        # We will keep track of devices to compute intervals
        self.devices_data = {}

    def detection_callback(self, device, advertisement_data):
        timestamp = time.time()
        mac_address = device.address
        rssi = advertisement_data.rssi
        name = device.name or "Unknown"
        services = advertisement_data.service_uuids
        services_count = len(services) if services else 0
        
        # Calculate advertisement interval
        interval = 0.0
        if mac_address in self.devices_data:
            last_timestamp = self.devices_data[mac_address]["last_seen"]
            interval = timestamp - last_timestamp
            
        self.devices_data[mac_address] = {
            "name": name,
            "mac_address": mac_address,
            "rssi": rssi,
            "services_count": services_count,
            "last_seen": timestamp,
            "interval(ms)": round(interval * 1000, 2)
        }
        
        # We only print devices with name or known services to reduce noise,
        # but for the prototype let's print everything nicely.
        int_ms = self.devices_data[mac_address]['interval(ms)']
        print(f"[{time.strftime('%H:%M:%S')}] MAC: {mac_address} | RSSI: {rssi:4} dBm | Interval: {int_ms:7} ms | Services: {services_count} | Name: {name}")

        # Export row to dataset for the AI model
        self.writer.writerow([timestamp, mac_address, rssi, int_ms, services_count, name])
        self.f.flush()

    async def run(self, scan_time=15):
        print(f"Starting BLE Scanner for {scan_time} seconds (Behavioral Capture)...")
        scanner = BleakScanner(detection_callback=self.detection_callback)
        await scanner.start()
        await asyncio.sleep(scan_time)
        await scanner.stop()
        print("\n--- Scanning complete. Summary ---")
        print(f"Total Unique Devices Captured: {len(self.devices_data)}")

if __name__ == "__main__":
    scanner = SignatureScanner()
    try:
        asyncio.run(scanner.run(scan_time=15))
    except KeyboardInterrupt:
        print("\nScanner stopped manually.")
