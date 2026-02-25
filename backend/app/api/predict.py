from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from app.ml.predictor import DiseasePredictor

router = APIRouter(prefix="", tags=["predict"])

predictor = DiseasePredictor(model_dir=os.getenv("MODEL_DIR", "app/ml"))

class PredictRequest(BaseModel):
    Age: int
    Gender: int
    Severity: int
    Duration_Min_Days: float

class PredictResponse(BaseModel):
    disease: str
    risk_level: str
    triage_guidance: str

@router.post("/predict", response_model=PredictResponse)
async def predict_disease(request: PredictRequest):
    try:
        disease = predictor.predict(
            age=request.Age,
            gender=request.Gender,
            severity=request.Severity,
            duration=request.Duration_Min_Days
        )
        # Determine risk and guidance based on PRD
        risk_level = "High" if request.Severity >= 3 else ("Moderate" if request.Severity == 2 else "Low")
        
        guidance = "Rest and drink plenty of fluids. Follow up with your doctor if symptoms persist."
        if risk_level == "High":
            guidance = "Seek medical attention immediately. Consider going to the nearest hospital."
            
        return PredictResponse(
            disease=disease,
            risk_level=risk_level,
            triage_guidance=guidance
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
