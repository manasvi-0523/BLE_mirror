# 🎓 Complete System Explanation

## 🤔 Your Questions Answered

### 1. "What's the difference between baseline and monitor scan?"

#### **BASELINE SCAN** (Training Phase)
**Purpose**: Learn what NORMAL looks like

**What it does**:
1. Scans your BLE environment (your devices: TV, phone, etc.)
2. Collects behavioral data for each device
3. **Trains the AI model** on this "normal" data
4. Saves the trained model to disk (`isolation_forest.pkl`)
5. Registers all devices in blockchain as "TRUSTED"

**When to use**: 
- First time setup
- When you want to reset what's considered "normal"
- In a clean, trusted environment (no attackers present)

**Analogy**: Like teaching a security guard what your family members look like

**Example Output**:
```
[Baseline] Device 6C:E8:C6:8C:87:10 (JioSTB) registered as TRUSTED
[Baseline] Device 01:B6:EC:B6:D7:E7 (SWAN) registered as TRUSTED
...
[AI] Training Isolation Forest on 7 baseline devices...
[AI] Using contamination rate: 0.300 (dynamic for small dataset)
[SUCCESS] Baseline complete! 7 devices learned.
```

---

#### **MONITOR SCAN** (Detection Phase)
**Purpose**: Detect anything DIFFERENT from normal

**What it does**:
1. **Loads the trained model** from disk
2. Scans current BLE environment
3. **Compares** new devices against learned baseline
4. Flags devices with anomalous behavior
5. Triggers alerts for suspicious devices

**When to use**:
- After baseline is established
- For ongoing security monitoring
- To detect new/rogue devices

**Analogy**: Like the security guard checking if someone is family or an intruder

**Example Output**:
```
[AI] Successfully loaded pre-trained model
[6C:E8:C6:8C:87:10] JioSTB → NORMAL [OK] (Score: 0.124)
[11:22:33:44:55:66] BLE_Flooder_Attack → ANOMALY DETECTED! [!] (Score: -0.345)

🚨 SECURITY ALERT: ANOMALOUS DEVICE DETECTED!
Device: BLE_Flooder_Attack
Criticality: HIGH
```

---

### 2. "How is the AI model trained? Should be visible"

#### **AI Training Process (Visible in Console)**

**Step 1: Data Collection**
```
Starting BLE Scanner for 15 seconds...
[12:30:15] MAC: 6C:E8:C6:8C:87:10 | RSSI: -28 dBm | Interval: 612 ms
[12:30:16] MAC: 01:B6:EC:B6:D7:E7 | RSSI: -46 dBm | Interval: 4 ms
...
```
**What's happening**: Raw BLE packets captured (MAC, signal strength, timing)

**Step 2: Feature Extraction**
```
Loaded 45 raw data points.
Extracted behavioral features for 7 unique devices.

Device Behavioral Fingerprints:
mac_address          mean_rssi  mean_interval  std_interval  packet_count
6C:E8:C6:8C:87:10    -32.5      487.3          312.1         32
01:B6:EC:B6:D7:E7    -46.5      2.5            1.2           2
...
```
**What's happening**: 
- Groups packets by device
- Calculates statistics per device:
  - `mean_rssi`: Average signal strength
  - `mean_interval`: Average time between packets
  - `std_interval`: How consistent the timing is
  - `packet_count`: How many times seen

**Step 3: AI Training**
```
[AI] Training Isolation Forest on 7 baseline behavioral fingerprints...
[AI] Using contamination rate: 0.300 (dynamic adjustment for 7 samples)
[AI] Model successfully trained & saved to ai_model\isolation_forest.pkl
```
**What's happening**:
- **Isolation Forest** algorithm learns boundaries of "normal" behavior
- Creates mathematical model of what's expected
- `contamination rate 0.300` = expects 30% of future data might be anomalies
- Saves model to disk for reuse

#### **The Math Behind It**

**Isolation Forest Algorithm**:
```
Normal Device Pattern (JioSTB):
- RSSI: -25 to -42 dBm (stable)
- Interval: 600-800ms (consistent)
- Variation: Low (±100ms)
→ Score: 0.124 (positive = normal)

Attack Device Pattern (Flooder):
- RSSI: -30 to -40 dBm (similar) ✓
- Interval: 1-10ms (VERY different!) ✗
- Variation: High (±5ms from 1-10ms range)
→ Score: -0.345 (negative = anomaly)
```

**Decision**: Interval 100x faster than baseline → **ANOMALY!**

---

### 3. "Where are the hashes seen and compared?"

#### **Blockchain Hash System** (Visible in blockchain.json)

**What Gets Hashed**:
```python
{
  "index": 1,
  "timestamp": 1780815250.82,
  "device_id": "6C:E8:C6:8C:87:10",
  "behavior_data": {
    "mean_rssi": -32.5,
    "mean_interval_ms": 487.3,
    "packet_count": 32
  },
  "previous_hash": "abc123..."  ← Links to previous block
}
↓ SHA-256 Hash
"def456789..."  ← This block's hash
```

