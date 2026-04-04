"""
Upchaar AI — SymptomScan Knowledge DB Builder
===============================================
Aggregates archive (5) CSVs into a unified JSON lookup dictionary.
Output: backend/app/ml/pipeline/sympscan_db.json

Run ONCE from the project root:
  python scripts/build_sympscan_db.py
"""

import os
import sys
import json
import csv
from collections import defaultdict

print("=" * 60)
print("Upchaar SymptomScan DB Builder")
print("=" * 60)

# ── Paths ─────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
ARCHIVE_DIR = os.path.join(ROOT_DIR, "archive (5)")

OUT_DIR = os.path.join(ROOT_DIR, "backend", "app", "ml", "pipeline")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_PATH = os.path.join(OUT_DIR, "sympscan_db.json")

def safe_read_csv(path):
    if not os.path.exists(path):
        print(f"  WARNING: {path} not found — skipping")
        return []
    with open(path, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

def normalise(name: str) -> str:
    return name.strip().lower()

# ── Load CSVs ─────────────────────────────────────────────────
print("\n[1/5] Loading precautions.csv...")
precautions_rows = safe_read_csv(os.path.join(ARCHIVE_DIR, "precautions.csv"))

print("[2/5] Loading medications.csv...")
medications_rows = safe_read_csv(os.path.join(ARCHIVE_DIR, "medications.csv"))

print("[3/5] Loading diets.csv...")
diets_rows = safe_read_csv(os.path.join(ARCHIVE_DIR, "diets.csv"))

print("[4/5] Loading description.csv...")
description_rows = safe_read_csv(os.path.join(ARCHIVE_DIR, "description.csv"))

# ── Build unified dict ────────────────────────────────────────
print("[5/5] Merging into SymptomScan DB...")
db = defaultdict(lambda: {
    "description": "",
    "precautions": [],
    "medications": [],
    "diet": [],
    "when_to_seek_help": [],
    "home_care": []
})

# Precautions — columns: Disease, Precaution_1, Precaution_2, Precaution_3, Precaution_4
for row in precautions_rows:
    disease = row.get("Disease", "").strip()
    if not disease:
        continue
    key = normalise(disease)
    db[key]["_canonical"] = disease
    precs = []
    for col in ["Precaution_1", "Precaution_2", "Precaution_3", "Precaution_4"]:
        val = row.get(col, "").strip()
        if val:
            # Capitalise and clean
            val = val[0].upper() + val[1:] if val else val
            precs.append(val)
    db[key]["precautions"] = precs

# Medications — columns: Disease, Medication (may be multiple semicolon/comma delimited)
for row in medications_rows:
    disease = row.get("Disease", "").strip()
    if not disease:
        continue
    key = normalise(disease)
    db[key]["_canonical"] = disease
    # Try multiple medication columns
    meds = []
    for col in row.keys():
        if col.lower() not in ["disease"] and row[col].strip():
            raw = row[col].strip()
            # Split if multiple meds separated by [ or ,
            parts = [p.strip().strip("'\"[]") for p in raw.replace("[", "").replace("]", "").split(",")]
            for p in parts:
                if p and len(p) > 1:
                    meds.append(p[0].upper() + p[1:])
    db[key]["medications"] = meds[:6]  # cap at 6

# Diets — columns: Disease, Diet
for row in diets_rows:
    disease = row.get("Disease", "").strip()
    if not disease:
        continue
    key = normalise(disease)
    db[key]["_canonical"] = disease
    raw = row.get("Diet", "").strip()
    if raw:
        # May be comma-separated or bracket-delimited
        parts = [p.strip().strip("'\"[]") for p in raw.replace("[", "").replace("]", "").split(",")]
        db[key]["diet"] = [p[0].upper() + p[1:] for p in parts if p and len(p) > 1][:5]

# Description — columns: Disease, Description
for row in description_rows:
    disease = row.get("Disease", "").strip()
    if not disease:
        continue
    key = normalise(disease)
    db[key]["_canonical"] = disease
    db[key]["description"] = row.get("Description", "").strip()

# ── Add universal home care & when_to_seek_help ───────────────
# These are disease-agnostic defaults added for all entries.
# More specific rules come from the hybrid orchestrator.
DEFAULT_HOME_CARE = [
    "Rest adequately and avoid strenuous activity",
    "Stay well-hydrated — drink at least 8 glasses of water per day",
    "Eat light, easily digestible meals",
    "Monitor your temperature and symptoms regularly"
]

DEFAULT_WHEN_TO_SEEK = [
    "Symptoms worsen significantly after 48 hours of home care",
    "You develop difficulty breathing or chest pain",
    "High fever (above 103°F / 39.4°C) persists beyond 2 days",
    "You feel confused, faint, or cannot keep fluids down"
]

for key in db:
    if not db[key].get("home_care"):
        db[key]["home_care"] = DEFAULT_HOME_CARE.copy()
    if not db[key].get("when_to_seek_help"):
        db[key]["when_to_seek_help"] = DEFAULT_WHEN_TO_SEEK.copy()

# ── Serialise ──────────────────────────────────────────────────
output = dict(db)
print(f"\nTotal diseases in SymptomScan DB: {len(output)}")

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✅ SymptomScan DB written to: {OUT_PATH}")
print(f"   Size: {os.path.getsize(OUT_PATH) / 1024:.1f} KB")

# ── Preview a few entries ──────────────────────────────────────
sample_keys = list(output.keys())[:3]
print("\nSample entries:")
for k in sample_keys:
    entry = output[k]
    print(f"  [{k}]")
    print(f"    precautions: {entry.get('precautions', [])[:2]}")
    print(f"    medications: {entry.get('medications', [])[:2]}")
    print(f"    diet:        {entry.get('diet', [])[:2]}")
print("=" * 60)
