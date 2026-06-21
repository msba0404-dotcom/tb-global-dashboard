import streamlit as st
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import check_password, load_burden, load_outcomes
from utils.theme import THEME_CSS, PLOTLY_TEMPLATE, COLOR_SEQUENCE

st.set_page_config(page_title="Overview | TB Dashboard", page_icon="📊", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

if not check_password():
    st.stop()

st.markdown('<p class="tb-eyebrow">Page 1</p>', unsafe_allow_html=True)
st.title("📊 Global Overview & KPIs")
st.markdown("Trends in TB incidence, mortality, and treatment success, 2000–2024.")
st.markdown("---")

burden = load_burden()
outcomes = load_outcomes()

# --- Sidebar filters ---
st.sidebar.header("Filters")
regions = ["All regions"] + sorted(burden["region_name"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox("WHO Region", regions)

year_min, year_max = int(burden["year"].min()), int(burden["year"].max())
year_range = st.sidebar.slider("Year range", year_min, year_max, (year_min, year_max))

df = burden[(burden["year"] >= year_range[0]) & (burden["year"] <= year_range[1])]
if region_sel != "All regions":
    df = df[df["region_name"] == region_sel]

latest_year = df["year"].max()
latest = df[df["year"] == latest_year]
first = df[df["year"] == df["year"].min()]

# --- KPI row ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("New cases", f"{latest['e_inc_num'].sum()/1e6:.2f}M", help=f"Estimated incidence, {int(latest_year)}")
with col2:
    st.metric("TB deaths", f"{latest['e_mort_num'].sum()/1e3:.0f}K", help=f"Estimated mortality, {int(latest_year)}")
with col3:
    avg_cfr = latest["cfr_pct"].mean()
    st.metric("Avg. case fatality ratio", f"{avg_cfr:.1f}%" if avg_cfr == avg_cfr else "N/A")
with col4:
    avg_cdr = latest["c_cdr"].mean()
    st.metric("Avg. case detection rate", f"{avg_cdr:.0f}%" if avg_cdr == avg_cdr else "N/A")

st.markdown("---")

# --- Trend chart: incidence & mortality over time ---
trend = df.groupby("year").agg(
    incidence=("e_inc_num", "sum"),
    incidence_lo=("e_inc_num_lo", "sum"),
    incidence_hi=("e_inc_num_hi", "sum"),
    mortality=("e_mort_num", "sum"),
).reset_index()

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Incidence trend")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend["year"], y=trend["incidence_hi"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=trend["year"], y=trend["incidence_lo"], fill="tonexty", line=dict(width=0),
                              fillcolor="rgba(31,92,130,0.15)", showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=trend["year"], y=trend["incidence"], mode="lines+markers",
                              line=dict(color="#1F5C82", width=3), name="Estimated incidence"))
    fig.update_layout(template=PLOTLY_TEMPLATE, height=380, margin=dict(t=10, b=10),
                       yaxis_title="New cases", xaxis_title="Year")
    st.plotly_chart(fig, width="stretch")

with col_b:
    st.subheader("Mortality trend")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=trend["year"], y=trend["mortality"], mode="lines+markers",
                               line=dict(color="#C0392B", width=3), name="Estimated deaths", fill="tozeroy",
                               fillcolor="rgba(192,57,43,0.1)"))
    fig2.update_layout(template=PLOTLY_TEMPLATE, height=380, margin=dict(t=10, b=10),
                        yaxis_title="Deaths", xaxis_title="Year")
    st.plotly_chart(fig2, width="stretch")

st.markdown(
    '<div class="tb-callout">📌 <b>Note:</b> Global incidence dipped sharply in 2020–2021 due to COVID-19 '
    'disruptions to TB case detection and reporting — not an actual decline in disease spread. Cases and deaths '
    "rebounded in 2022–2023 as health systems recovered detection capacity.</div>",
    unsafe_allow_html=True,
)

st.markdown("---")

# --- Treatment success trend ---
st.subheader("Treatment success rate over time")
outc_trend = outcomes.groupby("year")["c_new_tsr"].mean().reset_index().dropna()
fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=outc_trend["year"], y=outc_trend["c_new_tsr"], mode="lines+markers",
                           line=dict(color="#2E8B8B", width=3), name="Treatment success rate"))
fig3.add_hline(y=85, line_dash="dash", line_color="#E0A030", annotation_text="WHO target: 85%")
fig3.update_layout(template=PLOTLY_TEMPLATE, height=380, margin=dict(t=10, b=10),
                    yaxis_title="Treatment success rate (%)", xaxis_title="Year")
st.plotly_chart(fig3, width="stretch")

st.caption("Source: WHO Global TB Programme — TB_burden_countries.csv, TB_outcomes.csv")
