import os
import sys
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_PATH, FEATURES_FOR_MODEL, MIN_DEVICES_FOR_MODEL, CONTAMINATION_RATE, DYNAMIC_CONTAMINATION_THRESHOLD

class BehaviorAnomalyDetector:
    def __init__(self, contamination=None):
        """
        Initialize the Behavior Anomaly Detector with Isolation Forest.
        
        Args:
            contamination: The proportion of outliers in the data set. 
                          If None, uses config default or dynamic calculation.
        """
        self.base_contamination = contamination or CONTAMINATION_RATE
        self.model = None
        self.features = FEATURES_FOR_MODEL
        self.is_trained = False
        self.model_path = str(MODEL_PATH)
        
        # Ensure model directory exists
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

    def _calculate_dynamic_contamination(self, n_samples):
        """
        Calculate contamination rate dynamically based on sample size.
        For small datasets, use a higher rate. For larger datasets, use configured rate.
        
        Args:
            n_samples: Number of samples in the dataset
            
        Returns:
            float: Contamination rate between 0.01 and 0.5
        """
        if n_samples < DYNAMIC_CONTAMINATION_THRESHOLD:
            # For small datasets, use higher contamination to avoid overfitting
            return min(0.3, max(0.1, 2.0 / n_samples))
        else:
            return self.base_contamination

    def train(self, features_df):
        """
        Trains the model on baseline/normal behavioral features.
        
        Args:
            features_df: DataFrame with behavioral features
            
        Returns:
            bool: True if training successful, False otherwise
        """
        if features_df is None or features_df.empty:
            print("[AI] Cannot train: Dataset is empty.")
            return False
        
        if len(features_df) < MIN_DEVICES_FOR_MODEL:
            print(f"[AI] Warning: Only {len(features_df)} devices found. Minimum {MIN_DEVICES_FOR_MODEL} required for reliable model.")
            print("[AI] Training anyway, but results may not be meaningful.")
            
        print(f"\n[AI] Training Isolation Forest on {len(features_df)} baseline behavioral fingerprints...")
        
        # Extract numerical features
        X = features_df[self.features]
        
        # Calculate appropriate contamination rate
        contamination = self._calculate_dynamic_contamination(len(features_df))
        print(f"[AI] Using contamination rate: {contamination:.3f} (dynamic adjustment for {len(features_df)} samples)")
        
        # Initialize and train model
        self.model = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=42,
            n_jobs=-1  # Use all CPU cores for faster training
        )
        self.model.fit(X)
        self.is_trained = True
        
        # Save model to disk
        try:
            joblib.dump(self.model, self.model_path)
            print(f"[AI] Model successfully trained & saved to {self.model_path}")
        except Exception as e:
            print(f"[AI] Warning: Failed to save model: {e}")
        
        return True

    def load_model(self):
        """
        Loads a pre-trained model from disk.
        
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                print(f"[AI] Successfully loaded pre-trained Isolation Forest model from {self.model_path}")
                return True
            except Exception as e:
                print(f"[AI] Error loading model: {e}")
                return False
        else:
            print(f"[AI] No pre-trained model found at {self.model_path}")
            return False

    def detect(self, fingerprint_row, device_name, mac):
        """
        Takes a single device's fingerprint and determines if it is an anomaly.
        
        Args:
            fingerprint_row: DataFrame row with device behavioral features
            device_name: Name of the device
            mac: MAC address of the device
            
        Returns:
            bool: True if ANOMALY, False if NORMAL, None if model not trained
        """
        if not self.is_trained or self.model is None:
            print("[AI] Model is not trained. Cannot perform detection.")
            return None
            
        # Ensure input is a dataframe slice correctly formatted for sklearn
        X_new = fingerprint_row[self.features]
        
        # Isolation Forest predicts: 1 for normal, -1 for anomaly
        prediction = self.model.predict(X_new)
        # Decision function gives raw anomaly score (more negative = more anomalous)
        score = self.model.decision_function(X_new)[0]
        
        is_anomaly = (prediction[0] == -1)
        status = "ANOMALY DETECTED! [!]" if is_anomaly else "NORMAL [OK]"
        
        print(f"[{mac}] {device_name[:15]:15} -> {status} (Score: {score:.3f})")
        return is_anomaly

    def get_anomaly_score(self, fingerprint_row):
        """
        Get the anomaly score for a device without classification.
        
        Args:
            fingerprint_row: DataFrame row with device behavioral features
            
        Returns:
            float: Anomaly score (more negative = more anomalous), or None if model not trained
        """
        if not self.is_trained or self.model is None:
            return None
            
        X_new = fingerprint_row[self.features]
        return self.model.decision_function(X_new)[0]

if __name__ == "__main__":
    from feature_engine.feature_extract import extract_features
    
    df = extract_features()
    
    if df is not None:
        detector = BehaviorAnomalyDetector()
        detector.train(df)
        
        print("\n--- AI Model Inference Test ---")
        # Test the model on the training data to verify it works
        for index, row in df.iterrows():
            fingerprint_row = pd.DataFrame([row])
            detector.detect(fingerprint_row, row['name'], row['mac_address'])
    else:
        print("No dataset available. Please run scanning (Phase 1) first.")
