import pandas as pd
import numpy as np
import os
import re

def clean_symptom_name(name):
    # Ensure all column names are alphanumeric + underscores (XGBoost constraint)
    # Also standardize to lowercase
    return re.sub(r'[^a-zA-Z0-9]', '_', str(name).lower().strip())

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, 'Final_Augmented_dataset_Diseases_and_Symptoms.csv')
    severity_path = os.path.join(base_dir, 'Symptom-severity.csv')
    output_path = os.path.join(base_dir, 'data', 'new_training_dataset.csv')
    
    print(f"Loading datasets...")
    df = pd.read_csv(dataset_path)
    sev_df = pd.read_csv(severity_path)
    
    print(f"Original dataset shape: {df.shape}")
    
    # Clean severity mappings
    sev_df['Symptom'] = sev_df['Symptom'].apply(clean_symptom_name)
    severity_mapping = dict(zip(sev_df['Symptom'], sev_df['weight']))
    
    # Identify symptoms
    symptom_cols = df.columns[1:]
    
    # Map each column to a weight
    print("Mapping severity weights to symptoms...")
    weights = []
    for col in symptom_cols:
        clean_col = clean_symptom_name(col)
        # Default weight is 1 if not found in mapping
        weights.append(severity_mapping.get(clean_col, 1))
        
    weights_array = np.array(weights)
    
    # Calculate Severity using matrix operations for speed
    print("Calculating overall physical severity scores...")
    S = df[symptom_cols].values
    total_severity = S.dot(weights_array)
    count = S.sum(axis=1)
    
    # Avoid div by zero
    avg_severity = np.zeros_like(total_severity, dtype=float)
    mask = count > 0
    avg_severity[mask] = total_severity[mask] / count[mask]
    
    # Map average severity to 1, 2, 3 scale (1=Low, 2=Moderate, 3=Severe)
    final_severity = np.ones(len(df), dtype=int)
    final_severity[(avg_severity >= 3) & (avg_severity < 5)] = 2
    final_severity[avg_severity >= 5] = 3
    
    print("Adding synthetic demographics and duration...")
    np.random.seed(42)
    # Age: 5 to 90 years old
    df['Age'] = np.random.randint(5, 90, size=len(df))
    # Gender: 0 or 1
    df['Gender'] = np.random.randint(0, 2, size=len(df))
    # Duration: 1 to 14 days
    df['Duration_Min_Days'] = np.random.randint(1, 15, size=len(df))
    # Add computed severity
    df['Severity'] = final_severity
    
    # Clean up column names for XGBoost
    # XGBoost can't handle spaces or special characters in column names
    print("Cleaning symptom column names...")
    new_columns = []
    for c in df.columns:
        if c == 'diseases':
            new_columns.append('diseases')
        elif c in ['Age', 'Gender', 'Duration_Min_Days', 'Severity']:
            new_columns.append(c)
        else:
            new_columns.append(clean_symptom_name(c))
    
    df.columns = new_columns
    
    # Move specific columns to the front for easier inspection
    front_cols = ['diseases', 'Age', 'Gender', 'Severity', 'Duration_Min_Days']
    other_cols = [c for c in df.columns if c not in front_cols]
    df = df[front_cols + other_cols]
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"Saving new training dataset to {output_path}...")
    df.to_csv(output_path, index=False)
    print(f"Done! Final Shape: {df.shape}")

if __name__ == "__main__":
    main()
