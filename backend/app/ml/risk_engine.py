def calculate_risk(prediction: str, confidence: float, severity: int, duration_days: float, symptoms: list) -> tuple[str, int]:
    """
    Computes a comprehensive risk score and categorical risk level.
    Returns: (Risk Level String, Risk Score Integer 0-100)
    """
    base_score = 0
    
    # 1. Base Severity mapped to score (1=Low, 2=Moderate, 3=Severe)
    if severity == 3:
        base_score += 40
    elif severity == 2:
        base_score += 20
    else:
        base_score += 10
        
    # 2. Duration factor
    if duration_days > 14:
        base_score += 15 # Chronic/prolonged
    elif duration_days > 7:
        base_score += 10
    else:
        base_score += 5
        
    # 3. Critical Symptoms trigger rules
    critical_symptoms = [
        "chest_pain", "breathlessness", "fever", "loss_of_consciousness",
        "stiff_neck", "vomiting_blood", "seizures", "diminished_vision",
        "chills", "high_fever", "paralysis", "slurring_words",
        "coughing_up_sputum", "hemoptysis"
    ]
    
    critical_matches = [s for s in symptoms if any(cs in s.lower() for cs in critical_symptoms)]
    if len(critical_matches) >= 2:
        base_score += 30
    elif len(critical_matches) == 1:
        base_score += 15
        
    # 4. Confidence bounds (If model is highly confident it's a severe disease)
    emergency_conditions = [
        "heart disease", "heart attack", "stroke", "meningitis", 
        "pneumonia", "sepsis", "appendicitis", "emergency", "mi", "angina"
    ]
    
    is_emergency_disease = any(e.lower() in prediction.lower() for e in emergency_conditions)
    if is_emergency_disease and confidence > 0.6:
        base_score += 35
        
    # Cap score
    final_score = min(max(int(base_score), 0), 100)
    
    # Stratify risk level
    if final_score >= 80:
        return "Emergency", final_score
    elif final_score >= 55:
        return "High", final_score
    elif final_score >= 35:
        return "Moderate", final_score
    else:
        return "Low", final_score
