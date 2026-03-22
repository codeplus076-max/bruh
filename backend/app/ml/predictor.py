import os
import joblib
import numpy as np
from .symptom_mapper import SymptomMapper
from .risk_engine import calculate_risk

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
                "triage_model_v2.joblib"
            )
            cls._instance.meta_path = os.path.join(
                model_dir or os.path.dirname(os.path.abspath(__file__)), 
                "model_meta_v2.joblib"
            )
            # DELIBERATE LAZY LOADING: Do not load the model here to prevent Render 512MB RAM OOM on Uvicorn Boot.
        return cls._instance

    def load_model(self):
        # Prevent reloading if already in memory
        if self._model is not None and self._meta is not None:
            return

        import gc
        print(f"Loading ML Model from disk: {self.model_path}")
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.meta_path):
                # Removed mmap_mode because model is compressed
                self.__class__._model = joblib.load(self.model_path)
                self.__class__._meta = joblib.load(self.meta_path)
                print("Successfully loaded ML model and metadata.")
                gc.collect() # Immediate cleanup after load
            else:
                print(f"Warning: Model or meta not found in {self.model_path}. Using mock.")
                self.__class__._model = None
                self.__class__._meta = None
        except Exception as e:
            print(f"CRITICAL ERROR loading model: {e}")
            import traceback
            traceback.print_exc()
            self.__class__._model = None
            self.__class__._meta = None

    def predict(self, age: int, gender: int, severity: int, duration: float, clinical_symptoms: str = "") -> dict:
        """
        Predicts disease with medical confidence scoring, risk engine integration,
        and precise standardized JSON-like output schemas.
        """
        # Lazy load strictly at inference time
        if not self.is_loaded:
            self.load_model()

        if not self._model or not self._meta:
            return {
                "condition": "Mock Disease (Model Not Loaded)",
                "confidence": 0.0,
                "risk_level": "Low",
                "risk_score": 0,
                "important_features": []
            }

        # 1. Map text symptoms to feature flags
        mapped_features = SymptomMapper.extract_features(clinical_symptoms)
        
        # 2. Build input dictionary
        input_dict = {
            'Age': age,
            'Gender': gender,
            'Severity': severity,
            'Duration_Min_Days': duration
        }
        input_dict.update(mapped_features)
        
        # 3. Create Numpy Array for inference (Bypass Pandas to conserve ~50MB RAM)
        features = self._meta.get('features', [])
        row = {f: input_dict.get(f, 0) for f in features}
        
        # XGBoost expects a 2D array if Pandas is excluded
        X_infer = np.array([[row[f] for f in features]])
        
        # 4. Perform Inference
        disease_label = "Unknown Disease"
        confidence_score = 0.0
        
        try:
            # Get probabilities if supported
            if hasattr(self._model, "predict_proba"):
                probas = self._model.predict_proba(X_infer)[0]
                max_idx = np.argmax(probas)
                confidence_score = float(probas[max_idx])
                
                classes = self._meta.get('classes', [])
                if 0 <= max_idx < len(classes):
                    disease_label = str(classes[max_idx])
            else:
                # Fallback to direct prediction
                disease_label = str(self._model.predict(X_infer)[0])
                confidence_score = 0.5 # Default for non-probabilistic models
        except Exception as e:
            print(f"Prediction error: {e}")
            disease_label = "Error in Prediction"

        # 5. Calculate Medical Confidence & Explainability
        # Check matching features for explainability
        important_features = []
        if hasattr(self._model, 'feature_importances_'):
            importances = self._model.feature_importances_
            fi = list(zip(features, importances))
            fi.sort(key=lambda x: x[1], reverse=True)
            # Find the top 3 features the user ACTUALLY HAS that drove the prediction
            for feat, imp in fi:
                if row.get(feat, 0) > 0 and feat not in ['Age', 'Gender', 'Severity', 'Duration_Min_Days']:
                    important_features.append(feat)
                if len(important_features) >= 3:
                    break
            
        # 6. Comprehensive Risk Engine Logic
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
            "important_features": important_features
        }

    # Backward compatibility method if needed
    def predict_with_metadata(self, *args, **kwargs) -> dict:
        res = self.predict(*args, **kwargs)
        # Adapt new schema to old schema just in case something internally relies on it
        return {
            "disease": res["condition"],
            "confidence": "High" if res["confidence"] > 0.7 else "Moderate" if res["confidence"] > 0.4 else "Low",
            "confidence_score": res["confidence"],
            "matched_symptoms": res["important_features"]
        }

    @property
    def is_loaded(self) -> bool:
        """Returns True if the ML payload has successfully initialized into RAM."""
        return self._model is not None and self._meta is not None
