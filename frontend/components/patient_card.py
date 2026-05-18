import streamlit as st

RESPONSE_COLORS = {
    "CR": ("🟢", "Complete Response"),
    "PR": ("🔵", "Partial Response"),
    "SD": ("🟡", "Stable Disease"),
    "PD": ("🔴", "Progressive Disease"),
    "NE": ("⚪", "Not Evaluable"),
}
GRADE_COLORS = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴", 5: "💀"}
STATUS_COLORS = {"Active": "🟢", "Completed": "✅", "Withdrawn": "⬛", "Deceased": "💀", "Screening": "🔵"}


def render_patient_row(p: dict) -> None:
    icon = STATUS_COLORS.get(p["status"], "⚪")
    resp_icon, _ = RESPONSE_COLORS.get(p["best_response"], ("⚪", ""))
    ae_warning = "🚨" if p["high_grade_ae_count"] > 0 else ""
    label = (f"{icon} **{p['name']}** · {p['cancer_type']} {p['stage']} "
             f"· {resp_icon} {p['best_response']} "
             f"· Cycle {p['current_cycle']}/{p['total_cycles']} {ae_warning}")
    with st.expander(label, expanded=False):
        cols = st.columns(4)
        cols[0].metric("MRN", p["mrn"])
        cols[1].metric("ECOG", p["ecog"])
        cols[2].metric("Active AEs", p["active_ae_count"],
                       delta=f"{p['high_grade_ae_count']} Grade 3+" if p["high_grade_ae_count"] else None,
                       delta_color="inverse")
        cols[3].metric("Enrolled", p["enrollment_date"])
        st.caption(f"**Physician:** {p['physician']} · **Arm:** {p['arm']}")


def render_patient_detail(p: dict, alerts: list) -> None:
    resp_icon, resp_label = RESPONSE_COLORS.get(p["best_response"], ("⚪", p["best_response"]))
    st.subheader(f"{p['name']} — {p['cancer_type']} ({p['cancer_subtype']})")
    cols = st.columns(5)
    cols[0].metric("Stage", p["stage"])
    cols[1].metric("ECOG", p["ecog"])
    cols[2].metric("Best Response", f"{resp_icon} {p['best_response']}")
    cols[3].metric("Cycle", f"{p['current_cycle']} / {p['total_cycles']}")
    cols[4].metric("Status", p["status"])
    if alerts:
        st.error(f"⚠️ **{len(alerts)} Alert(s)**")
        for alert in alerts:
            st.warning(alert)
    st.divider()
    tab_overview, tab_meds, tab_aes, tab_imaging, tab_visits = st.tabs(
        ["Overview", "Medications", "Adverse Events", "Imaging / Response", "Visits"])
    with tab_overview:
        _render_overview(p)
    with tab_meds:
        _render_medications(p)
    with tab_aes:
        _render_adverse_events(p)
    with tab_imaging:
        _render_imaging(p)
    with tab_visits:
        _render_visits(p)


def _render_overview(p: dict) -> None:
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Patient Information**")
        for label, val in [("MRN", p["mrn"]), ("Age / Sex", f"{p['age']} / {p['sex']}"),
                           ("Trial ID", p["trial_id"]), ("Site", p["site"]),
                           ("Arm", p["arm"]), ("Enrollment", p["enrollment_date"]),
                           ("Physician", p["physician"]), ("Coordinator", p["coordinator"])]:
            st.markdown(f"- **{label}:** {val}")
    with cols[1]:
        st.markdown("**Cancer Profile**")
        st.markdown(f"- **Type:** {p['cancer_type']}")
        st.markdown(f"- **Subtype:** {p['cancer_subtype']}")
        st.markdown(f"- **Stage:** {p['stage']}")
        st.markdown("**Biomarkers**")
        for bm in p.get("biomarkers", []):
            st.markdown(f"  - {bm}")
        if p.get("notes"):
            st.info(p["notes"])


