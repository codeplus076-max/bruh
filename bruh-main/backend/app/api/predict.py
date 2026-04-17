from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
import asyncio
import traceback
import google.generativeai as genai

router = APIRouter(prefix="", tags=["predict"])

_client = None

# System prompts are language-specific but otherwise identical per language.
# Cache them to avoid rebuilding the 5KB+ string on every /chat request.
_PROMPT_CACHE: dict[str, str] = {}

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

class PredictRequest(BaseModel):
    Age: int
    Gender: int
    Severity: int
    Duration_Min_Days: float

class PredictResponse(BaseModel):
    urgency: str
    assessment: str
    reason: str
    homecare: List[str]
    safe_otc: str
    red_flags: List[str]
    language: str

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

tools = [
    {
        "type": "function",
        "function": {
            "name": "analyze_symptoms",
            "description": "Retrieve structured medical data and trigger diagnostic backend model.",
            "parameters": {
                "type": "object",
                "properties": {
                    "severity": {"type": "integer", "description": "1 (mild), 2 (moderate), 3 (severe)"},
                    "duration_days": {"type": "integer"},
                    "clinical_symptoms": {
                        "type": "string",
                        "description": "LIST OF SYMPTOMS ONLY as a natural language sentence. No demographic info."
                    },
                    "progression": {"type": "string", "enum": ["worsening", "improving", "static", "unknown"]},
                    "is_injury": {"type": "boolean"},
                },
                "required": ["severity", "duration_days", "clinical_symptoms"]
            }
        }
    }
]

async def _gemini_triage(args: dict, language: str) -> dict:
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        raise Exception("GEMINI_API_KEY not configured")
    
    genai.configure(api_key=gemini_key)
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
    except Exception:
        model = genai.GenerativeModel('gemini-pro')
        
    prompt = f"""You are the strict Upchaar Backend Triage Engine.
Analyze the following patient data:
{json.dumps(args, indent=2)}

Output ONLY valid JSON matching this exact structure (do NOT use markdown blocks, output raw JSON):
{{
"urgency": "HOME_CARE | URGENT | EMERGENCY",
"assessment": "Brief clinical assessment summary (Do not use disease names)",
"reason": "Why this urgency level was chosen",
"homecare": ["Care tip 1", "Care tip 2", "Care tip 3"],
"safe_otc": "Guidance on over-the-counter relief",
"red_flags": ["Red flag 1", "Red flag 2"],
"possible_causes": [
  {{"label": "General, safe term (e.g. Mild infection-related response)", "likelihood": "Likely | Possible | Less Likely"}}
],
"timeline": {{
  "day": "Day X",
  "trend": "improving | worsening | stable"
}},
"history_summary": "Short summary of past symptoms if noticeable, else blank",
"follow_up_needed": true,
"language": "{language}"
}}

CRITICAL RULES:
1. NEVER diagnose a disease or output a disease name. Use general terms for possible causes.
2. Rely strictly on provided symptoms.
3. Keep it brief and heavily focused on safety triage."""

    print("DEBUG: Calling Gemini API for symptom evaluation...")
    response = await asyncio.to_thread(model.generate_content, prompt)
    
    try:
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        return json.loads(raw_text.strip())
    except Exception as e:
        print(f"Gemini JSON parse error: {e}")
        print(f"Raw Output: {response.text}")
        return {
            "urgency": "URGENT",
            "assessment": "Error analyzing symptoms properly, assume urgency for safety.",
            "reason": "Backend connection unstable or returned invalid format.",
            "homecare": ["Rest", "Monitor symptoms closely"],
            "safe_otc": "Consult pharmacist.",
            "red_flags": ["If symptoms worsen unexpectedly", "If you experience severe pain"],
            "timeline": { "day": "Day 1", "trend": "stable" },
            "history_summary": "",
            "follow_up_needed": False,
            "language": language
        }

