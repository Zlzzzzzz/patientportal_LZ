import streamlit as st

def render_filters() -> dict:
    st.sidebar.header("Filters")
    status = st.sidebar.selectbox("Patient Status",
        ["All", "Active", "Completed", "Withdrawn", "Deceased", "Screening"])
    cancer_type = st.sidebar.selectbox("Cancer Type",
        ["All", "NSCLC", "Colorectal", "Breast", "Prostate", "Melanoma", "AML"])
    response = st.sidebar.selectbox("Best Response", ["All", "CR", "PR", "SD", "PD", "NE"],
        help="RECIST 1.1 response criteria")
    min_grade = st.sidebar.selectbox("Min AE Grade (has at least...)",
        ["Any", "Grade 1+", "Grade 2+", "Grade 3+", "Grade 4+"])
    st.sidebar.divider()
    st.sidebar.caption("Clinical Trial Portal v1.0")
    return {
        "status": None if status == "All" else status,
        "cancer_type": None if cancer_type == "All" else cancer_type,
        "response": None if response == "All" else response,
        "min_grade": None if min_grade == "Any" else int(min_grade.split()[1].replace("+", "")),
    }