**Hash Verification** (In `blockchain.py`):
```python
def is_chain_valid(self):
    for i in range(1, len(self.chain)):
        current = self.chain[i]
        previous = self.chain[i-1]
        
        # Recalculate hash
        if current.hash != current.calculate_hash():
            print("Block {i} has been tampered with!")
            return False
        
        # Verify chain link
        if current.previous_hash != previous.hash:
            print("Chain broken at block {i}!")
            return False
    
    return True
```

**How to See Hashes**:

**Option 1: Console Output** (during baseline/monitor)
```
[Blockchain] Block 1 Mined: Device 6C:E8:C6:8C:87:10 secured.
Hash: def456789abcdef...
Previous: abc123456789...
```

**Option 2: blockchain/chain.json file**
```json
[
  {
    "index": 0,
    "device_id": "Genesis",
    "hash": "abc123456789...",
    "previous_hash": "0"
  },
  {
    "index": 1,
    "device_id": "6C:E8:C6:8C:87:10",
    "hash": "def456789abc...",
    "previous_hash": "abc123456789..."  ← Must match block 0's hash
  }
]
```

**Option 3: Dashboard** (Blockchain Ledger section)
```
Block #1 | Device: 6C:E8:C6:8C:87:10
Hash: def456789abc...
```

**Hash Comparison Happens**:
1. When loading blockchain from disk (validates all hashes)
2. When adding new blocks (checks previous hash matches)
3. Dashboard shows validation status: "✓ Valid" or "✗ Invalid"

---

### 4. "What about the payload?"

#### **Complete Payload Breakdown**

**Raw BLE Packet** (captured by scanner):
```python
{
  "timestamp": 1780815250.82,      # When seen
  "mac_address": "6C:E8:C6:8C:87:10",  # Device ID
  "rssi": -28,                     # Signal strength (dBm)
  "interval_ms": 612.12,           # Time since last seen
  "services_count": 1,             # Number of BLE services
  "name": "JioSTB85892Living Room TV"  # Device name
}
```

**Behavioral Fingerprint** (extracted features):
```python
{
  "mac_address": "6C:E8:C6:8C:87:10",
  "mean_rssi": -32.5,              # Average signal
  "mean_interval": 487.3,          # Average timing
  "std_interval": 312.1,           # Timing consistency
  "packet_count": 32,              # Frequency
  "services_count": 1,             # Services
  "name": "JioSTB85892Living Room TV"
}
```

**Blockchain Payload** (stored in ledger):
```python
{
  "index": 1,
  "timestamp": 1780815250.82,
  "device_id": "6C:E8:C6:8C:87:10",
  "behavior_data": {               # Fingerprint stored
    "mean_rssi": -32.5,
    "mean_interval_ms": 487.3,
    "packet_count": 32
  },
  "previous_hash": "abc123...",
  "hash": "def456..."              # SHA-256 of all above
}
```

**Alert Payload** (when anomaly detected):
```python
{
  "timestamp": "2026-06-07 12:30:15",
  "mac_address": "11:22:33:44:55:66",
  "device_name": "BLE_Flooder_Attack",
  "anomaly_score": -0.345,         # How anomalous
  "criticality": "HIGH"            # Risk level
}
```

**Where to See Payloads**:
- **Console**: Full output during scans
- **dataset/ble_data.csv**: Raw packets
- **blockchain/chain.json**: Blockchain payloads
- **dataset/alerts.csv**: Alert payloads
- **Dashboard**: Formatted display

---

### 5. "How do I use it?"

#### **Complete Workflow (Step-by-Step)**

**SCENARIO**: You want to detect if someone is trying to attack your BLE devices

**Step 1: Fresh Start**
```bash
# Open dashboard
http://127.0.0.1:5000

# Click "Clear All Data"
→ Removes old scans, model, blockchain
→ Clean slate
```

