# 🎯 Quick Demo - See It Working in 5 Minutes

## What You Have Now

✅ **Dashboard running** at http://127.0.0.1:5000  
✅ **Attack simulator** ready to inject threats  
✅ **Main system** ready to detect anomalies  

---

## 🚀 5-Minute Demo

### Step 1: Open Dashboard (Already Running)
Visit: **http://127.0.0.1:5000**

You should see:
- Current data from your earlier baseline scan
- 7 devices detected
- Maybe old data showing

### Step 2: Clear Everything (Fresh Start)
**In the dashboard:**
1. Click **"🗑️ Clear All Data"** button
2. Confirm the popup
3. ✅ Everything reset!

### Step 3: Run Baseline (30 seconds)
**In a NEW PowerShell window:**
```bash
cd C:\Users\Lenovo\Desktop\mini_projects\BLE
python main.py --mode baseline --cycles 2
```

This scans your environment and trains the AI model.

**Dashboard will show:**
- Real devices appearing (JioSTB, SWAN, etc.)
- Packet counts increasing
- Model status: ✅ Trained

### Step 4: Inject Attack (From Dashboard!)
**In the dashboard:**
1. Click **"⚠️ Inject Attack"** button
2. Select **"💥 Packet Flooding"** (most obvious)
3. Confirm

✅ Attack injected! 20 malicious packets added.

### Step 5: Detect the Attack (20 seconds)
**In PowerShell:**
```bash
python main.py --mode monitor --cycles 1
```

Watch the console! You'll see:

```
[6C:E8:C6:8C:87:10] JioSTB... -> NORMAL [OK]
[11:22:33:44:55:66] BLE_Flooder_Attack -> ANOMALY DETECTED! [!]

🚨 SECURITY ALERT: ANOMALOUS DEVICE DETECTED!
Device: BLE_Flooder_Attack
Criticality: HIGH
```

### Step 6: View Results in Dashboard
**Refresh dashboard** (click 🔄 button)

You'll see:
- **Security Alerts section** shows the attack
- **Red/yellow highlighting** on anomalous device
- **HIGH criticality** badge
- **Anomaly score** displayed

---

## 🎭 Try Different Attacks

After the first demo, try other attack types:

### Attack #1: Device Spoofing
```bash
# Clear data
python attack_simulator.py spoofing 20 10
python main.py --mode monitor --cycles 1
```
**Effect**: Pretends to be your TV with different behavior

### Attack #2: Malicious Scanner
```bash
python attack_simulator.py scanner 15 12
python main.py --mode monitor --cycles 1
```
**Effect**: Reconnaissance device with unusual service count

### Attack #3: Rogue Access Point
```bash
python attack_simulator.py rogue_ap 25 10
python main.py --mode monitor --cycles 1
```
**Effect**: Strong signal, many services, MITM attempt

### Attack #4: All Attacks at Once
```bash
python attack_simulator.py
# Select option 6: Inject ALL attacks
python main.py --mode monitor --cycles 2
```
**Effect**: Multiple threat vectors detected!

---

## 📊 What Makes This Work

### The Key Difference

**❌ OLD WAY (What GitHub main still has):**
```
Scan → Train on same data → Predict on same data
Result: Everything looks normal (false negative)
```

