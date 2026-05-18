from fastapi import APIRouter
from models import AnalyticsSummary
from data import get_all_patients

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary():
    patients = get_all_patients()
    response_dist: dict[str, int] = {}
    ae_grade_dist: dict[str, int] = {}
    cancer_type_dist: dict[str, int] = {}
    ecog_total = 0
    high_grade_ae_patients = 0
    for p in patients:
        response_dist[p.best_response] = response_dist.get(p.best_response, 0) + 1
        cancer_type_dist[p.cancer_type] = cancer_type_dist.get(p.cancer_type, 0) + 1
        ecog_total += p.ecog
        has_high_grade = False
        for ae in p.adverse_events:
            label = f"Grade {ae.grade}"
            ae_grade_dist[label] = ae_grade_dist.get(label, 0) + 1
            if ae.grade >= 3:
                has_high_grade = True
        if has_high_grade:
            high_grade_ae_patients += 1
    n = len(patients)
    return AnalyticsSummary(
        total_patients=n,
        active_patients=sum(1 for p in patients if p.status == "Active"),
        response_distribution=response_dist,
        ae_grade_distribution=ae_grade_dist,
        cancer_type_distribution=cancer_type_dist,
        avg_ecog=round(ecog_total / n, 2) if n > 0 else 0.0,
        high_grade_ae_patients=high_grade_ae_patients,
    )
