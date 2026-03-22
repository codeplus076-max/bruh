import os
import sys
from dotenv import load_dotenv

# Add the project root to the python path to allow importing backend module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv('backend/.env')

from backend.app.ml.predictor import DiseasePredictor

def test_inference():
    print("Testing ML Inference Engine Integration...")
    
    predictor = DiseasePredictor()
    predictor.load_model()
    
    if not predictor.is_loaded:
        print("Model (Gemini API) failed to load. Ensure GEMINI_API_KEY is set.")
        return
        
    print("Model loaded successfully.")
    
    # 1. Test basic output schema and formatting
    result = predictor.predict(
        age=45,
        gender=1,
        severity=3,
        duration=5.0,
        clinical_symptoms="severe chest pain, breathlessness, sweating"
    )
    
    print("\n--- TEST CASE: Severe Symptoms ---")
    print(f"Condition: {result.get('condition')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Risk Level: {result.get('risk_level')}")
    print(f"Risk Score: {result.get('risk_score')}")
    print(f"Important Features: {result.get('important_features')}")
    
    # Verify strict schema contract
    assert "condition" in result
    assert "confidence" in result
    assert "risk_level" in result
    assert "risk_score" in result
    assert "important_features" in result
    
    # 2. Test mock fall back
    print("\n--- TEST CASE: Mild Symptoms ---")
    result_mild = predictor.predict(
        age=20,
        gender=0,
        severity=1,
        duration=2.0,
        clinical_symptoms="slight headache"
    )
    
    print(f"Condition: {result_mild.get('condition')}")
    print(f"Risk Level: {result_mild.get('risk_level')}")
    
    print("\nAll integration tests passed. Schema matches constraints.")

if __name__ == "__main__":
    test_inference()
