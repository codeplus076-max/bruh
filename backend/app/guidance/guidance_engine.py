from typing import List, Dict, Any
from app.guidance.first_aid import get_first_aid
from app.guidance.home_remedies import get_home_remedies
from app.guidance.routine import get_daily_routine
from app.guidance.otc_medicine import get_otc_medicines
from app.guidance.safety import get_safety_warnings
from app.guidance.escalation import get_escalation_rules

def generate_guidance(
    symptoms: List[str], 
    disease: str, 
    age: int, 
    severity_score: float, 
    risk_level: str, 
    urgency: str
) -> Dict[str, Any]:
    
    first_aid = get_first_aid(symptoms, disease)
    routine = get_daily_routine(age, severity_score, symptoms, disease)
    warnings = get_safety_warnings(symptoms, disease)
    when_to_seek_care = get_escalation_rules(risk_level, urgency)
    
    # If it's an emergency, completely strip home remedies and medicines to force hospital visit
    if risk_level == "Emergency":
        home_remedies = ["Supportive care at home is NOT appropriate for emergency conditions. Proceed to a hospital."]
        medicines = []
    else:
        home_remedies = get_home_remedies(symptoms)
        medicines = get_otc_medicines(symptoms, age, risk_level)

    return {
        "first_aid": first_aid,
        "home_remedies": home_remedies,
        "routine": routine,
        "medicines": medicines,
        "warnings": warnings,
        "when_to_seek_care": when_to_seek_care
    }
