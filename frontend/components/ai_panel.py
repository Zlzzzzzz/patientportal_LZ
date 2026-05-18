import requests
import streamlit as st

RISK_LEVEL_CONFIG = {
    "Low":      {"icon": "🟢"},
    "Moderate": {"icon": "🟡"},
    "High":     {"icon": "🔴"},
    "Critical": {"icon": "🚨"},
}


def render_ai_risk_panel(patient_id: str, patient_name: str, api_base: str) -> None:
    st.subheader("🤖 AI Risk Assessment")
    st.caption("Powered by Claude claude-opus-4-7 with adaptive thinking and prompt caching.")
    if st.button(f"Generate Risk Assessment for {patient_name}", type="primary"):
        with st.spinner("Claude is analyzing the patient record..."):
            _fetch_and_display(patient_id, api_base)
    else:
        st.info("Click the button above to generate an AI-powered risk assessment.")


def _fetch_and_display(patient_id: str, api_base: str) -> None:
    try:
        resp = requests.post(f"{api_base}/ai/risk/{patient_id}", timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach the backend. Is uvicorn running on port 8000?")
        return
    except requests.exceptions.HTTPError as e:
        st.error(f"Backend error: {e.response.text}")
        return
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return

    assessment = data.get("assessment", {})
    risk_level = assessment.get("risk_level", "Unknown")
    cfg = RISK_LEVEL_CONFIG.get(risk_level, {"icon": "⚪"})

    if data.get("cached"):
        st.success("⚡ System prompt served from Anthropic cache")

    if risk_level in ("Critical", "High"):
        st.error(f"{cfg['icon']} Risk Level: **{risk_level}**")
    elif risk_level == "Moderate":
        st.warning(f"{cfg['icon']} Risk Level: **{risk_level}**")
    else:
        st.success(f"{cfg['icon']} Risk Level: **{risk_level}**")

    st.markdown("**Clinical Summary**")
    st.markdown(assessment.get("summary", "—"))

    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Key Concerns**")
        for concern in assessment.get("key_concerns", []):
            st.markdown(f"- {concern}")
        if assessment.get("alert_flags"):
            st.markdown("**⚠️ Alert Flags**")
            for flag in assessment["alert_flags"]:
                st.error(flag)
    with cols[1]:
        st.markdown("**Recommendations**")
        for rec in assessment.get("recommendations", []):
            st.markdown(f"- {rec}")
