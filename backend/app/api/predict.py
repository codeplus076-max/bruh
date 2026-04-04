from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import asyncio
import traceback
from functools import lru_cache

from app.ml.hybrid_orchestrator import HybridOrchestrator

router = APIRouter(prefix="", tags=["predict"])

# ── Orchestrator singleton (lazy-loaded on first call) ────────────────────────
_hybrid_orchestrator = HybridOrchestrator()

# ── Lazy OpenAI client ────────────────────────────────────────────────────────
_client = None

def get_openai_client():
    global _client
    if _client is not None:
        return _client
    from openai import AsyncOpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY missing. Triage will use fallback model.")
        return None
    if api_key.startswith("sk-or-"):
        _client = AsyncOpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    else:
        _client = AsyncOpenAI(api_key=api_key)
    return _client


# ── Cached hybrid inference (args must be hashable) ──────────────────────────
@lru_cache(maxsize=64)
def _cached_hybrid_predict(
    age: int,
    gender: int,
    severity: int,
    duration_days: float,
    clinical_symptoms: str,
    fever: bool,
    cough: bool,
    sore_throat: bool,
    breathlessness: bool,
    chest_pain: bool,
    vomiting: bool,
    diarrhea: bool,
    headache: bool,
    rash: bool,
    joint_pain: bool,
):
    return _hybrid_orchestrator.predict(
        age=age,
        gender=gender,
        severity=severity,
        duration_days=duration_days,
        clinical_symptoms=clinical_symptoms,
        fever=fever,
        cough=cough,
        sore_throat=sore_throat,
        breathlessness=breathlessness,
        chest_pain=chest_pain,
        vomiting=vomiting,
        diarrhea=diarrhea,
        headache=headache,
        rash=rash,
        joint_pain=joint_pain,
    )


# ── Pydantic Models ───────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    Age: int
    Gender: int
    Severity: int
    Duration_Min_Days: float

class LikelyCondition(BaseModel):
    name: str
    raw_name: Optional[str] = None
    confidence_band: str
    score: float
    boosted_by_rules: bool = False

class PredictResponse(BaseModel):
    predictions: List[Dict[str, Any]] = []
    likely_conditions: List[LikelyCondition] = []
    risk_level: str
    risk_score: int
    important_features: List[str]
    urgency: str
    confidence: str
    first_aid: List[str]
    home_remedies: List[str]
    home_care: List[str]
    routine: List[str]
    medicines: List[Dict[str, str]]
    warnings: List[str]
    when_to_seek_care: List[str]
    when_to_seek_help: List[str]
    explanation: List[str]
    safety_disclaimer: str
    blacklist_applied: bool
    rules_applied: List[str]
    emergency: bool

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    language: str = "en"
    age: int
    gender: int  # 1=M, 0=F
    name: str = "Patient"

class ChatResponse(BaseModel):
    role: str
    content: str
    diagnosis: Optional[Dict[str, Any]] = None


# ── OpenAI Function Tools ─────────────────────────────────────────────────────

tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_symptoms",
            "description": "Retrieve structured medical data and trigger diagnostic ML model.",
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"type": "integer", "description": "1 (mild), 2 (moderate), 3 (severe)"},
                    "duration_days": {"type": "integer"},
                    "clinical_symptoms": {
                        "type": "string",
                        "description": "LIST OF SYMPTOMS ONLY as a natural language sentence. No demographic info."
                    },
                    "symptom_location": {"type": "string"},
                    "onset_type": {"type": "string", "enum": ["sudden", "gradual", "unknown"]},
                    "progression": {"type": "string", "enum": ["worsening", "improving", "static", "unknown"]},
                    "associated_symptoms": {"type": "string"},
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
                    "yellowish_skin": {"type": "boolean"},
                },
                "required": ["severity", "duration_days", "clinical_symptoms", "is_injury"]
            }
        }
    }
]


# ── Helper: build diagnosis_data from hybrid result ───────────────────────────

