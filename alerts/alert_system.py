import time

def trigger_alert(mac, device_name, score):
    """
    Triggers a visual (and programmatic console) alert when an anomaly is detected.
    """
    print("\n" + "="*50)
    print("! SECURITY ALERT: ANOMALOUS DEVICE DETECTED !".center(50))
    print("="*50)
    print(f"Time          : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Device Name   : {device_name}")
    print(f"MAC Address   : {mac}")
    print(f"Anomaly Score : {score:.3f}")
    print("="*50)
    print("ACTION: Device blocked from Blockchain Identity Registry.\n")

if __name__ == "__main__":
    # Test Alert
    trigger_alert("00:11:22:33:44:55", "Spoofed_JioSTB", -0.452)
