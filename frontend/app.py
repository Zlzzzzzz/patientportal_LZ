from typing import Optional
import requests
import streamlit as st
from components.filters import render_filters
from components.patient_card import render_patient_detail, render_patient_row
from components.charts import render_response_pie, render_ae_bar, render_cancer_type_bar
from components.ai_panel import render_ai_risk_panel

API_BASE = "https://patientportallz-production.up.railway.app"

st.set_page_config(page_title="Clinical Trial Portal", page_icon="🧬",
                   layout="wide", initial_sidebar_state="expanded")

USERS = {
    "admin":       {"password": "admin123",  "role": "Administrator",     "name": "Admin User"},
    "dr.okonkwo":  {"password": "trial2024", "role": "Investigator",      "name": "Dr. Sarah Okonkwo"},
    "coordinator": {"password": "coord2024", "role": "Trial Coordinator", "name": "Trial Coordinator"},
}


def render_login() -> None:
    col_l, col_mid, col_r = st.columns([1, 1.2, 1])
    with col_mid:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🧬 Clinical Trial Portal")
        st.markdown("##### Oncology Patient Monitoring System")
        st.divider()
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g. admin")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
        if submitted:
            user = USERS.get(username.lower())
            if user and user["password"] == password:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username.lower()
                st.session_state["user_name"] = user["name"]
                st.session_state["user_role"] = user["role"]
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Demo credentials")
        st.caption("Username: `admin` · Password: `admin123`")
        st.caption("Username: `dr.okonkwo` · Password: `trial2024`")
        st.caption("Username: `coordinator` · Password: `coord2024`")


if not st.session_state.get("authenticated"):
    render_login()
    st.stop()


@st.cache_data(ttl=30)
def fetch_analytics() -> Optional[dict]:
    try:
        r = requests.get(f"{API_BASE}/analytics/summary", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=30)
def fetch_patients(status=None, cancer_type=None, response=None, min_grade=None) -> list:
    params = {}
    if status: params["status"] = status
    if cancer_type: params["cancer_type"] = cancer_type
    if response: params["response"] = response
    if min_grade: params["min_grade"] = min_grade
    try:
        r = requests.get(f"{API_BASE}/patients", params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


@st.cache_data(ttl=30)
def fetch_patient_detail(patient_id: str) -> Optional[dict]:
    try:
        r = requests.get(f"{API_BASE}/patients/{patient_id}", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


@st.cache_data(ttl=30)
def fetch_alerts(patient_id: str) -> list:
    try:
        r = requests.get(f"{API_BASE}/patients/{patient_id}/alerts", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


with st.sidebar:
    st.markdown("## 🧬 Clinical Trial Portal")
    st.caption(f"Signed in as **{st.session_state['user_name']}**")
    st.caption(f"Role: {st.session_state['user_role']}")
    st.divider()

page = st.sidebar.radio("Navigate", ["Dashboard", "Patient Registry", "Patient Detail"])
st.sidebar.divider()
filters = render_filters()
st.sidebar.divider()
if st.sidebar.button("Sign Out", use_container_width=True):
    st.session_state.clear()
    st.rerun()

try:
    requests.get(f"{API_BASE}/health", timeout=2)
    backend_ok = True
except Exception:
    backend_ok = False

if not backend_ok:
    st.error("Cannot connect to backend at https://patientportallz-production.up.railway.app\n\n"
             "Run: `cd ~/clinical-trial-fullstack/backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000`")
    st.stop()

if page == "Dashboard":
    st.title("Trial Dashboard")
    analytics = fetch_analytics()
    patients = fetch_patients()
    if analytics:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Enrolled", analytics["total_patients"])
        col2.metric("Active Patients", analytics["active_patients"])
        col3.metric("High-Grade AE Patients", analytics["high_grade_ae_patients"],
                    delta="Grade 3+" if analytics["high_grade_ae_patients"] > 0 else None, delta_color="inverse")
        col4.metric("Avg ECOG", analytics["avg_ecog"])
        col5.metric("With Alerts", sum(1 for p in patients if p["high_grade_ae_count"] > 0 or p["best_response"] == "PD"))
        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1: render_response_pie(analytics["response_distribution"])
        with c2: render_ae_bar(analytics["ae_grade_distribution"])
        with c3: render_cancer_type_bar(analytics["cancer_type_distribution"])
    st.divider()
    st.subheader("⚠️ Patients Requiring Attention")
    alert_patients = [p for p in patients if p["high_grade_ae_count"] > 0 or p["best_response"] == "PD"]
    if alert_patients:
        for p in alert_patients:
            issues = []
            if p["high_grade_ae_count"] > 0: issues.append(f"{p['high_grade_ae_count']} Grade 3+ AE(s)")
            if p["best_response"] == "PD": issues.append("Progressive Disease")
            st.warning(f"🚨 **{p['name']}** ({p['cancer_type']} {p['stage']}) — {' · '.join(issues)} — ECOG {p['ecog']}")
    else:
        st.success("No patients currently flagged for immediate attention.")

elif page == "Patient Registry":
    st.title("Patient Registry")
    patients = fetch_patients(status=filters["status"], cancer_type=filters["cancer_type"],
                              response=filters["response"], min_grade=filters["min_grade"])
    search = st.text_input("Search by name or MRN", placeholder="e.g. Chen or MRN-7821034")
    if search:
        q = search.lower()
        patients = [p for p in patients if q in p["name"].lower() or q in p["mrn"].lower()]
    st.caption(f"Showing {len(patients)} patient(s)")
    if not patients:
        st.info("No patients match the current filters.")
    else:
        for p in patients:
            render_patient_row(p)

elif page == "Patient Detail":
    st.title("Patient Detail")
    all_patients = fetch_patients()
    if not all_patients:
        st.error("Could not load patient list from backend.")
        st.stop()
    options = {f"{p['name']} ({p['mrn']})": p["id"] for p in all_patients}
    selected_label = st.selectbox("Select Patient", options=list(options.keys()))
    selected_id = options[selected_label]
    patient = fetch_patient_detail(selected_id)
    alerts = fetch_alerts(selected_id)
    if not patient:
        st.error(f"Could not load patient {selected_id}")
        st.stop()
    render_patient_detail(patient, alerts)
    st.divider()
    render_ai_risk_panel(selected_id, patient["name"], API_BASE)
