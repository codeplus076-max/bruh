import os

_db = None

def get_db():
    """Lazy initialization of Firebase to save RAM on 512MB Free Tier."""
    global _db
    if _db is not None:
        return _db
        
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        if not firebase_admin._apps:
            # 1. Try JSON string
            service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
            if service_account_json:
                import json
                cred_dict = json.loads(service_account_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("Firebase initialized via ENV string (Lazy).")
            # 2. Try File Path
            else:
                cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
                if cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    print("Firebase initialized via FILE (Lazy).")
                else:
                    # 3. Default
                    try:
                        firebase_admin.initialize_app()
                        print("Firebase initialized via Default Credentials (Lazy).")
                    except Exception as e:
                        print(f"Warning: Firebase Admin skipping. Error: {e}")
                        return None
                        
        _db = firestore.client()
        return _db
    except Exception as e:
        print(f"Critical error in get_db: {e}")
        return None