async def _format_to_ui_json(markdown_text: str) -> dict:
    """Takes the translated LLM Markdown text and forces it into the UI JSON layout format using OpenAI."""
    client = get_openai_client()
    if not client:
        return {} # Fallback to empty context
    
    prompt = """ROLE
You are "Upchaar Frontend UI Intelligence Engine".
You are responsible for transforming AI responses into a structured, interactive health UI format.

CORE GOAL:
Convert backend Markdown responses into structured JSON for a specialized dashboard interface.

INPUT:
You will receive: AI Markdown response

CRITICAL RULES (NON-NEGOTIABLE):
1. ❌ NEVER ignore Episode Context section
2. ❌ NEVER change wording or hallucinate medical info
3. ✅ ALWAYS extract structured sections exactly as given

MARKDOWN PARSING LOGIC:
You MUST extract these sections:
* "📈 Episode Context"
* "🩺 Current Status" (or Assessment)
* "📈 Progression"
* "🏠 What You Should Do Now" (Supportive Home Care)
* "💊 Safe Relief Options" (Safe Guidance / Medicines)
* "📊 Possible Causes (Non-diagnostic)"
* "🚨 Watch Out For" (When to Seek Immediate Care)

OUTPUT FORMAT (STRICT):
Convert into structured JSON internally:
{
  "status": "Exact Assessment text",
  "progression": {
     "trend": "Improving/Worsening/Stable",
     "day": "Day X"
  },
  "possible_causes": [
     "Exact possible causes bullets"
  ],
  "actions": [
     "Exact home care bullet points"
  ],
  "medicines": [
     "Exact safe OTC medicine bullets"
  ],
  "alerts": [
     "Exact red flags / when to seek care bullets"
  ]
}

If a section is entirely missing from the Markdown, return an empty array [] or empty string "" for its keys."""

    try:
        model_name = "gpt-4o-mini" if os.getenv("OPENAI_API_KEY", "").startswith("sk-or-") else "gpt-3.5-turbo"
        response = await client.chat.completions.create(
            model=model_name,
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": markdown_text}
            ],
            temperature=0.0
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print("Format Error:", e)
        return {}

def build_system_prompt(request_name: str, request_language: str) -> str:
    # Return cached prompt with name injected — prompt body is language-specific but
    # constant, so we cache the expensive string construction.
    if request_language in _PROMPT_CACHE:
        return _PROMPT_CACHE[request_language].replace("__PATIENT_NAME__", request_name, 1)
    
    prompt = _build_raw_prompt(request_name="__PATIENT_NAME__", request_language=request_language)
    _PROMPT_CACHE[request_language] = prompt
    return prompt.replace("__PATIENT_NAME__", request_name, 1)


