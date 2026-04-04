import os
import pandas as pd
import json

def build_knowledge_dbs():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pipeline_dir = os.path.join(base_dir, "../backend/app/ml/pipeline")
    os.makedirs(pipeline_dir, exist_ok=True)
    
    # 1. Process MedQuAD
    medquad_path = os.path.join(base_dir, "../archive (7)/medquad.csv")
    medquad_json_path = os.path.join(pipeline_dir, "medquad_knowledge.json")
    
    print(f"Building MedQuAD DB from {medquad_path}...")
    medquad_db = {}
    if os.path.exists(medquad_path):
        # MedQuAD columns: ['question', 'answer', 'source', 'focus_area']
        df = pd.read_csv(medquad_path)
        
        # We only want general information to not bloat memory
        # 'What is (are)', 'What are the symptoms of'
        for _, row in df.iterrows():
            area = str(row.get('focus_area', '')).strip().lower()
            if not area or area == 'nan':
                continue
                
            q = str(row.get('question', '')).lower()
            a = str(row.get('answer', ''))
            
            if area not in medquad_db:
                medquad_db[area] = {
                    "overview": "",
                    "symptoms_desc": ""
                }
                
            if "what is" in q or "information about" in q:
                if not medquad_db[area]["overview"] or len(a) < len(medquad_db[area]["overview"]):
                    medquad_db[area]["overview"] = a[:1000] # Cap length
            elif "symptom" in q or "sign" in q:
                if not medquad_db[area]["symptoms_desc"] or len(a) < len(medquad_db[area]["symptoms_desc"]):
                    medquad_db[area]["symptoms_desc"] = a[:1000]
                    
        # Clean empty keys
        medquad_db = {k: v for k, v in medquad_db.items() if v["overview"] or v["symptoms_desc"]}
        
        with open(medquad_json_path, 'w', encoding='utf-8') as f:
            json.dump(medquad_db, f, indent=2)
        print(f"Built {medquad_json_path} with {len(medquad_db)} diseases.")
    else:
        print(f"Warning: {medquad_path} not found.")


    # 2. Process Symptom-Disease mappings
    sd_path = os.path.join(base_dir, "../archive (8)/final_symptoms_to_disease.csv")
    rules_json_path = os.path.join(pipeline_dir, "symptom_rules_db.json")
    
    print(f"Building Symptom Rules DB from {sd_path}...")
    rules_db = {}
    if os.path.exists(sd_path):
        df_sd = pd.read_csv(sd_path)
        
        # It's likely format: ['disease', 'symptom1', 'symptom2'...] or ['disease', 'symptoms' (string)]
        # We will parse whatever is available into a list of symptoms per disease
        for _, row in df_sd.iterrows():
            d = ""
            for k in ["diseases", "disease", "Disease"]:
                if k in df_sd.columns:
                    d = str(row[k]).strip().lower()
                    break
            
            if not d: continue
            
            symptoms = []
            if "symptoms" in df_sd.columns:
                s_str = str(row["symptoms"]).lower()
                symptoms = [s.strip() for s in s_str.split(',') if s.strip()]
            else:
                # Boolean matrix or comma sep columns? Let's just collect truthy ones
                for col in df_sd.columns:
                    if col.lower() not in ["disease", "diseases", "id"]:
                        if row[col] == 1 or row[col] == True or str(row[col]).lower() == 'yes':
                            symptoms.append(col.lower().replace("_", " "))
            
            rules_db[d] = list(set(symptoms))
            
        with open(rules_json_path, 'w', encoding='utf-8') as f:
            json.dump(rules_db, f, indent=2)
        print(f"Built {rules_json_path} with {len(rules_db)} diseases mapped to symptoms.")
    else:
        print(f"Warning: {sd_path} not found.")

if __name__ == "__main__":
    build_knowledge_dbs()
