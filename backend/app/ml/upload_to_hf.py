import os
import argparse
from huggingface_hub import HfApi

def upload_models(token: str, repo_id: str):
    """
    Uploads the triage_model.joblib and model_meta.joblib to the specified Hugging Face repository.
    """
    api = HfApi()
    
    # Path to models
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "triage_model.joblib")
    meta_path = os.path.join(current_dir, "model_meta.joblib")
    
    if not os.path.exists(model_path) or not os.path.exists(meta_path):
        print(f"Error: Could not find model files in {current_dir}.")
        print("Ensure 'triage_model.joblib' and 'model_meta.joblib' exist.")
        return
    
    print(f"Uploading models to {repo_id}...")
    
    try:
        api.upload_file(
            path_or_fileobj=model_path,
            path_in_repo="triage_model.joblib",
            repo_id=repo_id,
            token=token,
        )
        print("✅ Successfully uploaded triage_model.joblib")
        
        api.upload_file(
            path_or_fileobj=meta_path,
            path_in_repo="model_meta.joblib",
            repo_id=repo_id,
            token=token,
        )
        print("✅ Successfully uploaded model_meta.joblib")
        
        print("\n🎉 Upload complete! You can now use these models in your backend.")
    except Exception as e:
        print(f"❌ Error uploading models: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload models to Hugging Face Hub")
    parser.add_argument("--repo", required=True, help="Your Hugging Face Repo ID (e.g., username/repo-name)")
    parser.add_argument("--token", required=True, help="Your Hugging Face Write Token")
    
    args = parser.parse_args()
    upload_models(args.token, args.repo)
