import pandas as pd
import numpy as np
import os
import re

def clean_name(name):
    """Standardize column names: lowercase, underscores replacing special chars."""
    return re.sub(r'[^a-zA-Z0-9]', '_', str(name).lower().strip()).strip('_')

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # --- File paths ---
    dataset_path   = os.path.join(base_dir, 'dataset.csv')
    augmented_path = os.path.join(base_dir, 'Final_Augmented_dataset_Diseases_and_Symptoms.csv')
    severity_path  = os.path.join(base_dir, 'Symptom-severity.csv')
    output_path    = os.path.join(base_dir, 'data', 'new_training_dataset.csv')

    print("=== Loading Symptom-severity.csv ===")
    sev_df = pd.read_csv(severity_path)
    sev_df['Symptom'] = sev_df['Symptom'].apply(clean_name)
    severity_map = dict(zip(sev_df['Symptom'], sev_df['weight']))
    print(f"Loaded {len(severity_map)} symptom weights.")

    # ===========================================================
    # PART A: Process dataset.csv (long-format Symptom_1..._17)
    # ===========================================================
    print("\n=== Loading dataset.csv (long-format) ===")
    df_long = pd.read_csv(dataset_path)
    print(f"  Shape: {df_long.shape}")

    # The first column is 'Disease', the rest are Symptom_1 ... Symptom_17
    disease_col = df_long.columns[0]
    symptom_cols = df_long.columns[1:]

    # Melt all symptom columns into a single column, drop NaN/empty
    df_melted = df_long.melt(id_vars=[disease_col], value_vars=symptom_cols,
                              var_name='_col', value_name='symptom')
    df_melted = df_melted.dropna(subset=['symptom'])
    df_melted['symptom'] = df_melted['symptom'].apply(clean_name)
    df_melted = df_melted[df_melted['symptom'].str.len() > 0]
    df_melted = df_melted[[disease_col, 'symptom']]
    df_melted[disease_col] = df_melted[disease_col].str.strip()

    # Pivot to binary: each row = one original patient record, columns = symptoms
    print("  Pivoting to binary one-hot matrix...")
    df_pivot = df_melted.groupby([df_long.index.repeat(
        len(symptom_cols)).values[:len(df_melted)],
        disease_col, 'symptom']).size().unstack(fill_value=0)

    # Alternative safer pivot approach:
    # Build binary matrix directly from the original df_long
    all_symptoms = sorted(df_melted['symptom'].unique().tolist())
    print(f"  Total unique symptoms found: {len(all_symptoms)}")

    rows = []
    for _, row in df_long.iterrows():
        disease = str(row[disease_col]).strip()
        present = set()
        for sc in symptom_cols:
            val = row[sc]
            if pd.notna(val) and str(val).strip():
                present.add(clean_name(str(val).strip()))
        binary_row = {s: int(s in present) for s in all_symptoms}
        binary_row['diseases'] = disease
        rows.append(binary_row)

    df_bin = pd.DataFrame(rows)
    print(f"  Binary matrix shape: {df_bin.shape}")

    # ===========================================================
    # PART B: Process Final_Augmented_dataset (already binary)
    # ===========================================================
    print("\n=== Loading Final_Augmented_dataset (binary format) ===")
    df_aug = pd.read_csv(augmented_path)
    print(f"  Shape: {df_aug.shape}")

    # Find the disease column (should be first column)
    aug_disease_col = df_aug.columns[0]
    df_aug = df_aug.rename(columns={aug_disease_col: 'diseases'})
    df_aug['diseases'] = df_aug['diseases'].astype(str).str.strip()

    # Clean all symptom column names
    aug_symptom_cols = [c for c in df_aug.columns if c != 'diseases']
    rename_map = {c: clean_name(c) for c in aug_symptom_cols}
    df_aug = df_aug.rename(columns=rename_map)

    # Sample down to avoid memory issues (100k max from augmented)
    if len(df_aug) > 100_000:
        print(f"  Sampling augmented dataset to 100,000 rows...")
        df_aug = df_aug.sample(n=100_000, random_state=42)

    # ===========================================================
    # PART C: Align and merge both datasets
    # ===========================================================
    print("\n=== Merging datasets ===")

    # Get union of all symptom columns (excluding 'diseases')
    cols_a = set(df_bin.columns) - {'diseases'}
    cols_b = set(df_aug.columns) - {'diseases'}
    all_cols = sorted(cols_a | cols_b)

    # Add missing columns with 0 to each DF
    for col in all_cols:
        if col not in df_bin.columns:
            df_bin[col] = 0
        if col not in df_aug.columns:
            df_aug[col] = 0

    # Ensure int type
    for col in all_cols:
        df_bin[col] = df_bin[col].fillna(0).astype(int)
        df_aug[col] = df_aug[col].fillna(0).astype(int)

    # Combine
    df_merged = pd.concat([df_bin[['diseases'] + all_cols],
                            df_aug[['diseases'] + all_cols]],
                           ignore_index=True)
    print(f"  Merged shape: {df_merged.shape}")

    # ===========================================================
    # PART D: Compute severity & add demographics
    # ===========================================================
    print("\n=== Computing severity scores ===")
    symptom_features = [c for c in df_merged.columns if c != 'diseases']
    weights = np.array([severity_map.get(s, 1) for s in symptom_features])
    S = df_merged[symptom_features].values.astype(float)

    total_severity = S.dot(weights)
    count = S.sum(axis=1)
    avg_severity = np.zeros(len(df_merged), dtype=float)
    mask = count > 0
    avg_severity[mask] = total_severity[mask] / count[mask]

    # Map to 3-tier scale
    final_severity = np.ones(len(df_merged), dtype=int)
    final_severity[(avg_severity >= 3) & (avg_severity < 5)] = 2
    final_severity[avg_severity >= 5] = 3

    print("Adding synthetic demographics...")
    np.random.seed(42)
    df_merged['Age']             = np.random.randint(5, 90, size=len(df_merged))
    df_merged['Gender']          = np.random.randint(0, 2, size=len(df_merged))
    df_merged['Duration_Min_Days'] = np.random.randint(1, 15, size=len(df_merged))
    df_merged['Severity']        = final_severity

    # ===========================================================
    # PART E: Reorder columns and save
    # ===========================================================
    front_cols = ['diseases', 'Age', 'Gender', 'Severity', 'Duration_Min_Days']
    other_cols = [c for c in df_merged.columns if c not in front_cols]
    df_final = df_merged[front_cols + other_cols]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"\nSaving final dataset to {output_path}...")
    df_final.to_csv(output_path, index=False)
    print(f"Done! Final shape: {df_final.shape}")
    print(f"Classes ({df_final['diseases'].nunique()}): {sorted(df_final['diseases'].unique())[:10]}...")

if __name__ == "__main__":
    main()
