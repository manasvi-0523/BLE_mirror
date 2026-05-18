"""
Anomaly detector using Isolation Forest + One-Class SVM ensemble.
Trains on history-aware features from the SQLite device registry.
"""

import numpy as np
import pickle
import os
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler

MODEL_PATH  = os.path.join(os.path.dirname(__file__), 'model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), 'scaler.pkl')
OCSVM_PATH  = os.path.join(os.path.dirname(__file__), 'ocsvm.pkl')

# Minimum samples needed before the ML model is meaningful
MIN_SAMPLES = 3


def train(feature_matrix: np.ndarray, contamination: float = 0.05):
    """
    Train Isolation Forest on accumulated device history features.
    contamination lowered to 0.05 (5%) since registry history reduces noise.
    """
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(feature_matrix)

    model = IsolationForest(
        n_estimators=150,
        contamination=contamination,
        random_state=42,
    )
    model.fit(X_scaled)

    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)

    print(f"[OK] Isolation Forest trained on {len(X_scaled)} device(s). "
          f"Saved to {MODEL_PATH}\n")
    return model, scaler


def train_ocsvm(feature_matrix: np.ndarray, nu: float = 0.05):
    """
    Train One-Class SVM as second opinion model.
    nu = upper bound on fraction of outliers.
    """
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(feature_matrix)
    ocsvm    = OneClassSVM(kernel='rbf', gamma='auto', nu=nu)
    ocsvm.fit(X_scaled)
    with open(OCSVM_PATH, 'wb') as f:
        pickle.dump((ocsvm, scaler), f)
    print(f"[OK] OCSVM trained on {len(X_scaled)} device(s). "
          f"Saved to {OCSVM_PATH}\n")
    return ocsvm, scaler


def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("No trained model found. Run a scan first.")
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    return model, scaler


def predict_ensemble(feature_matrix: np.ndarray, model=None, scaler=None):
    """
    Ensemble: Isolation Forest + One-Class SVM.
    A device is flagged ANOMALY only when both models agree (-1).
    Returns (ensemble_predictions, if_scores).
    """
    if model is None or scaler is None:
        model, scaler = load_model()

    X_scaled  = scaler.transform(feature_matrix)
    if_preds  = model.predict(X_scaled)
    if_scores = model.decision_function(X_scaled)

    if os.path.exists(OCSVM_PATH):
        with open(OCSVM_PATH, 'rb') as f:
            ocsvm, ocsvm_scaler = pickle.load(f)
        X_ocsvm = ocsvm_scaler.transform(feature_matrix)
    else:
        ocsvm, ocsvm_scaler = train_ocsvm(feature_matrix)
        X_ocsvm = ocsvm_scaler.transform(feature_matrix)

    ocsvm_preds = ocsvm.predict(X_ocsvm)

    # Flag only when BOTH models agree
    ensemble_preds = np.where(
        (if_preds == -1) & (ocsvm_preds == -1), -1, 1
    )
    return ensemble_preds, if_scores


def normalize_risk(scores: np.ndarray) -> np.ndarray:
    """
    Normalize IF decision scores to 0-1 risk values.
    Higher risk = lower IF score (more anomalous).
    """
    s_min   = scores.min()
    s_range = scores.max() - s_min + 1e-9
    return 1.0 - (scores - s_min) / s_range


def risk_label(risk: float) -> str:
    if risk >= 0.7:
        return "HIGH"
    if risk >= 0.4:
        return "MEDIUM"
    return "LOW"


def label(prediction: int) -> str:
    return "NORMAL" if prediction == 1 else "ANOMALY"


if __name__ == '__main__':
    # Self-test with 12-feature dummy data (matches registry FEATURE_ORDER)
    np.random.seed(0)
    dummy    = np.random.randn(15, 12)
    dummy[0] = [1, 200, 80, 180, 220, 5.0, 500, 100, 15, 999, 0.9, 10]
    model, scaler = train(dummy)
    train_ocsvm(dummy)
    preds, scores = predict_ensemble(dummy, model, scaler)
    risks = normalize_risk(scores)
    for i, (p, s, r) in enumerate(zip(preds, scores, risks)):
        print(f"Device {i:2d}: {label(p):<8} | IF: {s:+.4f} | "
              f"Risk: {r:.3f} ({risk_label(r)})")
