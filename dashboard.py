"""
Simple Flask Dashboard for BLE Trust Registry
Opens in browser to show real-time monitoring results
"""
import os
import json
from flask import Flask, render_template, jsonify, request
from pathlib import Path
import pandas as pd
from datetime import datetime

from config import BLE_DATA_PATH, ALERTS_PATH, CHAIN_PATH, MODEL_PATH

app = Flask(__name__)

# Global scan status
scan_status = {
    'running': False,
    'mode': None,
    'cycle': 0,
    'total_cycles': 0,
    'message': 'Idle',
    'devices_found': 0
}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get system status"""
    status = {
        'model_trained': os.path.exists(MODEL_PATH),
        'blockchain_exists': os.path.exists(CHAIN_PATH),
        'dataset_exists': os.path.exists(BLE_DATA_PATH),
        'alerts_exist': os.path.exists(ALERTS_PATH),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(status)

@app.route('/api/devices')
def get_devices():
    """Get all detected devices with their behavioral features"""
    if not os.path.exists(BLE_DATA_PATH):
        return jsonify({'devices': [], 'count': 0})
    
    try:
        df = pd.read_csv(BLE_DATA_PATH)
        
        # Aggregate device information
        devices = []
        for mac, group in df.groupby('mac_address'):
            device = {
                'mac': mac,
                'name': group['name'].iloc[-1],  # Latest name
                'mean_rssi': round(group['rssi'].mean(), 2),
                'min_rssi': int(group['rssi'].min()),
                'max_rssi': int(group['rssi'].max()),
                'mean_interval': round(group['interval_ms'].mean(), 2),
                'packet_count': len(group),
                'services_count': int(group['services_count'].max()),
                'first_seen': datetime.fromtimestamp(group['timestamp'].min()).strftime('%H:%M:%S'),
                'last_seen': datetime.fromtimestamp(group['timestamp'].max()).strftime('%H:%M:%S')
            }
            devices.append(device)
        
        return jsonify({'devices': devices, 'count': len(devices)})
    except Exception as e:
        return jsonify({'error': str(e), 'devices': [], 'count': 0})

@app.route('/api/alerts')
def get_alerts():
    """Get all security alerts"""
    if not os.path.exists(ALERTS_PATH):
        return jsonify({'alerts': [], 'count': 0})
    
    try:
        df = pd.read_csv(ALERTS_PATH)
        alerts = df.to_dict('records')
        return jsonify({'alerts': alerts, 'count': len(alerts)})
    except Exception as e:
        return jsonify({'error': str(e), 'alerts': [], 'count': 0})

@app.route('/api/blockchain')
def get_blockchain():
    """Get blockchain ledger"""
    if not os.path.exists(CHAIN_PATH):
        return jsonify({'blocks': [], 'count': 0, 'valid': False})
    
    try:
        with open(CHAIN_PATH, 'r') as f:
            chain_data = json.load(f)
        
        # Verify chain integrity
        valid = True
        for i in range(1, len(chain_data)):
            current = chain_data[i]
            previous = chain_data[i-1]
            if current['previous_hash'] != previous['hash']:
                valid = False
                break
        
        return jsonify({
            'blocks': chain_data,
            'count': len(chain_data),
            'valid': valid
        })
    except Exception as e:
        return jsonify({'error': str(e), 'blocks': [], 'count': 0, 'valid': False})

@app.route('/api/scan_status')
def get_scan_status():
    """Get current scan status"""
    return jsonify(scan_status)

@app.route('/api/start_baseline', methods=['POST'])
def start_baseline():
    """Start baseline scan in background process"""
    try:
        data = json.loads(request.data) if request.data else {}
        cycles = data.get('cycles', 2)
        
        # Run as external process (non-blocking)
        import subprocess
        subprocess.Popen(
            ['python', 'main.py', '--mode', 'baseline', '--cycles', str(cycles)],
            cwd=os.path.dirname(__file__),
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        
        return jsonify({
            'success': True,
            'message': f'Baseline scan started ({cycles} cycles). Check the new console window!',
            'cycles': cycles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/start_monitor', methods=['POST'])
def start_monitor():
    """Start monitor scan in background process"""
    try:
        data = json.loads(request.data) if request.data else {}
        cycles = data.get('cycles', 2)
        
        # Check if model exists
        if not os.path.exists(MODEL_PATH):
            return jsonify({
                'success': False,
                'error': 'No trained model found. Run baseline first!'
            })
        
        # Run as external process (non-blocking)
        import subprocess
        subprocess.Popen(
            ['python', 'main.py', '--mode', 'monitor', '--cycles', str(cycles)],
            cwd=os.path.dirname(__file__),
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
        )
        
        return jsonify({
            'success': True,
            'message': f'Monitor scan started ({cycles} cycles). Check the new console window!',
            'cycles': cycles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def run_baseline_scan(cycles):
    """Deprecated - using external process instead"""
    pass

def run_monitor_scan(cycles):
    """Deprecated - using external process instead"""
    pass

@app.route('/api/clear_data', methods=['POST'])
def clear_data():
    """Clear all datasets to start fresh"""
    try:
        files_removed = []
        
        # Remove dataset
        if os.path.exists(BLE_DATA_PATH):
            os.remove(BLE_DATA_PATH)
            files_removed.append('dataset')
        
        # Remove alerts
        if os.path.exists(ALERTS_PATH):
            os.remove(ALERTS_PATH)
            files_removed.append('alerts')
        
        # Remove blockchain
        if os.path.exists(CHAIN_PATH):
            os.remove(CHAIN_PATH)
            files_removed.append('blockchain')
        
        # Remove model
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
            files_removed.append('model')
        
        return jsonify({
            'success': True,
            'message': f'Cleared: {", ".join(files_removed)}',
            'cleared': files_removed
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/inject_attack', methods=['POST'])
def inject_attack():
    """Inject an attack scenario for testing"""
    import json
    from attack_simulator import AttackSimulator
    
    try:
        data = json.loads(request.data) if request.data else {}
        attack_type = data.get('attack_type', 'spoofing')
        packet_count = data.get('packet_count', 20)
        duration = data.get('duration', 10)
        
        simulator = AttackSimulator()
        success = simulator.inject_attack(attack_type, packet_count, duration)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Injected {attack_type} attack with {packet_count} packets'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Attack injection failed'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    stats = {
        'total_devices': 0,
        'total_alerts': 0,
        'blockchain_blocks': 0,
        'total_packets': 0,
        'model_status': 'Not Trained',
        'blockchain_status': 'Not Initialized'
    }
    
    # Device count and packets
    if os.path.exists(BLE_DATA_PATH):
        try:
            df = pd.read_csv(BLE_DATA_PATH)
            stats['total_devices'] = df['mac_address'].nunique()
            stats['total_packets'] = len(df)
        except:
            pass
    
    # Alert count
    if os.path.exists(ALERTS_PATH):
        try:
            df = pd.read_csv(ALERTS_PATH)
            stats['total_alerts'] = len(df)
        except:
            pass
    
    # Blockchain status
    if os.path.exists(CHAIN_PATH):
        try:
            with open(CHAIN_PATH, 'r') as f:
                chain = json.load(f)
            stats['blockchain_blocks'] = len(chain)
            stats['blockchain_status'] = 'Active'
        except:
            pass
    
    # Model status
    if os.path.exists(MODEL_PATH):
        stats['model_status'] = 'Trained'
    
    return jsonify(stats)

def open_browser():
    """Open browser automatically"""
    import webbrowser
    import time
    time.sleep(1.5)  # Wait for Flask to start
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    # Auto-open browser
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    print("\n" + "="*60)
    print("  BLE TRUST REGISTRY - WEB DASHBOARD".center(60))
    print("="*60)
    print(f"\n  🌐 Opening browser at: http://127.0.0.1:5000")
    print(f"\n  Press Ctrl+C to stop the server\n")
    print("="*60 + "\n")
    
    app.run(debug=False, host='127.0.0.1', port=5000)
