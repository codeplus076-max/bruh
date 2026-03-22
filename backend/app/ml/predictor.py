import os
import gc
import json
import numpy as np
from .symptom_mapper import SymptomMapper
from .risk_engine import calculate_risk

class DiseasePredictor:
    """
    Ultra-Lean Singleton AI Disease Predictor. 
    Uses ONLY native XGBoost + Numpy to minimize RAM footprint on 512MB Free Tier.
    Eliminates scikit-learn and pandas dependencies.
    """
    _instance = None
    _model = None
    _meta = None

    def __new__(cls, model_dir: str = None):
        if cls._instance is None:
            cls._instance = super(DiseasePredictor, cls).__new__(cls)
            model_base = model_dir or os.path.dirname(os.path.abspath(__file__))
            
            # Using native JSON model for zero-overhead loading
            cls._instance.model_path = os.path.join(model_base, "triage_model_v2.json")
            cls._instance.meta_path = os.path.join(model_base, "model_meta_v2.joblib")
            
            # If JSON doesn't exist, fallback to legacy only if absolutely necessary
            if not os.path.exists(cls._instance.model_path):
                cls._instance.model_path = os.path.join(model_base, "triage_model_v2.joblib")
                
        return cls._instance

    def load_model(self):
        if self._model is not None and self._meta is not None:
            return

        import xgboost as xgb
        import joblib
        import gc
        
        print(f"ULTRA-LEAN START: Loading native model from {self.model_path}")
        try:
            # 1. Load Metadata (Contains feature names and class labels)
            if os.path.exists(self.meta_path):
                self.__class__._meta = joblib.load(self.meta_path)
                print("Metadata loaded.")
            
            # 2. Load Native Booster
            if os.path.exists(self.model_path):
                if self.model_path.endswith('.json'):
                    self.__class__._model = xgb.Booster()
                    self.__class__._model.load_model(self.model_path)
                    print("Native XGBoost Booster initialized (JSON).")
                else:
                    # Legacy fallback
                    model_obj = joblib.load(self.model_path)
                    if hasattr(model_obj, "get_booster"):
                        self.__class__._model = model_obj.get_booster()
                        print("Booster extracted from Joblib wrapper.")
                    else:
                        self.__class__._model = model_obj
                        print("Warning: Using legacy model object directly.")
                
                # Cleanup Joblib intermediates immediately
                gc.collect()
            else:
                print(f"CRITICAL: Model file not found at {self.model_path}")
        except Exception as e:
            print(f"CRITICAL ERROR loading model: {e}")
            import traceback
            traceback.print_exc()

    def predict(self, age: int, gender: int, severity: int, duration: float, clinical_symptoms: str = "") -> dict:
        if not self.is_loaded:
            self.load_model()

        if not self._model or not self._meta:
            return {
                "condition": "Analysis Error (Model Unavailable)",
                "confidence": 0.0,
                "risk_level": "Unknown",
                "risk_score": 0,
                "important_features": []
            }

        # 1. Feature Extraction (Numpy based)
        mapped_features = SymptomMapper.extract_features(clinical_symptoms)
        features = self._meta.get('features', [])
        
        input_data = {
            'Age': age,
            'Gender': gender,
            'Severity': severity,
            'Duration_Min_Days': duration
        }
        input_data.update(mapped_features)
        
        # 2. Build 2D Numpy sequence for inference (Memory efficient)
        row = [float(input_data.get(f, 0)) for f in features]
        X_infer = np.array([row], dtype=np.float32)
        
        # 3. Perform Inference using DMatrix (Required for raw Booster)
        import xgboost as xgb
        dmatrix = xgb.DMatrix(X_infer, feature_names=features)
        
        disease_label = "Unknown Condition"
        confidence_score = 0.0
        
        try:
            # Predict probabilities
            probas = self._model.predict(dmatrix)[0]
            max_idx = np.argmax(probas)
            confidence_score = float(probas[max_idx])
            
            classes = self._meta.get('classes', [])
            if 0 <= max_idx < len(classes):
                disease_label = str(classes[max_idx])
        except Exception as e:
            print(f"Inference error: {e}")
            disease_label = "Triage Inconclusive"

        # 4. Risk engine integration
        risk_level, risk_score = calculate_risk(
            prediction=disease_label, 
            confidence=confidence_score, 
            severity=severity, 
            duration_days=duration, 
            symptoms=list(mapped_features.keys())
        )

        return {
            "condition": disease_label,
            "confidence": round(confidence_score, 2),
            "risk_level": risk_level,
            "risk_score": risk_score,
            "important_features": [f for f in mapped_features.keys() if f in features][:3]
        }

    def predict_with_metadata(self, *args, **kwargs) -> dict:
        res = self.predict(*args, **kwargs)
        return {
            "disease": res["condition"],
            "confidence": "High" if res["confidence"] > 0.7 else "Moderate" if res["confidence"] > 0.4 else "Low",
            "confidence_score": res["confidence"],
            "matched_symptoms": res["important_features"]
        }

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._meta is not None
