import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def generate_synthetic_data(n_samples=500):
    np.random.seed(42)
    
    # Expanded feature columns for better diagnostic granularity
    features = [
        "Age", "Gender", "Severity", "Duration_Min_Days",
        "chest_pain", "breathlessness", "fever", "cough", "fatigue", 
        "headache", "abdominal_pain", "vomiting", "diarrhea", "dizziness",
        "sore_throat", "rash", "joint_pain", "muscle_ache", "chills",
        "nausea", "loss_of_appetite", "blurred_vision", "stiff_neck",
        "weight_loss", "sweating", "yellowish_skin", "dark_urine"
    ]
    
    df = pd.DataFrame(columns=features)
    
    # Generate random demographics and core clinical inputs
    df["Age"] = np.random.randint(1, 95, n_samples)
    df["Gender"] = np.random.randint(0, 2, n_samples)
    df["Severity"] = np.random.randint(1, 4, n_samples) 
    df["Duration_Min_Days"] = np.random.uniform(0.5, 21.0, n_samples)
    
    # Generate random binary symptoms with varying probabilities
    symptom_cols = features[4:]
    for symp in symptom_cols:
        prob = np.random.uniform(0.05, 0.35)
        df[symp] = np.random.binomial(1, prob, n_samples)
        
    labels = []
    for idx, row in df.iterrows():
        # Priority Heuristics - Highly Specific
        if row["chest_pain"] == 1 and row["breathlessness"] == 1:
            labels.append("Heart Disease (Angina/MI)")
        elif row["fever"] == 1 and row["stiff_neck"] == 1:
            labels.append("Meningitis (Emergency)")
        elif row["fever"] == 1 and row["rash"] == 1 and row["joint_pain"] == 1:
            labels.append("Dengue/Chikungunya")
        elif row["yellowish_skin"] == 1 or row["dark_urine"] == 1:
            labels.append("Jaundice/Hepatitis")
        elif row["fever"] == 1 and row["cough"] == 1 and row["breathlessness"] == 1:
            labels.append("Pneumonia/COVID-19")
        elif row["weight_loss"] == 1 and row["cough"] == 1 and row["sweating"] == 1:
            labels.append("Tuberculosis")
        elif row["vomiting"] == 1 and row["diarrhea"] == 1:
            labels.append("Gastroenteritis")
        elif row["blurred_vision"] == 1 and row["dizziness"] == 1 and row["Age"] > 45:
            labels.append("Hypertension/Diabetes complication")
        elif row["sore_throat"] == 1 and row["fever"] == 1:
            labels.append("Strep Throat/Viral Pharyngitis")
        elif row["headache"] == 1 and row["Severity"] == 3:
            labels.append("Migraine/Severe Headache")
        elif row["fever"] == 1 and row["chills"] == 1:
            labels.append("Malaria/Typhoid")
        elif row["muscle_ache"] == 1 and row["fatigue"] == 1 and row["fever"] == 1:
            labels.append("Influenza")
        elif row["fever"] == 1 and (row["cough"] == 1 or row["sore_throat"] == 1):
             labels.append("Common Cold")
        elif row["chest_pain"] == 1:
            labels.append("Heart Disease (Angina/MI)") # Sensitivity for single symptom
        elif row["breathlessness"] == 1:
            labels.append("Asthma/Pneumonia") # Sensitivity for single symptom
        elif row["fever"] == 1:
            labels.append("Common Cold/Viral Fever")
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
