import os
import joblib
import numpy as np
from .symptom_mapper import SymptomMapper

class TriageOrchestrator:
    """
    3-Stage Triage ML Pipeline.
    Stage 1: Disease Prediction (XGBoost)
    Stage 2: Reasoning / Verification (RandomForest)
    Stage 3: Guidance & Urgency (Dictionary Mapping)
    """
    _instance = None
    
    stage1_model = None
    stage1_meta = None
    
    stage2_model = None
    stage2_meta = None
    
    stage3_mapping = None

    def __new__(cls, model_dir: str = None):
        if cls._instance is None:
            cls._instance = super(TriageOrchestrator, cls).__new__(cls)
            cls._instance.model_base = model_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline")
        return cls._instance

    def load_models(self):
        if self.stage1_model is not None:
            return
            
        print(f"LOADING 3-Stage Pipeline from {self.model_base}")
        try:
            import xgboost as xgb
            
            # Load Stage 1
            path1_model = os.path.join(self.model_base, "stage1_disease_xgboost.json")
            path1_meta = os.path.join(self.model_base, "stage1_meta.joblib")
            if os.path.exists(path1_model) and os.path.exists(path1_meta):
                self.stage1_model = xgb.Booster()
                self.stage1_model.load_model(path1_model)
                self.stage1_meta = joblib.load(path1_meta)
            else:
                print("Warning: Stage 1 model missing")

            # Load Stage 2
            path2_model = os.path.join(self.model_base, "stage2_reasoning_rf.joblib")
            path2_meta = os.path.join(self.model_base, "stage2_meta.joblib")
            if os.path.exists(path2_model) and os.path.exists(path2_meta):
                self.stage2_model = joblib.load(path2_model)
                self.stage2_meta = joblib.load(path2_meta)
            else:
                print("Warning: Stage 2 model missing")

            # Load Stage 3
            path3_mapper = os.path.join(self.model_base, "stage3_guidance_mapper.joblib")
            if os.path.exists(path3_mapper):
                self.stage3_mapping = joblib.load(path3_mapper)
            else:
                print("Warning: Stage 3 mapping missing")
                
        except Exception as e:
            print(f"CRITICAL ERROR loading pipeline: {e}")

    def predict(self, age: int, gender: int, severity: int, duration: float, clinical_symptoms: str = "") -> dict:
        self.load_models()
        
        # Default Fallback
        res = {
            "disease": "Inconclusive",
            "confidence_score": 0.0,
            "confidence": "Low",
            "matched_symptoms": [],
            "risk_level": "Medium",
            "treatment_plan": "Consult a local healthcare provider for further diagnosis.",
            "medicine": "Symptomatic relief only (consult doctor)",
            "urgency": "Non-Urgent"
        }
        
        if not self.stage1_model or not self.stage1_meta:
            return res

        import xgboost as xgb
        
        # Extract features map
        mapped_features = SymptomMapper.extract_features(clinical_symptoms)
        
        # --- STAGE 1: DISEASE PREDICTION ---
        features1 = self.stage1_meta.get('features', [])
        row1 = [1.0 if mapped_features.get(f, False) else 0.0 for f in features1]
        
        X_infer1 = np.array([row1], dtype=np.float32)
        dmatrix = xgb.DMatrix(X_infer1, feature_names=features1)
        
        try:
            probas1 = self.stage1_model.predict(dmatrix)[0]
            max_idx1 = np.argmax(probas1)
            confidence_score = float(probas1[max_idx1])
            classes1 = self.stage1_meta.get('classes', [])
            disease_label = str(classes1[max_idx1]) if 0 <= max_idx1 < len(classes1) else "Unknown"
            disease_label = f"[V3 Pipeline] {disease_label}"
        except Exception as e:
            print(f"Stage 1 Error: {e}")
            disease_label = "Inconclusive"
            confidence_score = 0.0

        res["disease"] = disease_label
        res["confidence_score"] = float(confidence_score)
        res["confidence"] = "High" if confidence_score > 0.7 else "Moderate" if confidence_score > 0.4 else "Low"
        res["matched_symptoms"] = [f for f in mapped_features.keys()][:5]

        # --- STAGE 2: REASONING & VERIFICATION ---
        if self.stage2_model and self.stage2_meta and disease_label != "Inconclusive":
            features2 = self.stage2_meta.get('features', [])
            row2 = [1.0 if mapped_features.get(f, False) else 0.0 for f in features2]
            X_infer2 = np.array([row2], dtype=np.float32)
            
            try:
                # RandomForest predict_proba
                probas2 = self.stage2_model.predict_proba(X_infer2)[0]
                classes2 = self.stage2_model.classes_
                max_idx2 = np.argmax(probas2)
                disease_label_v2 = str(classes2[max_idx2])
                
                # Fetch medicine mapped to disease
                med_mapping = self.stage2_meta.get('medicine_mapping', {})
                res["medicine"] = med_mapping.get(disease_label, med_mapping.get(disease_label_v2, "Consult doctor"))

                # if stage1 and stage2 agree, boost confidence
                if disease_label == disease_label_v2:
                    res["confidence"] = "High"
            except Exception as e:
                print(f"Stage 2 Error: {e}")

        # --- STAGE 3: GUIDANCE & URGENCY MAPPING ---
        if self.stage3_mapping and disease_label != "Inconclusive":
            diag_key = disease_label.lower().strip()
            # Try direct match or partial match
            matched_guidance = None
            if diag_key in self.stage3_mapping:
                matched_guidance = self.stage3_mapping[diag_key]
            else:
                for k, v in self.stage3_mapping.items():
                    if k in diag_key or diag_key in k:
                        matched_guidance = v
                        break
                        
            if matched_guidance:
                res["risk_level"] = f"[Stage 3] {matched_guidance.get('severity', 'Medium')}"
                res["treatment_plan"] = matched_guidance.get("treatment_plan", res["treatment_plan"])
                
                urgency = "Non-Urgent"
                sev_lower = str(res["risk_level"]).lower()
                if "high" in sev_lower or "severe" in sev_lower:
                    urgency = "Immediate Visit"
                elif "medium" in sev_lower or "moderate" in sev_lower:
                    urgency = "Visit within 24h"
                res["urgency"] = urgency

        # Fallback if severity mapping wasn't found but model confident
        if res["risk_level"] == "Medium" and severity == 3:
            res["risk_level"] = "High"
            res["urgency"] = "Immediate Visit"

        return res
