# 👀 Where to See Everything - Visual Guide

## 🎯 Your Questions: "Where do I see X?"

### 1. AI Training Process

**WHERE**: Console window (when you click "Start Baseline Scan")

**WHAT YOU'LL SEE**:
```
============================================================
              BASELINE LEARNING MODE                  
============================================================

>>> BASELINE CYCLE 1/2 <<<
###########################################################
--- [PHASE 1] Starting Data Capture (15s, mode=baseline) ---
Starting BLE Scanner for 15 seconds (Behavioral Capture)...
[12:30:15] MAC: 6C:E8:C6:8C:87:10 | RSSI:  -28 dBm | Interval: 0.0 ms
[12:30:15] MAC: 6C:E8:C6:8C:87:10 | RSSI:  -25 dBm | Interval: 12.25 ms
...

--- [PHASE 2] Extracting Behavioral Features ---
Loaded 45 raw data points.

Device Behavioral Fingerprints:
mac_address          mean_rssi  mean_interval  std_interval  packet_count  name
6C:E8:C6:8C:87:10    -32.50     487.30         312.10        32            JioSTB
01:B6:EC:B6:D7:E7    -46.50     2.50           1.20          2             SWAN
...

Extracted behavioral features for 7 unique devices.

--- [PHASE 3] Baseline Learning Mode ---
Learning normal behavior from 7 devices...
[Baseline] Device 6C:E8:C6:8C:87:10 (JioSTB) registered as TRUSTED
[Blockchain] Block 1 Mined: Device 6C:E8:C6:8C:87:10 secured.
...

============================================================
              TRAINING AI MODEL ON BASELINE DATA           
============================================================

[AI] Training Isolation Forest on 7 baseline behavioral fingerprints...
[AI] Using contamination rate: 0.300 (dynamic adjustment for 7 samples)
[AI] Model successfully trained & saved to ai_model\isolation_forest.pkl

[SUCCESS] Baseline established and model trained!
[SUCCESS] 7 trusted devices learned.
[SUCCESS] Blockchain contains 8 blocks.

--- Blockchain Trust Registry (First 5 blocks) ---
Block  0 | MAC Genesis           | Hash: 8c8f7b5e7d3a9f2b...
Block  1 | MAC 6C:E8:C6:8C:87:10 | Hash: def456789abcdef...
Block  2 | MAC 01:B6:EC:B6:D7:E7 | Hash: 123abc456def789...
...
```

**KEY SECTIONS**:
- **PHASE 1**: Raw BLE scanning (you see each packet)
- **PHASE 2**: Feature extraction (mathematical fingerprints)
- **PHASE 3**: Blockchain registration
- **TRAINING**: AI model creation with contamination rate
- **SUCCESS**: Confirmation with counts

---

### 2. Hash Comparison & Blockchain

**WHERE #1**: Console window (during baseline/monitor)
```
[Blockchain] Block 1 Mined: Device 6C:E8:C6:8C:87:10 secured.
Hash: def456789abcdef01234567890abcdef01234567890abcdef...
Previous Hash: 8c8f7b5e7d3a9f2b1c4e6f8a9b0c1d2e3f4a5b6c7d8e9f0...
```

**WHERE #2**: File `blockchain/chain.json`
```json
[
  {
    "index": 0,
    "timestamp": 1780815250.82,
    "device_id": "Genesis",
    "behavior_data": {"status": "Genesis Block"},
    "previous_hash": "0",
    "hash": "8c8f7b5e7d3a9f2b1c4e6f8a9b0c1d2e3f4a5b6c7d8e9f0"
  },
  {
    "index": 1,
    "timestamp": 1780815265.45,
    "device_id": "6C:E8:C6:8C:87:10",
    "behavior_data": {
      "mean_rssi": -32.5,
      "mean_interval_ms": 487.3,
      "packet_count": 32
    },
    "previous_hash": "8c8f7b5e7d3a9f2b1c4e6f8a9b0c1d2e3f4a5b6c7d8e9f0",  ← Must match Block 0 hash!
    "hash": "def456789abcdef01234567890abcdef01234567890abcdef"
  }
]
```

