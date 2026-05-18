import json
from typing import Optional
import anthropic
from models import Patient, RiskAssessment, RiskAssessmentResponse

CLINICAL_SYSTEM_PROMPT = """You are an expert oncology clinical AI assistant embedded in a clinical trial patient monitoring portal.

Your role is to analyze patient data and produce a structured risk assessment that helps the clinical team prioritize their attention and take appropriate action. You have deep expertise in:
  - Oncology clinical trial management (Phase I-III)
  - CTCAE toxicity grading (Grades 1-5) and clinical significance
  - RECIST 1.1 response criteria (CR/PR/SD/PD/NE)
  - ECOG performance status trajectory
  - Common oncologic drug toxicities and management

Risk Level Definitions:
  - Low: Stable, no significant concerns. Continue current management.
  - Moderate: Active issues requiring monitoring or minor intervention.
  - High: Significant clinical concerns requiring prompt attention or protocol deviation.
  - Critical: Immediate action required. Patient safety at risk or major protocol decision needed.

When assessing risk, consider:
1. Current and recent Grade 3+ adverse events (always at least High risk)
2. Disease progression (PD response = High or Critical depending on context)
3. ECOG trajectory (worsening PS = elevated risk)
4. Cumulative toxicity burden across multiple organ systems
5. Dose modifications or drug holds indicating tolerability issues
6. Vitals abnormalities (HR > 100, SpO2 < 94, fever > 38C)

Always produce actionable, specific recommendations."""


def detect_alerts(patient: Patient) -> list[str]:
    alerts: list[str] = []
    active_high_grade = [
        ae for ae in patient.adverse_events
        if ae.grade >= 3 and ae.outcome in ("Ongoing", "Resolving")
    ]
    for ae in active_high_grade:
        alerts.append(f"ACTIVE Grade {ae.grade} AE: {ae.term} — Action: {ae.action}")
    if patient.best_response == "PD":
        alerts.append("DISEASE PROGRESSION: Best response is PD. Reassess treatment plan.")
    if patient.ecog >= 3:
        alerts.append(f"PERFORMANCE STATUS: ECOG {patient.ecog} — Consider dose modification.")
    if patient.visits:
        latest_visit = max(patient.visits, key=lambda v: v.date)
        vitals = latest_visit.vitals
        if vitals.hr > 100:
            alerts.append(f"VITAL SIGN: Tachycardia HR {vitals.hr} bpm at last visit ({latest_visit.date})")
        if vitals.o2sat < 94:
            alerts.append(f"VITAL SIGN: Low SpO2 {vitals.o2sat}% at last visit ({latest_visit.date})")
        if vitals.temp > 38.0:
            alerts.append(f"VITAL SIGN: Fever {vitals.temp}C at last visit ({latest_visit.date})")
    return alerts


def build_patient_context(patient: Patient) -> str:
    active_aes = [ae for ae in patient.adverse_events if ae.outcome in ("Ongoing", "Resolving")]
    recent_assessment = patient.progression_assessments[-1] if patient.progression_assessments else None
    recent_visit = max(patient.visits, key=lambda v: v.date) if patient.visits else None
    context = {
        "patient_id": patient.id,
        "demographics": {"name": patient.name, "age": patient.age, "sex": patient.sex, "ecog_ps": patient.ecog},
        "cancer": {"type": patient.cancer_type, "subtype": patient.cancer_subtype, "stage": patient.stage, "biomarkers": patient.biomarkers},
        "trial": {"trial_id": patient.trial_id, "arm": patient.arm, "status": patient.status,
                  "current_cycle": patient.current_cycle, "total_cycles": patient.total_cycles,
                  "best_response": patient.best_response},
        "active_medications": [
            {"name": m.name, "category": m.category, "dose": f"{m.dose} {m.unit}", "route": m.route, "frequency": m.frequency}
            for m in patient.medications if m.status == "Active"
        ],
        "active_adverse_events": [
            {"term": ae.term, "grade": ae.grade, "category": ae.category, "onset": ae.onset,
             "outcome": ae.outcome, "action": ae.action, "notes": ae.notes}
            for ae in active_aes
        ],
        "latest_imaging": {
            "date": recent_assessment.date, "method": recent_assessment.method,
            "response": recent_assessment.response, "tumor_burden_mm": recent_assessment.tumor_burden_mm,
            "percent_change": recent_assessment.percent_change, "new_lesions": recent_assessment.new_lesions,
        } if recent_assessment else None,
        "latest_vitals": {
            "date": recent_visit.date, "bp": recent_visit.vitals.bp, "hr": recent_visit.vitals.hr,
            "temp": recent_visit.vitals.temp, "o2sat_pct": recent_visit.vitals.o2sat,
        } if recent_visit else None,
        "clinical_notes": patient.notes,
    }
    return json.dumps(context, indent=2)


def generate_risk_assessment(patient: Patient) -> RiskAssessmentResponse:
    client = anthropic.Anthropic()
    patient_context = build_patient_context(patient)
    response = client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=[{
            "type": "text",
            "text": CLINICAL_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": f"Analyze this patient and provide a structured risk assessment:\n\n{patient_context}"}],
        output_format=RiskAssessment,
    )
    cached = getattr(response.usage, "cache_read_input_tokens", 0) > 0
    return RiskAssessmentResponse(
        patient_id=patient.id,
        patient_name=patient.name,
        assessment=response.parsed_output,
        cached=cached,
    )
