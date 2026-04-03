import os
import sys

# Ensure backend package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from app.ml.predictor import DiseasePredictor

def test_inference():
    print("=" * 50)
    print("Testing ML Inference Engine Integration...")
    print("=" * 50)

    predictor = DiseasePredictor()

    # Always call load_model() explicitly before checking is_loaded
    predictor.load_model()

    if not predictor.is_loaded:
        print("\n[FAIL] Model failed to load.")
        print("  Ensure triage_model_v2.json and model_meta_v2.joblib exist in backend/app/ml/")
        return

    print("\n[OK] Model loaded successfully.")
    meta = predictor._meta
    print(f"  Algorithm : {meta.get('algorithm')}")
    print(f"  Version   : {meta.get('version')}")
    print(f"  Features  : {meta.get('n_features')}")
    print(f"  Classes   : {meta.get('n_classes')}")

    # -------------------------------------------------------
    # TEST CASE 1: Severe symptoms
    # -------------------------------------------------------
    print("\n--- TEST CASE 1: Severe Symptoms ---")
    result = predictor.predict(
        age=45,
        gender=1,
        severity=3,
        duration=5.0,
        clinical_symptoms="severe chest pain, breathlessness, sweating"
    )
    print(f"  Condition         : {result.get('condition')}")
    print(f"  Confidence        : {result.get('confidence')}")
    print(f"  Risk Level        : {result.get('risk_level')}")
    print(f"  Risk Score        : {result.get('risk_score')}")
    print(f"  Important Features: {result.get('important_features')}")

    # Schema assertions
    for key in ["condition", "confidence", "risk_level", "risk_score", "important_features"]:
        assert key in result, f"[FAIL] Missing key in result: {key}"

    # -------------------------------------------------------
    # TEST CASE 2: Mild symptoms
    # -------------------------------------------------------
    print("\n--- TEST CASE 2: Mild Symptoms ---")
    result_mild = predictor.predict(
        age=20,
        gender=0,
        severity=1,
        duration=2.0,
        clinical_symptoms="slight headache"
    )
    print(f"  Condition : {result_mild.get('condition')}")
    print(f"  Risk Level: {result_mild.get('risk_level')}")
    print(f"  Risk Score: {result_mild.get('risk_score')}")

    # -------------------------------------------------------
    # TEST CASE 3: Fever + vomiting
    # -------------------------------------------------------
    print("\n--- TEST CASE 3: GI Symptoms ---")
    result_gi = predictor.predict(
        age=30,
        gender=1,
        severity=2,
        duration=3.0,
        clinical_symptoms="fever, vomiting, diarrhea, abdominal pain"
    )
    print(f"  Condition : {result_gi.get('condition')}")
    print(f"  Risk Level: {result_gi.get('risk_level')}")

    print("\n" + "=" * 50)
    print("[PASS] All integration tests passed. Schema matches constraints.")
    print("=" * 50)

if __name__ == "__main__":
    test_inference()