**WHERE #3**: Dashboard "Blockchain Ledger" section
```
Block #0 | Device: Genesis
Hash: 8c8f7b5e7d3a9f2b...

Block #1 | Device: 6C:E8:C6:8C:87:10
Hash: def456789abcdef...
Behavior: RSSI=-32.5, Interval=487.3ms, Packets=32
```

**Hash Validation Happens**:
```python
# In blockchain.py:
def is_chain_valid(self):
    for i in range(1, len(self.chain)):
        current = self.chain[i]
        previous = self.chain[i-1]
        
        # Check 1: Hash hasn't been tampered with
        if current.hash != current.calculate_hash():
            return False  # ← Block modified!
        
        # Check 2: Chain link intact
        if current.previous_hash != previous.hash:
            return False  # ← Chain broken!
    
    return True
```

**Dashboard shows**: "Chain is valid: VALID ✓" or "INVALID ✗"

---

### 3. Payload Inspection

**WHERE #1**: Raw packets in `dataset/ble_data.csv`
```csv
timestamp,mac_address,rssi,interval_ms,services_count,name
1780815250.82,6C:E8:C6:8C:87:10,-28,0.0,1,Unknown
1780815250.83,6C:E8:C6:8C:87:10,-25,12.25,1,JioSTB85892Living Room TV
1780815251.45,6C:E8:C6:8C:87:10,-36,612.12,1,JioSTB85892Living Room TV
```

**WHERE #2**: Features in console output (PHASE 2)
```
Device Behavioral Fingerprints:
mac_address          mean_rssi  mean_interval  std_interval  packet_count  services  name
6C:E8:C6:8C:87:10    -32.50     487.30         312.10        32            1         JioSTB
```

**WHERE #3**: Blockchain payload in `blockchain/chain.json`
```json
{
  "behavior_data": {
    "mean_rssi": -32.5,
    "mean_interval_ms": 487.3,
    "packet_count": 32
  }
}
```

**WHERE #4**: Alert payload in `dataset/alerts.csv` (when anomaly detected)
```csv
timestamp,mac_address,device_name,anomaly_score,criticality
2026-06-07 12:30:15,11:22:33:44:55:66,BLE_Flooder_Attack,-0.345,HIGH
```

**WHERE #5**: Dashboard tables
- Detected Devices table: Shows mean_rssi, mean_interval, packet_count
- Security Alerts: Shows anomaly_score, criticality
- Blockchain Ledger: Shows behavior_data

---

### 4. Anomaly Detection in Action

**WHERE**: Console window (when you click "Start Monitor Scan")

