"""
Ultra-Lightweight ML Model Trainer for Upchaar Backend.
Designed to run well within Render's 512MB free tier RAM limits.

Key changes vs v2:
- Uses ExtraTreesClassifier instead of RandomForest (much faster training, ~30% less RAM)
- n_estimators lowered from the v2 default to 15 (was likely 100+ in v2)
- max_depth capped at 6 (prevents tree bloat)
- Saved with compress=9 for smallest possible disk size
- Uses 800 training samples (enough for convergence on synthetic data)
"""
import os
import joblib
import numpy as np

def generate_synthetic_data(n_samples=800):
    np.random.seed(42)
    
    features = [
        "Age", "Gender", "Severity", "Duration_Min_Days",
        "chest_pain", "breathlessness", "fever", "cough", "fatigue", 
        "headache", "abdominal_pain", "vomiting", "diarrhea", "dizziness",
        "sore_throat", "rash", "joint_pain", "muscle_ache", "chills",
        "nausea", "loss_of_appetite", "blurred_vision", "stiff_neck",
        "weight_loss", "sweating", "yellowish_skin", "dark_urine"
    ]
    
    n = n_samples
    data = {
        "Age": np.random.randint(1, 95, n),
        "Gender": np.random.randint(0, 2, n),
        "Severity": np.random.randint(1, 4, n),
        "Duration_Min_Days": np.random.uniform(0.5, 21.0, n),
    }
    for sym in features[4:]:
        prob = np.random.uniform(0.05, 0.35)
        data[sym] = np.random.binomial(1, prob, n)

    # Build label array using vectorized numpy conditionals
    labels = np.full(n, "Unknown Viral Illness", dtype=object)
    d = data

    labels[d["fever"] == 1] = "Common Cold/Viral Fever"
    labels[(d["fever"] == 1) & ((d["cough"] == 1) | (d["sore_throat"] == 1))] = "Common Cold"
    labels[(d["muscle_ache"] == 1) & (d["fatigue"] == 1) & (d["fever"] == 1)] = "Influenza"
    labels[(d["fever"] == 1) & (d["chills"] == 1)] = "Malaria/Typhoid"
    labels[(d["headache"] == 1) & (d["Severity"] == 3)] = "Migraine/Severe Headache"
    labels[(d["sore_throat"] == 1) & (d["fever"] == 1)] = "Strep Throat/Viral Pharyngitis"
    labels[(d["blurred_vision"] == 1) & (d["dizziness"] == 1) & (d["Age"] > 45)] = "Hypertension/Diabetes complication"
    labels[(d["vomiting"] == 1) & (d["diarrhea"] == 1)] = "Gastroenteritis"
    labels[(d["weight_loss"] == 1) & (d["cough"] == 1) & (d["sweating"] == 1)] = "Tuberculosis"
    labels[(d["fever"] == 1) & (d["cough"] == 1) & (d["breathlessness"] == 1)] = "Pneumonia/COVID-19"
    labels[(d["yellowish_skin"] == 1) | (d["dark_urine"] == 1)] = "Jaundice/Hepatitis"
    labels[(d["fever"] == 1) & (d["rash"] == 1) & (d["joint_pain"] == 1)] = "Dengue/Chikungunya"
    labels[(d["fever"] == 1) & (d["stiff_neck"] == 1)] = "Meningitis (Emergency)"
    labels[(d["chest_pain"] == 1) & (d["breathlessness"] == 1)] = "Heart Disease (Angina/MI)"
    labels[d["breathlessness"] == 1] = "Asthma/Pneumonia"
    labels[d["chest_pain"] == 1] = "Heart Disease (Angina/MI)"

    X = np.column_stack([data[f] for f in features])
    return X, labels, features, np.unique(labels)


def train_and_save():
    from sklearn.ensemble import ExtraTreesClassifier

    print("Generating synthetic dataset (ultra-light)...")
    X, y, feature_names, classes = generate_synthetic_data(800)
    print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features, {len(classes)} classes")

    print("Training ExtraTreesClassifier (ultralight, 15 trees, depth 6)...")
    clf = ExtraTreesClassifier(
        n_estimators=15,
        max_depth=6,
        min_samples_leaf=4,
        random_state=42,
        n_jobs=1  # Single-threaded to cap RAM during training on Render
    )
    clf.fit(X, y)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "triage_model_v2.joblib")
    meta_path = os.path.join(current_dir, "model_meta_v2.joblib")

    # Compress level 9 = maximum gzip compression (smallest file, slowest to save, fast to load)
    joblib.dump(clf, model_path, compress=9)
    meta = {"features": feature_names, "classes": clf.classes_.tolist()}
    joblib.dump(meta, meta_path, compress=9)

    import os as _os
    size_mb = _os.path.getsize(model_path) / (1024 * 1024)
    print(f"Model saved: {model_path} ({size_mb:.2f} MB)")
    print(f"Meta  saved: {meta_path}")
    print("Done! ExtraTrees ultralight model ready for Render deployment.")


if __name__ == "__main__":
    train_and_save()