**Step 2: Establish Baseline** (What's Normal)
```bash
# Make sure ONLY your devices are on
# Turn off unknown Bluetooth devices
# This is your "trusted" environment

# Click "Start Baseline Scan"
→ Enter: 2 (cycles)
→ Confirm

# New console window opens
# Watch it scan your environment:
[12:30:15] MAC: 6C:E8:C6:8C:87:10 | JioSTB
[12:30:16] MAC: 01:B6:EC:B6:D7:E7 | SWAN
...

# After ~30 seconds:
[SUCCESS] Baseline established! 7 devices learned.

# Your devices are now "TRUSTED"
```

**What just happened**:
- Scanned your environment
- Found 7 devices (your TV, phone, etc.)
- Learned their behavior patterns
- Trained AI model on this data
- Saved model to disk
- Registered all devices in blockchain as "TRUSTED"

**Step 3: Simulate Attack** (Optional - For Testing)
```bash
# Back in dashboard
# Click "Inject Attack"
→ Select "Packet Flooding"
→ Confirm

# Fake attacker device injected into dataset
# MAC: 11:22:33:44:55:66
# Behavior: 1-10ms intervals (WAY faster than normal)
```

**Step 4: Monitor for Threats**
```bash
# Click "Start Monitor Scan"
→ Enter: 1 (cycle)
→ Confirm

# New console window opens
# Watch AI analyze each device:
[6C:E8:C6:8C:87:10] JioSTB → NORMAL [OK] (Score: 0.124)
[01:B6:EC:B6:D7:E7] SWAN → NORMAL [OK] (Score: 0.089)
[11:22:33:44:55:66] BLE_Flooder → ANOMALY DETECTED! [!] (Score: -0.345)

🚨 SECURITY ALERT!
Device: BLE_Flooder_Attack
Criticality: HIGH
```

**What happened**:
- Loaded trained AI model
- Scanned environment (including fake attack)
- Compared each device to baseline
- Your devices: Match baseline → NORMAL
- Attack device: Different behavior → **ANOMALY!**

**Step 5: View Results**
```bash
# Back in dashboard (auto-refreshes)
# See:
- Security Alerts: RED box showing attack
- Device table: All devices listed
- Blockchain: Trusted devices recorded
- Stats: 1 anomaly detected
```

---

#### **Real-World Usage**

**Setup Once**:
```bash
1. Run baseline in your home/office
2. Let it learn your devices
3. Model saved to disk
```

**Daily Monitoring**:
```bash
1. Open dashboard
2. Click "Start Monitor Scan"
3. Check for alerts
4. If alerts appear → investigate
```

**When Alert Appears**:
```bash
1. Check device MAC address
2. Is it a device you recognize?
   - YES → Might be false positive, re-run baseline
   - NO → Potential attacker/rogue device
3. Check criticality:
   - LOW: Minor deviation (maybe ignore)
   - MEDIUM: Investigate
   - HIGH: Immediate threat!
```

---

### 6. "How does AI know it's an attack?"

#### **The Detection Logic**

**Training (Baseline)**:
```
Device A: RSSI -30, Interval 700ms, Variation ±100ms
Device B: RSSI -45, Interval 500ms, Variation ±50ms
Device C: RSSI -35, Interval 800ms, Variation ±150ms

AI learns: "Normal devices have 500-800ms intervals, ±50-150ms variation"
```

**Detection (Monitor)**:
```
New Device X: RSSI -35, Interval 5ms, Variation ±2ms

AI compares:
- RSSI -35: ✓ Within range (-30 to -45)
- Interval 5ms: ✗ WAY outside range (500-800ms)
- Variation ±2ms: ✗ Much tighter than normal

Decision: ANOMALY! Score: -0.345 (very negative)
```

**Why It Works**:
- Normal devices: Consistent patterns
- Attack devices: Different patterns (faster, slower, erratic)
- AI spots the differences mathematically

**Examples**:

**Spoofing Attack**:
```
Real JioSTB: -28dBm, 700ms intervals
Fake JioSTB: -45dBm, 100ms intervals
→ Different signal + different timing = DETECTED!
```

**Flooding Attack**:
```
Normal: 500-800ms between packets
Flooder: 1-10ms between packets (100x faster!)
→ Abnormal rate = DETECTED!
```

**Scanner Attack**:
```
Normal: 0-1 services advertised
Scanner: 5 services advertised
→ Unusual service count = DETECTED!
```

---

## 📊 Summary

| Aspect | Baseline | Monitor |
|--------|----------|---------|
| **Purpose** | Learn normal | Detect anomalies |
| **When** | First time, clean environment | Ongoing monitoring |
| **AI Model** | Trains and saves | Loads from disk |
| **Output** | Registers all as TRUSTED | Flags anomalies |
| **Blockchain** | Creates new chain | Appends to chain |
| **Alerts** | None (everything normal) | Triggers on anomalies |

| Data | Where to See It |
|------|----------------|
| **Raw packets** | Console output, `dataset/ble_data.csv` |
| **Features** | Console output (feature extraction phase) |
| **AI training** | Console output (`[AI] Training...`) |
| **Hashes** | Console, `blockchain/chain.json`, dashboard |
| **Alerts** | Console, `dataset/alerts.csv`, dashboard |
| **Blockchain** | `blockchain/chain.json`, dashboard ledger section |

---

## 🎯 Quick Reference

**First Time Setup**:
1. Clear All Data
2. Start Baseline Scan (2 cycles)
3. Wait ~30 seconds
4. Done! Model trained.

**Daily Monitoring**:
1. Start Monitor Scan (1-2 cycles)
2. Check dashboard for alerts
3. Done!

**Testing with Attack**:
1. Clear All Data
2. Start Baseline (learn normal)
3. Inject Attack (simulate threat)
4. Start Monitor (detect threat)
5. See alert in dashboard!

---

**Need more details on any specific part? Let me know!**