def _build_diagnosis(
    ml_result: dict,
    args: dict,
    age: int,
    gender: int,
) -> dict:
    """
    Merge hybrid ML output with guidance engine output into a single
    UI-safe diagnosis dict. Avoids "You have X" phrasing — all disease
    references use the pre-softened names from the orchestrator.
    """
    likely = ml_result.get("likely_conditions", [])
    top_name = likely[0]["name"] if likely else ml_result.get("disease", "Inconclusive")

    # Explanation lines — what stages fired
    explanation = [
        f"Hybrid NLP pipeline processed: \"{args.get('clinical_symptoms', '')[:60]}\"",
        f"Confidence: {ml_result.get('confidence', 'Low')} ({ml_result.get('confidence_score', 0.0):.2f})",
    ]
    if ml_result.get("blacklist_applied"):
        explanation.append("⚠️ Safety filter: one or more high-severity conditions were suppressed (insufficient duration/severity).")
    for rule in ml_result.get("rules_applied", []):
        explanation.append(f"Clinical rule: {rule}")

    return {
        # Structured hybrid fields (new UI)
        "summary": ml_result.get("summary", "Assessed your symptoms."),
        "likely_conditions": likely,
        "home_care": ml_result.get("home_care", []),
        "precautions": ml_result.get("precautions", []),
        "diet_advice": ml_result.get("diet_advice", []),
        "when_to_seek_help": ml_result.get("when_to_seek_help", []),
        "safety_disclaimer": ml_result.get("safety_disclaimer", "This is not a medical diagnosis."),
        "reasoning_summary": ml_result.get("reasoning_summary", ""),
        "blacklist_applied": ml_result.get("blacklist_applied", False),
        "rules_applied": ml_result.get("rules_applied", []),

        # Backward-compatible fields (existing guidance card still works)
        "disease": top_name,
        "age": age,
        "gender": "Male" if gender == 1 else "Female",
        "clinical_symptoms": args.get("clinical_symptoms", "None reported"),
        "is_injury": args.get("is_injury", False),
        "risk_level": ml_result.get("risk_level", "Low"),
        "risk_score": args.get("severity", 1) * 3,
        "urgency": ml_result.get("urgency", "Home Care"),
        "confidence": ml_result.get("confidence", "Low"),
        "confidence_score": ml_result.get("confidence_score", 0.0),
        "matched_symptoms": ml_result.get("matched_symptoms", []),
        "important_features": ml_result.get("matched_symptoms", []),
        "routine": [ml_result.get("treatment_plan", "Rest")],
        "warnings": [],
        "when_to_seek_care": [],
        "explanation": explanation,
        "emergency": ml_result.get("emergency", False),
        "is_high_risk": ml_result.get("risk_level") in ["High", "Emergency"],
        "extracted_symptoms": args,
    }


