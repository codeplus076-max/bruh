"""
Firebase configuration with deferred lazy initialization.
The firebase_admin SDK (+ gRPC) costs ~100-150MB of RAM.
We defer initialization until the first actual DB request to avoid
consuming memory on boot if Firebase is not configured.
"""
import os

# Global state - initialized lazily on first use
_firebase_app = None
_db = None

def _ensure_initialized():
    """Initialize Firebase only on first actual use, not at import time."""
    global _firebase_app, _db
    if _db is not None:
        return _db
    
    # Only import firebase_admin when actually needed (saves RAM until first use)
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                _firebase_app = firebase_admin.initialize_app(cred)
                print("Firebase initialized with service account.")
            else:
                try:
                    _firebase_app = firebase_admin.initialize_app()
                    print("Firebase initialized with default credentials.")
                except Exception as e:
                    print(f"Warning: Firebase not configured. Reports/history disabled. {e}")
                    return None
        
        _db = firestore.client()
        return _db
    except Exception as e:
        print(f"Firebase init failed: {e}")
        return None


class _LazyDB:
    """Proxy that initializes Firebase only when its attributes are first accessed."""
    def __getattr__(self, name):
        real_db = _ensure_initialized()
        if real_db is None:
            raise AttributeError(f"Firebase is not initialized. Cannot call .{name}()")
        return getattr(real_db, name)
    
    def __bool__(self):
        return _ensure_initialized() is not None


# Drop-in replacement: code that does `if not db: ...` still works correctly
db = _LazyDB()