def _render_medications(p: dict) -> None:
    meds = p.get("medications", [])
    if not meds:
        st.info("No medications recorded.")
        return
    active = [m for m in meds if m["status"] == "Active"]
    historical = [m for m in meds if m["status"] != "Active"]
    if active:
        st.markdown(f"**Current Medications ({len(active)})**")
        for m in active:
            st.markdown(f"- 💊 **{m['name']}** ({m['category']}) — "
                        f"{m['dose']} {m['unit']} {m['route']} {m['frequency']}")
    if historical:
        st.markdown(f"**Historical Medications ({len(historical)})**")
        for m in historical:
            period = f"{m['start_date']} → {m.get('end_date', 'ongoing')}"
            reason = m.get("discontinued_reason", "")
            st.markdown(f"- ~~{m['name']}~~ ({m['status']}) — {period}"
                        + (f" · _{reason}_" if reason else ""))


def _render_adverse_events(p: dict) -> None:
    aes = p.get("adverse_events", [])
    if not aes:
        st.info("No adverse events recorded.")
        return
    active = [ae for ae in aes if ae["outcome"] in ("Ongoing", "Resolving")]
    resolved = [ae for ae in aes if ae["outcome"] not in ("Ongoing", "Resolving")]
    st.markdown("**Grade Summary**")
    grade_cols = st.columns(5)
    for i, grade in enumerate(range(1, 6)):
        count = sum(1 for ae in aes if ae["grade"] == grade)
        icon = GRADE_COLORS.get(grade, "⚪")
        grade_cols[i].metric(f"{icon} Grade {grade}", count)
    if active:
        st.markdown(f"**Active / Ongoing ({len(active)})**")
        for ae in sorted(active, key=lambda x: -x["grade"]):
            icon = GRADE_COLORS.get(ae["grade"], "⚪")
            with st.expander(f"{icon} Grade {ae['grade']} {ae['term']} — {ae['outcome']}", expanded=ae["grade"] >= 3):
                cols = st.columns(3)
                cols[0].markdown(f"**Onset:** {ae['onset']}")
                cols[1].markdown(f"**Action:** {ae['action']}")
                cols[2].markdown(f"**Related:** {'Yes' if ae['related_to_treatment'] else 'No'}")
                if ae.get("notes"):
                    st.caption(ae["notes"])
    if resolved:
        with st.expander(f"Resolved Events ({len(resolved)})", expanded=False):
            for ae in resolved:
                st.markdown(f"- ✅ Grade {ae['grade']} **{ae['term']}** "
                            f"({ae['onset']} → {ae.get('resolution', '—')})")


def _render_imaging(p: dict) -> None:
    assessments = p.get("progression_assessments", [])
    if not assessments:
        st.info("No imaging assessments recorded.")
        return
    for a in assessments:
        resp_icon, _ = RESPONSE_COLORS.get(a["response"], ("⚪", a["response"]))
        with st.container(border=True):
            cols = st.columns(4)
            cols[0].metric("Date", a["date"])
            cols[1].metric("Response", f"{resp_icon} {a['response']}")
            cols[2].metric("Tumor Burden", f"{a['tumor_burden_mm']} mm" if a["tumor_burden_mm"] else "Undetectable")
            change = a["percent_change"]
            cols[3].metric("Change", f"{'+' if change > 0 else ''}{change:.1f}%" if change != 0 else "Baseline")
            st.caption(f"**Method:** {a['method']} · **New Lesions:** {'Yes' if a['new_lesions'] else 'No'} · {a['notes']}")


def _render_visits(p: dict) -> None:
    visits = p.get("visits", [])
    if not visits:
        st.info("No visits recorded.")
        return
    for v in sorted(visits, key=lambda x: x["date"], reverse=True):
        with st.container(border=True):
            cols = st.columns(3)
            cols[0].markdown(f"**{v['date']}** — {v['type']}")
            cols[1].markdown(f"ECOG {v['ecog']} · {v['provider']}")
            cols[2].markdown(f"SpO2 {v['vitals']['o2sat']}% · Temp {v['vitals']['temp']}C")
            vcols = st.columns(5)
            vitals = v["vitals"]
            vcols[0].metric("BP", vitals["bp"])
            vcols[1].metric("HR", f"{vitals['hr']} bpm",
                            delta="High" if vitals["hr"] > 100 else None, delta_color="inverse")
            vcols[2].metric("Temp", f"{vitals['temp']}C",
                            delta="Fever" if vitals["temp"] > 38 else None, delta_color="inverse")
            vcols[3].metric("Weight", f"{vitals['weight']} kg")
            vcols[4].metric("SpO2", f"{vitals['o2sat']}%",
                            delta="Low" if vitals["o2sat"] < 94 else None, delta_color="inverse")
            st.caption(v["notes"])
