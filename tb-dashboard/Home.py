import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import check_password, load_burden, compute_endtb_progress
from utils.theme import THEME_CSS

st.set_page_config(
    page_title="TB Global Burden Dashboard",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(THEME_CSS, unsafe_allow_html=True)

if not check_password():
    st.stop()

# ---- Landing page content (shown after successful login) ----

st.markdown('<p class="tb-eyebrow">WHO Global TB Programme Data · 2000–2024</p>', unsafe_allow_html=True)
st.title("🫁 Tuberculosis Global Burden Dashboard")
st.markdown(
    "##### Tracking inequality, drug resistance, and progress toward WHO's End TB 2030 target across 217 countries"
)

st.markdown("---")

df = load_burden()
progress = compute_endtb_progress()
latest_year = int(df["year"].max())
latest = df[df["year"] == latest_year]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Global incidence", f"{latest['e_inc_num'].sum()/1e6:.1f}M", help=f"Estimated new TB cases, {latest_year}")
with col2:
    st.metric("Global deaths", f"{latest['e_mort_num'].sum()/1e3:.0f}K", help=f"Estimated TB deaths, {latest_year}")
with col3:
    on_track_pct = (progress["risk_category"] == "On track").mean() * 100
    st.metric("Countries on track", f"{on_track_pct:.0f}%", help="Share of countries with ≥50% incidence reduction since 2015")
with col4:
    worsening_pct = (progress["risk_category"] == "Worsening").mean() * 100
    st.metric("Countries worsening", f"{worsening_pct:.0f}%", help="Share of countries where incidence has increased since 2015")

st.markdown("---")

st.markdown(
    """
    ### About this dashboard

    This tool was built as a consulting deliverable to help healthcare decision-makers understand
    the global burden of **tuberculosis (TB)** — one of the world's leading infectious disease
    killers — through the lens of **inequality**: who bears the highest burden, who is being left
    behind in funding and treatment access, and which countries are at risk of missing the
    WHO **End TB Strategy 2030** target of an 80% reduction in incidence from the 2015 baseline.

    **Use the sidebar to navigate between pages:**
    """
)

pages = [
    ("📊 Overview & KPIs", "Global trends in incidence, mortality, and treatment success (2000–2024)"),
    ("🗺️ Geographic Map", "Country-level choropleth maps of TB burden, filterable by year and metric"),
    ("👥 Demographics", "Age and sex breakdowns, plus risk factors (HIV, diabetes, smoking, alcohol)"),
    ("🧬 Disease Subtypes", "Drug-resistant TB (MDR/XDR) burden, resistance surveillance, and outcomes"),
    ("💊 Treatment Outcomes", "Success, failure, death, and lost-to-follow-up rates by cohort and demographic"),
    ("💰 Funding & Inequality", "Budget vs. actual expenditure, funding sources, and burden vs. income"),
    ("🛡️ Latent TB & Prevention", "Household contact tracing and preventive treatment coverage gaps"),
    ("🔮 Predictive Analysis", "Incidence forecasts to 2030 and a risk classifier for End TB target progress"),
]

for icon_title, desc in pages:
    st.markdown(f"**{icon_title}** — {desc}")

st.markdown("---")
st.caption(
    "Data source: WHO Global Tuberculosis Programme (who.int/teams/global-tuberculosis-programme/data). "
    "Built for MSBA382 – Healthcare Analytics."
)
