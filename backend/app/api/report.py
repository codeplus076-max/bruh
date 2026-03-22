from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.firebase_config import get_db

router = APIRouter(prefix="/report", tags=["report"])

class ReportGenerateRequest(BaseModel):
    session_id: str


@router.post("/generate")
async def generate_report_data(
    request: ReportGenerateRequest,
    authorization: Optional[str] = Header(None)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization.split("Bearer ")[1]
    try:
        from firebase_admin import auth
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]
        
        db = get_db()
        if not db:
            raise HTTPException(status_code=500, detail="Database unavailable")
            
        # 1. Fetch User Profile (The Source of Truth)
        user_doc = db.collection("users").document(uid).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="User profile not found")
        user_data = user_doc.to_dict()
        
        # 2. Fetch Chat Session
        session_doc = db.collection("sessions").document(request.session_id).get()
        if not session_doc.exists:
            raise HTTPException(status_code=404, detail="Session not found")
        session_data = session_doc.to_dict()
        
        # Security: Ensure session belongs to user
        if session_data.get("userId") != uid:
            raise HTTPException(status_code=403, detail="Unauthorized access to session")
            
        # 3. Assemble Medical Record (Merging persistent profile into session data)
        return {
            "patient": {
                "name": user_data.get("fullName"),
                "age": user_data.get("age"),
                "gender": user_data.get("gender"),
                "language": user_data.get("language")
            },
            "session": session_data,
            "timestamp": session_data.get("timestamp"),
            "ref_id": request.session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
