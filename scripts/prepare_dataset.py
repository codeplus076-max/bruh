import pandas as pd
import numpy as np
import os
import re

def clean_name(name):
    """Standardize names: lowercase, underscores replacing special chars."""
    return re.sub(r'[^a-zA-Z0-9]', '_', str(name).lower().strip()).strip('_')

def main():
    base_dir  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    dataset_path  = os.path.join(base_dir, 'dataset.csv')
    severity_path = os.path.join(base_dir, 'Symptom-severity.csv')
    output_path   = os.path.join(base_dir, 'data', 'new_training_dataset.csv')

    for path in [dataset_path, severity_path]:
        if not os.path.exists(path):
            print(f"ERROR: Required file not found: {path}")
            return

    print("=== Loading Symptom-severity.csv ===")
    sev_df = pd.read_csv(severity_path)
    sev_df['Symptom'] = sev_df['Symptom'].apply(clean_name)
    severity_map = dict(zip(sev_df['Symptom'], sev_df['weight']))
    print(f"  Loaded {len(severity_map)} symptom weights.")

    print("\n=== Loading dataset.csv ===")
    df = pd.read_csv(dataset_path)
    df.columns = df.columns.str.strip()
    df['Disease'] = df['Disease'].str.strip()
    print(f"  Shape: {df.shape}")

    symptom_cols = [c for c in df.columns if c.lower().startswith('symptom_')]
    print(f"  Symptom columns: {len(symptom_cols)}")

    # -------------------------------------------------------
    # Vectorised melt → deduplicate symptoms per case
    # -------------------------------------------------------
    print("\n=== Building binary symptom matrix (vectorised) ===")

    # Add a row index so we can pivot back
    df = df.reset_index().rename(columns={'index': 'case_id'})

    # Melt all symptom columns
    melted = df.melt(
        id_vars=['case_id', 'Disease'],
        value_vars=symptom_cols,
        var_name='_col',
        value_name='symptom'
    )
    melted = melted.dropna(subset=['symptom'])
    melted['symptom'] = melted['symptom'].str.strip().apply(clean_name)
    melted = melted[melted['symptom'].str.len() > 0]
    melted = melted.drop_duplicates(subset=['case_id', 'symptom'])

    all_symptoms = sorted(melted['symptom'].unique().tolist())
    print(f"  Total unique symptoms: {len(all_symptoms)}")

    # Pivot to binary matrix (rows = case_id, cols = symptoms)
    print("  Pivoting to binary matrix...")
    melted['val'] = 1
    pivot = melted.pivot_table(
        index='case_id',
        columns='symptom',
        values='val',
        aggfunc='max',
        fill_value=0
    ).astype(int)

    # Re-attach disease column
    disease_series = df.set_index('case_id')['Disease']
    pivot['diseases'] = disease_series

    # Reset index cleanly
    df_bin = pivot.reset_index(drop=True)

    # Ensure all symptom columns come after 'diseases'
    sym_cols   = [c for c in df_bin.columns if c != 'diseases']
    df_bin     = df_bin[['diseases'] + sym_cols]
    print(f"  Binary matrix shape: {df_bin.shape}")

    # -------------------------------------------------------
    # Compute severity scores
    # -------------------------------------------------------
    print("\n=== Computing severity scores ===")
    weights      = np.array([severity_map.get(s, 1) for s in sym_cols])
    S            = df_bin[sym_cols].values.astype(float)
    total_sev    = S.dot(weights)
    count        = S.sum(axis=1)
    avg_sev      = np.zeros(len(df_bin), dtype=float)
    mask         = count > 0
    avg_sev[mask]= total_sev[mask] / count[mask]

    final_sev    = np.ones(len(df_bin), dtype=int)
    final_sev[(avg_sev >= 3) & (avg_sev < 5)] = 2
    final_sev[avg_sev >= 5] = 3

    # -------------------------------------------------------
    # Add synthetic demographics
    # -------------------------------------------------------
    np.random.seed(42)
    df_bin['Age']               = np.random.randint(5, 90, size=len(df_bin))
    df_bin['Gender']            = np.random.randint(0, 2, size=len(df_bin))
    df_bin['Duration_Min_Days'] = np.random.randint(1, 15, size=len(df_bin))
    df_bin['Severity']          = final_sev

    # -------------------------------------------------------
    # Reorder and save
    # -------------------------------------------------------
    front   = ['diseases', 'Age', 'Gender', 'Severity', 'Duration_Min_Days']
    others  = [c for c in df_bin.columns if c not in front]
    df_final = df_bin[front + others]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"\nSaving to {output_path}...")
    df_final.to_csv(output_path, index=False)
    print(f"Done! Final shape: {df_final.shape}")
    print(f"Classes ({df_final['diseases'].nunique()}): {sorted(df_final['diseases'].unique())[:10]}...")

if __name__ == "__main__":
    main()
