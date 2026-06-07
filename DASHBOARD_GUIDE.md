# 🎯 Dashboard & Attack Simulation Guide

## Understanding the Workflow

### ❌ What Dashboard Refresh DOESN'T Do
- **Does NOT scan for BLE devices**
- Just updates the display from existing files
- Only shows data already collected

### ✅ What You Need to Do

The workflow has **3 separate components**:

```
1. SCAN (main.py)  →  2. ATTACK (attack_simulator.py)  →  3. VIEW (dashboard.py)
```

---

## 🚀 Complete Workflow

### Step 1: Clear Old Data (Fresh Start)
```bash
# Option A: Use dashboard button
Click "🗑️ Clear All Data" in the dashboard

# Option B: Manual
python -c "import os; from config import *; [os.remove(f) for f in [BLE_DATA_PATH, ALERTS_PATH, CHAIN_PATH, MODEL_PATH] if os.path.exists(f)]"
```

### Step 2: Establish Baseline (Learn Normal Behavior)
```bash
# Scan your real environment
python main.py --mode baseline --cycles 3
```

**This will:**
- Scan for 3 cycles (45 seconds total)
- Detect your real devices (JioSTB, SWAN, etc.)
- Train AI model on NORMAL behavior
- Save model to disk

### Step 3: Inject Attack (Simulate Threat)

**Option A: Interactive Menu**
```bash
python attack_simulator.py
```
Select from 5 attack types:
1. Device Spoofing (pretends to be your TV)
2. Packet Flooding (rapid bursts)
3. Malicious Scanner (reconnaissance)
4. Erratic Device (unstable behavior)
5. Rogue Access Point (MITM attempt)

**Option B: Command Line**
```bash
python attack_simulator.py spoofing 20 10
# attack_type packets duration
```

**Option C: Dashboard Button**
1. Open dashboard: http://127.0.0.1:5000
2. Click "⚠️ Inject Attack"
3. Select attack type from menu

### Step 4: Monitor & Detect (See Anomalies)
```bash
python main.py --mode monitor --cycles 2
```

**This will:**
- Load the trained model
- Scan environment (including injected attack)
- **DETECT the attack as ANOMALY**
- Trigger security alerts
- Show in final report

### Step 5: View Results in Dashboard
```bash
# Dashboard should already be running
# If not: python dashboard.py

# Open: http://127.0.0.1:5000
```

**Dashboard shows:**
- All detected devices (normal + attack)
- **Security alerts** (attack flagged)
- Anomaly scores and criticality levels
- Blockchain ledger
- Real-time statistics

---

## 🎭 Attack Scenarios Explained

### 1. Device Spoofing
```python
MAC: AA:BB:CC:DD:EE:FF
Name: Spoofed_JioSTB_Attacker
Pattern: Different RSSI, faster intervals than real device
Detection: AI spots the behavioral mismatch
```

**Why it's detected:**
- Real JioSTB: ~700ms intervals, -25 to -42 dBm
- Fake device: ~100ms intervals, -45 to -55 dBm
- **AI sees the difference!**

### 2. Packet Flooding
```python
MAC: 11:22:33:44:55:66
Name: BLE_Flooder_Attack
Pattern: 1-10ms intervals (VERY fast)
Detection: Abnormally high packet rate
```

**Why it's detected:**
- Normal devices: 500-2000ms intervals
- Flooder: 1-10ms intervals (100x faster!)
- **Obvious anomaly**

### 3. Malicious Scanner
```python
MAC: DE:AD:BE:EF:CA:FE
Name: Malicious_Scanner
Pattern: 2000-5000ms intervals, 5 services
Detection: Unusual service count + slow pattern
```

**Why it's detected:**
- Your devices: 0-1 services
- Scanner: 5 services (reconnaissance tool)
- **Service count mismatch**

### 4. Erratic Device
```python
MAC: BA:D1:DE:A0:00:00
Name: Unstable_Device_Attack
Pattern: Wildly varying everything
Detection: High standard deviation in features
```

**Why it's detected:**
- Normal devices: Stable behavior
- Erratic: RSSI -90 to -20, intervals 5ms to 5000ms
- **Unstable = suspicious**

### 5. Rogue Access Point
```python
MAC: FA:KE:AP:01:02:03
Name: Rogue_AccessPoint
Pattern: Very strong signal, many services
Detection: Unusual combination of features
```

