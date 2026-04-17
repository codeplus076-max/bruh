from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.summary_service import extract_patient_info, merge_prediction_results, generate_summary

router = APIRouter(prefix="", tags=["summary"])

class SummaryRequestMessage(BaseModel):
    role: str
    content: str
    
class GenerateSummaryRequest(BaseModel):
    messages: List[SummaryRequestMessage]
    diagnosis: Dict[str, Any]
    patient_profile: Dict[str, Any]
    language: str = "en"

class GenerateSummaryResponse(BaseModel):
    structured_data: Dict[str, Any]
    summary_text: str

@router.post("/generate-summary", response_model=GenerateSummaryResponse)
async def generate_summary_endpoint(request: GenerateSummaryRequest):
    """
    Generates an AI structured summary and text report from the conversation and ML prediction.
    """
    try:
        # Convert Pydantic models to list of dicts for extraction
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # 1. Extract patient details via AI/NLP
        extracted_info = await extract_patient_info(messages_dict)
        
        # 2. Merge extracted data with existing ML prediction data AND Explicit patient profile
        merged_data = merge_prediction_results(extracted_info, request.diagnosis, request.patient_profile)
        
        # 3. Inject full conversation history
        merged_data["conversation_logs"] = messages_dict
        merged_data["language"] = request.language
        
        # 4. Generate Human Readable Text
        summary_text = generate_summary(merged_data, request.language)
        
        return GenerateSummaryResponse(
            structured_data=merged_data,
            summary_text=summary_text
        )
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate patient summary.")
