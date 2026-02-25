from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

router = APIRouter(prefix="/voice", tags=["voice"])

class TTSRequest(BaseModel):
    text: str

@router.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    # Mock response
    return {"text": "Transcribed text goes here."}

@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    # Mock response, in real scenario would return audio stream URL or blob
    return {"audio_url": "mock_audio_stream_url"}
