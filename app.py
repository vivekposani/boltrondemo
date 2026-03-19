import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="BizFlow Integration Monitoring Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp { background: radial-gradient(circle at top left, #09142a 0%, #07101f 45%, #050b17 100%); color: #f4f7ff; }
    div.block-container { padding-top: 1.2rem; padding-bottom: 1rem; max-width: 1500px; }
    .hero-title { font-size: 2.2rem; font-weight: 800; letter-spacing: 0.2px; margin-bottom: 0.15rem; }
    .hero-subtitle { color: #8ea2c9; font-size: 0.95rem; margin-bottom: 1rem; }
    .metric-card, .panel-card { background: linear-gradient(180deg, rgba(9,22,47,0.96), rgba(5,13,29,0.96)); border: 1px solid rgba(111,140,189,0.22); border-radius: 18px; box-shadow: 0 12px 30px rgba(0,0,0,0.28); }
    .metric-card { padding: 1rem 1rem 0.85rem 1rem; min-height: 138px; }
    .panel-card { padding: 1rem 1rem; }
    .metric-label { color: #9db0d3; font-size: 0.78rem; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.8rem; font-weight: 700; }
    .metric-value { font-size: 2.25rem; font-weight: 800; line-height: 1; margin-bottom: 0.55rem; }
    .metric-desc { color: #95a7c9; font-size: 0.9rem; line-height: 1.35; }
    .pill { display: inline-block; padding: 0.28rem 0.7rem; border-radius: 999px; font-size: 0.72rem; font-weight: 700; border: 1px solid rgba(255,255,255,0.16); }
    .issue-card, .recommendation, .insight-box { background: rgba(10,20,40,0.72); border: 1px solid rgba(120,145,190,0.18); border-radius: 16px; padding: 0.95rem 1rem; margin-bottom: 0.8rem; }
    .issue-title { font-size: 1.1rem; font-weight: 800; margin-bottom: 0.15rem; }
    .issue-sub { color: #99abd0; font-size: 0.92rem; margin-bottom: 0.35rem; }
    .section-title { color: #a8badb; font-size: 0.82rem; letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 1rem; font-weight: 800; }
    .recommendation h4 { margin: 0 0 0.2rem 0; font-size: 1.12rem; }
    .recommendation p, .insight-box { color: #97a9cd; font-size: 0.92rem; line-height: 1.65; }
    .stButton button { width: 100%; border-radius: 12px; border: 1px solid rgba(89,127,255,0.45); background: linear-gradient(180deg, #15305e 0%, #10264b 100%); color: #ffffff; font-weight: 700; min-height: 42px; }
    </style>
    """,
    unsafe_allow_html=True,
)

DEFAULT_CSV = Path(__file__).parent / "data" / "blockloadprofile__nfms_audit_sample.csv"

@st.cache_data
def load_csv_data(path_or_buffer):
    df = pd.read_csv(path_or_buffer)
    for col in ["created_ts", "updated_ts"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def build_metric_card(label: str, value: str, desc: str, color: str) -> str:
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{color};">{value}</div>
        <div class="metric-desc">{desc}</div>
    </div>
    """

def plot_failure_distribution(df: pd.DataFrame):
    data = pd.DataFrame({
        "Category": ["Device Not Found in MDM", "Missing / Incomplete MDM Data", "NFMS Push Failures"],
        "Value": [
            int((df["mdm_failure_category"] == "MDM_NOT_FOUND").sum()),
            int((df["mdm_failure_category"] == "MISSING_DATA").sum()),
            int((df["final_failure_source"] == "NFMS").sum()),
        ],
    })
    fig = go.Figure(go.Bar(
        x=data["Value"], y=data["Category"], orientation="h",
        text=data["Value"], textposition="outside",
        marker=dict(color=["#F6A61B", "#37B7FF", "#A98CFF"]),
        hovertemplate="%{y}: %{x}<extra></extra>",
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, tickfont=dict(color="#e8f0ff", size=13), automargin=True),
        height=300,
    )
    return fig

def donut_figure(labels, values, colors, center_text):
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.72,
        marker=dict(colors=colors), textinfo="none",
        hovertemplate="%{label}: %{value}<extra></extra>",
    )])
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.05, x=0.2, font=dict(color="#b6c7ea", size=11)),
        margin=dict(l=0, r=0, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(text=center_text, x=0.5, y=0.5, font=dict(size=26, color="#f3f7ff"), showarrow=False)],
        height=300,
    )
    return fig

def format_issue_cards(df: pd.DataFrame) -> str:
    if df.empty:
        return '<div class="issue-card"><div class="issue-title">No active issues</div><div class="issue-sub">The filtered scope has no failed or deviated devices.</div></div>'
    focus = df[df["final_status"].isin(["FAILED", "SKIPPED"])].copy()
    focus = focus.sort_values(["retry_count", "updated_ts"], ascending=[False, False]).head(4)
    cards = []
    for _, row in focus.iterrows():
        badge_color = "#A98CFF" if row["final_failure_source"] == "NFMS" else "#F6A61B"
        retry_count = int(row["retry_count"]) if pd.notna(row["retry_count"]) else 0
        badge_text = f"Retry {retry_count}" if retry_count > 0 else (row["final_failure_source"] or "Issue")
        cards.append(f"""
            <div class="issue-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                    <div>
                        <div class="issue-title">{row['device_id']}</div>
                        <div class="issue-sub">{row['final_message']}</div>
                    </div>
                    <div class="pill" style="background:{badge_color}22;color:{badge_color};border-color:{badge_color}55;">{badge_text}</div>
                </div>
            </div>
        """)
    return "".join(cards)

def build_recommendations(df: pd.DataFrame, retry_threshold: int) -> str:
    mdm_not_found = int((df["mdm_failure_category"] == "MDM_NOT_FOUND").sum())
    missing_data = int((df["mdm_failure_category"] == "MISSING_DATA").sum())
    nfms_failed = int((df["final_failure_source"] == "NFMS").sum())
    deviated = int((df["retry_count"] > retry_threshold).sum())
    items = [
        ("Review > Retry Devices", f"{deviated} devices exceeded retry threshold. Prioritize them before bulk re-trigger."),
        ("Validate MDM Enrollment", f"{mdm_not_found} devices failed with MDM not found. Confirm meter enrollment and master-data residency."),
        ("Check Payload Completeness", f"{missing_data} flows failed due to missing or incomplete MDM data. Review transformer inputs and field presence."),
        ("Inspect NFMS Errors", f"{nfms_failed} downstream NFMS failures need API and authorization validation before replay."),
    ]
    return "".join([f"<div class='recommendation'><h4>{title}</h4><p>{body}</p></div>" for title, body in items])

def build_insight(df: pd.DataFrame, retry_threshold: int) -> str:
    total = len(df)
    success = int((df["final_status"] == "SUCCESS").sum())
    failed = int((df["final_status"] == "FAILED").sum())
    deviated = int((df["retry_count"] > retry_threshold).sum())
    success_rate = round((success / total) * 100, 1) if total else 0.0
    mdm_failed = int((df["final_failure_source"] == "MDM").sum())
    nfms_failed = int((df["final_failure_source"] == "NFMS").sum())
    return f"""
    <div class="insight-box">
        BizFlow is currently delivering <b>{success_rate}% automation efficiency</b> by successfully integrating
        <b>{success}</b> out of <b>{total}</b> processed devices in the selected scope.
        <br><br>
        The filtered window contains <b>{failed}</b> failed executions, with <b>{mdm_failed}</b> MDM-origin issues
        and <b>{nfms_failed}</b> NFMS downstream failures. <b>{deviated}</b> devices breached the retry threshold
        of <b>{retry_threshold}</b> and should remain in the operator queue until root cause closure.
    </div>
    """
st.markdown('<div class="hero-title"></div>', unsafe_allow_html=True)
st.markdown('<div class="hero-title">BizFlow Integration Monitoring Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">MDM → NFMS | Block Load Profile </div>', unsafe_allow_html=True)


df = load_csv_data(DEFAULT_CSV)

required_columns = {"run_cycle","final_failure_source","retry_count","final_status","mdm_failure_category","final_message","device_id","updated_ts","deviated_flag"}
missing = required_columns - set(df.columns)
if missing:
    st.error(f"CSV is missing required columns: {sorted(missing)}")
    st.stop()

run_cycles = ["ALL"] + sorted([x for x in df["run_cycle"].dropna().astype(str).unique().tolist()])
failure_sources = ["ALL"] + sorted([x for x in df["final_failure_source"].dropna().astype(str).unique().tolist()])

filter_cols = st.columns([2, 2, 2, 1])
with filter_cols[0]:
    selected_run_cycle = st.selectbox("Run Cycle", options=run_cycles, index=0)
with filter_cols[1]:
    selected_failure_source = st.selectbox("Failure Source", options=failure_sources, index=0)
with filter_cols[2]:
    selected_retry_threshold = st.selectbox("Retry Threshold", options=[1, 2, 3, 4, 5], index=2)


filtered = df.copy()
if selected_run_cycle != "ALL":
    filtered = filtered[filtered["run_cycle"] == selected_run_cycle]
if selected_failure_source != "ALL":
    filtered = filtered[filtered["final_failure_source"] == selected_failure_source]

filtered["retry_count"] = pd.to_numeric(filtered["retry_count"], errors="coerce").fillna(0).astype(int)
filtered["deviated_flag"] = filtered["deviated_flag"].fillna(False).astype(bool)

total_devices = len(filtered)
successful_integrations = int((filtered["final_status"] == "SUCCESS").sum())
failed_integrations = int((filtered["final_status"] == "FAILED").sum())
mdm_failures = int((filtered["final_failure_source"] == "MDM").sum())
nfms_push_failures = int(((filtered["final_failure_source"] == "NFMS") & (~filtered["deviated_flag"])).sum())
deviated_list = int((filtered["retry_count"] > selected_retry_threshold).sum())
success_rate = round((successful_integrations / total_devices) * 100) if total_devices else 0
retry_attempts_total = int(filtered["retry_count"].sum())

metric_cols = st.columns(6)
metric_html = [
    build_metric_card("Total Devices Processed", f"{total_devices:,}", "Devices received for scheduled integration run", "#FFFFFF"),
    build_metric_card("Successful Integrations", f"{successful_integrations:,}", f"{success_rate}% overall success rate", "#29D166"),
    build_metric_card("Failed Integrations", f"{failed_integrations:,}", "Actionable failures requiring review", "#FF5F6D"),
    build_metric_card("MDM Failures", f"{mdm_failures:,}", "Master-data lookup or payload issues", "#FFB020"),
    build_metric_card("NFMS Push Failures", f"{nfms_push_failures:,}", "Downstream NFMS push failures below threshold", "#B28CFF"),
    build_metric_card("Deviated List (> retries)", f"{deviated_list:,}", "Persistent failures requiring manual action", "#4DB8FF"),
]
st.markdown('<div class="hero-title"></div>', unsafe_allow_html=True)
for col, html in zip(metric_cols, metric_html):
    with col:
        st.markdown(html, unsafe_allow_html=True)

row2_left, row2_mid, row2_right = st.columns([1.6, 1, 1])

with row2_left:
    st.markdown('<div class="panel-card"><div class="section-title">Failure Category Distribution</div>', unsafe_allow_html=True)
    st.plotly_chart(plot_failure_distribution(filtered), use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

with row2_mid:
    st.markdown('<div class="panel-card"><div class="section-title">Automation Success Rate</div>', unsafe_allow_html=True)
    success_donut = donut_figure(["Success","Failed"], [successful_integrations, max(failed_integrations, 0)], ["#29D166","#24324F"], f"{success_rate}%")
    st.plotly_chart(success_donut, use_container_width=True, config={"displayModeBar": False})
    st.caption("Automation Success Rate")
    st.markdown("</div>", unsafe_allow_html=True)

with row2_right:
    st.markdown('<div class="panel-card"><div class="section-title">Retry Intelligence</div>', unsafe_allow_html=True)
    retry_recovered = int(filtered.loc[(filtered["final_status"] == "SUCCESS") & (filtered["retry_count"] > 0), "retry_count"].sum())
    retry_failed = int(filtered.loc[(filtered["final_status"] == "FAILED") & (filtered["retry_count"] > 0), "retry_count"].sum())
    retry_donut = donut_figure(["Recovered","Failed"], [retry_recovered, max(retry_failed,0)], ["#29D166","#FF5F6D"], f"{retry_attempts_total:,}")
    st.plotly_chart(retry_donut, use_container_width=True, config={"displayModeBar": False})
    st.caption("Total Retry Attempts Executed")
    st.markdown("</div>", unsafe_allow_html=True)

row3_left, row3_mid, row3_right = st.columns([1.1, 1.1, 1])

with row3_left:
    st.markdown('<div class="panel-card"><div style="display:flex;justify-content:space-between;align-items:center;"><div class="section-title">Operator Focus Queue</div><div class="pill" style="background:#6D1B2C55;color:#FF8899;border-color:#FF5F6D55;">High Priority</div></div>', unsafe_allow_html=True)
    st.markdown(format_issue_cards(filtered), unsafe_allow_html=True)
    with st.expander("View all deviated devices"):
        queue = (
            filtered.loc[filtered["retry_count"] > selected_retry_threshold, ["device_id","final_failure_source","retry_count","final_message","updated_ts"]]
            .sort_values(["retry_count","updated_ts"], ascending=[False, False])
            .rename(columns={"device_id":"Device","final_failure_source":"Failure Source","retry_count":"Retry Count","final_message":"Message","updated_ts":"Updated"})
        )
        st.dataframe(queue, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

with row3_mid:
    st.markdown('<div class="panel-card"><div style="display:flex;justify-content:space-between;align-items:center;"><div class="section-title">Recommended Actions</div><div class="pill" style="background:#0E477455;color:#7ED0FF;border-color:#7ED0FF55;">Operator Guide</div></div>', unsafe_allow_html=True)
    st.markdown(build_recommendations(filtered, selected_retry_threshold), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with row3_right:
    st.markdown('<div class="panel-card"><div style="display:flex;justify-content:space-between;align-items:center;"><div class="section-title">Insight</div><div class="pill" style="background:#13593C55;color:#7CE1A7;border-color:#7CE1A755;">Automation Health</div></div>', unsafe_allow_html=True)
    st.markdown(build_insight(filtered, selected_retry_threshold), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

#----------------------Hide Streamlit footer----------------------------
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
#--------------------------------------------------------------------
