"""
Upchaar AI — Hybrid NLP Model Trainer
======================================
Trains a TF-IDF + Calibrated Logistic Regression classifier on Symptom2Disease.csv
Output: backend/app/ml/pipeline/{nlp_model.joblib, tfidf_vectorizer.joblib, nlp_classes.json}

Run ONCE from the project root:
  python scripts/train_hybrid_nlp_model.py
"""

import os
import sys
import json
import csv

print("=" * 60)
print("Upchaar NLP Model Trainer — TF-IDF + Logistic Regression")
print("=" * 60)

# ── Dependency check ──────────────────────────────────────────
try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, accuracy_score
    import joblib
except ImportError as e:
    print(f"\nERROR: Missing dependency — {e}")
    print("Install with:  pip install scikit-learn joblib numpy")
    sys.exit(1)

# ── Paths ─────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)

DATA_CSV = os.path.join(ROOT_DIR, "archive (3)", "Symptom2Disease.csv")
OUT_DIR = os.path.join(ROOT_DIR, "backend", "app", "ml", "pipeline")
os.makedirs(OUT_DIR, exist_ok=True)

MODEL_PATH = os.path.join(OUT_DIR, "nlp_model.joblib")
VECTORIZER_PATH = os.path.join(OUT_DIR, "tfidf_vectorizer.joblib")
CLASSES_PATH = os.path.join(OUT_DIR, "nlp_classes.json")

if not os.path.exists(DATA_CSV):
    print(f"\nERROR: Dataset not found at: {DATA_CSV}")
    print("Make sure 'archive (3)/Symptom2Disease.csv' exists in the project root.")
    sys.exit(1)

# ── Load Dataset ──────────────────────────────────────────────
print(f"\n[1/5] Loading dataset from: {DATA_CSV}")
texts = []
labels = []

with open(DATA_CSV, encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    for row in reader:
        text = (row.get("text") or "").strip()
        label = (row.get("label") or "").strip()
        if text and label:
            texts.append(text)
            labels.append(label)

print(f"      Loaded {len(texts)} samples, {len(set(labels))} unique diseases")
if len(texts) == 0:
    print("ERROR: No training samples found. Check CSV column names (expected: 'label', 'text')")
    sys.exit(1)

# ── TF-IDF Vectorization ──────────────────────────────────────
print("\n[2/5] Fitting TF-IDF vectorizer...")
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=8000,
    sublinear_tf=True,
    min_df=2,
    strip_accents="unicode",
    analyzer="word",
    token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b"
)
X = vectorizer.fit_transform(texts)
print(f"      Feature matrix: {X.shape[0]} samples × {X.shape[1]} features")

# ── Train / Test Split ────────────────────────────────────────
print("\n[3/5] Splitting train/test (80/20)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, labels, test_size=0.2, random_state=42, stratify=labels
)
print(f"      Train: {X_train.shape[0]}  |  Test: {X_test.shape[0]}")

# ── Train Calibrated Logistic Regression ──────────────────────
print("\n[4/5] Training Calibrated Logistic Regression (C=1.0, max_iter=1000)...")
base_lr = LogisticRegression(
    max_iter=1000,
    C=1.0,
    solver="lbfgs",
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
model = CalibratedClassifierCV(base_lr, cv=3, method="isotonic")
model.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────
print("\n[5/5] Evaluating model...")
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"      Test Accuracy: {acc:.4f} ({acc*100:.1f}%)")

classes = list(model.classes_)
print(f"\n      Diseases covered ({len(classes)}):")
for c in sorted(classes):
    print(f"        · {c}")

# ── Save Artifacts ────────────────────────────────────────────
print(f"\nSaving model → {MODEL_PATH}")
joblib.dump(model, MODEL_PATH, compress=3)

print(f"Saving vectorizer → {VECTORIZER_PATH}")
joblib.dump(vectorizer, VECTORIZER_PATH, compress=3)

print(f"Saving class list → {CLASSES_PATH}")
with open(CLASSES_PATH, "w") as f:
    json.dump({"classes": classes, "n_features": X.shape[1], "accuracy": round(acc, 4)}, f, indent=2)

print("\n" + "=" * 60)
print(f"✅ Training complete! Accuracy: {acc*100:.1f}%")
print(f"   Model saved to: {OUT_DIR}/")
print("=" * 60)
