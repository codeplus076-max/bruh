import firebase_admin
from firebase_admin import credentials, firestore
import os

def initialize_firebase():
    try:
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print("Firebase initialized with service account.")
            else:
                # Attempt default credentials, but don't crash if they fail
                try:
                    firebase_admin.initialize_app()
                    print("Firebase initialized with default credentials.")
                except Exception as e:
                    print(f"Warning: Firebase default credentials not found. Some features (reports/history) will be disabled. Error: {e}")
                    return None
        return firestore.client()
    except Exception as e:
        print(f"Critical Warning: Firebase Admin failed to initialize entirely: {e}")
        return None

db = initialize_firebase()
