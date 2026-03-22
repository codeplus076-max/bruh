import os
import json
import re
import requests
from .symptom_mapper import SymptomMapper
from .risk_engine import calculate_risk

# ─────────────────────────────────────────────────────────────────────────────
# Gemini-powered Disease Predictor (REST API Version)
# The XGBoost model files (triage_model_v2.json / model_meta_v2.joblib) are
# preserved on disk but are NOT loaded during inference.
# All disease prediction is now handled by the Gemini REST API.
# ─────────────────────────────────────────────────────────────────────────────

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

PREDICTION_PROMPT = """\
You are a precise medical AI trained to identify likely diseases from patient data and provide actionable home care guidance.
Given the following patient information, identify the SINGLE most likely disease/condition and construct a comprehensive triage plan.

Patient Data:
- Age: {age}
- Gender: {gender}
- Symptom Severity (1=mild, 2=moderate, 3=severe): {severity}
- Duration (days): {duration}
- Reported Symptoms: {symptoms}

Return ONLY a valid JSON object with no markdown formatting, no code blocks, no extra text matching this exact schema:
{{
  "condition": "<Most likely disease name, be specific>",
  "confidence": <float 0.0 to 1.0>,
  "key_symptoms": ["<symptom1>", "<symptom2>", "<symptom3>"],
  "first_aid": ["<immediate action 1>", "<immediate action 2>"],
  "home_remedies": ["<remedy 1>", "<diet plan 1>"],
  "routine": ["<daily habit 1>"],
  "medicines": [
    {{"name": "<low dosage OTC med>", "purpose": "<why>", "guidance": "<how to take>", "warning": "<optional side effect>"}}
  ],
  "warnings": ["<critical warning>", "Do NOT self-medicate with antibiotics. They only treat bacterial infections and can be harmful if misused."],
  "when_to_seek_care": ["<hospital trigger 1>"],
  "explanation": ["<medical reasoning>"]
}}

Rules:
- condition must be a real medical disease name (e.g. "Migraine", "Common Cold", "Type 2 Diabetes").
- confidence reflects how certain you are (0.9+ = very certain, 0.6-0.9 = likely, below 0.6 = uncertain).
- key_symptoms lists the 2-3 symptoms that most influenced the diagnosis.
- keep recommended medicines to strictly LOW DOSAGE, LOW POWER, Safe OTC Medicines only.
- focus heavily on supportive home care, home remedies, first aid, and diet plans (if needed).
- explicitly enforce the rule that antibiotics should NEVER be self-medicated.
- explanation must contain Medical Reasoning explaining the diagnosis.
"""

