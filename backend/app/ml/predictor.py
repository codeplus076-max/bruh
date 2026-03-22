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
            base_dir = model_dir or os.path.dirname(os.path.abspath(__file__))
            # Support both .joblib (sklearn) and .json (XGBoost native) model files
            joblib_path = os.path.join(base_dir, "triage_model_v2.joblib")
            json_path = os.path.join(base_dir, "triage_model_v2.json")
            if os.path.exists(joblib_path):
                cls._instance.model_path = joblib_path
                cls._instance.model_format = "joblib"
            elif os.path.exists(json_path):
                cls._instance.model_path = json_path
                cls._instance.model_format = "xgb_json"
            else:
                cls._instance.model_path = joblib_path  # Will fail gracefully
                cls._instance.model_format = "joblib"
            cls._instance.meta_path = os.path.join(base_dir, "model_meta_v2.joblib")
            # DELIBERATE LAZY LOADING: Do not load the model here to prevent Render 512MB RAM OOM on Uvicorn Boot.
        return cls._instance

    def load_model(self):
        # Prevent reloading if already in memory
        if self._model is not None and self._meta is not None:
            return

        print(f"Loading ML Model from disk into memory: {self.model_path} (format: {self.model_format})")
        if os.path.exists(self.model_path) and os.path.exists(self.meta_path):
            if self.model_format == "xgb_json":
                try:
                    import xgboost as xgb
                    booster = xgb.Booster()
                    booster.load_model(self.model_path)
                    self.__class__._model = booster
                    print("Successfully loaded XGBoost model from JSON format.")
                except Exception as e:
                    print(f"XGBoost JSON load failed: {e}. Falling back to joblib.")
                    self.__class__._model = None
            else:
                try:
                    # Use mmap_mode='r' to prevent loading the entire payload into active RAM
                    self.__class__._model = joblib.load(self.model_path, mmap_mode='r')
                    print("Successfully loaded model from joblib format.")
                except Exception as e:
                    print(f"Joblib model load failed: {e}")
                    self.__class__._model = None
            
            try:
                self.__class__._meta = joblib.load(self.meta_path, mmap_mode='r')
                print("Successfully loaded model metadata.")
            except Exception as e:
                print(f"Metadata load failed: {e}")
                self.__class__._meta = None
        else:
            missing = []
            if not os.path.exists(self.model_path):
                missing.append(self.model_path)
            if not os.path.exists(self.meta_path):
                missing.append(self.meta_path)
            print(f"Warning: Model files not found: {missing}. Using mock predictions.")
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
            import xgboost as xgb
            is_booster = isinstance(self._model, xgb.Booster)

            if is_booster:
                # XGBoost Booster path
                classes = self._meta.get('classes', [])
                dmatrix = xgb.DMatrix(X_infer, feature_names=features)
                probas = self._model.predict(dmatrix)
                # predict() on booster returns raw margin or probability matrix depending on objective
                if probas.ndim == 2:
                    max_idx = int(np.argmax(probas[0]))
                    confidence_score = float(probas[0][max_idx])
                else:
                    # Binary classification fallback
                    max_idx = int(round(probas[0]))
                    confidence_score = float(probas[0]) if max_idx == 1 else 1.0 - float(probas[0])
                if 0 <= max_idx < len(classes):
                    disease_label = str(classes[max_idx])
            elif hasattr(self._model, "predict_proba"):
                # Sklearn-compatible path
                probas = self._model.predict_proba(X_infer)[0]
                max_idx = int(np.argmax(probas))
                confidence_score = float(probas[max_idx])
                classes = self._meta.get('classes', [])
                if 0 <= max_idx < len(classes):
                    disease_label = str(classes[max_idx])
            else:
                # Fallback to direct prediction
                disease_label = str(self._model.predict(X_infer)[0])
                confidence_score = 0.5
        except Exception as e:
            print(f"Prediction error: {e}")
            disease_label = "Error in Prediction"

        # 5. Calculate Medical Confidence & Explainability
        important_features = []
        try:
            import xgboost as xgb
            if isinstance(self._model, xgb.Booster):
                scores = self._model.get_score(importance_type='gain')
                fi = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                for feat, _ in fi:
                    if row.get(feat, 0) > 0 and feat not in ['Age', 'Gender', 'Severity', 'Duration_Min_Days']:
                        important_features.append(feat)
                    if len(important_features) >= 3:
                        break
            elif hasattr(self._model, 'feature_importances_'):
                importances = self._model.feature_importances_
                fi = list(zip(features, importances))
                fi.sort(key=lambda x: x[1], reverse=True)
                for feat, imp in fi:
                    if row.get(feat, 0) > 0 and feat not in ['Age', 'Gender', 'Severity', 'Duration_Min_Days']:
                        important_features.append(feat)
                    if len(important_features) >= 3:
                        break
        except Exception as e:
            print(f"Feature importance error: {e}")
            
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
