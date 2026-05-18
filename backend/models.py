from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class Medication(BaseModel):
    id: str
    name: str
    category: str
    dose: float
    unit: str
    route: str
    frequency: str
    start_date: str
    end_date: Optional[str] = None
    status: str
    cycle_number: Optional[int] = None
    discontinued_reason: Optional[str] = None


class AdverseEvent(BaseModel):
    id: str
    term: str
    category: str
    grade: int
    onset: str
    resolution: Optional[str] = None
    outcome: str
    action: str
    related_to_treatment: bool
    date: str
    notes: Optional[str] = None


class ProgressionAssessment(BaseModel):
    id: str
    date: str
    method: str
    response: str
    tumor_burden_mm: float
    percent_change: float
    target_lesions: int
    non_target_lesions: str
    new_lesions: bool
    notes: str


class TreatmentCycle(BaseModel):
    id: str
    cycle_number: int
    start_date: str
    end_date: Optional[str] = None
    status: str
    dose_modification: Optional[str] = None
    delay_reason: Optional[str] = None
    notes: Optional[str] = None


class VitalSigns(BaseModel):
    bp: str
    hr: int
    temp: float
    weight: float
    o2sat: int


class Visit(BaseModel):
    id: str
    date: str
    type: str
    provider: str
    notes: str
    ecog: int
    vitals: VitalSigns


class Patient(BaseModel):
    id: str
    name: str
    age: int
    sex: str
    dob: str
    mrn: str
    trial_id: str
    site: str
    enrollment_date: str
    status: str
    cancer_type: str
    cancer_subtype: str
    stage: str
    biomarkers: list[str]
    ecog: int
    arm: str
    current_cycle: int
    total_cycles: int
    best_response: str
    medications: list[Medication]
    adverse_events: list[AdverseEvent]
    progression_assessments: list[ProgressionAssessment]
    cycles: list[TreatmentCycle]
    visits: list[Visit]
    physician: str
    coordinator: str
    notes: Optional[str] = None


class PatientSummary(BaseModel):
    id: str
    name: str
    age: int
    mrn: str
    cancer_type: str
    stage: str
    status: str
    arm: str
    current_cycle: int
    total_cycles: int
    best_response: str
    ecog: int
    active_ae_count: int
    high_grade_ae_count: int
    physician: str
    enrollment_date: str


class AnalyticsSummary(BaseModel):
    total_patients: int
    active_patients: int
    response_distribution: dict[str, int]
    ae_grade_distribution: dict[str, int]
    cancer_type_distribution: dict[str, int]
    avg_ecog: float
    high_grade_ae_patients: int


class RiskAssessment(BaseModel):
    risk_level: str = Field(description="Overall patient risk level: Low | Moderate | High | Critical")
    key_concerns: list[str] = Field(description="Top 3-5 specific clinical concerns")
    recommendations: list[str] = Field(description="Actionable clinical recommendations")
    alert_flags: list[str] = Field(description="Immediate alerts requiring urgent action")
    summary: str = Field(description="2-3 sentence clinical narrative")


class RiskAssessmentResponse(BaseModel):
    patient_id: str
    patient_name: str
    assessment: RiskAssessment
    cached: bool = False
