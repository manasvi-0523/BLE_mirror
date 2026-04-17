"""
RSSI-Based Distance Estimation Module
Uses the Log-Distance Path Loss Model to convert RSSI → meters.

Formula:  distance = 10 ^ ((RSSI_ref - RSSI_measured) / (10 * n))

Where:
  RSSI_ref = measured RSSI at 1 meter (calibration value, typically -59 dBm)
  n        = path loss exponent (2.0 = free space, 2.5-4.0 = indoor)
"""

# ── Calibration Constants ─────────────────────────────────────
# RSSI measured at exactly 1 meter from the transmitter
RSSI_AT_1M = -59  # dBm  (typical BLE beacon reference)

# Path loss exponent — higher = more signal attenuation
#   2.0 = free space (outdoor, line of sight)
#   2.5 = lightly obstructed indoor
#   3.0 = typical indoor with walls
#   4.0 = dense indoor (concrete walls, metal)
PATH_LOSS_EXPONENT = 2.5

# ── Proximity Zone Thresholds (meters) ────────────────────────
ZONE_NEAR     = 1.0    # < 1m  = Immediate / Near
ZONE_MEDIUM   = 5.0    # 1-5m  = Medium range
ZONE_FAR      = 15.0   # 5-15m = Far
                        # >15m  = Very Far


def estimate_distance(rssi: int | float,
                      rssi_ref: float = RSSI_AT_1M,
                      n: float = PATH_LOSS_EXPONENT) -> float | None:
    """
    Convert an RSSI value (dBm) to estimated distance (meters).

    Returns None if RSSI is invalid (e.g. -1 for Classic BT devices
    where RSSI is unavailable).
    """
    if rssi is None or rssi == -1 or rssi >= 0:
        return None

    try:
        distance = 10 ** ((rssi_ref - rssi) / (10 * n))
        return round(distance, 2)
    except (ValueError, ZeroDivisionError):
        return None


def get_proximity_zone(distance: float | None) -> str:
    """
    Classify a distance into a human-readable proximity zone.

    Returns one of: 'NEAR', 'MEDIUM', 'FAR', 'VERY FAR', or '—'
    """
    if distance is None:
        return "—"

    if distance <= ZONE_NEAR:
        return "NEAR"
    elif distance <= ZONE_MEDIUM:
        return "MEDIUM"
    elif distance <= ZONE_FAR:
        return "FAR"
    else:
        return "VERY FAR"


def get_zone_color(zone: str) -> list:
    """Return an RGBA color list for the proximity zone (for GUI use)."""
    return {
        "NEAR":     [0.92, 0.22, 0.22, 1],   # Red — device is very close
        "MEDIUM":   [0.85, 0.72, 0.12, 1],   # Yellow
        "FAR":      [0.18, 0.72, 0.92, 1],   # Blue
        "VERY FAR": [0.45, 0.45, 0.52, 1],   # Gray
        "—":        [0.35, 0.35, 0.42, 1],   # Dim gray
    }.get(zone, [0.5, 0.5, 0.58, 1])


def format_distance(rssi: int | float) -> str:
    """Return a formatted distance string like '~3.2m (MEDIUM)'."""
    dist = estimate_distance(rssi)
    zone = get_proximity_zone(dist)

    if dist is None:
        return "—"

    if dist < 1:
        return f"~{dist * 100:.0f}cm ({zone})"
    elif dist < 10:
        return f"~{dist:.1f}m ({zone})"
    else:
        return f"~{dist:.0f}m ({zone})"


if __name__ == '__main__':
    # Quick demo
    test_rssi = [-30, -45, -59, -65, -72, -80, -90, -100, -1]
    print(f"{'RSSI':>6}  {'Distance':>10}  {'Zone':>10}  {'Formatted'}")
    print("-" * 52)
    for rssi in test_rssi:
        dist = estimate_distance(rssi)
        zone = get_proximity_zone(dist)
        fmt = format_distance(rssi)
        dist_str = f"{dist:.2f}m" if dist else "—"
        print(f"{rssi:>5}  {dist_str:>10}  {zone:>10}  {fmt}")
