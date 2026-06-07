"""
Configuration file for BLE Device Trust Registry
Centralized paths and settings for cleaner code
"""
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
AI_MODEL_DIR = BASE_DIR / "ai_model"
BLOCKCHAIN_DIR = BASE_DIR / "blockchain"
ALERTS_DIR = BASE_DIR / "alerts"

# File paths
BLE_DATA_PATH = DATASET_DIR / "ble_data.csv"
ALERTS_PATH = ALERTS_DIR / "alerts.csv"
CHAIN_PATH = BLOCKCHAIN_DIR / "chain.json"
MODEL_PATH = AI_MODEL_DIR / "isolation_forest.pkl"
SCALER_PATH = AI_MODEL_DIR / "scaler.pkl"

# Ensure directories exist
DATASET_DIR.mkdir(exist_ok=True)
AI_MODEL_DIR.mkdir(exist_ok=True)
BLOCKCHAIN_DIR.mkdir(exist_ok=True)
ALERTS_DIR.mkdir(exist_ok=True)

# Scanning settings
SCAN_DURATION = 15  # seconds per scan cycle
SCAN_CYCLES_BASELINE = 2  # number of cycles to establish baseline
SCAN_CYCLES_MONITOR = 5  # number of monitoring cycles in demo

# AI Model settings
MIN_DEVICES_FOR_MODEL = 3  # minimum devices needed to train model
CONTAMINATION_RATE = 0.1  # proportion of outliers expected (10%)
DYNAMIC_CONTAMINATION_THRESHOLD = 10  # switch to dynamic contamination above this many devices

# Blockchain settings
MAX_BLOCKS_DISPLAY = 10  # maximum blocks to display in summary

# Alert settings
ALERT_CRITICALITY_HIGH = -0.2  # anomaly score threshold for HIGH criticality
ALERT_CRITICALITY_MEDIUM = -0.1  # anomaly score threshold for MEDIUM criticality

# Feature engineering
FEATURES_FOR_MODEL = ['mean_rssi', 'mean_interval', 'std_interval', 'packet_count', 'services_count']
