import os
import joblib
import pandas as pd
import numpy as np
import warnings
from huggingface_hub import hf_hub_download

class DiseasePredictor:
    def __init__(self, model_dir: str = None, hf_repo_id: str = None, hf_token: str = None):
        """
        Initialize the predictor.
        If `hf_repo_id` is provided, it attempts to download the models from Hugging Face Hub first.
        Otherwise, it falls back to the local `model_dir`.
        """
        self.hf_repo_id = hf_repo_id or os.getenv("HF_MODEL_REPO_ID")
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        
        if model_dir is None:
            model_dir = os.path.dirname(os.path.abspath(__file__))
            
        self.local_model_path = os.path.join(model_dir, "triage_model.joblib")
        self.local_meta_path = os.path.join(model_dir, "model_meta.joblib")
        
        self.model_path = None
        self.meta_path = None
        self._model = None
        self._meta = None
        
        self.load_model()

    def load_model(self):
        # 1. Try Hugging Face Hub
        if self.hf_repo_id:
            try:
                print(f"Attempting to download model from Hugging Face Hub: {self.hf_repo_id}")
                self.model_path = hf_hub_download(
                    repo_id=self.hf_repo_id, 
                    filename="triage_model.joblib", 
                    token=self.hf_token
                )
                self.meta_path = hf_hub_download(
                    repo_id=self.hf_repo_id, 
                    filename="model_meta.joblib", 
                    token=self.hf_token
                )
                print("Successfully downloaded models from Hugging Face Hub.")
            except Exception as e:
                print(f"Warning: Failed to download from Hugging Face Hub: {e}")
                self.model_path = None
                self.meta_path = None
        
        # 2. Fallback to Local
        if not self.model_path or not self.meta_path:
            if os.path.exists(self.local_model_path) and os.path.exists(self.local_meta_path):
                print(f"Loading local models from {self.local_model_path}")
                self.model_path = self.local_model_path
                self.meta_path = self.local_meta_path
            else:
                self.model_path = None
                self.meta_path = None
                
        # 3. Load Models
        if self.model_path and self.meta_path:
            try:
                self._model = joblib.load(self.model_path)
                self._meta = joblib.load(self.meta_path)
                print("Successfully loaded Random Forest model and metadata.")
            except Exception as e:
                print(f"Error loading models: {e}")
                self._model = None
                self._meta = None
        else:
            print("Warning: Model or meta not found (HF Hub and local failed). Using mock predictions.")
            self._model = None

    def predict(self, age: int, gender: int, severity: int, duration: float) -> str:
        if self._model and self._meta:
            input_dict = {
                'Age': age,
                'Gender': gender,
                'Severity': severity,
                'Duration_Min_Days': duration
            }
            
            # The model was trained on ~38 columns. We need to fill missing ones with 0.
            features = self._meta.get('features', [])
            row = {}
            for f in features:
                row[f] = input_dict.get(f, 0)  # Default all unseen symptoms to 0
                
            df = pd.DataFrame([row])
            
            # Predict returns an encoded integer — cast to plain Python int for safe indexing
            pred_idx = int(self._model.predict(df)[0])
            
            # Decode the integer back to a string disease label
            classes = self._meta.get('classes', [])
            if 0 <= pred_idx < len(classes):
                return str(classes[pred_idx])
            return "Unknown Disease"
        else:
            return "Mock Disease (Model Not Loaded)"
