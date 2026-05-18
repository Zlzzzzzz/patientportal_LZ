from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from models import Patient, PatientSummary
from data import get_all_patients, get_patient
from services.ai_service import detect_alerts

router = APIRouter(prefix="/patients", tags=["patients"])


def _to_summary(p: Patient) -> PatientSummary:
    active_aes = [ae for ae in p.adverse_events if ae.outcome in ("Ongoing", "Resolving")]
    high_grade = [ae for ae in active_aes if ae.grade >= 3]
    return PatientSummary(
        id=p.id, name=p.name, age=p.age, mrn=p.mrn,
        cancer_type=p.cancer_type, stage=p.stage, status=p.status, arm=p.arm,
        current_cycle=p.current_cycle, total_cycles=p.total_cycles,
        best_response=p.best_response, ecog=p.ecog,
        active_ae_count=len(active_aes), high_grade_ae_count=len(high_grade),
        physician=p.physician, enrollment_date=p.enrollment_date,
    )


@router.get("", response_model=list[PatientSummary])
def list_patients(
    status: Optional[str] = Query(None),
    cancer_type: Optional[str] = Query(None),
    response: Optional[str] = Query(None),
    min_grade: Optional[int] = Query(None, ge=1, le=5),
):
    patients = get_all_patients()
    if status:
        patients = [p for p in patients if p.status.lower() == status.lower()]
    if cancer_type:
        patients = [p for p in patients if cancer_type.lower() in p.cancer_type.lower()]
    if response:
        patients = [p for p in patients if p.best_response == response.upper()]
    if min_grade is not None:
        patients = [p for p in patients if any(ae.grade >= min_grade for ae in p.adverse_events)]
    return [_to_summary(p) for p in patients]


@router.get("/{patient_id}", response_model=Patient)
def get_patient_detail(patient_id: str):
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return patient


@router.get("/{patient_id}/alerts", response_model=list[str])
def get_patient_alerts(patient_id: str):
    patient = get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")
    return detect_alerts(patient)
