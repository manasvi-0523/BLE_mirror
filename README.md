# BLE Device Trust Registry
### AI-Powered Behavioral Fingerprinting & Blockchain Identity Ledger

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![BLE Security](https://img.shields.io/badge/Security-BLE-green.svg)](https://github.com/manasvi-0523/BLE_TRUST-REGISTRY)

A professional-grade security prototype designed to protect Bluetooth Low Energy (BLE) environments from spoofing and rogue device attacks. This system combines **Unsupervised Machine Learning** with an **Immutable Blockchain Ledger** to establish a "Behavioral Identity" for every device in range.

---

## 🏛️ System Architecture

The project is built on a 5-Phase engineering pipeline:

1.  **Phase 1: BLE Data Capture**: Asynchronous scanning of MAC addresses, RSSI (signal strength), and advertising intervals using the `Bleak` library.
2.  **Phase 2: Feature Engineering**: Raw packet data is processed via `Pandas` into mathematical "Behavioral Fingerprints" (Mean Inter-arrival Times, RSSI stability, etc.).
3.  **Phase 3: AI Anomaly Detection**: An **Isolation Forest** model learns the statistical boundaries of "normal" behavior and flags outliers with custom anomaly scores.
4.  **Phase 4: Blockchain Trust Ledger**: Legitimate devices are cryptographically secured using SHA-256 hashing in a local peer-to-peer blockchain simulation.
5.  **Phase 5: Real-time Alerting**: A security dashboard triggers visual alerts and blocks high-criticality threats from accessing the registry.

---

## 🚀 Getting Started

### Prerequisites
*   Windows 10/11 Laptop
*   Integrated or USB Bluetooth Adapter
*   Python 3.8 or higher

### Installation

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/manasvi-0523/BLE_TRUST-REGISTRY.git
    cd BLE_TRUST-REGISTRY
    ```

2.  **Set up Virtual Environment**:
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

---

## 💻 Usage

Run the integrated master loop to start the security monitoring:

```powershell
python main.py
```

### What to expect:
*   **Cycle 1 (Calibration)**: The system learns the environment and stores initial "Normal" devices into the blockchain.
*   **Cycle 2+ (Active Defense)**: The AI model becomes active and begins blocking any device that exhibits irregular or aggressive behavior.

---

## 📊 Output & Results

### Security Result Corner
At the end of each session, the system generates a **Security Result Corner** showing:
*   **Overall Status**: (SAFE or NOT SAFE)
*   **Spoofing Device Log**: A list of specific MAC addresses and Names that were blocked.
*   **Criticality Levels**:
    *   **LOW**: Slight deviation from baseline.
    *   **MEDIUM**: Intentional behavioral shift detected.
    *   **HIGH**: Major threat (e.g., Denial of Service or Packet Flooding).

---

## 📂 Project Structure

```text
BLE_TRUST-REGISTRY/
├── scanner/             # Phase 1: Raw BLE scanning logic
├── feature_engine/      # Phase 2: Data processing & Feature extraction
├── ai_model/            # Phase 3: Isolation Forest ML model
├── blockchain/          # Phase 4: SHA-256 Immutable Ledger logic
├── alerts/              # Phase 5: Incident response & Alerting
├── dataset/             # Temporary storage for behavioral CSVs
├── main.py              # Master Integration Loop
└── requirements.txt     # Python package definitions
```

---

## 🛡️ Security Disclaimer
This project is for **ethical security research and educational purposes only**. Always ensure you have permission before scanning or analyzing devices in a private environment.

---

**Developed with ❤️ by [manasvi-0523](https://github.com/manasvi-0523)**
