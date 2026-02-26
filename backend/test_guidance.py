from app.guidance.guidance_engine import generate_guidance
import json

print("\n--- TEST: MILD CASE (Fever) ---")
mild_guidance = generate_guidance(
    symptoms=["fever", "headache", "cough"],
    disease="Viral Fever",
    age=35,
    severity_score=1.2,
    risk_level="Low",
    urgency="Routine Care"
)
print(json.dumps(mild_guidance, indent=2))

print("\n--- TEST: EMERGENCY CASE (Dengue/Internal Bleeding) ---")
emergency_guidance = generate_guidance(
    symptoms=["fever", "severe abdominal pain", "vomiting blood"],
    disease="Dengue",
    age=10,
    severity_score=5.0,
    risk_level="Emergency",
    urgency="Immediate Hospitalization"
)
print(json.dumps(emergency_guidance, indent=2))
