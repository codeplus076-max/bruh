from typing import Dict, Any, List

def detect_severity_flags(severity_input: int, symptoms: dict) -> dict:
    """
    Map reported symptoms and explicit severity (1-3) to clinical severity indicators.
    Returns a dictionary of specific physiological compromises.
    """
    flags = []
    
    # 1. Base input severity from LLM or UI (1: mild, 2: moderate, 3: severe)
    base_severity = severity_input
    
    # 2. Add specific respiratory / infection / neuro flags based on presence
    if symptoms.get("breathlessness", 0) == 1 or symptoms.get("shortness_of_breath", 0) == 1:
        flags.append("Respiratory distress indicator")
        base_severity = max(base_severity, 2)
        
    if symptoms.get("fever", 0) == 1 and symptoms.get("duration_days", 1) > 3:
        flags.append("Prolonged infection marker")
        base_severity = max(base_severity, 2)
        
    if symptoms.get("dizziness", 0) == 1 or symptoms.get("confusion", 0) == 1 or symptoms.get("headache", 0) == 1 and severity_input == 3:
        flags.append("Neurological compromise indicator")
        base_severity = max(base_severity, 2)
        
    if symptoms.get("vomiting", 0) == 1 and symptoms.get("diarrhea", 0) == 1 and symptoms.get("duration_days", 1) >= 2:
        flags.append("Dehydration indicator")
        base_severity = max(base_severity, 2)

    return {
        "calculated_severity": base_severity,
        "flags": flags
    }
