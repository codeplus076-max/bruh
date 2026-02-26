from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
from openai import OpenAI
from app.ml.predictor import DiseasePredictor

router = APIRouter(prefix="", tags=["predict"])

# Always load from the ml/ directory relative to this file's location — works on Render and locally
predictor = DiseasePredictor()

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
    predictions: List[Dict[str, Any]] = []
    risk_level: str
    urgency: str
    confidence: str
    first_aid: List[str]
    home_remedies: List[str]
    routine: List[str]
    medicines: List[Dict[str, str]]
    warnings: List[str]
    when_to_seek_care: List[str]
    explanation: List[str]
    emergency: bool

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

# Module-level tools list — can be imported by tests and reused without rebuilding each request
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
        
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            if tool_call.function.name == "analyze_symptoms":
                args = json.loads(tool_call.function.arguments)
                
                try:
                    # Run the actual XGB/RF ML model locally
                    disease = predictor.predict(
                        age=args.get("age", 30),
                        gender=args.get("gender", 1),
                        severity=args.get("severity", 1),
                        duration=args.get("duration_days", 1.0)
                    )
                except Exception as e:
                    print(f"ML Model failed: {e}. Falling back to mock prediction.")
                    disease = "Mock Disease (Model Not Loaded)"
                
                # Analyze risk with the new clinical engine
                from app.triage.risk_engine import evaluate_patient_risk
                from app.guidance.guidance_engine import generate_guidance
                
                risk_assessment = evaluate_patient_risk(
                    age=args.get("age", 30),
                    base_severity=args.get("severity", 1),
                    symptoms=args,
                    ml_disease=disease
                )
                
                # Extract symptoms for guidance logic
                symptoms_list = [str(k) for k, v in args.items() if isinstance(v, bool) and v] + [disease]
                    
                guidance = generate_guidance(
                    symptoms=symptoms_list,
                    disease=disease,
                    age=args.get("age", 30),
                    severity_score=args.get("severity", 1),
                    risk_level=risk_assessment["risk_level"],
                    urgency=risk_assessment["urgency"]
                )
                    
                diagnosis_data = {
                    "disease": disease,
                    "risk_level": risk_assessment["risk_level"],
                    "urgency": risk_assessment["urgency"],
                    "confidence": risk_assessment["confidence"],
                    "first_aid": guidance["first_aid"],
                    "home_remedies": guidance["home_remedies"],
                    "routine": guidance["routine"],
                    "medicines": guidance["medicines"],
                    "warnings": guidance["warnings"],
                    "when_to_seek_care": guidance["when_to_seek_care"],
                    "is_high_risk": risk_assessment["risk_level"] in ["High", "Emergency"],
                    "extracted_symptoms": args,
                    "explanation": risk_assessment["explanation"],
                    "emergency": risk_assessment["emergency"]
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
                    model="openai/gpt-3.5-turbo",
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

@router.get("/debug-model")
def debug_model():
    """Debug endpoint to check model loading status on the server."""
    import os as _os
    from app.ml.predictor import DiseasePredictor as _DP
    ml_dir = _os.path.dirname(_os.path.abspath(_DP.__init__.__code__.co_filename))
    model_path = _os.path.join(ml_dir, "triage_model.joblib")
    meta_path = _os.path.join(ml_dir, "model_meta.joblib")
    return {
        "ml_dir": ml_dir,
        "model_exists": _os.path.exists(model_path),
        "meta_exists": _os.path.exists(meta_path),
        "model_loaded": predictor._model is not None,
        "cwd": _os.getcwd()
    }

@router.post("/predict", response_model=PredictResponse)
async def predict_disease(request: PredictRequest):
    try:
        try:
            disease = predictor.predict(
                age=request.Age,
                gender=request.Gender,
                severity=request.Severity,
                duration=request.Duration_Min_Days
            )
        except Exception as e:
            print(f"ML Model failed: {e}. Falling back to mock prediction.")
            disease = "Mock Disease (Model Not Loaded)"
        # Run the new Clinical Triage risk engine
        from app.triage.risk_engine import evaluate_patient_risk
        
        # In the simple /predict endpoint we synthesize a symptoms dict from the body 
        # (Though we recommend callers use the /chat or send more details)
        symptoms = {
            "duration_days": request.Duration_Min_Days
        }
        
        risk_assessment = evaluate_patient_risk(
            age=request.Age,
            base_severity=request.Severity,
            symptoms=symptoms,
            ml_disease=disease
        )
        
        from app.guidance.guidance_engine import generate_guidance
        
        guidance = generate_guidance(
            symptoms=[disease],
            disease=disease,
            age=request.Age,
            severity_score=request.Severity,
            risk_level=risk_assessment["risk_level"],
            urgency=risk_assessment["urgency"]
        )
            
        return PredictResponse(
            predictions=[{"disease": disease, "probability": 0.85}], # Simulated prob since we only get top prediction
            risk_level=risk_assessment["risk_level"],
            urgency=risk_assessment["urgency"],
            confidence=risk_assessment["confidence"],
            first_aid=guidance["first_aid"],
            home_remedies=guidance["home_remedies"],
            routine=guidance["routine"],
            medicines=guidance["medicines"],
            warnings=guidance["warnings"],
            when_to_seek_care=guidance["when_to_seek_care"],
            explanation=risk_assessment["explanation"],
            emergency=risk_assessment["emergency"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
