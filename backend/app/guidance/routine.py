from typing import List

def get_daily_routine(age: int, severity_score: float, symptoms: List[str] = None, disease: str = "") -> List[str]:
    routine = []
    if symptoms is None:
        symptoms = []
        
    s_lower = [s.lower().replace("_", " ") for s in symptoms]
    d_lower = disease.lower() if disease else ""
    
    # 1. Hydration (Dynamic)
    if any(k in d_lower or k in s_lower for k in ["diarrhea", "vomiting", "fever", "sweating", "heat", "malaria", "typhoid", "dengue"]):
        routine.append("Aggressive Hydration: Drink ORS (Oral Rehydration Solution) and at least 2.5-3 liters of clean water. Fluid loss is high.")
    elif "cough" in s_lower or "throat" in s_lower or "cold" in d_lower:
        routine.append("Hydration: Drink warm water, herbal teas, or warm broths to soothe the throat and loosen mucus.")
    else:
        routine.append("Hydration: Drink at least 2 liters of safe, clean water spread throughout the day.")
        
    # 2. Rest (Dynamic)
    if "pain" in s_lower or "injury" in s_lower or "fracture" in d_lower:
        if age < 12:
            routine.append("Rest: Keep the child comfortably resting. Restrict play that involves jumping or running.")
        else:
            routine.append("Rest: Immobilize the affected area. Avoid lifting weights or walking long distances.")
    elif "fatigue" in s_lower or "weakness" in s_lower or "anemia" in d_lower:
        routine.append("Rest: Extreme fatigue noted. Take frequent small naps during the day. Do not push through the tiredness.")
    else:
        if age < 12:
            routine.append("Rest: Ensure the child gets 10-12 hours of uninterrupted sleep, plus daytime naps.")
        elif age > 65:
            routine.append("Rest: Aim for 8-9 hours of sleep. Avoid strenuous physical activity.")
        else:
            routine.append("Rest: Aim for 8 hours of sleep. Reduce physical exertion.")

    # 3. Monitoring (Dynamic)
    if severity_score > 1.5 or "fever" in s_lower:
        routine.append("Monitoring: Check temperature and symptoms every 4-6 hours. Note if fever spikes above 101°F (38.3°C).")
    elif "rash" in s_lower or "skin" in d_lower or "allergy" in d_lower:
        routine.append("Monitoring: Check the skin rash daily. If it spreads rapidly, blisters, or forms pus, seek medical care.")
    else:
        routine.append("Monitoring: Check symptoms each morning and evening to ensure they are improving.")

    # 4. Nutrition (Dynamic)
    if "diarrhea" in s_lower or "vomiting" in s_lower or "stomach" in s_lower or "typhoid" in d_lower:
        routine.append("Nutrition: BRAT Diet (Bananas, Rice, Applesauce, Toast). Avoid spicy, oily, or dairy foods entirely until digestion settles.")
    elif "diabetes" in d_lower or "sugar" in d_lower:
        routine.append("Nutrition: Strictly limit sugar. Eat high-fiber foods and local green vegetables. Eat in small, frequent intervals.")
    else:
        routine.append("Nutrition: Eat light, easily digestible, and freshly cooked meals. Avoid street food.")

    # 5. Hygiene / Prevention (Dynamic)
    if "rash" in s_lower or "itch" in s_lower or "fungal" in d_lower:
        routine.append("Hygiene: Keep the affected skin dry. Do not scratch. Wear loose, breathable cotton clothing.")
    elif "cough" in s_lower or "sneezing" in s_lower or "tuberculosis" in d_lower or "pneumonia" in d_lower:
        routine.append("Hygiene: Cover your mouth when coughing/sneezing. Isolate from vulnerable family members (elders/infants) if possible.")
    else:
        routine.append("Hygiene: Wash hands frequently with soap and water to prevent spreading illness to family members.")

    return routine
