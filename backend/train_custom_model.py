import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib
import os

print("Starting model training process...")

# Load the dataset
dataset_path = r"c:\Users\krishna\OneDrive\Desktop\bak\bruh\Age,Gender,Severity,Duration_Min_Days,Du.csv"
print(f"Loading dataset from: {dataset_path}")
df = pd.read_csv(dataset_path)

# Print basic info
print(f"Dataset loaded. Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

# The target column is 'Disease'
if 'Disease' not in df.columns:
    raise ValueError("The dataset must contain a 'Disease' column.")

# Separate features(X) and target(y)
X_raw = df.drop('Disease', axis=1)
y_raw = df['Disease']

print("\nEncoding categorical variables...")
# Encode the target labels
le_target = LabelEncoder()
y = le_target.fit_transform(y_raw)

# Save the label encoder classes so we can decode predictions later
label_classes = le_target.classes_
print(f"Found {len(label_classes)} unique diseases.")

# Define the 4 core features our API expects
# The current API expects: Age, Gender, Severity, Duration_Min_Days
# We need to map the user input to exactly these 4 features, and impute the rest (symptoms)
expected_features = ['Age', 'Gender', 'Severity', 'Duration_Min_Days']
missing = [f for f in expected_features if f not in X_raw.columns]
if missing:
    raise ValueError(f"Dataset is missing required core features: {missing}")

# Keep track of all feature columns used for training
all_feature_cols = X_raw.columns.tolist()

print("\nSplitting dataset...")
X_train, X_test, y_train, y_test = train_test_split(X_raw, y, test_size=0.2, random_state=42)

print(f"Training set: {X_train.shape[0]} samples")
print(f"Testing set: {X_test.shape[0]} samples")

print("\nTraining Random Forest model...")
# Initialize and train the model
model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

print(f"Training complete. Accuracy on test set: {model.score(X_test, y_test):.4f}")

# Save the model and metadata
metadata = {
    'features': all_feature_cols,
    'classes': label_classes.tolist(),
    'core_features': expected_features
}

output_dir = r"c:\Users\krishna\OneDrive\Desktop\bak\bruh\backend\app\ml"
os.makedirs(output_dir, exist_ok=True)

model_path = os.path.join(output_dir, "triage_model.joblib")
meta_path = os.path.join(output_dir, "model_meta.joblib")

print(f"\nSaving model to: {model_path}")
joblib.dump(model, model_path)
joblib.dump(metadata, meta_path)

print("\nTraining script finished successfully!")
