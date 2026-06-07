# BLE Device Trust Registry
### AI-Powered Behavioral Fingerprinting & Blockchain Identity Ledger

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![BLE Security](https://img.shields.io/badge/Security-BLE-green.svg)](https://github.com/manasvi-0523/BLE_TRUST-REGISTRY)

A **production-grade** security system designed to protect Bluetooth Low Energy (BLE) environments from spoofing and rogue device attacks. This system combines **Unsupervised Machine Learning** with a **Tamper-Evident Blockchain Ledger** to establish a "Behavioral Identity" for every device in range.

### 🆕 What's New in This Branch
This `efficient-core-refactor` branch addresses critical bugs and introduces **scientifically sound** anomaly detection:

✅ **Baseline/Monitor Mode Separation** - The biggest fix: no longer trains and tests on the same data  
✅ **Dynamic Contamination Rate** - Adapts to dataset size for reliable detection  
✅ **Blockchain Persistence** - Chain survives restarts with integrity validation  
✅ **Resource Leak Fixes** - Proper file handle management  
✅ **Real Interval Calculation** - Fixed bug where `tx_power` was used instead of actual time intervals  
✅ **Centralized Configuration** - Clean architecture with `config.py`

---

## 🏛️ System Architecture

The project follows a **scientifically rigorous 5-phase pipeline** with proper train/test separation:

1.  **Phase 1: BLE Data Capture**: Asynchronous scanning using `Bleak` library with proper interval calculation
2.  **Phase 2: Feature Engineering**: Vectorized feature extraction via `Pandas` for behavioral fingerprints
3.  **Phase 3: AI Anomaly Detection**: **Isolation Forest** with dynamic contamination rate and baseline learning
4.  **Phase 4: Blockchain Trust Ledger**: Tamper-evident SHA-256 ledger with persistence and duplicate prevention
5.  **Phase 5: Real-time Alerting**: Persistent alert logging with criticality classification

### Key Architectural Improvements

**Baseline/Monitor Separation** (The Critical Fix):
- **Baseline Mode**: Scan trusted environment → train model → save to disk
- **Monitor Mode**: Load trained model → scan current environment → detect anomalies

This eliminates the fatal flaw of training and testing on the same data.

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

### Baseline Mode - Learn Normal Behavior

First, establish a baseline of trusted devices in a clean environment:

```powershell
python main.py --mode baseline
```

This will:
- Scan for devices over 2 cycles (configurable with `--cycles`)
- Extract behavioral features
- Train the AI model
- Save the model to disk
- Register all devices in the blockchain as trusted

### Monitor Mode - Detect Anomalies

Once baseline is established, activate real-time monitoring:

```powershell
python main.py --mode monitor
```

This will:
- Load the pre-trained model
- Scan for devices over 5 cycles (configurable)
- Detect anomalies using the learned baseline
- Trigger alerts for suspicious devices
- Add normal devices to the blockchain

### Custom Cycle Counts

```powershell
# Longer baseline learning (recommended for production)
python main.py --mode baseline --cycles 5

# Extended monitoring session
python main.py --mode monitor --cycles 20
```

---

## 🔬 What Makes This Scientifically Sound

### ❌ Old Approach (Flawed)
```
Scan → Extract Features → Train Model → Predict on same scan
```
Problem: Model predicts on the exact data it was trained on. Meaningless results.

### ✅ New Approach (Correct)
```
Baseline: Scan trusted environment → Train → Save model
Monitor:  Load model → Scan current environment → Detect anomalies
```
Result: True anomaly detection with proper train/test separation.

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
├── config.py            # Centralized configuration (NEW)
├── scanner/             # Phase 1: BLE scanning with proper interval tracking
├── feature_engine/      # Phase 2: Vectorized feature extraction
├── ai_model/            # Phase 3: Isolation Forest with dynamic contamination
├── blockchain/          # Phase 4: Persistent tamper-evident ledger
├── alerts/              # Phase 5: Alert logging with history
├── dataset/             # Temporary behavioral data storage
├── main.py              # Baseline/Monitor mode orchestration
└── requirements.txt     # Python dependencies
```

---

## 🛡️ Security Disclaimer
This project is for **ethical security research and educational purposes only**. Always ensure you have permission before scanning or analyzing devices in a private environment.

---

## 🐛 Bugs Fixed in This Branch

1. **Interval calculation bug**: Was using `tx_power` instead of actual time difference
2. **Resource leak**: Scanner file handle never closed properly
3. **Train/test contamination**: Model was predicting on its own training data
4. **Small dataset failure**: Model would fail or give meaningless results with <10 devices
5. **Blockchain persistence**: Chain was lost on restart
6. **Duplicate blocks**: Same device added repeatedly with unchanged behavior
7. **Hard-coded paths**: All modules had scattered path definitions

---

**Developed  by NEXUS ONLINE**  
**Refactored for production-grade quality**