**Why it's detected:**
- Strong signal (-25 to -35 dBm)
- 8 services advertised
- **Looks like fake AP**

---

## 📊 Expected Output Example

### After Running Monitor Mode:

```
[AI] Successfully loaded pre-trained Isolation Forest model

--- [PHASE 1] Starting Data Capture (15s, mode=monitor) ---
[12:30:15] MAC: 6C:E8:C6:8C:87:10 | ... | Name: JioSTB85892Living Room TV
[12:30:16] MAC: AA:BB:CC:DD:EE:FF | ... | Name: Spoofed_JioSTB_Attacker

--- [PHASE 3] Active Monitoring & Anomaly Detection ---
[6C:E8:C6:8C:87:10] JioSTB85892Liv -> NORMAL [OK] (Score: 0.124)
[AA:BB:CC:DD:EE:FF] Spoofed_JioSTB -> ANOMALY DETECTED! [!] (Score: -0.345)

==================================================
! SECURITY ALERT: ANOMALOUS DEVICE DETECTED !
==================================================
Time          : 2026-06-07 12:30:30
Device Name   : Spoofed_JioSTB_Attacker
MAC Address   : AA:BB:CC:DD:EE:FF
Anomaly Score : -0.345
Criticality   : HIGH
==================================================

╔══════════════════════════════════════════════════╗
║            FINAL SECURITY RESULT CORNER          ║
╠══════════════════════════════════════════════════╣
║  OVERALL STATUS: THREATS DETECTED ⚠               ║
║  Detected 1 Anomaly Event(s).                    ║
╠══════════════════════════════════════════════════╣
║  SPOOFING/ANOMALOUS DEVICE LOG:                  ║
║  • Spoofed_JioS AA:BB:CC:DD:EE:FF [  HIGH] ║
╚══════════════════════════════════════════════════╝
```

---

## 🔄 Complete Demo Script

```bash
# 1. Clear everything
python -c "from pathlib import Path; import os; from config import *; [os.remove(f) for f in [BLE_DATA_PATH, ALERTS_PATH, CHAIN_PATH, MODEL_PATH] if os.path.exists(f)]; print('✅ Cleared')"

# 2. Run baseline (learn normal)
python main.py --mode baseline --cycles 2

# 3. Inject attack
python attack_simulator.py spoofing 20 10

# 4. Detect attack
python main.py --mode monitor --cycles 1

# 5. View in dashboard (http://127.0.0.1:5000)
# Dashboard shows the attack in alerts!
```

---

## ❓ Troubleshooting

### "No anomalies detected"
**Problem**: Attack packets added, but model sees them as normal

**Solutions:**
1. Make sure baseline was run FIRST (model must be trained on normal data)
2. Inject MORE attack packets: `python attack_simulator.py spoofing 50 15`
3. Use a different attack type (try 'flooding' - most obvious)

### "Model not trained" error
**Problem**: Running monitor without baseline

**Solution:**
```bash
python main.py --mode baseline --cycles 2
```

### Attack not showing in dashboard
**Problem**: Dashboard caches data

**Solutions:**
1. Click "🔄 Refresh Dashboard"
2. Hard refresh browser: Ctrl+F5
3. Close and reopen dashboard

---

## 🎨 UI/UX Improvements (TODO)

As you mentioned, the dashboard UI needs work. Here's what we can improve:

1. **Better visualizations**
   - Real-time charts (RSSI over time, packet rates)
   - Device network graph
   - Alert timeline

2. **Enhanced controls**
   - Start/stop scanning from dashboard
   - Real-time scan progress
   - Attack simulation builder

3. **Improved styling**
   - Dark mode toggle
   - Better color scheme for alerts
   - Responsive mobile layout

4. **Advanced features**
   - Export reports (PDF/CSV)
   - Alert notifications (email/SMS)
   - Historical trend analysis

We can work on these after verifying the core functionality works!

---

## 🎯 Summary

**Key Points:**
1. Dashboard does NOT scan - it only displays
2. You must run `main.py` separately to scan
3. Attack simulator injects fake packets into dataset
4. Monitor mode detects attacks using trained model
5. Dashboard shows results in real-time

**Workflow:**
```
Baseline → Inject Attack → Monitor → View Dashboard
```

This separation ensures proper train/test methodology and makes the system production-ready!