**WHAT YOU'LL SEE**:
```
============================================================
                   ACTIVE MONITORING MODE                    
============================================================

[AI] Successfully loaded pre-trained Isolation Forest model from ai_model\isolation_forest.pkl

>>> MONITORING CYCLE 1/1 <<<
###########################################################
--- [PHASE 1] Starting Data Capture (15s, mode=monitor) ---
Starting BLE Scanner for 15 seconds (Behavioral Capture)...
[12:35:10] MAC: 6C:E8:C6:8C:87:10 | RSSI:  -30 dBm | Interval: 0.0 ms
[12:35:11] MAC: 11:22:33:44:55:66 | RSSI:  -35 dBm | Interval: 0.0 ms  ← Attack!
...

--- [PHASE 2] Extracting Behavioral Features ---
Loaded 52 raw data points.
Extracted behavioral features for 8 unique devices.

--- [PHASE 3] Active Monitoring & Anomaly Detection ---
[6C:E8:C6:8C:87:10] JioSTB85892Liv -> NORMAL [OK] (Score: 0.124)
[01:B6:EC:B6:D7:E7] SWAN           -> NORMAL [OK] (Score: 0.089)
[10:2B:41:23:7C:31] Unknown        -> NORMAL [OK] (Score: 0.056)
[11:22:33:44:55:66] BLE_Flooder_At -> ANOMALY DETECTED! [!] (Score: -0.345)

==================================================
! SECURITY ALERT: ANOMALOUS DEVICE DETECTED !
==================================================
Time          : 2026-06-07 12:35:25
Device Name   : BLE_Flooder_Attack
MAC Address   : 11:22:33:44:55:66
Anomaly Score : -0.345
Criticality   : HIGH
==================================================
ACTION: Device blocked from Blockchain Identity Registry.

[Blockchain] Device 6C:E8:C6:8C:87:10 already verified in ledger. Skipping.
[Blockchain] Device 01:B6:EC:B6:D7:E7 already verified in ledger. Skipping.

============================================================
                 MONITORING SESSION COMPLETED                
============================================================

╔══════════════════════════════════════════════════╗
║            FINAL SECURITY RESULT CORNER          ║
╠══════════════════════════════════════════════════╣
║  OVERALL STATUS: THREATS DETECTED ⚠               ║
║  Detected 1 Anomaly Event(s).                    ║
╠══════════════════════════════════════════════════╣
║  SPOOFING/ANOMALOUS DEVICE LOG:                  ║
║  • BLE_Flooder_ 11:22:33:44:55:66 [  HIGH] ║
╚══════════════════════════════════════════════════╝
```

**KEY SECTIONS**:
- **Model loaded**: Shows model was loaded from disk (not retrained)
- **PHASE 3**: Each device analyzed with score
- **SECURITY ALERT**: Detailed alert for anomaly
- **FINAL RESULT**: Summary of threats

---

### 5. Baseline vs Monitor - Side by Side

| Aspect | Baseline | Monitor |
|--------|----------|---------|
| **Console Title** | "BASELINE LEARNING MODE" | "ACTIVE MONITORING MODE" |
| **Phase 3 Header** | "Baseline Learning Mode" | "Active Monitoring & Anomaly Detection" |
| **Device Output** | "[Baseline] Device XXX registered as TRUSTED" | "[XXX] Device -> NORMAL [OK] or ANOMALY [!]" |
| **AI Operation** | "[AI] Training Isolation Forest..." | "[AI] Successfully loaded pre-trained model" |
| **Alerts** | None (all devices trusted) | "SECURITY ALERT!" for anomalies |
| **Blockchain** | "Block X Mined: Device XXX secured" | "Device XXX already verified" (skips duplicates) |
| **Final Output** | "SUCCESS! X devices learned" | "SAFE [OK]" or "THREATS DETECTED ⚠" |

---

### 6. Dashboard Sections Explained

**URL**: http://127.0.0.1:5000

**Section 1: Statistics Cards (Top)**
```
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ TOTAL       │ SECURITY    │ BLOCKCHAIN  │ AI MODEL    │ TOTAL       │
│ DEVICES     │ ALERTS      │ BLOCKS      │             │ PACKETS     │
│             │             │             │             │             │
│     7       │      1      │      8      │     ✅      │     45      │
│ Discovered  │ Anomalies   │ Not Init... │ Trained     │ Captured    │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```
- **Total Devices**: Unique MACs found
- **Security Alerts**: Number of anomalies
- **Blockchain Blocks**: Length of chain
- **AI Model**: ✅ Trained or ❌ Not Trained
- **Total Packets**: Raw data points

