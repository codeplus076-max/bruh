import sys
import pandas as pd
import json
import os
sys.path.append('c:\\Users\\krishna\\OneDrive\\Desktop\\bak\\bruh\\backend')
from app.api.predict import predictor

features = predictor._meta.get('features', [])
print(f'Length of features: {len(features)}')
input_dict = {'Age': 25, 'Gender': 1, 'Severity': 2, 'Duration_Min_Days': 2.0}
row = {}
for f in features:
    row[f] = input_dict.get(f, 0)
    
df = pd.DataFrame([row])
print(f'DataFrame shape: {df.shape}')
print(f'Columns: {df.columns.tolist()}')

try:
    predictor._model.predict(df)
except Exception as e:
    import traceback
    traceback.print_exc()
