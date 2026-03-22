from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
from openai import AsyncOpenAI
import asyncio
import traceback
from functools import lru_cache
from app.ml.predictor import DiseasePredictor
from app.triage.risk_engine import evaluate_patient_risk
from app.guidance.guidance_engine import generate_guidance

router = APIRouter(prefix="", tags=["predict"])

# Initialize Predictor
predictor = DiseasePredictor()

# Initialize OpenAI-compatible client
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key and openai_api_key.startswith("sk-or-"):
    client = AsyncOpenAI(
        api_key=openai_api_key,
        base_url="https://openrouter.ai/api/v1"
    )
else:
    client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None

@lru_cache(maxsize=64)
def get_cached_prediction_metadata(age: int, gender: int, severity: int, duration: float, symptoms: str):
    return predictor.predict_with_metadata(
        age=age, gender=gender, severity=severity, duration=duration, clinical_symptoms=symptoms
    )

@lru_cache(maxsize=64)
def get_cached_prediction(age: int, gender: int, severity: int, duration: float):
    return predictor.predict(
        age=age, gender=gender, severity=severity, duration=duration
    )

# --- Pydantic Models ---

class PredictRequest(BaseModel):
    Age: int
    Gender: int
    Severity: int
    Duration_Min_Days: float

class PredictResponse(BaseModel):
    predictions: List[Dict[str, Any]] = []
    risk_level: str
    risk_score: int
    important_features: List[str]
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
    age: int
    gender: int # 1=M, 0=F

class ChatResponse(BaseModel):
    role: str
    content: str
    diagnosis: Optional[Dict[str, Any]] = None

# --- OpenAI Tools ---

tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_symptoms",
            "description": "Retrieved structured medical data and trigger diagnostic ML model.",
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"type": "integer", "description": "1 (mild), 2 (moderate), 3 (severe)"},
                    "duration_days": {"type": "integer"},
                    "clinical_symptoms": {
                        "type": "string", 
                        "description": "LIST OF SYMPTOMS ONLY. No demographic info."
                    },
                    "symptom_location": {"type": "string", "description": "Specific body part or area where symptoms are felt."},
                    "onset_type": {"type": "string", "enum": ["sudden", "gradual", "unknown"], "description": "How the symptoms started."},
                    "associated_symptoms": {"type": "string", "description": "Secondary symptoms reported during follow-up."},
                    "is_injury": {"type": "boolean"},
                    "injury_type": {"type": "string"},
                    "chest_pain": {"type": "boolean"},
                    "breathlessness": {"type": "boolean"},
                    "fever": {"type": "boolean"},
                    "cough": {"type": "boolean"},
                    "headache": {"type": "boolean"},
                    "vomiting": {"type": "boolean"},
                    "diarrhea": {"type": "boolean"},
                    "sore_throat": {"type": "boolean"},
                    "rash": {"type": "boolean"},
                    "joint_pain": {"type": "boolean"},
                    "muscle_ache": {"type": "boolean"},
                    "chills": {"type": "boolean"},
                    "stiff_neck": {"type": "boolean"},
                    "yellowish_skin": {"type": "boolean"}
                },
                "required": ["severity", "duration_days", "clinical_symptoms", "is_injury"]
            }
        }
    }
]

