from typing import Dict, Any

def calculate_comorbidity_score(age: int, symptoms: dict) -> float:
    """
    Calculate a rough risk multiplier based on age and chronic indicators.
    Base score is 1.0. Higher is more risk.
    """
    score = 1.0
    
    # Age adjustments
    if age < 5:
        score += 0.3  # Pediatric risk
    elif age > 65:
        score += 0.3  # Elderly risk
    elif age > 80:
        score += 0.5  # High elderly risk
        
    # Chronic indicators mapped from symptoms (if expanded in future)
    # E.g., if we extract "diabetic" or "hypertension" from text
    if symptoms.get("diabetes", 0) == 1:
        score += 0.4
    if symptoms.get("hypertension", 0) == 1:
        score += 0.3
    if symptoms.get("immunocompromised", 0) == 1:
        score += 0.5
    if symptoms.get("pregnant", 0) == 1:
        score += 0.4
        
    return score