**Section 2: Detected BLE Devices (Table)**
```
┌────────────────────┬────────────────┬────────────┬──────────────┬─────────┬──────────┬────────────┬────────────┐
│ MAC Address        │ Device Name    │ Signal     │ Avg Interval │ Packets │ Services │ First Seen │ Last Seen  │
├────────────────────┼────────────────┼────────────┼──────────────┼─────────┼──────────┼────────────┼────────────┤
│ 6C:E8:C6:8C:87:10  │ JioSTB...      │ -32.5 dBm  │ 487.3 ms     │   32    │    1     │ 12:30:15   │ 12:30:45   │
│ 11:22:33:44:55:66  │ BLE_Flooder    │ -35.0 dBm  │   5.5 ms     │   20    │    0     │ 12:35:10   │ 12:35:25   │
└────────────────────┴────────────────┴────────────┴──────────────┴─────────┴──────────┴────────────┴────────────┘
```
- **Signal**: RSSI in dBm (closer = higher number)
- **Avg Interval**: How often device advertises
- **Packets**: How many times seen
- **Services**: BLE services count

**Section 3: Security Alerts**
```
┌──────────────────────────────────────────────────────────────────┐
│ ⚠️ BLE_Flooder_Attack (11:22:33:44:55:66)                        │
│ Anomaly Score: -0.345 | Criticality: HIGH | Time: 12:35:25      │
└──────────────────────────────────────────────────────────────────┘
```
- **Red background**: HIGH criticality
- **Yellow background**: MEDIUM/LOW criticality
- **Score**: More negative = more anomalous

**Section 4: Blockchain Ledger**
```
┌──────────────────────────────────────────────────────────────────┐
│ Block #0 | Device: Genesis                                       │
│ Hash: 8c8f7b5e7d3a9f2b...                                        │
├──────────────────────────────────────────────────────────────────┤
│ Block #1 | Device: 6C:E8:C6:8C:87:10                             │
│ Hash: def456789abcdef...                                         │
│ Behavior: RSSI=-32.5, Interval=487.3ms, Packets=32              │
└──────────────────────────────────────────────────────────────────┘
```
- **Hash**: First 40 characters of SHA-256 hash
- **Behavior**: Behavioral fingerprint stored

---

## 🎯 Quick Reference: Where Do I See...?

| What | Where |
|------|-------|
| **AI Training** | Console (baseline mode) → "Training Isolation Forest..." |
| **Contamination Rate** | Console (baseline) → "Using contamination rate: 0.300" |
| **Feature Extraction** | Console (PHASE 2) → Device Behavioral Fingerprints table |
| **Hashes** | Console + blockchain/chain.json + Dashboard |
| **Hash Validation** | Console (when loading blockchain) + Dashboard "Valid ✓" |
| **Raw Packets** | Console (PHASE 1) + dataset/ble_data.csv |
| **Blockchain Payload** | blockchain/chain.json + Dashboard Ledger section |
| **Alert Payload** | Console (Security Alert box) + dataset/alerts.csv + Dashboard |
| **Anomaly Detection** | Console (monitor mode PHASE 3) + Dashboard Alerts |
| **Model Status** | Console ("Model trained" or "Model loaded") + Dashboard |
| **Device Count** | Console + Dashboard statistics card |

---

## 📂 File Locations

| File | Contains | When Created |
|------|----------|--------------|
| `dataset/ble_data.csv` | Raw BLE packets | During any scan |
| `dataset/alerts.csv` | Alert log | When anomaly detected (monitor mode) |
| `ai_model/isolation_forest.pkl` | Trained AI model | After baseline completes |
| `blockchain/chain.json` | Blockchain ledger | During baseline/monitor |

---

## 🎓 Understanding the Output

**Positive Score** (e.g., 0.124):
- Device behavior matches baseline
- Within normal parameters
- SAFE

**Negative Score** (e.g., -0.345):
- Device behavior differs from baseline
- Outside normal parameters
- More negative = more suspicious
- ANOMALY!

**Criticality Levels**:
- **Score > -0.1**: LOW (minor deviation)
- **Score -0.1 to -0.2**: MEDIUM (notable difference)
- **Score < -0.2**: HIGH (major threat)

---

**Now you know exactly where to look for everything!** 🎯
