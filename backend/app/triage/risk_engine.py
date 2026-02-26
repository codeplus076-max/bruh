from .comorbidity import calculate_comorbidity_score
from .severity import detect_severity_flags
from .emergency_rules import check_emergency_rules
from .explanation import generate_explanation

def evaluate_patient_risk(age: int, base_severity: int, symptoms: dict, ml_disease: str) -> dict:
    """
    The core risk engine combining MIMIC-inspired logic:
    1. Comorbidity Score (Age/Demographics)
    2. Physiological Severity
    3. Emergency Overrides
    4. ML output integration
    """
    
    # 1. Calculate Comorbidity Score
    c_score = calculate_comorbidity_score(age, symptoms)
    
    # 2. Detect Severity Flags
    sev_assessment = detect_severity_flags(base_severity, symptoms)
    calc_severity = sev_assessment["calculated_severity"]
    sev_flags = sev_assessment["flags"]
    
    # 3. Check Emergency Overrides
    emerg_assessment = check_emergency_rules(symptoms)
    is_emergency = emerg_assessment["is_emergency"]
    emerg_reasons = emerg_assessment["reasons"]
    
    # 4. Integrate to find final Risk Level
    final_risk_score = calc_severity * c_score
    
    risk_level = "Low"
    urgency = "Standard Care"
    confidence = "Medium"
    
    if is_emergency:
        risk_level = "Emergency"
        urgency = "Immediate Hospitalization"
        confidence = "High"
    elif final_risk_score >= 3.5 or calc_severity == 3:
        risk_level = "High"
        urgency = "Urgent Medical Attention"
        confidence = "Medium to High"
    elif final_risk_score >= 2.0 or calc_severity == 2:
        risk_level = "Moderate"
        urgency = "See a Doctor Soon"
        confidence = "Medium"
    else:
        risk_level = "Low"
        urgency = "Home Care / Observation"
        confidence = "High"

    # Convert confidence based on clear clinical boundaries (just illustrative rules for explainability)
    if is_emergency or risk_level == "Low":
        confidence = "High confidence"
    else:
        confidence = "Medium confidence (requires doctor validation)"
        
    # 5. Generate human readable explanation
    explanation = generate_explanation(
        risk_level=risk_level, 
        disease=ml_disease, 
        comorbidity_score=c_score, 
        severity_flags=sev_flags, 
        emergency_reasons=emerg_reasons, 
        age=age
    )
    
    # 6. Output mapping
    return {
        "risk_level": risk_level,
        "urgency": urgency,
        "confidence": confidence,
        "first_aid": [],  # Can be mapped to specific diseases later
        "explanation": explanation,
        "emergency": is_emergency,
        "calculated_severity_score": round(final_risk_score, 2),
    }
