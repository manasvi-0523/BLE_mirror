import os
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

class BehaviorAnomalyDetector:
    def __init__(self, contamination=0.1):
        """
        contamination: The proportion of outliers in the data set. 
        For a prototype, 0.1 (10%) is a good starting point to force anomaly detection on outliers.
        """
        self.model = IsolationForest(
            n_estimators=100, 
            contamination=contamination, 
            random_state=42
        )
        # These are the mathematical parameters the AI looks at to decide if the behavior matches
        self.features = ['mean_rssi', 'mean_interval', 'std_interval', 'packet_count', 'services_count']
        self.is_trained = False
        
        self.model_dir = os.path.dirname(__file__)
        self.model_path = os.path.join(self.model_dir, 'isolation_forest.pkl')

    def train(self, features_df):
        """Trains the model on baseline/normal behavioral features."""
        if features_df is None or features_df.empty:
            print("Cannot train: Dataset is empty.")
            return False
            
        print("\n[AI] Training Isolation Forest on baseline behavioral fingerprints...")
        # Extract numerical features explicitly
        X = features_df[self.features]
        self.model.fit(X)
        self.is_trained = True
        
        # Save model to disk so we don't have to retrain every boot
        joblib.dump(self.model, self.model_path)
        print(f"[AI] Model successfully trained & saved to {self.model_path}")
        return True

    def load_model(self):
        """Loads a pre-trained model from disk."""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.is_trained = True
            print("[AI] Successfully loaded pre-trained Isolation Forest model.")
            return True
        return False

    def detect(self, fingerprint_row, device_name, mac):
        """
        Takes a single device's fingerprint and determines if it is an anomaly.
        Returns: True if ANOMALY, False if NORMAL
        """
        if not self.is_trained:
            print("[AI] Model is not trained. Cannot perform detection.")
            return None
            
        # Ensure input is a dataframe slice correctly formatted for sklearn
        X_new = fingerprint_row[self.features]
        
        # Isolation Forest predicts: 1 for normal, -1 for anomaly
        prediction = self.model.predict(X_new)
        # Decision function gives raw anomaly score (negative is bad)
        score = self.model.decision_function(X_new)[0]
        
        is_anomaly = (prediction[0] == -1)
        status = "ANOMALY DETECTED! [!]" if is_anomaly else "NORMAL [OK]"
        
        print(f"[{mac}] {device_name[:15]:15} -> {status} (Score: {score:.3f})")
        return is_anomaly

if __name__ == "__main__":
    import sys
    # Add parent directory to path to import other modules
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from feature_engine.feature_extract import extract_features
    
    dataset_path = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'ble_data.csv')
    df = extract_features(dataset_path)
    
    if df is not None:
        detector = BehaviorAnomalyDetector(contamination=0.2) # set 20% outlier to force a hit on small dataset
        detector.train(df)
        
        print("\n--- AI Model Inference Test ---")
        # We test the model on the exact data it trained on.
        # Since contamination is 0.2, it will mathematically FORCE the 20% most odd devices to be flagged as anomalies!
        for index, row in df.iterrows():
            fingerprint_row = pd.DataFrame([row])
            detector.detect(fingerprint_row, row['name'], row['mac_address'])
    else:
        print("No dataset available. Please run scanning (Phase 1) first.")
