import pandas as pd
import numpy as np
import joblib
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text.strip()

def filter_disease(label):
    # Minor safety: standardize labels to title case
    return label.strip().title()

def train_model():
    print("Loading Symptom2Disease dataset...")
    data_path = os.path.join("..", "archive (3)", "Symptom2Disease.csv")
    if not os.path.exists(data_path):
        data_path = os.path.join("archive (3)", "Symptom2Disease.csv")
    
    df = pd.read_csv(data_path)
    
    # Preprocess
    df['text'] = df['text'].apply(clean_text)
    df['label'] = df['label'].apply(filter_disease)
    
    X = df['text']
    y = df['label']
    
    print("Training TF-IDF + Calibrated Logistic Regression...")
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=5000, stop_words='english')),
        ('clf', CalibratedClassifierCV(LogisticRegression(max_iter=1000, class_weight='balanced', C=1.0)))
    ])
    
    pipeline.fit(X, y)
    
    # Save the model
    os.makedirs(os.path.join("..", "backend", "app", "ml", "models"), exist_ok=True)
    os.makedirs(os.path.join("backend", "app", "ml", "models"), exist_ok=True)
    
    model_path = os.path.join("backend", "app", "ml", "models", "nlp_pipeline.joblib")
    if not os.path.exists("backend"):
        model_path = os.path.join("..", "backend", "app", "ml", "models", "nlp_pipeline.joblib")
        
    joblib.dump(pipeline, model_path)
    print(f"✅ NLP Pipeline saved to {model_path}!")
    
    # Test it out
    sample = "I have a sore throat, mild fever, and I have been coughing slowly."
    pred = pipeline.predict_proba([clean_text(sample)])[0]
    classes = pipeline.classes_
    top_indices = np.argsort(pred)[::-1][:3]
    
    print("\n[Test Prediction for: 'Sore throat and fever']")
    for i in top_indices:
        print(f" - {classes[i]}: {pred[i]*100:.1f}%")

if __name__ == "__main__":
    train_model()
