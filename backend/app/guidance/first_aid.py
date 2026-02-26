from typing import List

def get_first_aid(symptoms: List[str], disease: str) -> List[str]:
    advice = set()
    s_lower = [s.lower().replace("_", " ") for s in symptoms]
    disease_lower = disease.lower()

    if any("bleeding" in s or "wound" in s for s in s_lower):
        advice.add("Apply firm pressure to any bleeding wounds with a clean cloth.")
    if any("burn" in s for s in s_lower):
        advice.add("Cool the burn under cool running water for 10-20 minutes. Do NOT apply ice or butter.")
    if any("fever" in s or "chills" in s for s in s_lower):
        advice.add("Apply a cool, damp cloth to the forehead to help reduce body temperature. Remove heavy extra layers of clothing.")
    if any("vomiting" in s or "diarrhea" in s for s in s_lower):
        advice.add("Begin oral rehydration immediately (ORS or clean water with a pinch of salt and sugar/honey) in small, frequent sips.")
    if any("chest pain" in s for s in s_lower):
        advice.add("Have the patient sit down, rest, and try to keep calm while awaiting emergency transport.")
    if any("breath" in s for s in s_lower):
        advice.add("Help the patient sit upright to make breathing easier. Loosen any tight clothing.")

    if disease_lower == "dengue":
        advice.add("Ensure strict hydration. Do not give Aspirin or Ibuprofen.")
    elif disease_lower == "malaria":
        advice.add("Keep the patient cool if feverish, and warm if shivering. Ensure hydration.")

    return list(advice)