# ── /chat Endpoint ────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    start_time = asyncio.get_event_loop().time()
    print(f"DEBUG: /chat — language={request.language}")

    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")

    system_prompt = (
        f"ROLE:\n"
        f"You are 'Upchaar AI Language Assistant' talking to {request.name}. Your job is LIMITED to asking follow-up questions in QUESTION MODE. You DO NOT perform medical reasoning or decision-making. All medical logic is handled by the backend system.\n\n"
        "MODE 1: QUESTION MODE\n"
        "Your task: Ask 1-3 concise, relevant questions ONLY for missing critical info: Severity (1-10 string), Progression (worsening/improving), Functional ability (can walk/eat), or Fever (temp).\n"
        "Rules:\n"
        "- Be short and clear.\n"
        "- Do NOT provide any advice, guess, assume, or mention any diagnosis.\n"
        "- Do NOT output any structured triage format.\n\n"
        "TRIGGER: Call analyze_symptoms IMMEDIATELY if you have collected the baseline data, OR if the user provides conflicting input, OR if a critical RED FLAG is detected (cannot walk, heavy bleeding, difficulty breathing, high fever). If a red flag is present, SKIP Question Mode and strictly call analyze_symptoms immediately.\n"
        f"Reply concisely in {request.language}."
    )

    chat_history = request.messages[-8:] if len(request.messages) > 8 else request.messages
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({"role": msg.role, "content": msg.content})

    try:
        model_name = (
            "gpt-4o-mini"
            if os.getenv("OPENAI_API_KEY", "").startswith("sk-or-")
            else "gpt-3.5-turbo"
        )

        print(f"DEBUG: Calling OpenAI ({model_name}) for tool dispatch...")
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model_name,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=600,
            ),
            timeout=25.0,
        )

        response_message = response.choices[0].message
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"DEBUG: OpenAI responded in {elapsed:.2f}s")

        # ── Tool call branch ──────────────────────────────────────────────────
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            if tool_call.function.name == "analyze_symptoms":
                args = json.loads(tool_call.function.arguments)
                print(f"DEBUG: tool_call args = {json.dumps(args, indent=2)}")

                # ── Injury bypass (no ML needed) ──────────────────────────────
                if args.get("is_injury"):
                    ml_result = {
                        "likely_conditions": [
                            {
                                "name": f"Physical Injury — {args.get('injury_type', 'General')}",
                                "raw_name": "Injury",
                                "confidence_band": "High",
                                "score": 1.0,
                                "boosted_by_rules": False,
                            }
                        ],
                        "disease": f"Physical Injury ({args.get('injury_type', 'General')})",
                        "confidence": "High",
                        "confidence_score": 1.0,
                        "matched_symptoms": ["injury"],
                        "risk_level": "Moderate",
                        "urgency": "URGENT",
                        "emergency": False,
                        "home_care": ["Clean and dress the wound", "Rest the injured area", "Apply ice pack for swelling"],
                        "when_to_seek_help": ["Wound is deep, won't stop bleeding, or shows signs of infection"],
                        "blacklist_applied": False,
                        "rules_applied": ["Injury bypass — ML skipped"],
                        "safety_disclaimer": "Upchaar AI is a triage aid. Please visit a clinic for wound assessment.",
                        "treatment_plan": "Clean wound, rest, monitor for infection",
                        "medicine": "Consult pharmacist for antiseptic and pain relief",
                    }
                else:
                    # ── Hybrid ML inference ───────────────────────────────────
                    print("DEBUG: Starting Hybrid 7-Stage NLP Inference...")
                    step_start = asyncio.get_event_loop().time()
                    try:
                        ml_result = await asyncio.to_thread(
                            _cached_hybrid_predict,
                            request.age,
                            request.gender,
                            int(args.get("severity", 1)),
                            float(args.get("duration_days", 1.0)),
                            str(args.get("clinical_symptoms", "")),
                            bool(args.get("fever", False)),
                            bool(args.get("cough", False)),
                            bool(args.get("sore_throat", False)),
                            bool(args.get("breathlessness", False)),
                            bool(args.get("chest_pain", False)),
                            bool(args.get("vomiting", False)),
                            bool(args.get("diarrhea", False)),
                            bool(args.get("headache", False)),
                            bool(args.get("rash", False)),
                            bool(args.get("joint_pain", False)),
                            progression=str(args.get("progression", "unknown")),
                        )
                        print(f"DEBUG: Hybrid ML took {asyncio.get_event_loop().time() - step_start:.2f}s")
                    except Exception as e:
                        print(f"ERROR: Hybrid ML Pipeline failed: {e}")
                        traceback.print_exc()
                        ml_result = {
                            "likely_conditions": [],
                            "disease": "Analysis Error — please try again",
                            "confidence": "Low",
                            "confidence_score": 0.0,
                            "matched_symptoms": [],
                            "risk_level": "Low",
                            "urgency": "URGENT",
                            "emergency": False,
                            "home_care": [],
                            "when_to_seek_help": [],
                            "blacklist_applied": False,
                            "rules_applied": [],
                            "safety_disclaimer": "An error occurred. Please consult a physician directly.",
                            "treatment_plan": "Consult a local healthcare provider",
                            "medicine": "Consult doctor",
                        }

                print("DEBUG: Generating safe guidance map...")
                step_start = asyncio.get_event_loop().time()
                diagnosis_data = _build_diagnosis(ml_result, args, request.age, request.gender)

                # ── Final LLM call for conversational summary ─────────────────
                FINAL_SYSTEM_PROMPT = f"""ROLE:
You are "Upchaar AI Language Assistant".
Your job is LIMITED to Translating structured triage data into the user's language (TRIAGE MODE).
You DO NOT perform any medical reasoning or decision-making. 
All medical logic is handled by the backend system.

MODE 2: TRANSLATION MODE (TRIAGE MODE)
Your task is to convert the JSON payload into a clean, user-facing response, translated into {request.language}.
Preserve meaning EXACTLY. Format strictly using the defined structure.

OUTPUT FORMAT (STRICT):
# 📋 Upchaar Health Assessment

### 🩺 Assessment
(translated assessment)

### 🏥 Urgency
- **Level:** [HOME_CARE / URGENT / EMERGENCY]
- **Reason:** (translated reason)

### 🏠 Supportive Home Care
* (translated bullet points)

### 💊 Safe Guidance
* (translated safe_otc)

### 🚨 When to Seek Immediate Care
* (translated red_flags)

TRANSLATION RULES (CRITICAL):
- DO NOT change medical meaning. DO NOT add extra advice. DO NOT remove any information. DO NOT introduce disease names.
- KEEP "HOME_CARE / URGENT / EMERGENCY" EXACTLY as-is (do not translate these labels).
- Translate everything else naturally and clearly into {request.language}.

SAFETY GUARDRAILS:
- You are NOT a medical decision-maker. Must not diagnose diseases, suggest antibiotics/steroids, change urgency level, or add new symptoms.
- Respond ONLY with the formatted response. NO extra commentary. NO markdown deviations."""

                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": "analyze_symptoms",
                            "arguments": tool_call.function.arguments
                        }
                    }]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "analyze_symptoms",
                    "content": json.dumps(diagnosis_data, default=str)
                })
                messages.append({"role": "system", "content": FINAL_SYSTEM_PROMPT})

                print("DEBUG: Calling OpenAI (final response)...")
                step_start = asyncio.get_event_loop().time()
                final_response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        max_tokens=800,
                    ),
                    timeout=25.0,
                )
                print(f"DEBUG: Final LLM call took {asyncio.get_event_loop().time() - step_start:.2f}s")

                return ChatResponse(
                    role="assistant",
                    content=final_response.choices[0].message.content,
                    diagnosis=diagnosis_data,
                )

        # ── No tool call — pure conversational reply ──────────────────────────
        return ChatResponse(role="assistant", content=response_message.content)

    except asyncio.TimeoutError:
        print("ERROR: OpenAI request timed out (>25s)")
        raise HTTPException(status_code=504, detail="AI Service Timeout")
    except Exception as e:
        print(f"ERROR: /chat endpoint failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ── /predict Endpoint (standalone, no LLM) ───────────────────────────────────

@router.post("/predict", response_model=PredictResponse)
async def predict_endpoint(request: PredictRequest):
    try:
        ml_result = await asyncio.to_thread(
            _cached_hybrid_predict,
            request.Age,
            request.Gender,
            request.Severity,
            float(request.Duration_Min_Days),
            "",           # no text input for standalone endpoint
            False, False, False, False, False, False, False, False, False, False,
        )
        top_name = (
            ml_result["likely_conditions"][0]["name"]
            if ml_result.get("likely_conditions")
            else ml_result.get("disease", "Inconclusive")
        )
        return PredictResponse(
            predictions=[{"disease": top_name, "confidence": ml_result.get("confidence_score", 0.0)}],
            likely_conditions=ml_result.get("likely_conditions", []),
            risk_level=ml_result.get("risk_level", "Low"),
            risk_score=request.Severity * 3,
            important_features=ml_result.get("matched_symptoms", []),
            urgency=ml_result.get("urgency", "HOME_CARE"),
            confidence=ml_result.get("confidence", "Low"),
            first_aid=[],
            home_remedies=[],
            home_care=ml_result.get("home_care", []),
            routine=[ml_result.get("treatment_plan", "Rest")],
            medicines=[],
            warnings=[],
            when_to_seek_care=[],
            when_to_seek_help=ml_result.get("when_to_seek_help", []),
            explanation=["Hybrid NLP pipeline evaluation"],
            safety_disclaimer=ml_result.get("safety_disclaimer", ""),
            blacklist_applied=ml_result.get("blacklist_applied", False),
            rules_applied=ml_result.get("rules_applied", []),
            emergency=ml_result.get("emergency", False),
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
