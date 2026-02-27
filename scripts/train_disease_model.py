import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

import warnings
warnings.filterwarnings('ignore')

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'new_training_dataset.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run prepare_dataset.py first.")
        return
        
    print(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)
    
    # Sample down to 25,000 for speed if it's larger
    if len(df) > 25000:
        print("Sampling dataset to 25,000 instances to optimize training time...")
        df = df.sample(n=25000, random_state=42)
    
    print("Filtering rare classes (< 5 samples) to allow proper stratification...")
    class_counts = df['diseases'].value_counts()
    valid_classes = class_counts[class_counts >= 5].index
    df = df[df['diseases'].isin(valid_classes)]
    
    print("Preparing features and target...")
    y_raw = df['diseases']
    X = df.drop(columns=['diseases'])
    
    feature_names = list(X.columns)
    
    print("Encoding target labels...")
    le = LabelEncoder()
    y = le.fit_transform(y_raw)
    class_names = list(le.classes_)
    
    print(f"Total samples: {len(X)}, Features: {len(feature_names)}, Classes: {len(class_names)}")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("\n--- Training XGBoost (Primary Objective) ---")
    model = XGBClassifier(n_estimators=100, max_depth=6, random_state=42, eval_metric='mlogloss', n_jobs=-1)
    
    best_name = "XGBoost"
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    prec = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_test, y_pred, average='weighted', zero_division=0)
    
    print(f"Accuracy: {acc:.4f} | F1 Score: {f1:.4f} | Precision: {prec:.4f} | Recall: {rec:.4f}")
    
    best_model = model
    best_f1 = f1
            
    print(f"\nBest Model selected: {best_name} with F1: {best_f1:.4f}")
    
    print("\nEvaluating Best Model in detail:")
    y_pred_best = best_model.predict(X_test)
    cr = classification_report(y_test, y_pred_best, target_names=class_names, output_dict=True)
    print(f"Macro avg F1: {cr['macro avg']['f1-score']:.4f}")
    
    # Save Model and Metadata
    model_dir = os.path.join(base_dir, 'backend', 'app', 'ml')
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'triage_model_v2.joblib')
    meta_path = os.path.join(model_dir, 'model_meta_v2.joblib')
    
    print(f"\nSaving final model to {model_path}...")
    joblib.dump(best_model, model_path, compress=3)
    
    meta = {
        "features": feature_names,
        "classes": class_names,
        "version": "2.0",
        "algorithm": best_name
    }
    joblib.dump(meta, meta_path)
    print(f"Saved metadata to {meta_path}")
    
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
        indices = np.argsort(importances)[::-1]
        print("\nTop 10 Important Features:")
        for i in range(min(10, len(indices))):
            print(f"{i+1}. {feature_names[indices[i]]} ({importances[indices[i]]:.4f})")

if __name__ == "__main__":
    main()
