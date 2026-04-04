# Upchaar AI Framework

Upchaar AI is a safety-first, dual-mode symptom triage agent designed to evaluate non-diagnostic medical queries efficiently. 

It fuses a deterministic Multi-Stage Python Inference Engine with an LLM-driven conversation logic to protect against over-diagnosis and LLM hallucination.

## 🏗 Architecture Overview

```mermaid
graph TD
    User([User]) --> ChatAPI[/chat Enpoint]
    
    subgraph LLM Conversation Engine
        ChatAPI --> |System Prompt| LLM((OpenAI / LLM))
        LLM --> |Conf < 80% or Missing Data| Q_MODE{Question Mode}
        Q_MODE --> |Ask Follow-ups| User
        LLM --> |Conf > 80% + Full Data| T_MODE{Triage Mode}
    end
    
    subgraph Deterministic Backend
        T_MODE --> |analyze_symptoms tool| Orchestrator[Hybrid Orchestrator]
        Orchestrator --> |Stage 1| NLP(TF-IDF Predictor)
        Orchestrator --> |Stage 2| SafetyFilter(Red Flag Check)
        Orchestrator --> |Stage 3| Rules(Abdominal, Trauma, Worsening)
        Orchestrator --> |Stage 4| SoftMap(Disease -> Soft Lang)
    end
    
    Orchestrator --> |Rules & Urgency JSON| T_MODE
    T_MODE --> |Format Strict Markdown| ChatAPI
```

## 🧠 Core Concepts

### 1. The Dual Mode System
The LLM is strictly restricted into one of two operational states via System Prompting:
- **QUESTION MODE**: Collects critical baseline metrics (Severity, Progression, Functional Ability). Blocks diagnostic output.
- **TRIAGE MODE**: Triggers the deterministic `hybrid_orchestrator.py`. Emits a strictly structured Markdown block containing an `Assessment`, `Urgency`, and `Red Flags`. 

### 2. The Urgency Engine
Hardcoded mappings supersede ML probabilities. Output is strictly bounded:
- **HOME_CARE**: Symptoms are mild, stable, < 48 hours.
- **URGENT**: Worsening symptoms, duration > 48hr, localized abdominal markers, or trauma without deformity.
- **EMERGENCY**: Any true Red Flags (Inability to walk, heavy bleeding, >102F fever).

### 3. Soft Diagnosis (Stage 6)
To prevent the legal liability of AI diagnosis, exact disease maps from the NLP predictor are intercepted by the Orchestrator. `"Appendicitis"` is overridden and returned as `"possible abdominal inflammation"`. 

## 🔌 API Endpoints
- `POST /chat`: Conversational triage endpoint. Maintains session history and dynamically navigates Question/Triage modes.
- `POST /predict`: Standalone parameter check. Detached from LLM, pure deterministic inference pipeline. 

## 🛠 Setup Instructions

### Backend (FastAPI Python)
```bash
cd backend
python -m venv venv
source venv/Scripts/activate # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```

### Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables (.env)
```env
# /backend/.env
OPENAI_API_KEY="sk-..."
```

## 🛡️ Safety Design Principles & Limitations
- **Backend Rules Superiority**: The LLM NEVER generates urgency states. The NLP + Rule engine dictates risk.
- **No Prescriptions**: Explicit prompt conditioning forces the AI to reject steroid/antibiotic recommendations.
- **Limitation**: The initial NLP Model is trained on `Symptom2Disease`, relying heavily on rural NLP phrases. Complex multi-system failures may default to generalized fallback logic.