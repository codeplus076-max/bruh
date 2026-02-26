from typing import List

def check_emergency_rules(symptoms: dict) -> dict:
    """
    Check input symptoms against hardcoded emergency criteria.
    Returns { "is_emergency": bool, "reasons": List[str] }
    """
    reasons = []
    
    # Example physiological emergencies
    if symptoms.get("chest_pain", 0) == 1 and symptoms.get("breathlessness", 0) == 1:
        reasons.append("Chest pain combined with breathlessness suggests possible cardiac event.")
        
    if symptoms.get("seizure", 0) == 1 or symptoms.get("convulsions", 0) == 1:
        reasons.append("Reported seizures/convulsions.")
        
    if symptoms.get("unconscious", 0) == 1 or symptoms.get("fainting", 0) == 1:
        reasons.append("Loss of consciousness reported.")
        
    if symptoms.get("severe_bleeding", 0) == 1:
        reasons.append("Severe bleeding reported.")
        
    if symptoms.get("stroke_symptoms", 0) == 1 or (symptoms.get("facial_droop", 0) == 1 or symptoms.get("speech_difficulty", 0) == 1):
        reasons.append("Possible neurological/stroke symptoms detected.")
        
    if symptoms.get("oxygen_distress", 0) == 1 or (symptoms.get("blue_lips", 0) == 1):
        reasons.append("Signs of severe oxygen deprivation.")

    return {
        "is_emergency": len(reasons) > 0,
        "reasons": reasons
    }
