"""
BLE Device Registry - SQLite persistent store.
Tracks device identity, scan history, behavioral features, and spoofing signals.
"""

import hashlib
import json
import os
import sqlite3
import statistics
import uuid as _uuid
from contextlib import contextmanager
from datetime import datetime

import numpy as np

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'ble_registry.db')

# ── Helpers ───────────────────────────────────────────────────────────────────

@contextmanager
def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Schema ────────────────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS device_profiles (
    fingerprint_id        TEXT PRIMARY KEY,
    mac                   TEXT NOT NULL,
    device_name           TEXT DEFAULT 'Unknown',
    scan_type             TEXT DEFAULT 'BLE',
    uuid_set_hash         TEXT,
    company_id            INTEGER DEFAULT -1,
    tx_power              INTEGER DEFAULT -1,
    is_random_mac         INTEGER DEFAULT 0,
    first_seen            TEXT NOT NULL,
    last_seen             TEXT NOT NULL,
    total_scans           INTEGER DEFAULT 1,
    scan_sessions         INTEGER DEFAULT 1,
    mean_rssi             REAL,
    std_rssi              REAL,
    min_rssi              REAL,
    max_rssi              REAL,
    mean_payload          REAL,
    mean_services         REAL,
    anomaly_score         REAL DEFAULT 0.0,
    risk_level            TEXT DEFAULT 'LOW',
    is_flagged            INTEGER DEFAULT 0,
    mac_change_count      INTEGER DEFAULT 0,
    identity_change_count INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_dp_mac       ON device_profiles(mac);
CREATE INDEX IF NOT EXISTS idx_dp_uuid_hash ON device_profiles(uuid_set_hash);
CREATE INDEX IF NOT EXISTS idx_dp_company   ON device_profiles(company_id);

CREATE TABLE IF NOT EXISTS scan_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint_id TEXT NOT NULL REFERENCES device_profiles(fingerprint_id),
    mac            TEXT NOT NULL,
    session_id     TEXT NOT NULL,
    scanned_at     TEXT NOT NULL,
    rssi           REAL,
    tx_power       INTEGER DEFAULT -1,
    payload_size   INTEGER DEFAULT 0,
    service_count  INTEGER DEFAULT 0,
    raw_services   TEXT DEFAULT '',
    company_id     INTEGER DEFAULT -1,
    distance_m     REAL,
    proximity_zone TEXT,
    uuid_set_hash  TEXT,
    anomaly_score  REAL,
    is_anomaly     INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_sh_fingerprint ON scan_history(fingerprint_id);
CREATE INDEX IF NOT EXISTS idx_sh_session     ON scan_history(session_id);
CREATE INDEX IF NOT EXISTS idx_sh_scanned_at  ON scan_history(scanned_at);

CREATE TABLE IF NOT EXISTS identity_change_log (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint_id TEXT NOT NULL,
    detected_at    TEXT NOT NULL,
    change_type    TEXT NOT NULL,
    old_value      TEXT,
    new_value      TEXT,
    session_id     TEXT,
    severity       TEXT DEFAULT 'INFO'
);

CREATE INDEX IF NOT EXISTS idx_icl_fingerprint ON identity_change_log(fingerprint_id);
CREATE INDEX IF NOT EXISTS idx_icl_type        ON identity_change_log(change_type);
"""


def init_db():
    """Create database and tables if they don't exist."""
    with get_db() as conn:
        conn.executescript(_SCHEMA)


# ── Fingerprinting ────────────────────────────────────────────────────────────

def compute_uuid_hash(raw_services: str) -> str:
    """Order-independent hash of the UUID set."""
    if not raw_services:
        return hashlib.sha256(b'').hexdigest()
    uuids = sorted(u.strip().lower() for u in raw_services.split('|') if u.strip())
    return hashlib.sha256(json.dumps(uuids).encode()).hexdigest()


def compute_fingerprint_id(uuid_hash: str, company_id: int) -> str:
    """
    Stable device identity that survives MAC randomization.
    Based on UUID set + manufacturer company ID.
    """
    key = f"{uuid_hash}:{company_id}"
    return hashlib.sha256(key.encode()).hexdigest()


# ── Upsert ────────────────────────────────────────────────────────────────────

def upsert_device(conn, record: dict, session_id: str) -> str:
    """
    Insert or update a device profile from a scan record dict.
    Returns the fingerprint_id.
    """
    uuid_hash  = compute_uuid_hash(record.get('raw_services', ''))
    company_id = int(record.get('company_id', -1))
    fp_id      = compute_fingerprint_id(uuid_hash, company_id)
    now        = record.get('timestamp', datetime.now().isoformat())

    existing = conn.execute(
        "SELECT * FROM device_profiles WHERE fingerprint_id = ?", (fp_id,)
    ).fetchone()

    if existing is None:
        conn.execute("""
            INSERT INTO device_profiles
              (fingerprint_id, mac, device_name, scan_type,
               uuid_set_hash, company_id, tx_power, is_random_mac,
               first_seen, last_seen, total_scans, scan_sessions)
            VALUES (?,?,?,?,?,?,?,?,?,?,1,1)
        """, (fp_id, record['mac'], record.get('name', 'Unknown'),
              record.get('scan_type', 'BLE'), uuid_hash, company_id,
              record.get('tx_power', -1), record.get('is_random_mac', 0),
              now, now))
    else:
        mac_changed  = existing['mac'] != record['mac']
        uuid_changed = existing['uuid_set_hash'] != uuid_hash

        conn.execute("""
            UPDATE device_profiles
            SET mac = ?, last_seen = ?,
                total_scans           = total_scans + 1,
                mac_change_count      = mac_change_count + ?,
                identity_change_count = identity_change_count + ?
            WHERE fingerprint_id = ?
        """, (record['mac'], now,
              1 if mac_changed else 0,
              1 if uuid_changed else 0,
              fp_id))

        if mac_changed:
            _log_change(conn, fp_id, 'MAC_ROTATION',
                        existing['mac'], record['mac'], session_id, 'INFO')
        if uuid_changed:
            _log_change(conn, fp_id, 'UUID_SET_CHANGE',
                        existing['uuid_set_hash'], uuid_hash, session_id, 'WARN')

    # Always record this raw scan in history
    conn.execute("""
        INSERT INTO scan_history
          (fingerprint_id, mac, session_id, scanned_at,
           rssi, tx_power, payload_size, service_count,
           raw_services, company_id, distance_m, proximity_zone, uuid_set_hash)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (fp_id, record['mac'], session_id, now,
          record.get('rssi'), record.get('tx_power', -1),
          record.get('payload_size', 0), record.get('service_count', 0),
          record.get('raw_services', ''), company_id,
          record.get('distance_m'), record.get('proximity_zone'), uuid_hash))

    return fp_id


def _log_change(conn, fp_id, change_type, old_val, new_val, session_id, severity):
    conn.execute("""
        INSERT INTO identity_change_log
          (fingerprint_id, detected_at, change_type,
           old_value, new_value, session_id, severity)
        VALUES (?,?,?,?,?,?,?)
    """, (fp_id, datetime.now().isoformat(), change_type,
          str(old_val), str(new_val), session_id, severity))


# ── Behavioral Features from History ─────────────────────────────────────────

def get_behavioral_features(conn, fingerprint_id: str, window: int = 30) -> dict | None:
    """
    Compute 12 history-aware features from the last `window` scan rows.
    Returns None if fewer than 2 observations exist.
    """
    rows = conn.execute("""
        SELECT rssi, tx_power, payload_size, service_count,
               uuid_set_hash, scanned_at
        FROM scan_history
        WHERE fingerprint_id = ?
        ORDER BY scanned_at DESC
        LIMIT ?
    """, (fingerprint_id, window)).fetchall()

    if len(rows) < 2:
        return None

    rssi_vals    = [r['rssi'] for r in rows if r['rssi'] is not None]
    payload_vals = [r['payload_size'] or 0 for r in rows]
    svc_vals     = [r['service_count'] or 0 for r in rows]
    n            = len(rows)

    # RSSI slope: positive = signal getting stronger over time (possible approach)
    rssi_slope = 0.0
    if len(rssi_vals) >= 3:
        x = list(range(len(rssi_vals)))
        rssi_slope = float(np.polyfit(x, rssi_vals, 1)[0])

    # UUID change rate: fraction of consecutive pairs where UUID set changed
    uuid_hashes = [r['uuid_set_hash'] for r in rows]
    uuid_changes = sum(
        1 for i in range(1, len(uuid_hashes))
        if uuid_hashes[i] and uuid_hashes[i] != uuid_hashes[i - 1]
    )
    uuid_change_rate = uuid_changes / (len(uuid_hashes) - 1) if len(uuid_hashes) > 1 else 0.0

    # MAC rotation count from change log
    rot_row = conn.execute("""
        SELECT COUNT(*) as cnt FROM identity_change_log
        WHERE fingerprint_id = ? AND change_type = 'MAC_ROTATION'
    """, (fingerprint_id,)).fetchone()
    mac_rotations = rot_row['cnt'] if rot_row else 0

    # Scan frequency: appearances per hour over observed window
    scan_freq = 0.0
    if n >= 2:
        t0 = datetime.fromisoformat(rows[-1]['scanned_at'])
        t1 = datetime.fromisoformat(rows[0]['scanned_at'])
        hours = max((t1 - t0).total_seconds() / 3600, 1e-6)
        scan_freq = n / hours

    return {
        'scan_count':         n,
        'mean_rssi':          sum(rssi_vals) / len(rssi_vals) if rssi_vals else 0.0,
        'std_rssi':           statistics.stdev(rssi_vals) if len(rssi_vals) >= 2 else 0.0,
        'min_rssi':           min(rssi_vals) if rssi_vals else 0.0,
        'max_rssi':           max(rssi_vals) if rssi_vals else 0.0,
        'rssi_slope':         rssi_slope,
        'mean_payload':       sum(payload_vals) / n,
        'std_payload':        statistics.stdev(payload_vals) if n >= 2 else 0.0,
        'mean_services':      sum(svc_vals) / n,
        'scan_frequency':     scan_freq,
        'uuid_change_rate':   uuid_change_rate,
        'mac_rotation_count': float(mac_rotations),
    }


# ── Training Matrix ───────────────────────────────────────────────────────────

FEATURE_ORDER = [
    'scan_count', 'mean_rssi', 'std_rssi', 'min_rssi', 'max_rssi',
    'rssi_slope', 'mean_payload', 'std_payload', 'mean_services',
    'scan_frequency', 'uuid_change_rate', 'mac_rotation_count',
]


def build_training_matrix(conn, min_scans: int = 3):
    """
    Build feature matrix from all BLE devices with >= min_scans observations.
    Classic BT devices (rssi == -1 always) are excluded from ML.
    Returns (fingerprint_ids, feature_df_rows, X_numpy).
    """
    profiles = conn.execute("""
        SELECT fingerprint_id, device_name, mac, scan_type
        FROM device_profiles
        WHERE total_scans >= ? AND scan_type = 'BLE'
    """, (min_scans,)).fetchall()

    fp_ids = []
    names  = []
    macs   = []
    rows   = []

    for p in profiles:
        feats = get_behavioral_features(conn, p['fingerprint_id'])
        if feats is None:
            continue
        fp_ids.append(p['fingerprint_id'])
        names.append(p['device_name'])
        macs.append(p['mac'])
        rows.append([feats[k] for k in FEATURE_ORDER])

    X = np.array(rows, dtype=float) if rows else np.empty((0, len(FEATURE_ORDER)))
    return fp_ids, names, macs, X


# ── Spoofing Detection ────────────────────────────────────────────────────────

def check_spoofing(conn, fingerprint_id: str, current_record: dict) -> list[dict]:
    """
    Rule-based spoofing signals layered on top of ML.
    Returns list of signal dicts (empty = nothing suspicious).
    """
    profile = conn.execute(
        "SELECT * FROM device_profiles WHERE fingerprint_id = ?",
        (fingerprint_id,)
    ).fetchone()

    if profile is None or profile['total_scans'] < 5:
        return []

    signals = []
    rssi = current_record.get('rssi')

    # Rule 1: RSSI far outside established baseline
    mean_r = profile['mean_rssi']
    std_r  = profile['std_rssi']
    if rssi and mean_r and std_r and std_r > 0:
        z = abs(rssi - mean_r) / std_r
        if z > 3.5:
            signals.append({
                'type':     'RSSI_OUTLIER',
                'detail':   f"RSSI {rssi} is {z:.1f}σ from baseline {mean_r:.1f}",
                'severity': 'WARN',
            })

    # Rule 2: TX power shifted significantly
    stored_tx  = profile['tx_power']
    current_tx = current_record.get('tx_power', -1)
    if stored_tx not in (-1, None) and current_tx not in (-1, None):
        if abs(stored_tx - current_tx) > 5:
            signals.append({
                'type':     'TX_POWER_SHIFT',
                'detail':   f"TX power {stored_tx} -> {current_tx} dBm",
                'severity': 'ALERT',
            })

    # Rule 3: Device returns after long absence
    try:
        last   = datetime.fromisoformat(profile['last_seen'])
        gap_h  = (datetime.now() - last).total_seconds() / 3600
        if gap_h > 24 and profile['total_scans'] > 10:
            signals.append({
                'type':     'LONG_ABSENCE_RETURN',
                'detail':   f"Absent {gap_h:.1f}h, reappeared",
                'severity': 'INFO',
            })
    except (ValueError, TypeError):
        pass

    return signals


# ── Profile Update After ML ───────────────────────────────────────────────────

def update_anomaly_result(conn, fingerprint_id: str, score: float,
                          risk_level: str, is_anomaly: bool):
    """Persist the latest ML result back onto the device profile."""
    conn.execute("""
        UPDATE device_profiles
        SET anomaly_score = ?, risk_level = ?, is_flagged = ?
        WHERE fingerprint_id = ?
    """, (score, risk_level, int(is_anomaly), fingerprint_id))

    # Also stamp the most recent scan_history row
    conn.execute("""
        UPDATE scan_history SET anomaly_score = ?, is_anomaly = ?
        WHERE id = (
            SELECT id FROM scan_history
            WHERE fingerprint_id = ?
            ORDER BY scanned_at DESC LIMIT 1
        )
    """, (score, int(is_anomaly), fingerprint_id))


# ── Quick Stats ───────────────────────────────────────────────────────────────

def get_registry_stats(conn) -> dict:
    """Return summary counts for display in the GUI."""
    row = conn.execute("""
        SELECT
            COUNT(*)                                AS total_devices,
            SUM(CASE WHEN scan_type='BLE' THEN 1 ELSE 0 END)     AS ble_count,
            SUM(CASE WHEN scan_type='CLASSIC' THEN 1 ELSE 0 END)  AS classic_count,
            SUM(is_flagged)                         AS flagged_count,
            SUM(total_scans)                        AS total_observations
        FROM device_profiles
    """).fetchone()
    return dict(row) if row else {}


if __name__ == '__main__':
    init_db()
    print("[OK] Registry initialized at", os.path.abspath(DB_PATH))
    with get_db() as conn:
        stats = get_registry_stats(conn)
    print("[INFO] Stats:", stats)