**✅ NEW WAY (What you're running now):**
```
Day 1: Baseline → Train on normal devices → Save model
Day 2: Monitor → Load model → Scan → Detect NEW threats
Result: Real anomaly detection!
```

### Why Attacks Are Detected

**Your JioSTB (Normal):**
- RSSI: -25 to -42 dBm
- Intervals: ~700ms
- Services: 1
- Packet count: 30-40 per scan

**BLE_Flooder_Attack (Malicious):**
- RSSI: -30 to -40 dBm (similar)
- Intervals: **1-10ms** (100x faster!)
- Services: 0
- Packet count: 20

**AI sees the interval difference → ANOMALY!**

---

## 🎨 Dashboard Features

### Current Features
- ✅ Real-time data display (auto-refresh every 5s)
- ✅ Device list with behavioral stats
- ✅ Security alerts with criticality levels
- ✅ Blockchain ledger viewer
- ✅ **Clear all data** button
- ✅ **Inject attack** button (5 attack types)
- ✅ Statistics dashboard

### Coming Soon (UI/UX Improvements)
- 📈 Real-time charts (RSSI trends, packet rates)
- 🌓 Dark mode toggle
- 📱 Better mobile layout
- 📧 Email/SMS alerts
- 📄 Export reports (PDF/CSV)
- ▶️ Start/stop scanning from dashboard
- 📊 Device network graph

---

## ⚡ Pro Tips

### Tip 1: Multiple Attack Vectors
```bash
# Inject several attacks
python attack_simulator.py flooding 30 8
python attack_simulator.py spoofing 20 10
python attack_simulator.py rogue_ap 25 12

# Detect all of them
python main.py --mode monitor --cycles 2
```

### Tip 2: Extended Monitoring
```bash
# Long monitoring session
python main.py --mode monitor --cycles 20
```
Watch devices over time!

### Tip 3: Reset and Repeat
```bash
# Quick reset workflow
python dashboard.py  # Keep running in background

# In another terminal:
python -c "from pathlib import Path; import os; from config import *; [os.remove(f) for f in [BLE_DATA_PATH, ALERTS_PATH, CHAIN_PATH, MODEL_PATH] if os.path.exists(f)]"
python main.py --mode baseline --cycles 2
python attack_simulator.py flooding 30 10
python main.py --mode monitor --cycles 1
```

### Tip 4: Verify Model Training
```bash
# Check if model exists
ls ai_model/isolation_forest.pkl

# Check blockchain
cat blockchain/chain.json

# Check alerts
cat dataset/alerts.csv
```

---

## 🐛 Common Issues

### Issue: "No anomalies detected"
**Cause**: Model trained on normal + attack data together

**Fix**: Clear data and run baseline BEFORE injecting attack
```bash
# Clear, baseline, then attack
```

### Issue: Dashboard shows old data
**Fix**: Hard refresh browser (Ctrl+F5)

### Issue: Can't inject attack from dashboard
**Fix**: Make sure `attack_simulator.py` is in the same directory

---

## 🎉 Success Indicators

You know it's working when:

1. **Baseline completes:**
   ```
   [SUCCESS] Baseline established and model trained!
   [SUCCESS] 7 trusted devices learned.
   ```

2. **Attack injected:**
   ```
   ✅ Attack injection complete!
   💾 Packets written to: dataset/ble_data.csv
   ```

3. **Anomaly detected:**
   ```
   🚨 SECURITY ALERT: ANOMALOUS DEVICE DETECTED!
   Criticality: HIGH
   ```

4. **Dashboard shows alert:**
   - Red/yellow alert box
   - Device in anomaly list
   - Anomaly score displayed

---

## 📝 Summary

**What You've Built:**

1. ✅ **Production-grade anomaly detection** with proper train/test separation
2. ✅ **Attack simulator** with 5 realistic threat scenarios
3. ✅ **Web dashboard** for real-time monitoring
4. ✅ **Blockchain audit trail** for verified devices
5. ✅ **Alert system** with criticality levels

**What Makes It Professional:**

- Scientifically valid ML methodology
- Persistent state (survives restarts)
- Real behavioral fingerprinting
- Tamper-evident blockchain
- Clear separation of concerns
- Extensible architecture

**Next Steps:**

1. ✅ Test all 5 attack scenarios
2. 🎨 Improve dashboard UI/UX (your request)
3. 📧 Add email/SMS alerts (optional)
4. 📊 Add charts and visualizations
5. 📱 Mobile-responsive design

---

**Now go ahead and run the 5-minute demo!** 🚀
