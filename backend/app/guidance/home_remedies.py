from typing import List

def get_home_remedies(symptoms: List[str]) -> List[str]:
    remedies = set()
    s_lower = [s.lower().replace("_", " ") for s in symptoms]

    if any("cough" in s or "throat" in s for s in s_lower):
        remedies.add("Gargle with warm salt water 3 times a day to soothe the throat.")
        remedies.add("Drink warm fluids with honey and lemon (for patients over 1 year old).")
    if any("congestion" in s or "nose" in s for s in s_lower):
        remedies.add("Do steam inhalation with plain water to clear nasal passages. Take care with boiling water.")
    if any("stomach" in s or "abdominal" in s or "vomiting" in s or "diarrhea" in s or "nausea" in s for s in s_lower):
        remedies.add("Consume bland foods (like rice, bananas, or toast). Avoid spicy, greasy, or dairy-heavy foods.")
        remedies.add("Take small, frequent sips of ORS (Oral Rehydration Solution) or clean water to prevent dehydration.")
    if any("diarrhea" in s or "loose motion" in s for s in s_lower):
        remedies.add("Eat yogurt or probiotic-rich foods if tolerated. Avoid caffeine and sweetened drinks.")
    if any("headache" in s for s in s_lower):
        remedies.add("Rest in a quiet, dimly lit room. Apply a cool compress to the forehead.")
    if any("joint" in s or "muscle" in s or "injury" in s or "sprain" in s or "strain" in s for s in s_lower):
        remedies.add("Use the RICE method: Rest, Ice (15 mins), Compression (clean wrap), and Elevation (above heart level).")
        remedies.add("Apply warm or cold compresses to aching muscles or joints for 15 minutes at a time.")
    if any("rash" in s or "skin" in s for s in s_lower):
        remedies.add("Keep the affected area clean and dry. Avoid scratching to prevent infection.")
        remedies.add("Use cool water compresses to soothe itchy or inflamed skin.")
    if any("yellowish" in s or "jaundice" in s or "hepatitis" in s for s in s_lower):
        remedies.add("Strictly avoid all oily, spicy, and heavy foods. Stick to simple boiled foods like porridge or khichdi.")
        remedies.add("Complete physical rest is essential for liver recovery.")

    # Generic
    remedies.add("Get plenty of rest to allow the body's immune system to focus on recovery.")
    return list(remedies)
