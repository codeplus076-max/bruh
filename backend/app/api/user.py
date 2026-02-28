from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.firebase_config import db
from firebase_admin import auth

router = APIRouter(prefix="/user", tags=["user"])

@router.get("/profile")
async def get_user_profile(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token")
    
    token = authorization.split("Bearer ")[1]
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]
        
        if not db:
            raise HTTPException(status_code=500, detail="Firestore not initialized")
            
        doc_ref = db.collection("users").document(uid)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User profile not found")
            
        data = doc.to_dict()
        return {
            "name": data.get("fullName"),
            "age": data.get("age"),
            "gender": data.get("gender"),
            "language": data.get("language")
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
