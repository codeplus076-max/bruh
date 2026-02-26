import sys
import pandas as pd
import joblib
sys.path.append('c:\\Users\\krishna\\OneDrive\\Desktop\\bak\\bruh\\backend')
from app.ml.predictor import DiseasePredictor

p = DiseasePredictor()
features = p._meta.get('features', [])
print(f'Length of features: {len(features)}')
input_dict = {'Age': 25, 'Gender': 1, 'Severity': 2, 'Duration_Min_Days': 2.0}
row = {}
for f in features:
    row[f] = input_dict.get(f, 0)
    
df = pd.DataFrame([row])
print(f'DataFrame shape: {df.shape}')

try:
    print(f'Model expects {p._model.n_features_in_} features. Calling predict...')
    p._model.predict(df)
except Exception as e:
    print(repr(e))
