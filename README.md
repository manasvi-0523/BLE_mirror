# BLE Behavioral Fingerprinting Security System
### AI + Blockchain Prototype | by [@manasvi-0523](https://github.com/manasvi-0523)

A real-time BLE device security system that uses **AI-based anomaly detection** and a **local blockchain** to detect rogue, spoofed, or behaviorally anomalous Bluetooth Low Energy devices.

---

## Architecture

```
BLE Devices
    ↓
BLE Scanner (bleak)
    ↓
Feature Extraction (behavioral fingerprint)
    ↓
Isolation Forest (anomaly detection)
    ↓
Blockchain Identity Store (tamper-proof)
    ↓
Alert System
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| BLE Scanning | Python + Bleak |
| Feature Engineering | Pandas + NumPy |
| AI Model | Scikit-learn (Isolation Forest) |
| Blockchain | Python simulation (SHA-256) |
| Alerts | CSV log + console |

---

## Project Structure

```
ble-security-project/
├── scanner/           # BLE packet capture
├── feature_engine/    # Behavioral fingerprinting
├── ai_model/          # Anomaly detection (Isolation Forest)
├── blockchain/        # Tamper-proof identity store
├── alerts/            # Alert logging
├── dataset/           # Captured data + alert logs
└── main.py            # Full pipeline
```

---

## Setup

```bash
pip install bleak scikit-learn pandas
python main.py
```

> Requires: Windows 10/11, Python 3.10+, Bluetooth enabled

---

## How It Works

1. **Scan** — Captures nearby BLE devices (MAC, RSSI, services, payload)
2. **Fingerprint** — Extracts behavioral signature per device
3. **Detect** — Isolation Forest flags statistically anomalous devices
4. **Record** — Each device is hashed and stored on a local blockchain
5. **Alert** — Anomalies trigger alerts and are logged to `alerts.csv`

---

## Sample Output

```
✅ Smart Watch (AA:BB:CC:11:22:33) — NORMAL | Score: 0.0823
🚨 ALERT TRIGGERED
   Device  : Unknown (FF:FF:FF:FF:FF:FF)
   Status  : ANOMALY
   Score   : -0.1542
   Action  : BLOCK
```

---

## Roadmap

- [x] Phase 1 — BLE Scanner
- [x] Phase 2 — Feature Extraction
- [x] Phase 3 — AI Anomaly Detection
- [x] Phase 4 — Blockchain Identity Store
- [ ] Phase 5 — Web Dashboard
- [ ] Phase 6 — Ethereum integration
- [ ] Phase 7 — Real-time alerting (email/SMS)
