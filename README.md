# BLE Behavioral Fingerprinting Security System

### AI + Blockchain Prototype | by [@manasvi-0523](https://github.com/manasvi-0523) & [@mithun50](https://github.com/mithun50)

A real-time **Bluetooth** device security system that combines **BLE + Classic Bluetooth scanning**, **AI-based anomaly detection** (Isolation Forest), and a **tamper-proof local blockchain** to identify, fingerprint, and flag rogue or spoofed devices in your environment.

> **Live Dashboard** included — a cybersecurity-themed web interface for real-time monitoring.

---

## Architecture

```
                    ┌──────────────────────┐
                    │   Nearby BLE Devices  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  BLE Scanner (Bleak)  │
                    │   MAC, RSSI, Services │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Feature Extraction   │
                    │  Behavioral Signature │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
     ┌──────────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
     │  Isolation Forest│ │Blockchain│ │Alert System │
     │  Anomaly Detect  │ │ SHA-256  │ │ CSV + BLOCK │
     └──────────┬──────┘ └────┬─────┘ └──────┬──────┘
                │              │              │
                └──────────────┼──────────────┘
                               │
                    ┌──────────▼───────────┐
                    │  Flask Web Dashboard  │
                    │   Real-Time Charts    │
                    └──────────────────────┘
```

---

## Features

- **Real-Time BLE Scanning** — Captures nearby BLE devices with MAC address, RSSI signal strength, advertised services, and payload size using `bleak`
- **Classic Bluetooth Scanning** — Discovers nearby Classic Bluetooth devices (phones, speakers, laptops) via Windows PnP APIs with proper MAC address extraction
- **Behavioral Fingerprinting** — Extracts a per-device feature vector (mean/std RSSI, payload stats, service count, scan frequency)
- **AI Anomaly Detection** — Trains an Isolation Forest model to flag statistically anomalous devices
- **Blockchain Identity Store** — Each device's behavioral hash is recorded on a local SHA-256 blockchain for tamper-proof audit
- **Automated Alert System** — Anomalous devices trigger `BLOCK` actions, logged to `alerts.csv`
- **Live Web Dashboard** — Cybersecurity-themed Flask dashboard with real-time charts, device tables, blockchain explorer, and alert logs

---

## Tech Stack

