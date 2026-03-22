import firebase_admin
from firebase_admin import credentials, firestore
import os

def initialize_firebase():
    try:
        if not firebase_admin._apps:
            # 1. Try JSON string from environment variable (Best for Render/Vercel)
            service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
            if service_account_json:
                import json
                try:
                    # Parse JSON string and initialize
                    cred_dict = json.loads(service_account_json)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                    print("Firebase initialized via FIREBASE_SERVICE_ACCOUNT_JSON string.")
                except Exception as je:
                    print(f"Error parsing FIREBASE_SERVICE_ACCOUNT_JSON: {je}")
                    return None
            
            # 2. Try Local File Path (Fallback for local dev)
            else:
                cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
                if cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    print(f"Firebase initialized with service account file: {cred_path}")
                else:
                    # 3. Last Resort: Default Application Credentials
                    try:
                        firebase_admin.initialize_app()
                        print("Firebase initialized with default credentials (likely local GCloud auth).")
                    except Exception as e:
                        print(f"Warning: Firebase Admin could not be initialized. History/Profiles will fail. Error: {e}")
                        return None
        return firestore.client()
    except Exception as e:
        print(f"Critical error in initialize_firebase: {e}")
        return None

db = initialize_firebase()
