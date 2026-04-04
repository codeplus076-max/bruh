import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

def main():
    print("--- Stage 2: Reasoning & Verification Evaluator ---")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'reasoning_dataset.csv')
    
    if not os.path.exists(data_path):
        print(f"ERROR: Dataset not found at {data_path}")
        return

    print("Loading Stage 2 Data...")
    df = pd.read_csv(data_path)
    
    # We use this model to verify the disease, so target is prognosis.
    # We will also extract a medicine mapping from this dataset.
    y_raw = df['prognosis']
    
    # Save disease -> medicine mapping
    if 'medicine' in df.columns:
        disease_to_med = df.groupby('prognosis')['medicine'].agg(lambda x: pd.Series.mode(x)[0] if not x.empty else 'General care').to_dict()
    else:
        disease_to_med = {}
        
    cols_to_drop = ['prognosis', 'medicine'] if 'medicine' in df.columns else ['prognosis']
    X = df.drop(columns=cols_to_drop, errors='ignore')
    feature_names = list(X.columns)

    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    class_names = list(le.classes_)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training Random Forest on {len(feature_names)} features...")
    # Random Forest is better for extracting probabilities for overlapping symptoms
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(f"Stage 2 Accuracy: {accuracy_score(y_test, y_pred):.4f}")

    # Save
    model_dir = os.path.join(base_dir, 'backend', 'app', 'ml', 'pipeline')
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'stage2_reasoning_rf.joblib')
    joblib.dump(model, model_path)
    
    meta_path = os.path.join(model_dir, 'stage2_meta.joblib')
    joblib.dump({
        "features": feature_names,
        "classes": class_names,
        "medicine_mapping": disease_to_med,
        "version": "3.0"
    }, meta_path)

    print(f"Stage 2 Complete. Saved to {model_path}")

if __name__ == "__main__":
    main()
