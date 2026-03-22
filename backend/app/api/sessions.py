from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.firebase_config import get_db

router = APIRouter(prefix="/sessions", tags=["sessions"])

class ChatMessage(BaseModel):
    role: str
    content: str
    diagnosis: Optional[Dict[str, Any]] = None

class SessionSaveRequest(BaseModel):
    sessionId: str
    messages: List[ChatMessage]
    language: str
    title: Optional[str] = None
    risk_level: Optional[str] = "Normal"


async def get_uid(authorization: Optional[str]):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split("Bearer ")[1]
    try:
        from firebase_admin import auth
        decoded = auth.verify_id_token(token)
        return decoded["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Auth failed")

@router.post("/save")
async def save_session(request: SessionSaveRequest, authorization: Optional[str] = Header(None)):
    uid = await get_uid(authorization)
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database not ready")
    
    # Auto-generate title if missing
    title = request.title
    if not title and len(request.messages) > 0:
        first_user_msg = next((m.content for m in request.messages if m.role == "user"), "New Conversation")
        title = " ".join(first_user_msg.split()[:6])
    
    session_data = {
        "sessionId": request.sessionId,
        "userId": uid,
        "messages": [m.dict() for m in request.messages],
        "language": request.language,
        "title": title,
        "risk_level": request.risk_level,
        "updatedAt": time.time(),
        "createdAt": request.messages[0].dict().get('timestamp', time.time()) if request.messages else time.time()
    }
    
    db.collection("users").document(uid).collection("sessions").document(request.sessionId).set(session_data, merge=True)
    return {"status": "success", "title": title}

@router.get("/history")
async def get_history(authorization: Optional[str] = Header(None)):
    uid = await get_uid(authorization)
    if not db:
        return []
    
    sessions_ref = db.collection("users").document(uid).collection("sessions")
    docs = sessions_ref.order_by("updatedAt", direction="DESCENDING").limit(20).stream()
    
    history = []
    for doc in docs:
        data = doc.to_dict()
        history.append({
            "sessionId": data.get("sessionId"),
            "title": data.get("title", "Untitled Chat"),
            "createdAt": data.get("updatedAt", 0),
            "language": data.get("language", "en")
        })
    return history

@router.get("/{sessionId}")
async def get_session(sessionId: str, authorization: Optional[str] = Header(None)):
    uid = await get_uid(authorization)
    if not db:
        raise HTTPException(status_code=500, detail="Database not ready")
    
    doc = db.collection("users").document(uid).collection("sessions").document(sessionId).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return doc.to_dict()
