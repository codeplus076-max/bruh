import os
import joblib
import pandas as pd
import numpy as np
from functools import lru_cache

class DiseasePredictor:
    """
    Singleton AI Disease Predictor. Uses a class-level instance state to ensure 
    the model weights are only loaded into RAM exactly once per worker process.
    """
    _instance = None
    _model = None
    _meta = None

    def __new__(cls, model_dir: str = None):
        if cls._instance is None:
            cls._instance = super(DiseasePredictor, cls).__new__(cls)
            cls._instance.model_path = os.path.join(
                model_dir or os.path.dirname(os.path.abspath(__file__)), 
                "triage_model.joblib"
            )
            cls._instance.meta_path = os.path.join(
                model_dir or os.path.dirname(os.path.abspath(__file__)), 
                "model_meta.joblib"
            )
            cls._instance.load_model()
        return cls._instance

    def load_model(self):
        # Prevent reloading if already in memory
        if self._model is not None and self._meta is not None:
            return

        print(f"Loading ML Model from disk into memory: {self.model_path}")
        if os.path.exists(self.model_path) and os.path.exists(self.meta_path):
            self.__class__._model = joblib.load(self.model_path)
            self.__class__._meta = joblib.load(self.meta_path)
            print("Successfully loaded custom Random Forest model and metadata.")
        else:
            print(f"Warning: Model or meta not found in {self.model_path}. Using mock predictions.")
            self.__class__._model = None

    @lru_cache(maxsize=1024)
    def predict(self, age: int, gender: int, severity: int, duration: float) -> str:
        """
        Predicts disease probabilistically.
        Cached with LRU since inputs are deterministic for the same symptom payload.
        """
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
            
            # Predict returns an encoded integer OR direct string label
            pred_val = self._model.predict(df)[0]
            
            # If it's a string (our light RF model), just return it
            if isinstance(pred_val, str) or isinstance(pred_val, np.str_):
                return str(pred_val)
                
            # Decode the integer back to a string disease label (legacy model)
            classes = self._meta.get('classes', [])
            if hasattr(pred_val, 'item'):
                pred_val = pred_val.item() # get pure int
                
            if isinstance(pred_val, int) and 0 <= pred_val < len(classes):
                return str(classes[pred_val])
            return "Unknown Disease"
        else:
            return "Mock Disease (Model Not Loaded)"

    @property
    def is_loaded(self) -> bool:
        """Returns True if the ML payload has successfully initialized into RAM."""
        return self._model is not None and self._meta is not None
