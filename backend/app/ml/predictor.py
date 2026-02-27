import os
import joblib
import pandas as pd
import numpy as np
from .symptom_mapper import SymptomMapper

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

    def predict(self, age: int, gender: int, severity: int, duration: float, clinical_symptoms: str = "") -> str:
        """Legacy wrapper for backward compatibility."""
        res = self.predict_with_metadata(age, gender, severity, duration, clinical_symptoms)
        return res["disease"]

    def predict_with_metadata(self, age: int, gender: int, severity: int, duration: float, clinical_symptoms: str) -> dict:
        """
        Predicts disease with medical confidence scoring and symptom mapping.
        """
        if not self._model or not self._meta:
            return {
                "disease": "Mock Disease (Model Not Loaded)",
                "confidence": "Low",
                "confidence_score": 0.0,
                "matched_symptoms": []
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
        
        # 3. Create DataFrame for inference
        features = self._meta.get('features', [])
        row = {f: input_dict.get(f, 0) for f in features}
        df = pd.DataFrame([row])
        
        # 4. Perform Inference
        disease_label = "Unknown Disease"
        confidence_score = 0.0
        
        try:
            # Get probabilities if supported
            if hasattr(self._model, "predict_proba"):
                probas = self._model.predict_proba(df)[0]
                max_idx = np.argmax(probas)
                confidence_score = float(probas[max_idx])
                
                classes = self._meta.get('classes', [])
                if 0 <= max_idx < len(classes):
                    disease_label = str(classes[max_idx])
            else:
                # Fallback to direct prediction
                disease_label = str(self._model.predict(df)[0])
                confidence_score = 0.5 # Default for non-probabilistic models
        except Exception as e:
            print(f"Prediction error: {e}")
            disease_label = "Error in Prediction"

        # 5. Calculate Medical Confidence
        # Factor in: model probability + how many symptoms were actually mapped
        mapping_count = len(mapped_features)
        
        # Sanity check: If almost zero features matched, drop confidence
        if mapping_count == 0:
            confidence_score *= 0.5
            
        final_confidence = "Low"
        if confidence_score > 0.7 and mapping_count >= 1:
            final_confidence = "High"
        elif confidence_score > 0.4:
            final_confidence = "Moderate"
        else:
            final_confidence = "Low"

        # 6. Sanity Validation Layer: Handle "hand numb" vs "Unknown Viral illness"
        # If confidence is too low or disease seems unlikely, provide caveat
        if final_confidence == "Low" and disease_label == "Unknown Viral Illness":
            disease_label = "Undetermined Condition (Low Confidence)"

        return {
            "disease": disease_label,
            "confidence": final_confidence,
            "confidence_score": round(confidence_score, 2),
            "matched_symptoms": list(mapped_features.keys())
        }

    @property
    def is_loaded(self) -> bool:
        """Returns True if the ML payload has successfully initialized into RAM."""
        return self._model is not None and self._meta is not None
