import os
import pandas as pd
import numpy as np
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

def main():
    print("--- Stage 1: Primary Disease Predictor ---")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'disease_prediction_dataset.csv')
    
    if not os.path.exists(data_path):
        print(f"ERROR: Dataset not found at {data_path}")
        return

    print("Loading data...")
    df = pd.read_csv(data_path)
    
    # Drop unnamed columns if any
    cols_to_drop = [c for c in df.columns if 'unnamed' in c.lower()]
    df.drop(columns=cols_to_drop, inplace=True, errors='ignore')
    
    y_raw = df['prognosis']
    X = df.drop(columns=['prognosis'])
    feature_names = list(X.columns)

    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    class_names = list(le.classes_)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"Training XGBoost Model on {len(feature_names)} features and {len(class_names)} classes...")
    model = XGBClassifier(
        n_estimators=150,
        max_depth=6,
        learning_rate=0.1,
        eval_metric='mlogloss',
        n_jobs=-1,
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")

    # Save
    model_dir = os.path.join(base_dir, 'backend', 'app', 'ml', 'pipeline')
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'stage1_disease_xgboost.json')
    model.get_booster().save_model(model_path)
    
    meta_path = os.path.join(model_dir, 'stage1_meta.joblib')
    joblib.dump({
        "features": feature_names,
        "classes": class_names,
        "version": "3.0"
    }, meta_path)

    print(f"Stage 1 Complete. Saved to {model_path}")

if __name__ == "__main__":
    main()
