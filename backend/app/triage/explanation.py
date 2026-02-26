from typing import List

def generate_explanation(risk_level: str, disease: str, comorbidity_score: float, severity_flags: List[str], emergency_reasons: List[str], age: int) -> List[str]:
    """
    Produce user-friendly medical reasoning based on clinical triage outputs.
    """
    explanation = []
    
    # Base ML confidence/prediction note
    explanation.append(f"The symptom profile is consistent with {disease}.")
    
    # Comorbidity/Age mapping
    if age < 5:
        explanation.append("Pediatric patient context requires higher precaution.")
    elif age >= 65:
        explanation.append("Elderly patient status increases overall risk tier.")
    
    if comorbidity_score > 1.5:
        explanation.append("Chronic or demographic factors elevate the risk profile.")
        
    # Severity mapping
    for flag in severity_flags:
        if "Respiratory" in flag:
            explanation.append("Breathing difficulties significantly increase severity.")
        elif "Dehydration" in flag:
            explanation.append("Prolonged fluid loss symptoms indicate high risk of dehydration.")
        elif "Prolonged infection" in flag:
            explanation.append("Extended duration of fever suggests a persistent infection requiring assessment.")
        elif "Neurological" in flag:
            explanation.append("Neurological symptoms detected; close monitoring required.")
        else:
            explanation.append(flag)
            
    # Emergency mapping
    for reason in emergency_reasons:
        explanation.append(f"EMERGENCY OVERRIDE: {reason}")
        
    if not explanation or risk_level == "Low":
         explanation = [
             "Symptoms align with typical low-risk presentations.",
             "No severe physiological flags or high-risk demographics detected."
         ]

    return explanation
