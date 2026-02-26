import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def generate_synthetic_data(n_samples=500):
    np.random.seed(42)
    
    # Feature columns expected by frontend/backend
    # We add common symptom flags (0 or 1) so the model has something to chew on if provided
    features = [
        "Age", "Gender", "Severity", "Duration_Min_Days",
        "chest_pain", "breathlessness", "fever", "cough", "fatigue", 
        "headache", "abdominal_pain", "vomiting", "diarrhea", "dizziness"
    ]
    
    df = pd.DataFrame(columns=features)
    
    # Generate random demographics and core clinical inputs
    df["Age"] = np.random.randint(5, 90, n_samples)
    df["Gender"] = np.random.randint(0, 2, n_samples)
    df["Severity"] = np.random.randint(1, 4, n_samples)  # 1 to 3
    df["Duration_Min_Days"] = np.random.uniform(1.0, 14.0, n_samples)
    
    # Generate random binary symptoms
    for symp in [
        "chest_pain", "breathlessness", "fever", "cough", "fatigue", 
        "headache", "abdominal_pain", "vomiting", "diarrhea", "dizziness"
    ]:
        # Typically symptoms are somewhat correlated with severity, but we'll leave it random for this synthetic mock
        prob = np.random.uniform(0.1, 0.4)
        df[symp] = np.random.binomial(1, prob, n_samples)
        
    # Generate labels (Diseases) based on loose heuristics to ensure the model learns *something*
    labels = []
    diseases = [
        "Common Cold", "Influenza", "COVID-19", "Gastroenteritis", "Migraine", 
        "Hypertension", "Asthma", "Heart Disease (Angina)", "Food Poisoning", "Unknown Viral Illness"
    ]
    
    for idx, row in df.iterrows():
        # Heuristics
        if row["chest_pain"] == 1 and row["breathlessness"] == 1:
            labels.append("Heart Disease (Angina)")
        elif row["fever"] == 1 and row["cough"] == 1 and row["breathlessness"] == 1:
            labels.append("COVID-19")
        elif row["vomiting"] == 1 and row["diarrhea"] == 1:
            if row["fever"] == 1:
                labels.append("Gastroenteritis")
            else:
                labels.append("Food Poisoning")
        elif row["headache"] == 1 and row["Severity"] == 3:
            labels.append("Migraine")
        elif row["Age"] > 50 and row["Severity"] >= 2 and row["dizziness"] == 1:
            labels.append("Hypertension")
        elif row["cough"] == 1 and row["breathlessness"] == 1:
            labels.append("Asthma")
        elif row["fever"] == 1 and row["cough"] == 1:
            labels.append("Influenza")
        elif row["fever"] == 1 or row["cough"] == 1 or row["fatigue"] == 1:
             labels.append("Common Cold")
        else:
             labels.append("Unknown Viral Illness")

    return df, np.array(labels), features, np.unique(labels)


def train_and_save():
    print("Generating synthetic dataset...")
    X, y, feature_names, classes = generate_synthetic_data(1000)
    
    print(f"Features ({len(feature_names)}):", feature_names)
    print(f"Classes ({len(classes)}):", classes)
    
    print("Training Random Forest Classifier...")
    # Very lightweight model
    rf = RandomForestClassifier(n_estimators=20, max_depth=5, random_state=42)
    rf.fit(X, y)
    
    # Determine save path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "triage_model.joblib")
    meta_path = os.path.join(current_dir, "model_meta.joblib")
    
    # Save model
    joblib.dump(rf, model_path, compress=3)
    
    # Save meta (we save the exact feature list and the classes directly to match the predictor)
    meta = {
        "features": feature_names,
        "classes": rf.classes_.tolist()
    }
    joblib.dump(meta, meta_path)
    
    print(f"Successfully saved to:\n  - {model_path}\n  - {meta_path}")

if __name__ == "__main__":
    train_and_save()
