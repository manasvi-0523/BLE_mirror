# BLE Behavioral Fingerprinting Security System

### AI + Blockchain Prototype | by [@manasvi-0523](https://github.com/manasvi-0523) & [@mithun50](https://github.com/mithun50)

A real-time **Bluetooth** device security system that combines **BLE + Classic Bluetooth scanning**, **AI-based anomaly detection** (Isolation Forest), and a **tamper-proof local blockchain** to identify, fingerprint, and flag rogue or spoofed devices in your environment.

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
                               ▼
                         [ Output / GUI ]
```

---

## Features

- **Real-Time BLE Scanning** — Captures nearby BLE devices with MAC address, RSSI signal strength, advertised services, and payload size using `bleak`
- **Classic Bluetooth Scanning** — Discovers nearby Classic Bluetooth devices (phones, speakers, laptops) via Windows PnP APIs with proper MAC address extraction
- **Behavioral Fingerprinting** — Extracts a per-device feature vector (mean/std RSSI, payload stats, service count, scan frequency)
- **AI Anomaly Detection** — Trains an Isolation Forest model to flag statistically anomalous devices
- **Blockchain Identity Store** — Each device's behavioral hash is recorded on a local SHA-256 blockchain for tamper-proof audit
- **Automated Alert System** — Anomalous devices trigger `BLOCK` actions, logged to `alerts.csv`
- **Desktop GUI (Kivy)** — Professional dark-themed desktop app with metric cards, device table, and analytics tab
- **Analytics Dashboard** — Built-in donut chart (device type distribution), RSSI signal bars, anomaly score chart, and live pipeline flow diagram
- **One-click EXE Build** — GitHub Actions workflow auto-builds a Windows `.exe` on every push
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
| Desktop GUI          | Kivy (pure-canvas charts, dark theme)   |
| EXE Packaging        | PyInstaller (via GitHub Actions)        |


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
├── .github/
│   └── workflows/
│       └── build-exe.yml        # GitHub Actions → Windows .exe
├── dataset/                     # Scan data + alert logs (gitignored)
├── main.py                      # CLI pipeline entry point
├── gui_app.py                   # Kivy desktop GUI (Devices + Analytics)
├── ble_security.spec            # PyInstaller build spec
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
1. Scan for nearby BLE and Classic Bluetooth devices
2. Extract behavioral features
3. Train an Isolation Forest model
4. Register each device on the local blockchain
5. Log alerts for anomalous devices

### Run the Desktop GUI

```bash
python gui_app.py
```

The GUI features two tabs:
- **DEVICES** — Real-time device table with status badges, anomaly scores, and RSSI
- **ANALYTICS** — Donut chart (BLE/Classic/Threats), RSSI signal strength bars, anomaly score chart, and a live 4-stage pipeline flow diagram

### Download Pre-built EXE

A Windows `.exe` is automatically built on every push via GitHub Actions.  
Go to **Actions → Build EXE → latest run → Artifacts** to download `BLE_Security_System`.

---

## How It Works

| Phase | Action | Details |
| ----- | ------ | ------- |
| **1. Scan** | BLE + Classic BT discovery | BLE via `bleak`, Classic via Windows PnP API. MAC addresses extracted and formatted |
| **2. Fingerprint** | Feature extraction | Computes mean/std RSSI, payload stats, service count per device |
| **3. Detect** | Anomaly detection | Isolation Forest flags statistically outlier devices |
| **4. Record** | Blockchain logging | Each device's behavioral hash is stored on a SHA-256 chain |
| **5. Alert** | Threat response | Anomalies trigger `BLOCK` action, logged to `alerts.csv` |


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
- [x] Phase 5 — Desktop GUI (Kivy + Analytics)
- [x] Phase 5b — Automated EXE Build (GitHub Actions)
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
