import os
import joblib
import pandas as pd
import numpy as np

class DiseasePredictor:
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            model_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(model_dir, "triage_model.joblib")
        self.meta_path = os.path.join(model_dir, "model_meta.joblib")
        self._model = None
        self._meta = None
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path) and os.path.exists(self.meta_path):
            self._model = joblib.load(self.model_path)
            self._meta = joblib.load(self.meta_path)
            print("Successfully loaded custom Random Forest model and metadata.")
        else:
            print(f"Warning: Model or meta not found in {self.model_path}. Using mock predictions.")
            self._model = None

    def predict(self, age: int, gender: int, severity: int, duration: float) -> str:
        if self._model and self._meta:
            input_dict = {
                'Age': age,
                'Gender': gender,
                'Severity': severity,
                'Duration_Min_Days': duration
            }
            
            # The model was trained on ~38 columns. We need to fill missing ones with 0.
            features = self._meta.get('features', [])
            row = {}
            for f in features:
                row[f] = input_dict.get(f, 0)  # Default all unseen symptoms to 0
                
            df = pd.DataFrame([row])
            
            # Predict returns an encoded integer
            pred_idx = self._model.predict(df)[0]
            
            # Decode the integer back to a string disease label
            classes = self._meta.get('classes', [])
            if 0 <= pred_idx < len(classes):
                return str(classes[pred_idx])
            return "Unknown Disease"
        else:
            return "Mock Disease (Model Not Loaded)"