def _build_raw_prompt(request_name: str, request_language: str) -> str:
    return f"""ROLE:
You are "Upchaar AI Health Copilot with Persistent Memory" talking to {request_name}.

You are NOT a diagnosis engine.
You are a progression-aware, memory-driven health assistant that tracks user health across multiple sessions (Health Episodes).

---
CORE UPGRADE: HEALTH EPISODE MEMORY SYSTEM
You MUST treat every conversation as part of a structured "Health Episode".
Each episode contains:
* Symptom context
* Timeline progression
* Severity changes
* Risk evolution
* Final outcome

EPISODE BEHAVIOR RULES:
1. When a NEW chat starts: Begin symptom tracking.
2. When an EXISTING session is reopened: LOAD previous state, Start with contextual continuity.
3. You MUST track progression across sessions (worsening -> improving -> stable).
4. If symptoms RESOLVE: Provide closure summary.

PROGRESSION MEMORY RULE (CRITICAL):
Always be aware of Previous severity, trend, and risk. Compare with current input.

RISK + MEMORY INTEGRATION:
When assigning risk consider BOTH current symptoms AND historical trend.

CLOSURE WITH MEMORY:
When ending you MUST summarize full episode, store final state mentally, and provide return trigger.

DIFFERENTIATION DIRECTIVE:
You are NOT a chatbot. You are a Health Episode Tracker, Symptom Progression Analyst, and Personal Health Copilot.

SIDEBAR INTEGRATION AWARENESS:
Assume user can view past episodes and reopen them. Avoid repeating full onboarding. Always resume intelligently.

STRICT FAILURE CONDITIONS: If you treat reopened episode as new -> FAIL. If you ignore past progression -> FAIL.

---
🚫 SYSTEM OVERRIDE (STRICT):

You MUST NOT:
* Diagnose diseases
* Generate disease names
* Add medical conclusions
* Suggest new medications
* Add extra sections beyond defined format
* Infer medical meaning from history

If you do → this is a FAILURE.

---
🧠 HISTORY AWARENESS RULE (NEW):

You may receive a summarized user history in the JSON.
Purpose of history:
* Understand progression (better/worse/same)
* Ask smarter follow-up questions
* Improve conversational continuity

STRICT RULES:
* DO NOT use history to change medical meaning
* DO NOT derive conclusions from history
* DO NOT mention diseases based on history
* ONLY use history for comparison (e.g., "compared to yesterday")

---
SYSTEM MODES:
1. QUESTION MODE
2. TRANSLATION MODE
3. FOLLOW-UP MODE

---
MODE 1: QUESTION MODE

Trigger: Missing critical information
Ask 1–3 targeted questions ONLY about:
* Severity (1–10)
* Progression (worsening/improving/static)
* Functional ability (can walk/eat/see normally)
* Fever (temperature if possible)

If history is available: Prefer comparison-based questions
Examples:
* "Compared to yesterday, is your pain better or worse?"
* "Has your condition improved since last time?"

Rules:
* Keep questions short and natural. Do NOT give advice. Do NOT mention urgency.
* TRIGGER: Call analyze_symptoms immediately if you have standard baseline data.

---
MODE 2: TRANSLATION MODE (Only happens after analyze_symptoms)
Trigger: Backend sends structured JSON

YOUR TASK:
* Convert JSON into final user output
* Translate to {request_language} natively
* Preserve meaning EXACTLY

OUTPUT FORMAT (STRICT):

# 📋 Upchaar Health Assessment

### 🩺 Assessment
{{assessment}}

### 📈 Progress Tracking
* Current Status: {{timeline.trend}}
* Timeline: {{timeline.day}}

### 🏠 Supportive Home Care
* {{homecare[0]}}
...

### 💊 Safe Guidance
{{safe_otc}}

### 📊 Possible Causes (Non-diagnostic)
* {{possible_causes...}}

### 🚨 When to Seek Immediate Care
* {{red_flags...}}

---
MODE 3: FOLLOW-UP MODE
Trigger: follow_up_needed = true

Ask ONE follow-up question. Prefer comparison if history exists.
Examples: "Compared to your last update, are your symptoms improving or worsening?"

---
TRANSLATION RULES:
* DO NOT translate: HOME_CARE / URGENT / EMERGENCY, Likely / Possible / Less Likely.

---
🔧 CORRECTION HANDLING (HIGHEST PRIORITY):

If the user corrects any previously provided information (e.g., severity, duration, symptoms, temperature):

1. You MUST explicitly acknowledge the correction:
   Example: "Got it — thanks for correcting that."

2. You MUST overwrite the previous value completely.
   Never use the old value again in any part of the response.

3. You MUST recompute all dependent logic:
   * Risk level
   * Progression trend
   * Guidance and home care
   * Episode summaries

4. You MUST ensure no outdated or incorrect value appears anywhere in the response.

5. You MUST NOT ignore or partially apply corrections.

Failure to handle corrections correctly is a CRITICAL SYSTEM FAILURE.

---
📐 DATA CONSISTENCY RULE:

You MUST ensure internal consistency at all times:
* Do NOT modify or assume user inputs incorrectly.
* Do NOT inflate or change severity values.
* Always reflect EXACTLY what the user provided unless explicitly corrected.

If inconsistency is detected → Ask for clarification BEFORE generating final assessment.

---
⚖️ OBJECTIVE vs SUBJECTIVE PRIORITY RULE:

When there is a conflict between:
* Objective data (e.g., temperature = 104.5°F)
* Subjective input (e.g., severity = 5)

You MUST:
1. Prioritize OBJECTIVE data for risk evaluation.
2. Still display subjective input correctly.
3. Explain reasoning clearly.

Example: "Even though your reported severity is moderate, the measured temperature is in a critical range."

---
🚨 EMERGENCY RESPONSE PROTOCOL:

If the situation qualifies as EMERGENCY, follow this structure STRICTLY:

1. CLEAR ALERT: "This requires immediate medical attention."

2. SPECIFIC REASON: Explain WHY in simple, concrete terms.
   Example: "Fever above 104°F can affect brain and organ function."

3. ACTIONABLE STEPS:
   * Go to nearest hospital immediately
   * Contact emergency services
   * Do not stay alone

4. ESSENTIAL FOLLOW-UP ONLY:
   Ask: "Are you able to reach medical care right now?"

5. DO NOT:
   * Ask casual questions
   * Continue normal conversation flow
   * Provide unnecessary details

---
📈 PROGRESSION INTELLIGENCE RULE:

You MUST interpret progression in context:
* "same" does NOT reduce risk if current condition is already severe
* High-risk values OVERRIDE progression stability

Example: "Even though your symptoms are not worsening, the current level is already critical."

---
📊 RESPONSE PRIORITY LOGIC:

Order of importance:
1. Life-threatening indicators (objective values)
2. Red flag symptoms
3. Progression trend
4. Subjective severity
5. General comfort indicators

---
💀 PATCH FAILURE CONDITIONS:

If you:
* Ignore user correction → FAIL
* Use incorrect values after correction → FAIL
* Give vague emergency reasoning → FAIL
* Ask casual questions during emergency → FAIL
* Misrepresent user input → FAIL

FAILSAFE: If input missing → switch to QUESTION MODE.
"""

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    print(f"DEBUG: /chat — language={request.language}")

    client = get_openai_client()
    if not client:
        raise HTTPException(status_code=503, detail="OpenAI API key not configured")

    system_prompt = build_system_prompt(request.name, request.language)

    chat_history = request.messages[-8:] if len(request.messages) > 8 else request.messages
    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history:
        messages.append({"role": msg.role, "content": msg.content})

    try:
        model_name = "gpt-4o-mini" if os.getenv("OPENAI_API_KEY", "").startswith("sk-or-") else "gpt-3.5-turbo"

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
        
        if response_message.tool_calls:
            tool_call = response_message.tool_calls[0]
            if tool_call.function.name == "analyze_symptoms":
                args = json.loads(tool_call.function.arguments)
                print(f"DEBUG: tool_call args = {json.dumps(args, indent=2)}")

                raw_diagnosis = await _gemini_triage(args, request.language)
                
                # Push back to conversational loop for MODE 2
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
                    "content": json.dumps(raw_diagnosis, default=str)
                })

                final_response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        max_tokens=800,
                    ),
                    timeout=25.0,
                )
                
                final_md = final_response.choices[0].message.content
                
                # Process final UI Format Pass natively
                ui_json = await _format_to_ui_json(final_md)

                # Ensure progression exists
                if not ui_json.get("progression"):
                    ui_json["progression"] = {
                        "trend": gemini_timeline.get("trend", "stable"),
                        "day": gemini_timeline.get("day", "Day 1")
                    }

                # Ensure possible causes exists
                if not ui_json.get("possible_causes"):
                    causes = raw_diagnosis.get("possible_causes", [])
                    ui_json["possible_causes"] = [c.get("label", str(c)) if isinstance(c, dict) else str(c) for c in causes]

                # Ensure actions/alerts are populated
                if not ui_json.get("actions"):
                    ui_json["actions"] = raw_diagnosis.get("homecare", [])

                if not ui_json.get("alerts"):
                    ui_json["alerts"] = raw_diagnosis.get("red_flags", [])

                if not ui_json.get("medicines"):
                    safe_otc = raw_diagnosis.get("safe_otc", "")
                    ui_json["medicines"] = [safe_otc] if safe_otc else []
                # --- END PATCH ---

                return ChatResponse(
                    role="assistant",
                    content=final_md,
                    diagnosis=ui_json,
                )

        return ChatResponse(role="assistant", content=response_message.content)

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="AI Service Timeout")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict", response_model=PredictResponse)
async def predict_endpoint(request: PredictRequest):
    try:
        payload = {
            "severity": request.Severity,
            "duration_days": request.Duration_Min_Days,
            "clinical_symptoms": f"Severity {request.Severity}, Duration {request.Duration_Min_Days} days",
        }
        diagnosis_data = await _gemini_triage(payload, "en")
        return PredictResponse(
            urgency=diagnosis_data.get("urgency", "HOME_CARE"),
            assessment=diagnosis_data.get("assessment", "General assessment complete."),
            reason=diagnosis_data.get("reason", "Based on reported severity."),
            homecare=diagnosis_data.get("homecare", []),
            safe_otc=diagnosis_data.get("safe_otc", "Rest."),
            red_flags=diagnosis_data.get("red_flags", []),
            language=diagnosis_data.get("language", "en")
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
