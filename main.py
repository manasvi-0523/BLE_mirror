from scanner.ble_scanner import SignatureScanner
import asyncio

async def main():
    print("--- BLE Trust Registry: Main System ---")
    # Step 1: Scan BLE Devices
    scanner = SignatureScanner()
    await scanner.run(scan_time=10)
    
    # Next steps will integrate feature extraction, ML and Blockchain here
    
if __name__ == "__main__":
    asyncio.run(main())
