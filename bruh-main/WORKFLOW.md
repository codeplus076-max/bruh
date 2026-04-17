# System Architecture & Workflow

This document outlines the end-to-end execution flow of the AI Multilingual Rural Health Triage Assistant, ensuring production viability for deployment on Render (Backend) and Vercel (Frontend).

## 1. High-Level User Interaction Flow
1. **Landing:** User opens the Next.js frontend (Vercel).
2. **Localization:** User selects an Indic language (Hindi, Marathi, or English).
3. **Voice/Text Dialogue:** User types or speaks (using browser TTS/STT mapped through the STT endpoint) their symptoms.
4. **LLM Symphony:** The AI organically gathers exactly 4 things: *Age*, *Gender*, *Symptom Duration*, and *Symptom Severity*.
5. **Disease & Risk Prediction:** The AI calls the `analyze_symptoms` backend tool, passing the gathered metrics.
6. **Action Guidance:** The system overlays a dynamic Google Map showing the nearest emergency or standard hospitals based on the AI’s computed risk score.

---

## 2. Backend Processing Pipeline & Clinical ML

**Sequence:** User Payload → FastAPI `/predict` OR `/chat` → ML Layer → Risk Engine → Response Payload.

### Part A: ML Prediction Flow
- Payload strikes `app/api/predict.py`.
- Features (Age, Gender, Severity, Duration) are passed into `app/ml/predictor.py`.
- The `triage_model.joblib` (a lightweight, Github-friendly Random Forest) executes prediction.
- It returns the most statistically likely disease mapping (e.g., *Influenza*, *Heart Disease*).

### Part B: Clinical Risk Stratification Flow (MIMIC-inspired)
Instead of blindly returning the disease, it passes through `app/triage/risk_engine.py`:
1. **Comorbidity Calculation (`comorbidity.py`):** Adds a multiplier if the user is `< 5` or `> 65`.
2. **Physiological Severity (`severity.py`):** Elevates baseline severity based on specific symptom flags (like diarrhea + vomiting = Dehydration risk).
3. **Emergency Override (`emergency_rules.py`):** Hard rules. If symptoms include *chest pain* AND *breathlessness*, the ML prediction is overridden to `EMERGENCY`.
4. **Explainable AI (`explanation.py`):** Translates all triggered rules into a human-readable list (e.g., "Elderly patient status increases overall risk tier.")

---

## 3. Hospital Search & Map Rendering Flow

**Sequence:** Next.js `navigator.geolocation` → FastAPI `/hospitals/nearby` → Google Places API → Dynamic UI Render.

1. **Trigger:** If the risk level is `Moderate`, `High`, or `Emergency`, the frontend prompts permission to access GPS.
2. **Backend API:** FastAPI fetches raw places from Google Maps API.
3. **Enrichment:** `app/api/location.py` dynamically infers the hospital "Specialty", computes exact distance (Km), formats "Open Now / Opening Hours", and extracts the specific Google Map navigation Intent URI.
4. **UI Update:** Next.js `HospitalMap.tsx` and `Map.tsx` render the beautiful, colored markers (Red = Emergency) and full detailed property cards.

---

## 4. Deployment Readiness Checklist

### Backend (Render / Docker)
- [x] Unused dependencies purged (Over 100+ packages removed, shrinking the Docker image drastically).
- [x] Model dimensions aligned and weights pushed (Fast inference, small memory footprint).
- [x] `pip install python-multipart` included natively for voice data uploads.
- [x] `OPENAI_API_KEY` and `MAPS_API_KEY` mapped securely in `.env`.
- [x] **Command:** `gunicorn app.main:app -k uvicorn.workers.UvicornWorker`

### Frontend (Vercel)
- [x] Extraneous legacy mapping layers (`leaflet`, `react-leaflet`) cleanly uninstalled.
- [x] `package.json` optimized for strict `next build`.
- [x] Environment variables `.env.local`: `NEXT_PUBLIC_MAPS_API_KEY`, `NEXT_PUBLIC_API_URL`
- [x] **Command:** `npm run build` & `npm start`

### Identified Risk Areas & Next Steps
- **Rate Limits:** Since we route via our own FastAPI to fetch Google Places, ensure your GCP billing restricts the API Key to your Vercel domains to prevent abuse.
- **Voice TTS Costs:** Moving the Voice TTS pipeline fully to the browser `window.speechSynthesis` (which we did during the `ChatInterface.tsx` update) successfully mitigated backend OpenAI TTS audio costs.
