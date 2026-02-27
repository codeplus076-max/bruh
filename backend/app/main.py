from dotenv import load_dotenv
load_dotenv() # Load at very top

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import os
from app.api.predict import predictor

app = FastAPI(
    title="UPCHAAR - AI Rural Health Triage Assistant API",
    description="Backend for the AI Triage Assistant",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression for large JSON payloads (like Hospital Lists)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)

@app.get("/health")
def health_check():
    """
    Enhanced health check for Render cold starts. 
    Verifies that the ML model has been loaded into memory.
    """
    model_loaded = predictor.is_loaded
    if not model_loaded:
        # Pings the singleton to attempt load
        predictor.load_model()
        
    return {
        "status": "healthy", 
        "ml_model_status": "loaded" if predictor.is_loaded else "unavailable"
    }

from app.api import predict, voice, location, user, report, sessions

app.include_router(predict.router)
app.include_router(voice.router)
app.include_router(location.router)
app.include_router(user.router)
app.include_router(report.router)
app.include_router(sessions.router)
