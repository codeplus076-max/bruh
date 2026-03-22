from typing import List, Dict

def get_otc_medicines(symptoms: List[str], age: int, risk_level: str) -> List[Dict[str, str]]:
    if risk_level == "Emergency":
        return []

    medicines = []
    s_lower = [s.lower().replace("_", " ") for s in symptoms]

    if any("fever" in s or "headache" in s or "pain" in s or "injury" in s or "fracture" in s for s in s_lower):
        if age >= 12:
            medicines.append({
                "name": "Paracetamol (Acetaminophen)",
                "purpose": "Reduce fever and relieve mild to moderate pain.",
                "guidance": "Usually 500mg - 1000mg every 4-6 hours as needed. Do not exceed 4000mg per day.",
                "warning": "Avoid if you have liver disease. Never give adult doses to children."
            })
        else:
            medicines.append({
                "name": "Pediatric Paracetamol Syrup",
                "purpose": "Reduce fever and mild pain in children.",
                "guidance": "Use exact dosage syringe measuring based on the child's weight, not age.",
                "warning": "Do not combine with other cough/cold medicines containing paracetamol to prevent overdose."
            })

    if any("vomiting" in s or "diarrhea" in s for s in s_lower):
        medicines.append({
            "name": "Oral Rehydration Solution (ORS)",
            "purpose": "Prevent and treat dehydration from fluid loss.",
            "guidance": "Mix 1 packet of ORS powder in 1 liter of safe, boiled, and cooled water. Sip continuously.",
            "warning": "Make fresh daily. Seek immediate help if unable to keep fluids down."
        })
        if age > 5:
            medicines.append({
                "name": "Zinc Supplements",
                "purpose": "Reduce the duration and severity of diarrhea.",
                "guidance": "1 tablet daily for 10-14 days.",
                "warning": "Take with food to avoid stomach upset."
            })

    if any("cough" in s or "throat" in s for s in s_lower):
        if age > 6:
            medicines.append({
                "name": "Cough Lozenges or Plain Honey",
                "purpose": "Soothe a sore throat and reduce coughing.",
                "guidance": "Dissolve 1 lozenge slowly in the mouth every 2-3 hours as needed. Alternatively, 1 spoonful of honey.",
                "warning": "Do NOT give honey or lozenges to children under 1 year old due to choking and botulism risks."
            })

    if any("congestion" in s or "nose" in s for s in s_lower):
        medicines.append({
            "name": "Saline Nasal Drops",
            "purpose": "Moisturize nasal passages and wash away mucus.",
            "guidance": "2-3 drops in each nostril as needed.",
            "warning": "Use a dedicated sterile dropper per person to prevent cross-contamination."
        })

    if any("chills" in s or "shivering" in s for s in s_lower):
        medicines.append({
            "name": "Paracetamol (Acetaminophen)",
            "purpose": "Control high fever and chills.",
            "guidance": "500-1000mg as needed, max 4 doses/day.",
            "warning": "Fever with chills in rural areas may indicate Malaria or Typhoid. See a doctor."
        })

    if any("rash" in s or "yellowish" in s or "stiff neck" in s for s in s_lower):
        # These are high-risk symptoms where we don't want to encourage self-medication
        pass

    # Fallback: If no specific OTC was matched and the patient isn't in an emergency/high risk state,
    # provide a general mild medicine recommendation as requested by the user.
    if not medicines and risk_level in ["Low", "Moderate"]:
        medicines.append({
            "name": "General Mild Medicine (e.g., Paracetamol 500mg)",
            "purpose": "Relieve general body ache, mild fever, or discomfort.",
            "guidance": "Take 1 tablet only if experiencing discomfort or fever. Do not exceed 3 days without doctor consultation.",
            "warning": "Ensure you have no liver conditions or allergies. Always follow exact package dosage."
        })

    return medicines
