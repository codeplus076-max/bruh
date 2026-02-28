import json
import os
from openai import AsyncOpenAI
from typing import Dict, Any, List

openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key and openai_api_key.startswith("sk-or-"):
    client = AsyncOpenAI(
        api_key=openai_api_key,
        base_url="https://openrouter.ai/api/v1"
    )
else:
    client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None


async def extract_patient_info(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Extracts structured patient information from the conversation history using an LLM.
    """
    if not client:
        return _fallback_extraction()
        
    model_name = "gpt-4o-mini" if not os.getenv("OPENAI_API_KEY", "").startswith("sk-") or "openrouter" in str(client.base_url) else "gpt-3.5-turbo"

    # Convert the messages list into a string format for the prompt
    history_text = ""
    for msg in messages:
        role = msg.get("role", "unknown")
        # only keep user messages to extract info, or keep both for context
        if role in ["user", "assistant"]:
            history_text += f"{role.upper()}: {msg.get('content', '')}\n"

    system_prompt = """You are a medical data extraction bot. 
Extract the following clinical information from the conversation history if available:
1. Symptoms (Extract a list of symptoms)
2. Duration of symptoms (e.g., '2 days', '1 week')
3. Severity description (e.g., 'Mild', 'Severe', 'Moderate to Severe', default to 'Unknown')

Respond ONLY with a JSON object exactly following this structure:
{
    "symptoms": ["string"],
    "duration": "string",
    "severity": "string"
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
            max_tokens=300
        )
        
        result_content = response.choices[0].message.content
        extracted_data = json.loads(result_content)
        return extracted_data
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        return _fallback_extraction()


def _fallback_extraction() -> Dict[str, Any]:
    """Fallback if OpenAI fails or is not configured."""
    return {
        "symptoms": ["Data extraction failed"],
        "duration": "Unknown",
        "severity": "Unknown"
    }


def merge_prediction_results(extracted_info: Dict[str, Any], prediction_diagnosis: Dict[str, Any], patient_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combines the extracted patient clinical info, ML model's diagnosis data, and verbatim frontend patient profile.
    """
    # Safely get properties, falling back to empty strings/unknowns
    disease = prediction_diagnosis.get("disease", "Unknown Condition")
    confidence = prediction_diagnosis.get("confidence", "Unknown")
    risk_level = prediction_diagnosis.get("risk_level", "Unknown")
    
    # Extract detailed medical reasoning explicitly added by the bot during ML prediction phase
    explanation = prediction_diagnosis.get("explanation", [])
    
    # If the ML model provided mapped symptoms via 'extracted_symptoms' or 'matched_symptoms'
    ml_symptoms = []
    if "matched_symptoms" in prediction_diagnosis:
        ml_symptoms = prediction_diagnosis["matched_symptoms"]
        
    # Combine symptoms, keeping unique
    all_symptoms = list(set(extracted_info.get("symptoms", []) + ml_symptoms))
    
    return {
        "patient": {
            "name": patient_profile.get("name", "Unknown"),
            "age": str(patient_profile.get("age", "Unknown")),
            "gender": str(patient_profile.get("gender", "Unknown")),
        },
        "clinical_info": {
            "symptoms": all_symptoms,
            "duration": extracted_info.get("duration", "Unknown"),
            "severity": extracted_info.get("severity", "Unknown"),
            "predicted_condition": disease,
            "confidence": confidence,
            "risk_level": risk_level,
            "medical_reasoning": explanation
        }
    }


def generate_summary(merged_data: Dict[str, Any], lang: str = "en") -> str:
    """
    Generates a human-readable text summary from the merged data in the requested language.
    """
    patient = merged_data.get("patient", {})
    clinical = merged_data.get("clinical_info", {})
    
    symptoms_str = ", ".join(clinical.get("symptoms", [])) if clinical.get("symptoms") else "None reported"
    
    if lang == "hi":
        summary = f"""मरीज़ का विवरण:
नाम: {patient.get('name', 'Unknown')}
उम्र: {patient.get('age', 'Unknown')}
लिंग: {patient.get('gender', 'Unknown')}

लक्षण: {symptoms_str}
अवधि: {clinical.get('duration', 'Unknown')}
गंभीरता: {clinical.get('severity', 'Unknown')}

संभावित बीमारी: {clinical.get('predicted_condition', 'Unknown')}
जोखिम का स्तर: {clinical.get('risk_level', 'Unknown')}
आत्मविश्वास: {clinical.get('confidence', 'Unknown')}

यह रिपोर्ट एआई द्वारा तैयार की गई है और यह पेशेवर चिकित्सा सलाह का विकल्प नहीं है।
"""
    elif lang == "mr":
        summary = f"""रुग्णाचा तपशील:
नाव: {patient.get('name', 'Unknown')}
वय: {patient.get('age', 'Unknown')}
लिंग: {patient.get('gender', 'Unknown')}

लक्षणे: {symptoms_str}
कालावधी: {clinical.get('duration', 'Unknown')}
तीव्रता: {clinical.get('severity', 'Unknown')}

संभाव्य आजार: {clinical.get('predicted_condition', 'Unknown')}
धोक्याची पातळी: {clinical.get('risk_level', 'Unknown')}
आत्मविश्वास: {clinical.get('confidence', 'Unknown')}

हा अहवाल एआयने तयार केला आहे आणि तो व्यावसायिक वैद्यकीय सल्ल्याला पर्याय नाही.
"""
    else:
        summary = f"""Patient Summary:
Name: {patient.get('name', 'Unknown')}
Age: {patient.get('age', 'Unknown')}
Gender: {patient.get('gender', 'Unknown')}

Symptoms: {symptoms_str}
Duration: {clinical.get('duration', 'Unknown')}
Severity: {clinical.get('severity', 'Unknown')}

Predicted Condition: {clinical.get('predicted_condition', 'Unknown')}
Risk Level: {clinical.get('risk_level', 'Unknown')}
Confidence: {clinical.get('confidence', 'Unknown')}

This summary is AI-generated and should not replace professional medical diagnosis.
"""
    return summary