| Layer                | Tool / Library                          |
| -------------------- | --------------------------------------- |
| BLE Scanning         | Python + [Bleak](https://github.com/hbldh/bleak) |
| Classic BT Scanning  | PowerShell + Windows PnP APIs           |
| Feature Engineering  | Pandas + NumPy                          |
| AI Model             | Scikit-learn (Isolation Forest)         |
| Blockchain           | Python SHA-256 simulation (local chain) |
| Alert Logging        | CSV log + console output                |
| Web Dashboard        | Flask + Chart.js                        |
| Frontend Design      | Custom CSS (Orbitron, cyber-noir theme) |

---

## Project Structure

```
ble_claude/
├── scanner/
│   └── ble_scanner.py           # BLE + Classic BT scanning
├── feature_engine/
│   └── feature_extract.py       # Behavioral fingerprint extraction
├── ai_model/
│   ├── anomaly_detector.py      # Isolation Forest training + prediction
│   └── scaler.pkl               # Fitted StandardScaler
├── blockchain/
│   └── blockchain.py            # Local blockchain (SHA-256 chain)
├── alerts/
│   └── alert_system.py          # Alert triggering + CSV logging
├── ble-security-project/
│   └── dashboard/
│       ├── app.py               # Flask backend (REST APIs)
│       └── templates/
│           └── index.html       # Cybersecurity-themed dashboard UI
├── dataset/                     # Scan data + alert logs (gitignored)
├── main.py                      # Full pipeline entry point
├── requirements.txt             # Python dependencies
├── .gitignore
└── README.md
```

---

## Setup & Installation

### Prerequisites

- **OS**: Windows 10/11
- **Python**: 3.10+
- **Bluetooth**: Must be enabled on your machine

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run the Full Pipeline

```bash
python main.py
```

This will:
1. Launch the Flask dashboard automatically on [http://localhost:5000](http://localhost:5000)
2. Scan for nearby BLE and Classic Bluetooth devices
3. Extract behavioral features
4. Train an Isolation Forest model
5. Register each device on the local blockchain
6. Log alerts for anomalous devices

After the scan completes, the dashboard stays running — press **Ctrl+C** to stop it.

To run **without** the dashboard:

```bash
python main.py --no-dashboard
```

### Launch the Dashboard Standalone

```bash
cd ble-security-project/dashboard
python app.py
```

Open your browser at [http://localhost:5000](http://localhost:5000)

---

## How It Works

| Phase | Action | Details |
| ----- | ------ | ------- |
| **1. Scan** | BLE + Classic BT discovery | BLE via `bleak`, Classic via Windows PnP API. MAC addresses extracted and formatted |
| **2. Fingerprint** | Feature extraction | Computes mean/std RSSI, payload stats, service count per device |
| **3. Detect** | Anomaly detection | Isolation Forest flags statistically outlier devices |
| **4. Record** | Blockchain logging | Each device's behavioral hash is stored on a SHA-256 chain |
| **5. Alert** | Threat response | Anomalies trigger `BLOCK` action, logged to `alerts.csv` |
| **6. Visualize** | Dashboard | Real-time charts, device table, blockchain explorer |

---

## Sample Console Output

```
============================================================
  BLE SECURITY SYSTEM — AI + Blockchain Prototype
  github: manasvi-0523 | mithun50
============================================================

[Phase 1] Bluetooth Scanning (BLE + Classic)...

[SCAN] Starting Bluetooth scan (BLE + Classic)...

[SCAN] Scanning for BLE devices (15s)...

[OK] BLE scan complete. 0 unique device(s) found.
[SCAN] Discovering Classic Bluetooth devices...

[2026-04-15T19:20:00.000] 2C:BE:EE:15:B9:B3 | Mithun's Phone       | CLASSIC
[2026-04-15T19:20:00.001] 41:42:FF:2F:B2:8E | Rover 9              | CLASSIC

[OK] Classic scan complete. 2 device(s) found.

[OK] Total: 2 device(s) — 0 BLE, 2 Classic

[Phase 2] Extracting behavioral features...
[OK] Features extracted for 2 device(s).

[Phase 3] Training Isolation Forest model...
[OK] Model trained on 2 device(s).

[Phase 4] Registering devices on blockchain...
[CHAIN] Block #1 added | Device: 2C:BE:EE:15:B9:B3 | Hash: d6af1d80...
[OK] Mithun's Phone (2C:BE:EE:15:B9:B3) — NORMAL | Score: 0.0000
[CHAIN] Block #2 added | Device: 41:42:FF:2F:B2:8E | Hash: 59a08b39...
[OK] Rover 9 (41:42:FF:2F:B2:8E) — NORMAL | Score: 0.0000

[Blockchain] Verifying chain integrity...
[OK] Blockchain integrity verified.

============================================================
  Scan complete. Check dataset/alerts.csv for full log.
============================================================
```

---

## Dashboard Preview

The web dashboard features a **cybersecurity-themed** dark interface with:
- **Summary cards** — Total devices, scans, anomalies, normal, chain blocks
- **RSSI Signal Trend** — Real-time line chart per device
- **Anomaly Distribution** — Doughnut chart (Normal vs Anomaly)
- **Detected Devices Table** — MAC, name, RSSI, services, payload, last seen
- **Blockchain Explorer** — Visual chain with block index, device, and hash
- **Alert Log** — Timestamped alerts with status badges and action labels

---

## Security & Privacy

This project takes privacy seriously:
- **`blockchain/chain.json`** — Contains real MAC addresses from scans and is **gitignored** (never pushed to the remote)
- **`dataset/*.csv`** — All scan data and alert logs are **gitignored**
- **`ai_model/model.pkl`** — Trained model binary is **gitignored**
- No API keys, tokens, or secrets are stored in the codebase

---

## Roadmap

- [x] Phase 1 — BLE Scanner (Bleak)
- [x] Phase 1b — Classic Bluetooth Scanner (Windows PnP API)
- [x] Phase 2 — Feature Extraction (Behavioral Fingerprinting)
- [x] Phase 3 — AI Anomaly Detection (Isolation Forest)
- [x] Phase 4 — Blockchain Identity Store (SHA-256)
- [x] Phase 5 — Web Dashboard (Flask + Chart.js)
- [ ] Phase 6 — Ethereum Smart Contract Integration
- [ ] Phase 7 — Real-time Alerting (Email / SMS / Push)
- [ ] Phase 8 — Multi-device collaborative scanning

---

## License

This project is for educational and research purposes.

---

<p align="center">
  <b>Built with Python, AI, and Blockchain</b><br>
  <a href="https://github.com/manasvi-0523">@manasvi-0523</a> &middot; <a href="https://github.com/mithun50">@mithun50</a>
</p>
