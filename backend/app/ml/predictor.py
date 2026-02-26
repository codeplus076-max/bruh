import os
import joblib
import pandas as pd

class DiseasePredictor:
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            model_dir = os.path.dirname(os.path.abspath(__file__))

        model_path = os.path.join(model_dir, "triage_model.joblib")
        meta_path  = os.path.join(model_dir, "model_meta.joblib")

        self._model = None
        self._meta  = None

        if os.path.exists(model_path) and os.path.exists(meta_path):
            try:
                self._model = joblib.load(model_path)
                self._meta  = joblib.load(meta_path)
                print("Successfully loaded Random Forest model and metadata.")
            except Exception as e:
                print(f"Error loading models: {e}")
        else:
            print("Warning: Model files not found. Using mock predictions.")

    def predict(self, age: int, gender: int, severity: int, duration: float) -> str:
        if self._model and self._meta:
            features = self._meta.get("features", [])
            input_dict = {
                "Age": age,
                "Gender": gender,
                "Severity": severity,
                "Duration_Min_Days": duration,
            }
            row = {f: input_dict.get(f, 0) for f in features}
            df = pd.DataFrame([row])

            pred_idx = int(self._model.predict(df)[0])
            classes  = self._meta.get("classes", [])
            if 0 <= pred_idx < len(classes):
                return str(classes[pred_idx])
            return "Unknown Disease"
        else:
            return "Mock Disease (Model Not Loaded)"
