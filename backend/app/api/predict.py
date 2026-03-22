from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
from openai import AsyncOpenAI
import asyncio
from functools import lru_cache
from app.ml.predictor import DiseasePredictor

router = APIRouter(prefix="", tags=["predict"])

# Always load from the ml/ directory relative to this file's location — works on Render and locally
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

# Module-level tools list
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
                    # Granular Symptom Flags for ML precision
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


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
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
        # Use gpt-4o-mini for better tool precision if available, fallback to 3.5
        model_name = "gpt-4o-mini" if not os.getenv("OPENAI_API_KEY", "").startswith("sk-") or "openrouter" in str(client.base_url) else "gpt-3.5-turbo"
        
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=600
        )
        
        response_message = response.choices[0].message
        
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            if tool_call.function.name == "analyze_symptoms":
                args = json.loads(tool_call.function.arguments)
                
                # 1. Prediction Mapping & ML Logic
                if args.get("is_injury"):
                    injury_type = args.get("injury_type", "Injury")
                    ml_result = {
                        "disease": f"Physical Injury ({injury_type})",
                        "confidence": "High",
                        "confidence_score": 1.0,
                        "matched_symptoms": ["injury"],
                        "first_aid": ["Apply R.I.C.E: Rest, Ice, Compression, Elevation.", "Clean and cover any open wounds.", "Do not move the affected area if fracture is suspected."],
                        "home_remedies": ["Use an ice pack for 15-20 minutes every 2 hours."],
                        "routine": ["Rest and avoid putting weight on the injured area."],
                        "medicines": [{"name": "Acetaminophen", "purpose": "Pain relief", "guidance": "Take as directed on package.", "warning": "Do not exceed maximum daily dose."}],
                        "warnings": ["Do not apply heat to a fresh injury."],
                        "when_to_seek_care": ["Severe pain, obvious deformity, bone protruding, or inability to move the limb."],
                        "explanation": ["Based on your reported physical injury, standard first aid applies."]
                    }
                else:
                    try:
                        # Use the demographics from the request payload
                        ml_result = await asyncio.to_thread(
                            get_cached_prediction_metadata,
                            request.age,
                            request.gender,
                            args.get("severity", 1),
                            args.get("duration_days", 1.0),
                            args.get("clinical_symptoms", "")
                        )
                    except Exception as e:
                        print(f"ML Model failed: {e}")
                        ml_result = {
                            "disease": "System Error (ML Failed)",
                            "confidence": "Low",
                            "confidence_score": 0.0,
                            "matched_symptoms": [],
                            "first_aid": [], "home_remedies": [], "routine": [], "medicines": [], "warnings": [], "when_to_seek_care": [], "explanation": []
                        }

                disease = ml_result["disease"]
                
                # Debug Logging
                print(f"--- ML DIAGNOSIS DEBUG ---")
                print(f"Inputs: Age={args.get('age')}, Gender={args.get('gender')}, Clinical={args.get('clinical_symptoms')}")
                print(f"Mapped Symptoms: {ml_result['matched_symptoms']}")
                print(f"Prediction: {disease} (Conf: {ml_result['confidence']}, Score: {ml_result['confidence_score']})")
                
                # 2. Risk Engine
                from app.triage.risk_engine import evaluate_patient_risk
                
                risk_assessment = evaluate_patient_risk(
                    age=request.age,
                    base_severity=args.get("severity", 1),
                    symptoms=args,
                    ml_disease=disease
                )
                diagnosis_data = {
                    "disease": disease,
                    "age": request.age,
                    "gender": "Male" if request.gender == 1 else "Female",
                    "clinical_symptoms": args.get("clinical_symptoms", "None reported"),
                    "is_injury": args.get("is_injury", False),
                    "risk_level": risk_assessment["risk_level"],
                    "risk_score": risk_assessment.get("risk_score", 0), # Added risk score
                    "urgency": risk_assessment["urgency"],
                    "confidence": ml_result["confidence"],
                    "confidence_score": ml_result["confidence_score"],
                    "matched_symptoms": ml_result["matched_symptoms"],
                    "important_features": ml_result["matched_symptoms"], # Explicitly map important features
                    "first_aid": ml_result.get("first_aid", []),
                    "home_remedies": ml_result.get("home_remedies", []),
                    "routine": ml_result.get("routine", []),
                    "medicines": ml_result.get("medicines", []),
                    "warnings": ml_result.get("warnings", []),
                    "when_to_seek_care": ml_result.get("when_to_seek_care", []),
                    "is_high_risk": risk_assessment["risk_level"] in ["High", "Emergency"],
                    "extracted_symptoms": args,
                    "explanation": ml_result.get("explanation", risk_assessment["explanation"]),
                    "emergency": risk_assessment["emergency"]
                }
                
                # Send the function result back to OpenAI to generate a final response
                # CRITICAL: We instruct the AI to provide guidance IMMEDIATELY.
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
                
                # Enhanced Instruction for proactive guidance
                messages.append({
                    "role": "system", 
                    "content": """
                    PROACTIVE GUIDANCE ENFORCEMENT:
                    1. State the diagnosis clearly and empathetically.
                    2. IMMEDIATELY provide the essential First Aid, Home Remedies, and Recovery Routine from the tool output.
                    3. Do NOT wait for the patient to ask for these. 
                    4. Keep instructions clear, bulleted, and in the user's language.
                    """
                })
                
                # Ensure generation is fast with minimal tokens
                final_response = await client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=350
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
            prediction_result = await asyncio.to_thread(
                get_cached_prediction,
                request.Age,
                request.Gender,
                request.Severity,
                request.Duration_Min_Days
            )
            disease = prediction_result.get("condition", "Unknown")
            risk_score = prediction_result.get("risk_score", 0)
            important_features = prediction_result.get("important_features", [])
        except Exception as e:
            print(f"ML Model failed: {e}. Falling back to mock prediction.")
            disease = "Mock Disease (Model Not Loaded)"
            risk_score = 0
            important_features = []
        
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
            
        return PredictResponse(
            predictions=[{"disease": disease, "probability": prediction_result.get("confidence", 0.5)}],
            risk_level=risk_assessment["risk_level"],
            risk_score=risk_score,
            important_features=important_features,
            urgency=risk_assessment["urgency"],
            confidence=risk_assessment["confidence"],
            first_aid=prediction_result.get("first_aid", []),
            home_remedies=prediction_result.get("home_remedies", []),
            routine=prediction_result.get("routine", []),
            medicines=prediction_result.get("medicines", []),
            warnings=prediction_result.get("warnings", []),
            when_to_seek_care=prediction_result.get("when_to_seek_care", []),
            explanation=prediction_result.get("explanation", risk_assessment["explanation"]),
            emergency=risk_assessment["emergency"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
