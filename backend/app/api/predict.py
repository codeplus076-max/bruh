from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
from openai import OpenAI
from app.ml.predictor import DiseasePredictor

router = APIRouter(prefix="", tags=["predict"])

predictor = DiseasePredictor(model_dir=os.getenv("MODEL_DIR"))

# Initialize OpenAI-compatible client (supports both OpenAI and OpenRouter keys)
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key and openai_api_key.startswith("sk-or-"):
    # OpenRouter key — use their OpenAI-compatible endpoint
    client = OpenAI(
        api_key=openai_api_key,
        base_url="https://openrouter.ai/api/v1"
    )
else:
    client = OpenAI(api_key=openai_api_key) if openai_api_key else None

class PredictRequest(BaseModel):
    Age: int
    Gender: int
    Severity: int
    Duration_Min_Days: float

class PredictResponse(BaseModel):
    disease: str
    risk_level: str
    triage_guidance: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    language: str = "en"

class ChatResponse(BaseModel):
    role: str
    content: str
    diagnosis: Optional[Dict[str, Any]] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
    system_prompt = f"""You are a highly empathetic and professional rural health triage assistant.
Your goal is to politely understand the patient's symptoms and organically gather 4 key pieces of information:
1. Patient's Age
2. Patient's Gender (try to infer organically, or ask gently)
3. Duration of symptoms (in days)
4. Severity of symptoms (1=mild, 2=moderate, 3=severe)

Converse naturally in this locale language code: {request.language}
Ask one or two questions at a time. Keep responses concise and supportive.
Once you have ALL 4 required pieces of information, you MUST call the `analyze_symptoms` function to get a medical triage assessment.
Do NOT attempt to diagnose the patient yourself without calling the function.
"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})
        
    tools = [
        {
            "type": "function",
            "function": {
                "name": "analyze_symptoms",
                "description": "Trigger the medical ML model to get a diagnosis once age, gender, severity, and duration are known.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "age": {"type": "integer"},
                        "gender": {"type": "integer", "description": "1 for Male, 0 for Female"},
                        "severity": {"type": "integer", "description": "1 (mild), 2 (moderate), or 3 (severe)"},
                        "duration_days": {"type": "integer"}
                    },
                    "required": ["age", "gender", "severity", "duration_days"]
                }
            }
        }
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            if tool_call.function.name == "analyze_symptoms":
                args = json.loads(tool_call.function.arguments)
                
                # Run the actual XGB/RF ML model locally
                disease = predictor.predict(
                    age=args.get("age", 30),
                    gender=args.get("gender", 1),
                    severity=args.get("severity", 1),
                    duration=args.get("duration_days", 1.0)
                )
                
                severity = args.get("severity", 1)
                risk_level = "High" if severity >= 3 else ("Moderate" if severity == 2 else "Low")
                guidance = "Rest and drink plenty of fluids. Follow up with your doctor if symptoms persist."
                if risk_level == "High":
                    guidance = "Seek medical attention immediately. Consider going to the nearest hospital."
                    
                diagnosis_data = {
                    "disease": disease,
                    "risk_level": risk_level,
                    "triage_guidance": guidance,
                    "is_high_risk": risk_level == "High",
                    "extracted_symptoms": args
                }
                
                # Send the function result back to OpenAI to generate a final empathetic response
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": "analyze_symptoms",
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "analyze_symptoms",
                    "content": json.dumps(diagnosis_data)
                })
                
                final_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages
                )
                
                return ChatResponse(
                    role="assistant",
                    content=final_response.choices[0].message.content,
                    diagnosis=diagnosis_data
                )
                
        # If no function call, just return the AI's standard conversational text
        return ChatResponse(
            role="assistant",
            content=response_message.content
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict", response_model=PredictResponse)
async def predict_disease(request: PredictRequest):
    try:
        disease = predictor.predict(
            age=request.Age,
            gender=request.Gender,
            severity=request.Severity,
            duration=request.Duration_Min_Days
        )
        # Determine risk and guidance based on PRD
        risk_level = "High" if request.Severity >= 3 else ("Moderate" if request.Severity == 2 else "Low")
        
        guidance = "Rest and drink plenty of fluids. Follow up with your doctor if symptoms persist."
        if risk_level == "High":
            guidance = "Seek medical attention immediately. Consider going to the nearest hospital."
            
        return PredictResponse(
            disease=disease,
            risk_level=risk_level,
            triage_guidance=guidance
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
