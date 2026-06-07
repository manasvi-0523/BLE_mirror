import asyncio
from bleak import BleakScanner
import time
import csv
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BLE_DATA_PATH

class SignatureScanner:
    def __init__(self):
        # Track devices to compute intervals and behavioral data
        self.devices_data = {}
        
        # Setup dataset directory and CSV logger using centralized config
        self.csv_file = str(BLE_DATA_PATH)
        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)
        
        # Use context manager pattern for file handling (fixed resource leak)
        self.f = None
        self.writer = None
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers if needed."""
        file_exists = os.path.exists(self.csv_file)
        self.f = open(self.csv_file, 'a', newline='', encoding='utf-8')
        self.writer = csv.writer(self.f)
        if not file_exists or os.path.getsize(self.csv_file) == 0:
            self.writer.writerow(['timestamp', 'mac_address', 'rssi', 'interval_ms', 'services_count', 'name'])
    
    def __del__(self):
        """Ensure file handle is properly closed."""
        if self.f and not self.f.closed:
            self.f.close()
    
    def detection_callback(self, device, advertisement_data):
        timestamp = time.time()
        mac_address = device.address
        rssi = advertisement_data.rssi
        name = device.name or "Unknown"
        services = advertisement_data.service_uuids
        services_count = len(services) if services else 0
        
        # Calculate REAL advertisement interval (time since last seen)
        # This fixes the bug where tx_power was incorrectly used as interval
        interval_ms = 0.0
        if mac_address in self.devices_data:
            last_timestamp = self.devices_data[mac_address]["last_seen"]
            interval_ms = round((timestamp - last_timestamp) * 1000, 2)
            
        self.devices_data[mac_address] = {
            "name": name,
            "mac_address": mac_address,
            "rssi": rssi,
            "services_count": services_count,
            "last_seen": timestamp
        }
        
        # Print device information
        print(f"[{time.strftime('%H:%M:%S')}] MAC: {mac_address} | RSSI: {rssi:4} dBm | Interval: {interval_ms:7} ms | Services: {services_count} | Name: {name}")

        # Export row to dataset for the AI model
        self.writer.writerow([timestamp, mac_address, rssi, interval_ms, services_count, name])
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
