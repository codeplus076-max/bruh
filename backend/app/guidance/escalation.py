from typing import List

def get_escalation_rules(risk_level: str, urgency: str) -> List[str]:
    escalation = []
    
    if risk_level == "Emergency" or "immediate" in urgency.lower():
        escalation.append("🚨 GO TO THE NEAREST HOSPITAL EMERGENCY UNIT IMMEDIATELY.")
        escalation.append("Do not wait for symptoms to improve. Time is absolutely critical.")
    elif risk_level == "High" or "urgent" in urgency.lower():
        escalation.append("⚠️ VISIT A CLINIC OR DOCTOR TODAY. Do not delay assessment.")
        escalation.append("If symptoms suddenly worsen or you experience difficulty breathing, go to an emergency unit immediately.")
    elif risk_level == "Moderate":
        escalation.append("Monitor yourself closely. Schedule a visit with a local healthcare worker or clinic within 24-48 hours if it doesn't improve.")
        escalation.append("Seek immediate help if you develop a very high fever, severe pain, or inability to keep fluids down.")
    else:
        escalation.append("Monitor your symptoms at home. If you do not see improvement within 3-5 days, visit a local clinic.")
        escalation.append("Return to the clinic sooner if symptoms become significantly worse or new severe symptoms appear.")

    return escalation
