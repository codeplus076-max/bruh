import os
import pandas as pd
import joblib

def main():
    print("--- Stage 3: Guidance & Urgency Mapper ---")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'data', 'guidance_dataset.csv')
    
    if not os.path.exists(data_path):
        print(f"ERROR: Dataset not found at {data_path}")
        return

    print("Loading Stage 3 Data...")
    df = pd.read_csv(data_path)
    
    # We want to build a deterministic mapping from Diagnosis -> Severity -> Treatment_Plan
    # Since there might be slight variations, we'll take the mode (most common) severity and treatment for each diagnosis.
    print(f"Total records: {len(df)}")
    
    # Clean up column names in case of whitespace
    df.columns = [c.strip() for c in df.columns]
    
    mapping = {}
    grouped = df.groupby('Diagnosis')
    
    for diag, group in grouped:
        mode_sev = group['Severity'].mode()
        sev = mode_sev[0] if not mode_sev.empty else 'Moderate'
        
        mode_treat = group['Treatment_Plan'].mode()
        treat = mode_treat[0] if not mode_treat.empty else 'Consult a doctor for guidance.'
        
        mapping[diag.lower().strip()] = {
            "severity": sev,
            "treatment_plan": treat
        }

    print(f"Extracted {len(mapping)} distinct guidance routes.")

    # Save
    model_dir = os.path.join(base_dir, 'backend', 'app', 'ml', 'pipeline')
    os.makedirs(model_dir, exist_ok=True)
    
    mapper_path = os.path.join(model_dir, 'stage3_guidance_mapper.joblib')
    joblib.dump(mapping, mapper_path)

    print(f"Stage 3 Complete. Saved to {mapper_path}")

if __name__ == "__main__":
    main()
