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
    lat: Optional[float] = None  # User location for hospital search
    lng: Optional[float] = None

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
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearby_hospitals",
            "description": "Find hospitals near the user's location. Call this ONLY when the user explicitly asks for nearby hospitals, clinics, emergency rooms, or wants to know where to go for treatment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "urgency": {
                        "type": "string",
                        "enum": ["emergency", "urgent", "routine"],
                        "description": "How urgently the user needs a hospital."
                    }
                },
                "required": ["urgency"]
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
4. HOSPITALS: Call `find_nearby_hospitals` ONLY if the user explicitly asks for a hospital, clinic, or emergency room near them.
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
                        "matched_symptoms": ["injury"]
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
                            "matched_symptoms": []
                        }

                disease = ml_result["disease"]
                
                # Debug Logging
                print(f"--- ML DIAGNOSIS DEBUG ---")
                print(f"Inputs: Age={args.get('age')}, Gender={args.get('gender')}, Clinical={args.get('clinical_symptoms')}")
                print(f"Mapped Symptoms: {ml_result['matched_symptoms']}")
                print(f"Prediction: {disease} (Conf: {ml_result['confidence']}, Score: {ml_result['confidence_score']})")
                
                # 2. Risk & Guidance Engine
                from app.triage.risk_engine import evaluate_patient_risk
                from app.guidance.guidance_engine import generate_guidance
                
                risk_assessment = evaluate_patient_risk(
                    age=request.age,
                    base_severity=args.get("severity", 1),
                    symptoms=args,
                    ml_disease=disease
                )
                
                # Guidance symptoms list: Combine tools + mapped symptoms + disease
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
                
        # --- HOSPITAL SEARCH TOOL HANDLER ---
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            if tool_call.function.name == "find_nearby_hospitals":
                args = json.loads(tool_call.function.arguments)
                urgency = args.get("urgency", "routine")
                
                if not request.lat or not request.lng:
                    # If user has no location sharing, prompt them to use the hospitals page
                    return ChatResponse(
                        role="assistant",
                        content=(
                            "🏥 I'd love to find hospitals near you, but I need your location. "
                            "Please enable location access on the **Hospitals** page to see nearby hospitals on an interactive map, or share your coordinates with me."
                        )
                    )
                
                # Call the existing hospital service internally
                from app.api.location import _fetch_hospitals_from_google, calculate_distance, infer_specialty
                try:
                    rounded_lat = round(request.lat, 3)
                    rounded_lng = round(request.lng, 3)
                    raw_results = _fetch_hospitals_from_google(rounded_lat, rounded_lng)
                    
                    if not raw_results:
                        return ChatResponse(
                            role="assistant",
                            content="🏥 I couldn't find any hospitals near your location at the moment. Please check the **Hospitals** tab for more options."
                        )
                    
                    # Format top 5 hospitals for a concise chat response
                    top5 = raw_results[:5]
                    hospital_lines = []
                    for i, place in enumerate(top5, 1):
                        geometry = place.get("geometry", {}).get("location", {})
                        h_lat = geometry.get("lat", 0)
                        h_lng = geometry.get("lng", 0)
                        dist = calculate_distance(request.lat, request.lng, h_lat, h_lng)
                        name = place.get("name", "Unknown")
                        address = place.get("vicinity", "")
                        place_id = place.get("place_id", "")
                        maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else f"https://maps.google.com/?q={h_lat},{h_lng}"
                        open_now = place.get("opening_hours", {}).get("open_now")
                        status_emoji = "🟢" if open_now else ("🔴" if open_now is False else "⚪")
                        types = place.get("types", [])
                        specialty = infer_specialty(types, name)
                        hospital_lines.append(
                            f"{i}. **{name}** {status_emoji}\n"
                            f"   📍 {address} ({dist} km away)\n"
                            f"   🏷️ {specialty}\n"
                            f"   🗺️ [Directions]({maps_url})"
                        )
                    
                    urgency_prefix = {
                        "emergency": "🚨 **Emergency!** Here are the nearest hospitals — go immediately!\n\n",
                        "urgent": "⚠️ **Urgent Care Needed.** Here are the nearest hospitals:\n\n",
                        "routine": "🏥 Here are nearby hospitals for your reference:\n\n"
                    }.get(urgency, "🏥 Nearby hospitals:\n\n")
                    
                    hospital_text = urgency_prefix + "\n\n".join(hospital_lines)
                    hospital_text += "\n\n*For more details including ratings, phone numbers and hours, visit the **Hospitals** page.*"
                    
                    return ChatResponse(role="assistant", content=hospital_text)
                    
                except Exception as e:
                    print(f"Hospital search in chat failed: {e}")
                    return ChatResponse(
                        role="assistant",
                        content="🏥 I had trouble fetching nearby hospitals right now. Please visit the **Hospitals** tab for a full map view."
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
            predictions=[{"disease": disease, "probability": prediction_result.get("confidence", 0.5)}],
            risk_level=risk_assessment["risk_level"],
            risk_score=risk_score,
            important_features=important_features,
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
