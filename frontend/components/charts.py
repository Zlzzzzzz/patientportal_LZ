import plotly.graph_objects as go
import streamlit as st

RESPONSE_PALETTE = {"CR": "#10b981", "PR": "#3b82f6", "SD": "#f59e0b", "PD": "#ef4444", "NE": "#94a3b8"}
GRADE_PALETTE = {"Grade 1": "#10b981", "Grade 2": "#f59e0b", "Grade 3": "#f97316", "Grade 4": "#ef4444", "Grade 5": "#7f1d1d"}


def render_response_pie(response_distribution: dict) -> None:
    if not response_distribution:
        return
    labels = list(response_distribution.keys())
    values = list(response_distribution.values())
    colors = [RESPONSE_PALETTE.get(l, "#94a3b8") for l in labels]
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.55,
                           marker=dict(colors=colors), textinfo="label+value",
                           hovertemplate="%{label}: %{value} patients<extra></extra>"))
    fig.update_layout(title="Best Response Distribution", height=320,
                      margin=dict(t=40, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)


def render_ae_bar(ae_grade_distribution: dict) -> None:
    if not ae_grade_distribution:
        return
    ordered = {k: ae_grade_distribution.get(k, 0)
                for k in ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"]
                if k in ae_grade_distribution}
    fig = go.Figure(go.Bar(
        x=list(ordered.keys()), y=list(ordered.values()),
        marker_color=[GRADE_PALETTE.get(k, "#94a3b8") for k in ordered],
        text=list(ordered.values()), textposition="outside",
        hovertemplate="%{x}: %{y} events<extra></extra>"))
    fig.update_layout(title="Adverse Events by CTCAE Grade", height=300,
                      margin=dict(t=40, b=10, l=40, r=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


def render_cancer_type_bar(cancer_type_distribution: dict) -> None:
    if not cancer_type_distribution:
        return
    sorted_types = sorted(cancer_type_distribution.items(), key=lambda x: x[1], reverse=True)
    types = [t[0] for t in sorted_types]
    counts = [t[1] for t in sorted_types]
    fig = go.Figure(go.Bar(
        y=types, x=counts, orientation="h", marker_color="#6366f1",
        text=counts, textposition="outside",
        hovertemplate="%{y}: %{x} patients<extra></extra>"))
    fig.update_layout(title="Patients by Cancer Type",
                      height=max(200, len(types) * 45 + 60),
                      margin=dict(t=40, b=10, l=10, r=30), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
