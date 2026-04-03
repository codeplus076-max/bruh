import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, classification_report
)
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')

def main():
    base_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'new_training_dataset.csv')

    if not os.path.exists(data_path):
        print(f"ERROR: {data_path} not found. Run prepare_dataset.py first.")
        return

    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"  Loaded shape: {df.shape}")

    # Filter rare classes (< 5 samples) to allow proper stratification
    print("Filtering rare classes (< 5 samples)...")
    class_counts  = df['diseases'].value_counts()
    valid_classes = class_counts[class_counts >= 5].index
    df = df[df['diseases'].isin(valid_classes)]
    print(f"  Remaining samples: {len(df)} | Classes: {df['diseases'].nunique()}")

    # Prepare features and target
    y_raw         = df['diseases']
    X             = df.drop(columns=['diseases'])
    feature_names = list(X.columns)

    # Encode target labels
    le         = LabelEncoder()
    y          = le.fit_transform(y_raw)
    class_names= list(le.classes_)

    print(f"Features: {len(feature_names)} | Classes: {len(class_names)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # -------------------------------------------------------
    # Train XGBoost
    # -------------------------------------------------------
    print("\n--- Training XGBoost ---")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        eval_metric='mlogloss',
        n_jobs=-1,
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    acc  = accuracy_score(y_test,  y_pred)
    f1   = f1_score(y_test,        y_pred, average='weighted')
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec  = recall_score(y_test,    y_pred, average='weighted', zero_division=0)

    print(f"\nAccuracy : {acc:.4f}")
    print(f"F1 Score : {f1:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")

    cr = classification_report(y_test, y_pred, target_names=class_names, output_dict=True)
    print(f"Macro avg F1: {cr['macro avg']['f1-score']:.4f}")

    # -------------------------------------------------------
    # Save model outputs
    # -------------------------------------------------------
    model_dir = os.path.join(base_dir, 'backend', 'app', 'ml')
    os.makedirs(model_dir, exist_ok=True)

    # 1. Native XGBoost JSON — required by the lean predictor
    json_path = os.path.join(model_dir, 'triage_model_v2.json')
    print(f"\nSaving native XGBoost JSON → {json_path}")
    model.get_booster().save_model(json_path)

    # 2. Metadata joblib — features, classes, version
    meta_path = os.path.join(model_dir, 'model_meta_v2.joblib')
    meta = {
        "features"  : feature_names,
        "classes"   : class_names,
        "version"   : "2.0",
        "algorithm" : "XGBoost",
        "n_classes" : len(class_names),
        "n_features": len(feature_names),
    }
    joblib.dump(meta, meta_path)
    print(f"Saved metadata → {meta_path}")

    # Top-10 Feature Importances
    importances = model.feature_importances_
    indices     = np.argsort(importances)[::-1]
    print("\nTop 10 Important Features:")
    for i in range(min(10, len(indices))):
        print(f"  {i+1:2d}. {feature_names[indices[i]]:35s} ({importances[indices[i]]:.4f})")

    print("\n✓ Training complete. Model files ready for the backend.")

if __name__ == "__main__":
    main()
