import firebase_admin
from firebase_admin import credentials, firestore
import os

def initialize_firebase():
    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            # Fallback to default credentials (useful for cloud environments)
            try:
                firebase_admin.initialize_app()
            except Exception as e:
                print(f"Warning: Firebase Admin failed to initialize: {e}")
                return None
    return firestore.client()

db = initialize_firebase()
