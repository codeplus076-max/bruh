import pandas as pd
import os

def build_knowledge_base():
    # Use the project root directory (one level above scripts/)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Load all datasets
    print("Loading datasets...")
    desc_path = os.path.join(base_dir, 'symptom_Description.csv')
    prec_path = os.path.join(base_dir, 'symptom_precaution.csv')
    data_path = os.path.join(base_dir, 'dataset.csv')

    for path in [desc_path, prec_path, data_path]:
        if not os.path.exists(path):
            print(f"ERROR: File not found: {path}")
            return

    df_desc = pd.read_csv(desc_path)
    df_prec = pd.read_csv(prec_path)
    df_data = pd.read_csv(data_path)

    print(f"  symptom_Description.csv : {df_desc.shape}")
    print(f"  symptom_precaution.csv  : {df_prec.shape}")
    print(f"  dataset.csv             : {df_data.shape}")

    # 1. Map Descriptions
    descriptions = {}
    for _, row in df_desc.iterrows():
        disease = str(row['Disease']).strip()
        descriptions[disease] = str(row['Description']).strip()

    # 2. Map Precautions
    precautions = {}
    for _, row in df_prec.iterrows():
        disease = str(row['Disease']).strip()
        precs = []
        for i in range(1, 5):
            val = row.get(f'Precaution_{i}')
            if pd.notna(val) and str(val).strip():
                precs.append(str(val).strip().capitalize())
        precautions[disease] = precs

    # 3. Extract unique symptoms per disease from main dataset
    disease_symptoms = {}
    symptom_cols = [c for c in df_data.columns if c.lower().startswith('symptom_')]

    for _, row in df_data.iterrows():
        disease = str(row['Disease']).strip()
        if disease not in disease_symptoms:
            disease_symptoms[disease] = set()
        for sc in symptom_cols:
            val = row.get(sc)
            if pd.notna(val) and str(val).strip():
                symptom = str(val).strip().replace('_', ' ').capitalize()
                disease_symptoms[disease].add(symptom)

    # Convert sets to sorted lists
    for disease in disease_symptoms:
        disease_symptoms[disease] = sorted(list(disease_symptoms[disease]))

    # 4. Build knowledge base text
    print("\nBuilding knowledge base text file...")
    lines = []
    lines.append("=== MED-AI CLINICAL KNOWLEDGE BASE ===")
    lines.append("This is the trusted source of truth for disease diagnostics. Use ONLY this information when making medical assessments.")
    lines.append("")

    sorted_diseases = sorted(disease_symptoms.keys())
    print(f"  Total diseases found: {len(sorted_diseases)}")

    for d in sorted_diseases:
        lines.append(f"DISEASE: {d}")
        desc = descriptions.get(d, "No description available.")
        lines.append(f"DESCRIPTION: {desc}")
        symps = ", ".join(disease_symptoms[d]) if disease_symptoms[d] else "N/A"
        lines.append(f"COMMON SYMPTOMS: {symps}")
        precs = precautions.get(d, [])
        if precs:
            lines.append(f"RECOMMENDED PRECAUTIONS/TREATMENTS: {', '.join(precs)}")
        else:
            lines.append("RECOMMENDED PRECAUTIONS/TREATMENTS: Consult a healthcare professional.")
        lines.append("-" * 40)

    # Write to same directory as this script's parent (project root)
    output_path = os.path.join(base_dir, "medical_knowledge_base.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nKnowledge base successfully created at: {output_path}")
    print(f"Total entries: {len(sorted_diseases)}")

if __name__ == "__main__":
    build_knowledge_base()