# --- Endpoints ---

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    start_time = asyncio.get_event_loop().time()
    print(f"DEBUG: Incoming /chat request from language={request.language}")
    
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
        
    system_prompt = f"""You are a fast Medical Triage AI. Extract structured data for ML model.
RULES:
1. NO DEMOGRAPHICS: Never ask Age/Gender.
2. SYMPTOM FOCUS: Ask 1-2 quick questions max (e.g., location, duration).
3. TRIGGER: Call `analyze_symptoms` immediately once symptoms are known.
Reply concisely in {request.language}. Map severity to 1(mild), 2(mod), 3(severe)."""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})
        
    try:
        model_name = "gpt-4o-mini" if not os.getenv("OPENAI_API_KEY", "").startswith("sk-") or "openrouter" in str(client.base_url) else "gpt-3.5-turbo"
        
        print(f"DEBUG: Calling OpenAI ({model_name}) for tool/response...")
        response = await asyncio.wait_for(client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=600
        ), timeout=25.0)
        
        response_message = response.choices[0].message
        print(f"DEBUG: OpenAI response received in {asyncio.get_event_loop().time() - start_time:.2f}s")
        
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            if tool_call.function.name == "analyze_symptoms":
                print(f"DEBUG: Tool call detected: {tool_call.function.name}")
                args = json.loads(tool_call.function.arguments)
                
                # 1. Prediction Mapping & ML Logic
                step_start = asyncio.get_event_loop().time()
                if args.get("is_injury"):
                    ml_result = {
                        "disease": f"Physical Injury ({args.get('injury_type', 'General')})",
                        "confidence": "High",
                        "confidence_score": 1.0,
                        "matched_symptoms": ["injury"]
                    }
                else:
                    try:
                        print("DEBUG: Logic - Starting ML Inference...")
                        ml_result = await asyncio.to_thread(
                            get_cached_prediction_metadata,
                            request.age,
                            request.gender,
                            args.get("severity", 1),
                            args.get("duration_days", 1.0),
                            args.get("clinical_symptoms", "")
                        )
                        print(f"DEBUG: ML Inference took {asyncio.get_event_loop().time() - step_start:.2f}s")
                    except Exception as e:
                        print(f"ERROR: ML Model failed: {e}")
                        traceback.print_exc()
                        ml_result = {"disease": "Analysis Error", "confidence": "Low", "confidence_score": 0.0, "matched_symptoms": []}

                disease = ml_result["disease"]
                print(f"DEBUG: Diagnosis: {disease}")
                
                # 2. Risk & Guidance Engine
                step_start = asyncio.get_event_loop().time()
                print("DEBUG: Logic - Starting Risk Assessment...")
                risk_assessment = evaluate_patient_risk(
                    age=request.age,
                    base_severity=args.get("severity", 1),
                    symptoms=args,
                    ml_disease=disease
                )
                print(f"DEBUG: Risk Assessment took {asyncio.get_event_loop().time() - step_start:.2f}s")
                
                step_start = asyncio.get_event_loop().time()
                print("DEBUG: Logic - Starting Guidance Generation...")
                symptoms_list = [str(k) for k, v in args.items() if v is True and k not in ["is_injury", "gender", "age", "severity", "duration_days"]]
                symptoms_list += ml_result["matched_symptoms"]
                symptoms_list += [disease]
                
                guidance = generate_guidance(
                    symptoms=symptoms_list,
                    disease=disease,
                    age=request.age,
                    severity_score=args.get("severity", 1),
                    risk_level=risk_assessment["risk_level"],
                    urgency=risk_assessment["urgency"]
                )
                print(f"DEBUG: Guidance Generation took {asyncio.get_event_loop().time() - step_start:.2f}s")
                    
                diagnosis_data = {
                    "disease": disease,
                    "age": request.age,
                    "gender": "Male" if request.gender == 1 else "Female",
                    "clinical_symptoms": args.get("clinical_symptoms", "None reported"),
                    "is_injury": args.get("is_injury", False),
                    "risk_level": risk_assessment["risk_level"],
                    "risk_score": risk_assessment.get("calculated_severity_score", 0),
                    "urgency": risk_assessment["urgency"],
                    "confidence": ml_result["confidence"],
                    "confidence_score": ml_result["confidence_score"],
                    "matched_symptoms": ml_result["matched_symptoms"],
                    "important_features": ml_result["matched_symptoms"],
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
                
                # 3. Final OpenAI Call
                messages.append({"role": "assistant", "content": None, "tool_calls": [{"id": tool_call.id, "type": "function", "function": {"name": "analyze_symptoms", "arguments": tool_call.function.arguments}}]})
                messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": "analyze_symptoms", "content": json.dumps(diagnosis_data)})
                messages.append({"role": "system", "content": "FINAL STEP: Empathize, list the diagnosis, and provide the exact guidance from the tool. Be concise."})
                
                print("DEBUG: Calling OpenAI (Final) for diagnosis summary...")
                step_start = asyncio.get_event_loop().time()
                final_response = await asyncio.wait_for(client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=400
                ), timeout=25.0)
                print(f"DEBUG: Final OpenAI call took {asyncio.get_event_loop().time() - step_start:.2f}s")
                
                return ChatResponse(
                    role="assistant",
                    content=final_response.choices[0].message.content,
                    diagnosis=diagnosis_data
                )
        
        return ChatResponse(role="assistant", content=response_message.content)
        
    except asyncio.TimeoutError:
        print("ERROR: OpenAI Request timed out (>25s)")
        raise HTTPException(status_code=504, detail="AI Service Timeout")
    except Exception as e:
        print(f"ERROR: Chat endpoint failed: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict", response_model=PredictResponse)
async def predict_endpoint(request: PredictRequest):
    try:
        ml_result = await asyncio.to_thread(
            get_cached_prediction,
            request.Age,
            request.Gender,
            request.Severity,
            request.Duration_Min_Days
        )
        disease = ml_result["disease"]
        risk_assessment = evaluate_patient_risk(
            age=request.Age,
            base_severity=request.Severity,
            symptoms={},
            ml_disease=disease
        )
        return PredictResponse(
            predictions=[{"disease": disease, "confidence": ml_result["confidence"]}],
            risk_level=risk_assessment["risk_level"],
            risk_score=int(risk_assessment.get("calculated_severity_score", 0)),
            important_features=[],
            urgency=risk_assessment["urgency"],
            confidence=ml_result["confidence"],
            first_aid=[],
            home_remedies=[],
            routine=[],
            medicines=[],
            warnings=[],
            when_to_seek_care=[],
            explanation=[risk_assessment["explanation"]],
            emergency=risk_assessment["emergency"]
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
