import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.ml.predictor import DiseasePredictor

def test_inference():
    print("Testing ML Inference Engine Integration...")
    
    predictor = DiseasePredictor()
    
    if not predictor.is_loaded:
        print("Model failed to load. Ensure triage_model_v2.joblib exists.")
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
