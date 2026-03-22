from dotenv import load_dotenv
load_dotenv() # Load at very top

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import gc
import os
from app.api.predict import predictor

app = FastAPI(
    title="UPCHAAR - AI Rural Health Triage Assistant API",
    description="Backend for the AI Triage Assistant",
    version="1.0.0"
)

# Configure CORS — Must come before middleware registration
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

if "*" in origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False, # Browsers reject allow_credentials=True when origin is "*"
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/")
def read_root():
    return {"message": "Welcome to UPCHAAR AI Backend!", "health_check": "/health"}

# Add GZip compression only for large JSON payloads (hospital lists etc)
# minimum_size raised to 2000 bytes - avoids compressing small chat/summary responses
app.add_middleware(GZipMiddleware, minimum_size=2000, compresslevel=3)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the exact error securely to the console for Render logs
    print(f"Global Error caught on {request.url.path}: {str(exc)}")
    
    # Return a structured error response that the frontend can parse smoothly
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing your request. Our team has been notified.",
            "path": request.url.path
        },
    )

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

from app.api import predict, voice, location, user, report, sessions, summary

app.include_router(predict.router)
app.include_router(summary.router)
app.include_router(voice.router)
app.include_router(location.router)
app.include_router(user.router)
app.include_router(report.router)
app.include_router(sessions.router)
