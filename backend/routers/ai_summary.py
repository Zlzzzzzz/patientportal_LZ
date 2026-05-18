from fastapi import APIRouter, HTTPException
from models import RiskAssessmentResponse
from data import get_patient
from services.ai_service import generate_risk_assessment

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/risk/{patient_id}", response_model=RiskAssessmentResponse)
def get_ai_risk_assessment(patient_id: str):
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    try:
        return generate_risk_assessment(patient)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")
