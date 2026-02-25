# AI Multilingual Rural Health Triage Assistant

A full-stack application for rural health triage with voice interaction, multilingual chatbot, and nearby hospital finder.

## Architecture
- **Frontend**: Next.js 14, React, TailwindCSS, ShadCN UI
- **Backend**: FastAPI, Python, Scikit-learn, XGBoost
- **Features**: Live Speech-to-Text, Text-to-Speech, AI disease prediction, Geo-location hospital finding.

## Setup Instructions

### Backend (FastAPI)
1. `cd backend`
2. `python -m venv venv`
3. `source venv/bin/activate` or `.\venv\Scripts\activate` on Windows
4. `pip install -r requirements.txt`
5. Create `.env` from template.
6. `uvicorn app.main:app --reload`

### Frontend (Next.js)
1. `cd frontend`
2. `npm install`
3. Create `.env.local` with API keys.
4. `npm run dev`

### Production / Docker
Refer to `Dockerfile` in `frontend` and `backend` directories.