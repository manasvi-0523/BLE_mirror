import numpy as np
import pickle
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'model.pkl')
SCALER_PATH = os.path.join(os.path.dirname(__file__), 'scaler.pkl')

def train(feature_matrix: np.ndarray, contamination: float = 0.1):
    """
    Train Isolation Forest on collected device features.
    contamination = expected % of anomalies in training data (0.1 = 10%)
    """
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(feature_matrix)

    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42
    )
    model.fit(X_scaled)

    # Save model and scaler
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)

    print(f"✅ Model trained on {len(X_scaled)} device(s). Saved to {MODEL_PATH}\n")
    return model, scaler

def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("No trained model found. Run training first.")
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(SCALER_PATH, 'rb') as f:
        scaler = pickle.load(f)
    return model, scaler

def predict(feature_matrix: np.ndarray, model=None, scaler=None):
    """
    Returns list of predictions: 1 = Normal, -1 = Anomaly
    Also returns anomaly scores (lower = more anomalous)
    """
    if model is None or scaler is None:
        model, scaler = load_model()

    X_scaled = scaler.transform(feature_matrix)
    predictions = model.predict(X_scaled)       # 1 or -1
    scores = model.decision_function(X_scaled)  # higher = more normal

    return predictions, scores

def label(prediction: int) -> str:
    return "✅ NORMAL" if prediction == 1 else "🚨 ANOMALY"

if __name__ == '__main__':
    # Quick test with dummy data
    dummy = np.random.rand(10, 9)
    dummy[0] = [100, 50, 80, 120, 200, 10, 5, 1, 999]  # inject obvious anomaly
    model, scaler = train(dummy)
    preds, scores = predict(dummy, model, scaler)
    for i, (p, s) in enumerate(zip(preds, scores)):
        print(f"Device {i}: {label(p)} | Score: {s:.4f}")