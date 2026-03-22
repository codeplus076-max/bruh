from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.tts_service import tts_service
from typing import Optional

router = APIRouter(prefix="/voice", tags=["voice"])

class TTSRequest(BaseModel):
    text: str
    language: str = "en"

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Generates MP3 audio for a given text using Inworld TTS"""
    try:
        audio_content = await tts_service.generate_tts(request.text, request.language)
        return Response(content=audio_content, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_voice(request: TTSRequest):
    """Streams MP3 audio for live call mode using Inworld Streaming TTS"""
    try:
        return StreamingResponse(
            tts_service.stream_tts_iterator(request.text, request.language),
            media_type="audio/mpeg"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/call/start")
async def start_call():
    return {"status": "call_started"}

@router.post("/call/stop")
async def stop_call():
    return {"status": "call_stopped"}
