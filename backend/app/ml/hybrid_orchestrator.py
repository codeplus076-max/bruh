import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── STAGE 3: SAFETY FILTER ──────────────────────────────────────────────────────────
BLACKLISTED_HIGH_SEVERITY = ["aids", "hiv", "cancer", "tumor", "sepsis", "stroke", "cervical cancer", "meningitis"]
CHRONIC_ALLOWED = ["diabetes", "hypertension", "asthma", "spondylosis", "arthritis"]

# ── STAGE 6: COMMON CONDITION PRIORITY ──────────────────────────────────────────────
COMMON_CONDITIONS = [
    "common cold",
    "viral infection",
    "muscle strain",
    "postural pain",
    "mild gastritis",
    "allergy",
    "flu"
]

# ── EMERGENCY DISEASES ──────────────────────────────────────────────────────────────
EMERGENCY_DISEASES = {"heart attack", "stroke", "meningitis", "pulmonary embolism", "sepsis"}

# ── STAGE 8: OUTPUT REFRESH / SOFT MAP ──────────────────────────────────────────────
SOFT_NAME_MAP = {
    "cervical spondylosis": "posture-related neck discomfort",
    "arthritis": "joint inflammation or discomfort",
    "migraine": "severe headache episode",
    "gastroenteritis": "stomach bug or digestion issue",
    "hypertension": "elevated blood pressure",
    "appendicitis": "possible abdominal inflammation",
    "fracture": "possible bone injury",
    "infection": "possible localized infection",
    "injury": "possible traumatic injury"
}


def _confidence_band(score: float) -> str:
    if score >= 0.7: return "High"
    elif score >= 0.5: return "Moderate"
    else: return "Low"

def _safe_name(disease: str, score: float) -> str:
    d = disease.strip().lower()
    mapped = False
    for k, v in SOFT_NAME_MAP.items():
        if k in d:
            d = v
            mapped = True
            break
            
    if not mapped and score < 0.3:
        d = "possible inflammation or discomfort in the affected area"
    elif not mapped:
        d = d.title()
        
    if "possible" not in d.lower() and "likely" not in d.lower():
        return f"Likely {d}" if score >= 0.7 else f"Possible {d}"
    return d.title()


