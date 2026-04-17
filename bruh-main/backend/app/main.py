from dotenv import load_dotenv
load_dotenv()  # Load .env before anything else

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import gc
import os

app = FastAPI(
    title="UPCHAAR - AI Rural Health Triage Assistant API",
    description="Backend for the AI Triage Assistant",
    version="1.0.0"
)

# Global Request Logger
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"DEBUG: Incoming Request: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"DEBUG: Response Status: {response.status_code}")
    # Trigger GC after every response to keep RAM floor low on 512MB limit
    if request.url.path == "/chat":
        gc.collect()
    return response

# GZip must be added first (outermost in LIFO stack) so it compresses full responses
app.add_middleware(GZipMiddleware, minimum_size=2000)

# Configure CORS
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in origins else origins,
    allow_credentials=False if "*" in origins else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.head("/")
def read_root():
    return {"message": "Welcome to UPCHAAR AI Backend!", "health_check": "/health"}

@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Backend is reachable!"}

@app.get("/verify-env")
def verify_env():
    return {
        "openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
        "maps_key_present": bool(os.getenv("MAPS_API_KEY")),
        "firebase_auth_present": bool(os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")),
        "allowed_origins": os.getenv("ALLOWED_ORIGINS", "*")
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"Global Error caught on {request.url.path}: {str(exc)}")
    traceback.print_exc()
    response = JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": str(exc), "path": request.url.path},
    )
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# EXTREME LEAN: Lazy Router Inclusion
@app.on_event("startup")
def include_routers():
    from app.api import predict, voice, location, user, report, sessions, summary
    app.include_router(predict.router)
    app.include_router(summary.router)
    app.include_router(voice.router)
    app.include_router(location.router)
    app.include_router(user.router)
    app.include_router(report.router)
    app.include_router(sessions.router)
    print("BOOT: Ultra-lean router initialization complete.")
