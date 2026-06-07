# 🎛️ Dashboard Guide - Web-Based Control Center

## Quick Start

**Start Dashboard**:
```bash
python dashboard.py
```
**Open**: http://127.0.0.1:5000

---

## Dashboard Features

### 5 Control Buttons

1. **🔄 Refresh Dashboard** - Update data display
2. **📊 Start Baseline Scan** - Train AI on normal devices (opens new window)
3. **🔍 Start Monitor Scan** - Detect anomalies (opens new window)
4. **🗑️ Clear All Data** - Fresh start (removes all datasets)
5. **⚠️ Inject Attack** - Simulate threat for testing

### Real-Time Display

- **Statistics Cards**: Devices, alerts, blockchain status, model status
- **Device Table**: All detected devices with behavioral stats
- **Security Alerts**: Anomalies with criticality levels
- **Blockchain Ledger**: Tamper-evident chain with hash validation

---

## Complete Workflow

### 1. Fresh Start
```
Click "🗑️ Clear All Data" → Confirm
```

### 2. Baseline (Learn Normal)
```
Click "📊 Start Baseline Scan" → Enter 2 → Confirm
→ New console window opens
→ Watch AI training in console
→ Wait ~30 seconds
→ Model trained and saved
```

### 3. Test with Attack (Optional)
```
Click "⚠️ Inject Attack" → Select "Packet Flooding" → Confirm
→ Simulated attack injected
```

### 4. Monitor (Detect Threats)
```
Click "🔍 Start Monitor Scan" → Enter 1 → Confirm
→ New console window opens
→ Watch anomaly detection
→ See alerts in dashboard
```

---

## How Console Windows Work

Dashboard launches external processes (new windows) for scanning:
- **Dashboard stays responsive** (no freezing)
- **Full scan output visible** in console
- **Windows stay open** for review
- **Dashboard auto-updates** when complete

---

## Complete Documentation

- **`COMPLETE_EXPLANATION.md`**: Theory, AI training, baseline vs monitor
- **`WHERE_TO_SEE_EVERYTHING.md`**: Visual guide, console output examples
- **`DASHBOARD_GUIDE.md`**: Detailed workflow and troubleshooting
- **`QUICK_DEMO.md`**: 5-minute walkthrough

---

## Key Points

✅ Dashboard = Control center (buttons, data display)  
✅ Console windows = Detailed progress (AI training, detection)  
✅ Both work together seamlessly  
✅ No terminal commands needed  

**Try it**: http://127.0.0.1:5000 🚀