class HybridOrchestrator:
    _instance = None
    _model = None
    _vectorizer = None
    _classes: list = []
    _sympscan_db: dict = {}
    _medquad_db: dict = {}
    _symptom_rules: dict = {}

    def __new__(cls, pipeline_dir: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            base = pipeline_dir or os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "pipeline"
            )
            cls._instance._pipeline_dir = base
        return cls._instance

    def _load(self):
        if self._model is not None:
            return
        import joblib
        model_path = os.path.join(self._pipeline_dir, "nlp_model.joblib")
        vec_path = os.path.join(self._pipeline_dir, "tfidf_vectorizer.joblib")
        
        # Datasets
        classes_path = os.path.join(self._pipeline_dir, "nlp_classes.json")
        symp_path = os.path.join(self._pipeline_dir, "sympscan_db.json")
        medquad_path = os.path.join(self._pipeline_dir, "medquad_knowledge.json")
        rules_path = os.path.join(self._pipeline_dir, "symptom_rules_db.json")

        if not os.path.exists(model_path) or not os.path.exists(vec_path):
            return

        try:
            self.__class__._model = joblib.load(model_path)
            self.__class__._vectorizer = joblib.load(vec_path)

            if os.path.exists(classes_path):
                with open(classes_path, encoding="utf-8") as f:
                    self.__class__._classes = json.load(f).get("classes", [])
            else:
                self.__class__._classes = list(self._model.classes_)

            if os.path.exists(symp_path):
                with open(symp_path, encoding="utf-8") as f:
                    self.__class__._sympscan_db = json.load(f)
                    
            if os.path.exists(medquad_path):
                with open(medquad_path, encoding="utf-8") as f:
                    self.__class__._medquad_db = json.load(f)
                    
            if os.path.exists(rules_path):
                with open(rules_path, encoding="utf-8") as f:
                    self.__class__._symptom_rules = json.load(f)

        except Exception as e:
            logger.exception(f"HybridOrchestrator: Failed to load — {e}")

    @property
    def is_ready(self) -> bool:
        return self._model is not None and self._vectorizer is not None


    def _stage3_safety_filter(self, d_name: str, duration_days: float, severity: int) -> tuple[bool, Optional[str]]:
        """Stage 3: SAFETY FILTER"""
        for bl in BLACKLISTED_HIGH_SEVERITY:
            if bl in d_name:
                if duration_days > 14 and severity >= 3:
                    return True, None
                return False, f"Suppressed extreme high-severity disease '{d_name}' due to insufficient markers."
        return True, None


    def _stage4_context_filter(self, d_name: str, has_dig: bool, has_resp: bool, duration_days: float, severity: int) -> tuple[bool, str]:
        """Stage 4: CONTEXT FILTERING"""
        if duration_days < 7:
            for chr_d in CHRONIC_ALLOWED:
                if chr_d in d_name:
                    return False, f"Removed chronic/degenerative condition '{d_name}' because duration < 7 days."
                    
        if not has_dig:
            if "gerd" in d_name or "gastritis" in d_name or "peptic" in d_name:
                return False, f"Removed '{d_name}' because no digestive symptoms are present."
                
        # If no systemic/chronic markers, we can suppress diabetes/hypertension
        if duration_days < 7 and severity < 2:
             if "diabetes" in d_name or "hypertension" in d_name:
                return False, f"Removed chronic trait '{d_name}' because presentation does not match advanced chronic stage."
                
        return True, ""


    def _stage5_body_location(self, d_name: str, symp_text: str, duration_days: float, active_bools: dict) -> tuple[float, list]:
        """Stage 5: BODY LOCATION LOGIC (Back Pain Rule Engine)"""
        rule_score = 0.0
        reasons = []
        symp_lower = symp_text.lower()
        
        has_back_pain = "back pain" in symp_lower or "backache" in symp_lower or "pain in back" in symp_lower
        
        # General back pain + short duration
        if has_back_pain and duration_days <= 5:
            if "muscle strain" in d_name or "postural pain" in d_name:
                rule_score += 0.5
                reasons.append("Boosted 'Muscle Strain / Postural Pain' due to short duration back pain.")
        
        # Location specific
        if has_back_pain:
            if "upper" in symp_lower or "neck" in symp_lower:
                if "cervical" in d_name or "neck" in d_name or "shoulder" in d_name:
                    rule_score += 0.4
                    reasons.append("Boosted neck/shoulder conditions due to 'upper' location.")
            
            if "middle" in symp_lower:
                if "muscle strain" in d_name or "postural" in d_name:
                    rule_score += 0.5
                    reasons.append("Boosted muscle strain due to 'middle' back pain.")
                if "cervical" in d_name:
                    rule_score -= 1.0 # Suppress
                    reasons.append("Suppressed cervical condition due to 'middle' back pain.")
                    
            if "lower" in symp_lower or "lumbar" in symp_lower:
                if "lumbar" in d_name or "sciatica" in d_name:
                    rule_score += 0.4
                    reasons.append("Boosted lumbar conditions due to 'lower' back pain.")
                    
        return rule_score, reasons


    def predict(
        self,
        age: int,
        gender: int,
        severity: int,
        duration_days: float,
        clinical_symptoms: str = "",
        fever: bool = False,
        cough: bool = False,
        sore_throat: bool = False,
        breathlessness: bool = False,
        chest_pain: bool = False,
        vomiting: bool = False,
        diarrhea: bool = False,
        headache: bool = False,
        rash: bool = False,
        joint_pain: bool = False,
        progression: str = "unknown",
        **_extra_flags,
    ) -> dict:
        self._load()

        fallback = {
            "summary": "Please provide more details about your symptoms.",
            "likely_conditions": [],
            "confidence": "Low",
            "risk_level": "Low",
            "urgency": "Home Care",
            "reasoning_summary": "Insufficient symptoms mapped to make a reliable assessment.",
            "home_care": ["Rest", "Drink fluids", "Monitor for changes"],
            "safety_disclaimer": "This is not a medical diagnosis."
        }

        if not self.is_ready:
            return fallback

        # ── INITIALIZE SYMPTOM VECTORS
        symp_text = clinical_symptoms.strip() or "general symptoms"
        active_bools = {
            "fever": fever, "cough": cough, "sore_throat": sore_throat, "breathlessness": breathlessness,
            "chest_pain": chest_pain, "vomiting": vomiting, "diarrhea": diarrhea, "headache": headache,
            "rash": rash, "joint_pain": joint_pain
        }
        matched_symptoms = [s for s, v in active_bools.items() if v]

        # ── STAGE 1: NLP Prediction
        try:
            X = self._vectorizer.transform([symp_text])
            probas = self._model.predict_proba(X)[0]
            import numpy as np
            top_idx = np.argsort(probas)[::-1][:15]
            candidates = [{"name": str(self._classes[i]), "ml_prob": float(probas[i])} for i in top_idx]
        except Exception:
            return fallback

        has_resp = cough or sore_throat or breathlessness
        has_dig = vomiting or diarrhea or "nausea" in symp_text.lower() or "stomach" in symp_text.lower() or "abdom" in symp_text.lower()

        # OVERRIDE FLAG TRACKERS
        is_abdominal_override = False
        is_trauma_override = False
        
        # Abdominal Rule
        if "lower right" in symp_text.lower() and ("abdom" in symp_text.lower() or "stomach" in symp_text.lower()):
            if (vomiting or fever or "nausea" in symp_text.lower() or "appetite" in symp_text.lower()) and progression == "worsening":
                is_abdominal_override = True
                
        # Trauma Rule 
        is_injury = _extra_flags.get("is_injury", False)
        cannot_walk = "walk" in symp_text.lower() and ("cannot" in symp_text.lower() or "can't" in symp_text.lower() or "unable" in symp_text.lower())
        has_deformity = "deform" in symp_text.lower()
        
        if is_injury:
             is_trauma_override = True

        filtered_candidates = []
        for c in candidates:
            d_name = c["name"].lower()
            ml_prob = c["ml_prob"]
            rule_reasons = []

            # STAGE 3: Safety Filter
            allowed, rs_s3 = self._stage3_safety_filter(d_name, duration_days, severity)
            if not allowed: continue

            # STAGE 4: Context Filtering
            allowed, rs_s4 = self._stage4_context_filter(d_name, has_dig, has_resp, duration_days, severity)
            if not allowed: continue

            # STAGE 5: Body Location Logic & Ext. Rules
            r_score, r_reasons = self._stage5_body_location(d_name, symp_text, duration_days, active_bools)
            rule_score = max(0.0, r_score)
            if r_score < 0: continue # Hard suppressed
            rule_reasons.extend(r_reasons)
            
            # Duration Match
            duration_match = 0.0
            if duration_days <= 5 and any(k in d_name for k in ["cold", "flu", "viral", "strain", "pain"]):
                duration_match = 0.8
            elif duration_days > 14 and severity >= 2 and any(k in d_name for k in CHRONIC_ALLOWED):
                duration_match = 0.8

            # STAGE 6: Common Condition Priority
            common_boost = 0.0
            if any(k in d_name for k in COMMON_CONDITIONS):
                common_boost = 1.0

            if is_abdominal_override and "appendicitis" in d_name:
                rule_score += 2.0
                rule_reasons.append("Clinical pattern matched possible severe abdominal inflammation.")
            if is_trauma_override and ("fracture" in d_name or "injury" in d_name):
                rule_score += 1.0
                rule_reasons.append("Physical trauma detected.")

            # Compute symptom coverage via Disease-Symptom database
            coverage = ml_prob + 0.2 # Fallback
            if d_name in self._symptom_rules and matched_symptoms:
                db_symps = self._symptom_rules[d_name]
                if db_symps:
                    matches = sum(1 for ms in matched_symptoms if any(ms in ds for ds in db_symps) or any(ds in ms for ds in db_symps))
                    coverage = matches / len(matched_symptoms)

            # STAGE 7: Advanced Scoring formula exactly as provided
            final_score = (
                0.40 * ml_prob +
                0.25 * min(1.0, coverage) +
                0.20 * min(1.0, rule_score) +
                0.10 * duration_match +
                0.05 * common_boost
            )
            
            # Normalization floor ensuring final top condition displays logic cleanly
            final_score = min(0.99, final_score * 1.5)

            filtered_candidates.append({
                "name": c["name"],
                "raw_name": c["name"],
                "score": final_score,
                "reasons": rule_reasons,
                "d_name_lower": d_name,
                "ml_prob": ml_prob
            })

        # STAGE 8: Output Generation
        filtered_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = filtered_candidates[:3]

        if not top_candidates:
            return fallback

        top_score = top_candidates[0]["score"]
        top_disease = top_candidates[0]["name"]
        
        confidence = _confidence_band(top_score)
        
        # Expand Urgency Engine
        urgency = "HOME_CARE"
        risk_level = "Low"
        summary_text = "Your symptoms suggest a mild condition requiring home observation."
        reasoning_summary = "Evaluated based on clinical presentation and intelligent symptom mapping."
        
        # Base Urgency mapping
        if severity <= 1 and duration_days <= 3:
             urgency = "HOME_CARE"
             risk_level = "Low"
             summary_text = "Your symptoms suggest a mild condition, commonly caused by posture, minor strain, or a brief viral reaction."
             reasoning_summary = "Short duration and absence of serious warning signs indicate a non-serious condition. " + (top_candidates[0]["reasons"][0] if top_candidates[0]["reasons"] else "")
        elif severity == 2 and duration_days <= 5:
             urgency = "URGENT"
             risk_level = "Moderate"
        elif severity >= 3 or ("radiating" in symp_text.lower()):
             urgency = "URGENT"
             risk_level = "High"
             summary_text = "Your symptoms require medical attention to successfully evaluate the severity."
             
        # Worsening & Duration Rule
        if progression == "worsening" or (duration_days > 2.0 and progression != "improving"):
             if urgency == "HOME_CARE":
                 urgency = "URGENT"
                 risk_level = "Moderate"

        # Trauma Logic
        if is_trauma_override:
            if cannot_walk or has_deformity:
                 urgency = "EMERGENCY"
                 risk_level = "Emergency"
                 summary_text = "Severe trauma indicators detected. Please seek immediate medical help."
            else:
                 urgency = "URGENT"
                 risk_level = "High"
                 
        # Abdominal Logic
        if is_abdominal_override:
             urgency = "URGENT"
             risk_level = "High"
             summary_text = "Pattern suggests potential abdominal inflammation requiring same-day clinical assessment."

        # Hard overrides RED FLAGS
        if any(ed in top_disease.lower() for ed in EMERGENCY_DISEASES) or (chest_pain and breathlessness) or ("bleeding" in symp_text.lower() and "heavy" in symp_text.lower()) or cannot_walk or has_deformity:
            urgency = "EMERGENCY"
            risk_level = "Emergency"
            summary_text = "Critical symptoms detected. Please seek immediate emergency care."
            
        # STAGE 8: FINAL SAFETY RECHECK
        if urgency == "HOME_CARE":
            if progression == "worsening" or duration_days > 2.0 or "increasing" in symp_text.lower() or "localized" in symp_text.lower():
                urgency = "URGENT"
                risk_level = "Moderate"

        likely_conditions = []
        for c in (top_candidates if confidence != "Low" else top_candidates[:1]):
            # STAGE 2: KNOWLEDGE ENRICHMENT loop
            # Query MedQuAD generic description for this disease to improve output context implicitly
            mq_desc = ""
            for mq_k, mq_v in self._medquad_db.items():
                if mq_k in c["d_name_lower"] or c["d_name_lower"] in mq_k:
                    mq_desc = mq_v.get("overview", "")
                    break
                    
            if c == top_candidates[0] and mq_desc and "Short duration" not in reasoning_summary:
                reasoning_summary = f"{mq_desc[:120]}... (MedQuAD DB Enrichment)"

            likely_conditions.append({
                "name": _safe_name(c["name"], c["score"]),
                "raw_name": c["raw_name"],
                "confidence_band": _confidence_band(c["score"]),
                "score": c["score"],
                "boosted_by_rules": bool(c["reasons"]),
                "confidence": _confidence_band(c["score"]),
                "raw_score": c["score"]
            })

        # Fetch knowledge base for supportive care
        db_key = top_disease.strip().lower()
        db_data = self._sympscan_db.get(db_key, {})
        for k in self._sympscan_db:
             if k in db_key or db_key in k:
                 db_data = self._sympscan_db[k]
                 break

        return {
            "summary": summary_text,
            "likely_conditions": likely_conditions,
            "confidence": confidence,
            "risk_level": risk_level,
            "urgency": urgency,
            "reasoning_summary": reasoning_summary,
            "home_care": db_data.get("home_care") or ["Rest adequately", "Drink warm fluids", "Monitor for changes"],
            "precautions": db_data.get("precautions") or ["Maintain hygiene", "Avoid excessive physical strain"],
            "when_to_seek_help": db_data.get("when_to_seek_help") or ["If symptoms persist beyond 5 days", "If fever becomes high", "If breathing difficulty occurs"],
            "safety_disclaimer": "This is not a medical diagnosis. Always prioritize safety over AI guidance.",
            
            # Extras
            "disease": f"Possible {top_disease}",
            "confidence_score": top_score,
            "emergency": urgency == "Emergency",
            "blacklist_applied": False,
            "rules_applied": top_candidates[0]["reasons"] if top_candidates[0]["reasons"] else []
        }
