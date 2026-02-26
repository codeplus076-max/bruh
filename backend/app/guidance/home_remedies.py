from typing import List

def get_home_remedies(symptoms: List[str]) -> List[str]:
    remedies = set()
    s_lower = [s.lower().replace("_", " ") for s in symptoms]

    if any("cough" in s or "throat" in s for s in s_lower):
        remedies.add("Gargle with warm salt water 3 times a day to soothe the throat.")
        remedies.add("Drink warm fluids with honey and lemon (for patients over 1 year old).")
    if any("congestion" in s or "nose" in s for s in s_lower):
        remedies.add("Do steam inhalation with plain water to clear nasal passages. Take care with boiling water.")
    if any("stomach" in s or "abdominal" in s for s in s_lower):
        remedies.add("Consume bland foods (like rice, bananas, or toast). Avoid spicy, greasy, or dairy-heavy foods.")
    if any("headache" in s for s in s_lower):
        remedies.add("Rest in a quiet, dimly lit room. Apply a cool compress to the forehead.")
    if any("joint" in s or "muscle" in s for s in s_lower):
        remedies.add("Apply warm or cold compresses to aching muscles or joints for 15 minutes at a time.")

    # Generic
    remedies.add("Get plenty of rest to allow the body's immune system to focus on recovery.")
    return list(remedies)
