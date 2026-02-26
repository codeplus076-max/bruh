from typing import List

def get_safety_warnings(symptoms: List[str], disease: str) -> List[str]:
    warnings = set()
    warnings.add("Do NOT self-medicate with antibiotics. They only treat bacterial infections and can be harmful if misused.")
    
    s_lower = [s.lower().replace("_", " ") for s in symptoms]
    disease_lower = disease.lower()

    if disease_lower == "dengue" or any("fever" in s and ("joint" in s or "muscle" in s or "eye" in s) for s in s_lower):
        warnings.add("Do NOT take Ibuprofen, Aspirin, or NSAIDs. These can cause life-threatening bleeding if you have Dengue fever.")
    
    if any("stomach" in s or "abdominal" in s for s in s_lower):
        warnings.add("Do NOT take strong painkillers or laxatives without consulting a doctor, as they can worsen certain abdominal emergencies.")

    if any("cough" in s for s in s_lower):
        warnings.add("Do NOT use over-the-counter cough suppressants for children under 6 years old without a doctor's order.")

    return list(warnings)
