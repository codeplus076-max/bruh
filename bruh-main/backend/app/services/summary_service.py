import json
import os
from typing import Dict, Any, List

_client = None

def get_openai_client():
    global _client
    if _client is not None:
        return _client
    from openai import AsyncOpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key.startswith("sk-or-"):
        _client = AsyncOpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    else:
        _client = AsyncOpenAI(api_key=api_key) if api_key else None
    return _client


async def extract_patient_info(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Extracts structured patient information from the conversation history using an LLM.
    Returns symptoms, duration, severity, and the structured health assessment fields.
    """
    client = get_openai_client()
    if not client:
        return _fallback_extraction()

    model_name = (
        "gpt-4o-mini"
        if not os.getenv("OPENAI_API_KEY", "").startswith("sk-") or "openrouter" in str(client.base_url)
        else "gpt-3.5-turbo"
    )

    history_text = ""
    for msg in messages:
        role = msg.get("role", "unknown")
        if role in ["user", "assistant"]:
            history_text += f"{role.upper()}: {msg.get('content', '')}\n"

    system_prompt = """You are a medical data extraction bot for UPCHAAR — an "assist, not diagnose" AI health assistant.
Extract the following from the conversation history:

1. symptoms           — list of reported symptoms (strings)
2. duration           — how long symptoms lasted (e.g. "2 days", "1 week")
3. severity           — e.g. "Mild", "Moderate", "Severe"
4. assessment         — The overall health assessment text from the AI (verbatim or summarized, NO disease names)
5. urgency_level      — HOME_CARE | URGENT | EMERGENCY (from AI response)
6. reason             — why this urgency level was chosen
7. current_status     — e.g. "Stable", "Worsening", "Improving"
8. timeline           — e.g. "Day 2", "Week 1"
9. first_aid          — list of first-aid instruction strings
10. home_care         — list of home care tip strings
11. otc_guidance      — list of safe OTC guidance strings
12. when_to_seek_care — list of red-flag / emergency warning strings

IMPORTANT:
- Do NOT include disease names, diagnoses, or confidence scores.
- If a field is missing from the conversation, use "" or [].

Respond ONLY with a JSON object:
{
    "symptoms": ["string"],
    "duration": "string",
    "severity": "string",
    "assessment": "string",
    "urgency_level": "string",
    "reason": "string",
    "current_status": "string",
    "timeline": "string",
    "first_aid": ["string"],
    "home_care": ["string"],
    "otc_guidance": ["string"],
    "when_to_seek_care": ["string"]
}
"""

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": history_text}
            ],
            response_format={"type": "json_object"},
            max_tokens=600
        )
        result_content = response.choices[0].message.content
        return json.loads(result_content)

    except Exception as e:
        print(f"Error during extraction: {e}")
        return _fallback_extraction()


def _fallback_extraction() -> Dict[str, Any]:
    """Fallback if OpenAI fails or is not configured."""
    return {
        "symptoms": ["Data extraction failed"],
        "duration": "Unknown",
        "severity": "Unknown",
        "assessment": "",
        "urgency_level": "Unknown",
        "reason": "",
        "current_status": "",
        "timeline": "",
        "first_aid": [],
        "home_care": [],
        "otc_guidance": [],
        "when_to_seek_care": [],
    }


def merge_prediction_results(
    extracted_info: Dict[str, Any],
    prediction_diagnosis: Dict[str, Any],
    patient_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Builds the structured report payload without any disease names, confidence scores,
    or prediction labels — only structured health assessment data.
    """
    def _get(d, *keys):
        for key in keys:
            val = d.get(key) or extracted_info.get(key)
            if val:
                return val
        return ""

    def _get_list(*sources):
        for src in sources:
            val = src if isinstance(src, list) else []
            if val:
                result = []
                for item in val:
                    if isinstance(item, str):
                        result.append(item)
                    elif isinstance(item, dict):
                        name = item.get("name", "")
                        detail = item.get("guidance") or item.get("purpose") or ""
                        result.append(f"{name}: {detail}".strip(": "))
                return result
        return []

    prog = prediction_diagnosis.get("progression") or {}

    return {
        "patient": {
            "name": patient_profile.get("name", "Unknown"),
            "age": str(patient_profile.get("age", "Unknown")),
            "gender": str(patient_profile.get("gender", "Unknown")),
        },
        "clinical_info": {
            "symptoms":          list(set(extracted_info.get("symptoms", []))),
            "duration":          extracted_info.get("duration", "Unknown"),
            "severity":          extracted_info.get("severity", "Unknown"),
            # ── Structured Health Assessment (no disease names) ──
            "assessment":        _get(prediction_diagnosis, "assessment", "status"),
            "urgency_level":     _get(prediction_diagnosis, "urgency", "urgency_level"),
            "reason":            _get(prediction_diagnosis, "reason") or (prediction_diagnosis.get("risk") or {}).get("reason", ""),
            "current_status":    _get(prediction_diagnosis, "current_status") or prog.get("trend", ""),
            "timeline":          _get(prediction_diagnosis, "timeline") or prog.get("day", ""),
            "first_aid":         _get_list(
                                     prediction_diagnosis.get("actions"),
                                     prediction_diagnosis.get("first_aid"),
                                     extracted_info.get("first_aid"),
                                 ),
            "home_care":         _get_list(
                                     prediction_diagnosis.get("home_care"),
                                     prediction_diagnosis.get("homecare"),
                                     extracted_info.get("home_care"),
                                 ),
            "otc_guidance":      _get_list(
                                     prediction_diagnosis.get("medicines"),
                                     prediction_diagnosis.get("otc_guidance"),
                                     extracted_info.get("otc_guidance"),
                                 ),
            "when_to_seek_care": _get_list(
                                     prediction_diagnosis.get("alerts"),
                                     prediction_diagnosis.get("red_flags"),
                                     extracted_info.get("when_to_seek_care"),
                                 ),
            "medical_reasoning": prediction_diagnosis.get("explanation", []),
        }
    }


def generate_summary(merged_data: Dict[str, Any], lang: str = "en") -> str:
    """
    Generates a human-readable text summary. No disease names or confidence scores.
    """
    patient = merged_data.get("patient", {})
    clinical = merged_data.get("clinical_info", {})
    symptoms_str = ", ".join(clinical.get("symptoms", [])) if clinical.get("symptoms") else "None reported"

    if lang == "hi":
        return f"""मरीज़ का विवरण:
नाम: {patient.get('name', 'Unknown')}
उम्र: {patient.get('age', 'Unknown')}
लिंग: {patient.get('gender', 'Unknown')}

लक्षण: {symptoms_str}
अवधि: {clinical.get('duration', 'Unknown')}
गंभीरता: {clinical.get('severity', 'Unknown')}

स्वास्थ्य मूल्यांकन: {clinical.get('assessment', '')}
तत्कालता स्तर: {clinical.get('urgency_level', '')}
वर्तमान स्थिति: {clinical.get('current_status', '')}

यह रिपोर्ट एआई द्वारा तैयार की गई है और यह पेशेवर चिकित्सा सलाह का विकल्प नहीं है।
"""
    elif lang == "mr":
        return f"""रुग्णाचा तपशील:
नाव: {patient.get('name', 'Unknown')}
वय: {patient.get('age', 'Unknown')}
लिंग: {patient.get('gender', 'Unknown')}

लक्षणे: {symptoms_str}
कालावधी: {clinical.get('duration', 'Unknown')}
तीव्रता: {clinical.get('severity', 'Unknown')}

आरोग्य मूल्यांकन: {clinical.get('assessment', '')}
तातडीची पातळी: {clinical.get('urgency_level', '')}
सद्यस्थिती: {clinical.get('current_status', '')}

हा अहवाल एआयने तयार केला आहे आणि तो व्यावसायिक वैद्यकीय सल्ल्याला पर्याय नाही.
"""
    else:
        return f"""Patient Summary:
Name: {patient.get('name', 'Unknown')}
Age: {patient.get('age', 'Unknown')}
Gender: {patient.get('gender', 'Unknown')}

Symptoms: {symptoms_str}
Duration: {clinical.get('duration', 'Unknown')}
Severity: {clinical.get('severity', 'Unknown')}

Health Assessment: {clinical.get('assessment', '')}
Urgency Level: {clinical.get('urgency_level', '')}
Current Status: {clinical.get('current_status', '')}
Reason: {clinical.get('reason', '')}

This summary is AI-assisted and should not replace professional medical diagnosis or treatment.
"""