class DiseasePredictor:
    """
    Singleton Disease Predictor powered by Google Gemini REST API.
    The local XGBoost model files are preserved on disk but not used for inference.
    """
    _instance = None

    def __new__(cls, model_dir: str = None):
        if cls._instance is None:
            cls._instance = super(DiseasePredictor, cls).__new__(cls)
            cls._instance._api_key = None
            cls._instance._initialized = False
        return cls._instance

    def _init_client(self):
        if self._initialized:
            return
        
        self._api_key = os.getenv("GEMINI_API_KEY")
        if self._api_key:
            print(f"Gemini REST predictor initialized with model: {GEMINI_MODEL}")
        else:
            print("Warning: GEMINI_API_KEY not set. Predictions will use fallback mock.")
        self._initialized = True

    def load_model(self):
        """No-op. Gemini predictor has no local model to load."""
        self._init_client()

    @property
    def is_loaded(self) -> bool:
        """Returns True if Gemini API key is configured."""
        if not self._initialized:
            self._init_client()
        return bool(self._api_key)

    def predict(self, age: int, gender: int, severity: int, duration: float,
                clinical_symptoms: str = "") -> dict:
        """
        Predicts disease using Gemini REST API.
        Returns the same schema as the old XGBoost predictor so all downstream
        code works without changes.
        """
        if not self._initialized:
            self._init_client()

        condition = "Unknown Condition"
        confidence_score = 0.0
        important_features = []
        first_aid = []
        home_remedies = []
        routine = []
        medicines = []
        warnings = []
        when_to_seek_care = []
        explanation = []

        # Map symptom text → feature flags (kept for risk engine compatibility)
        mapped_features = SymptomMapper.extract_features(clinical_symptoms)

        if self._api_key:
            gender_str = "Male" if gender == 1 else "Female"
            symptom_text = clinical_symptoms.strip() or ", ".join(mapped_features.keys()) or "None reported"

            prompt = PREDICTION_PROMPT.format(
                age=age,
                gender=gender_str,
                severity=severity,
                duration=duration,
                symptoms=symptom_text
            )

            try:
                # Gemini REST payload
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 2048
                    }
                }
                
                resp = requests.post(
                    f"{GEMINI_API_URL}?key={self._api_key}",
                    json=payload,
                    timeout=30
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    # Parse REST API response structure
                    raw = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    
                    # Clean the raw text and extract JSON block
                    raw = raw.strip()
                    # Find first '{' and last '}'
                    start_idx = raw.find('{')
                    end_idx = raw.rfind('}')
                    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
                        raw = raw[start_idx:end_idx+1]
                    else:
                        raise ValueError("No JSON object '{...}' found in response.")

                    parsed = json.loads(raw)
                    condition = parsed.get("condition", "Unknown Condition")
                    confidence_score = float(parsed.get("confidence", 0.5))
                    important_features = parsed.get("key_symptoms", [])
                    first_aid = parsed.get("first_aid", [])
                    home_remedies = parsed.get("home_remedies", [])
                    routine = parsed.get("routine", [])
                    medicines = parsed.get("medicines", [])
                    warnings = parsed.get("warnings", ["Do NOT self-medicate with antibiotics."])
                    when_to_seek_care = parsed.get("when_to_seek_care", [])
                    explanation = parsed.get("explanation", [])
                    print(f"[Gemini] Predicted: {condition} (conf={confidence_score:.2f})")
                elif resp.status_code == 429:
                    print("[Gemini] Rate limit exceeded (HTTP 429).")
                    condition = "API Rate Limit Exceeded"
                    confidence_score = 0.0
                    warnings = ["Google Gemini API rate limit exceeded. Please wait a moment and try again."]
                else:
                    print(f"[Gemini] REST API error {resp.status_code}: {resp.text}")
                    condition = "Prediction API Error"
                    confidence_score = 0.0

            except json.JSONDecodeError as e:
                print(f"[Gemini] JSON parse error: {e}")
                condition = "Prediction Parse Error"
                confidence_score = 0.3
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[Gemini] Prediction error: {e}")
                condition = "Prediction Service Error"
                confidence_score = 0.0
        else:
            return {
                "condition": "Mock Disease (Gemini Not Configured)",
                "confidence": 0.0,
                "risk_level": "Low",
                "risk_score": 0,
                "important_features": [],
                "first_aid": [],
                "home_remedies": [],
                "routine": [],
                "medicines": [],
                "warnings": [],
                "when_to_seek_care": [],
                "explanation": []
            }

        # ── Risk engine (unchanged) ────────────────────────────────────────────
        risk_level, risk_score = calculate_risk(
            prediction=condition,
            confidence=confidence_score,
            severity=severity,
            duration_days=duration,
            symptoms=list(mapped_features.keys())
        )

        return {
            "condition": condition,
            "confidence": round(confidence_score, 2),
            "risk_level": risk_level,
            "risk_score": risk_score,
            "important_features": important_features,
            "first_aid": first_aid,
            "home_remedies": home_remedies,
            "routine": routine,
            "medicines": medicines,
            "warnings": warnings,
            "when_to_seek_care": when_to_seek_care,
            "explanation": explanation
        }

    def predict_with_metadata(self, *args, **kwargs) -> dict:
        """Backward-compatible wrapper used by the /chat endpoint."""
        res = self.predict(*args, **kwargs)
        return {
            "disease": res["condition"],
            "confidence": "High" if res["confidence"] > 0.7 else "Moderate" if res["confidence"] > 0.4 else "Low",
            "confidence_score": res["confidence"],
            "matched_symptoms": res["important_features"],
            "first_aid": res["first_aid"],
            "home_remedies": res["home_remedies"],
            "routine": res["routine"],
            "medicines": res["medicines"],
            "warnings": res["warnings"],
            "when_to_seek_care": res["when_to_seek_care"],
            "explanation": res["explanation"]
        }
