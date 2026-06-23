import streamlit as st
import plotly.express as px
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import check_password, load_burden, relabel
from utils.theme import THEME_CSS, PLOTLY_TEMPLATE

st.set_page_config(page_title="Geographic Map | TB Dashboard", page_icon="🗺️", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

if not check_password():
    st.stop()

st.markdown('<p class="tb-eyebrow">Page 2</p>', unsafe_allow_html=True)
st.title("🗺️ Geographic Distribution")
st.markdown("Country-level TB burden across 217 countries. Use the year slider to see how the map evolves.")
st.markdown("---")

burden = load_burden()

st.sidebar.header("Filters")
metric_options = {
    "Incidence rate (per 100k)": "e_inc_100k",
    "Mortality rate (per 100k)": "e_mort_100k",
    "TB/HIV incidence (per 100k)": "e_inc_tbhiv_100k",
    "Case detection rate (%)": "c_cdr",
    "Case fatality ratio (%)": "cfr_pct",
}
METRIC_EXPLANATIONS = {
    "Incidence rate (per 100k)": "The estimated number of **new TB cases per 100,000 people** in a country in a given year. This is the standard way to compare disease burden across countries of very different population sizes.",
    "Mortality rate (per 100k)": "The estimated number of **TB deaths per 100,000 people** in a given year.",
    "TB/HIV incidence (per 100k)": "The estimated number of **new TB cases among people also living with HIV**, per 100,000 people. TB/HIV co-infection carries a much higher risk of death than TB alone.",
    "Case detection rate (%)": "The share of **estimated** TB cases that were actually **diagnosed and notified** to health authorities. A low rate means many cases are going undetected, not necessarily that TB is rare.",
    "Case fatality ratio (%)": "The share of people with TB who are estimated to **die from it**, whether or not they were ever diagnosed or treated.",
}
metric_label = st.sidebar.selectbox("Metric to map", list(metric_options.keys()))
metric_col = metric_options[metric_label]

st.markdown(
    f'<div class="tb-callout">📌 <b>What this map shows — {metric_label}:</b> {METRIC_EXPLANATIONS[metric_label]}</div>',
    unsafe_allow_html=True,
)

year_sel = st.sidebar.slider("Year", int(burden["year"].min()), int(burden["year"].max()), int(burden["year"].max()))

df = burden[burden["year"] == year_sel].dropna(subset=[metric_col])

fig = px.choropleth(
    df,
    locations="iso3",
    color=metric_col,
    hover_name="country",
    color_continuous_scale=["#EAF3F7", "#1F5C82", "#0E2A42"],
    labels={metric_col: metric_label},
)
fig.update_layout(template=PLOTLY_TEMPLATE, height=560, margin=dict(t=10, b=10),
                   geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"))
st.plotly_chart(fig, width="stretch")

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.subheader(f"Top 10 — {metric_label} ({year_sel})")
    top10 = df.nlargest(10, metric_col)[["country", metric_col]].reset_index(drop=True)
    st.dataframe(relabel(top10), width="stretch", hide_index=True)
with col2:
    st.subheader(f"Bottom 10 — {metric_label} ({year_sel})")
    bottom10 = df[df[metric_col] > 0].nsmallest(10, metric_col)[["country", metric_col]].reset_index(drop=True)
    st.dataframe(relabel(bottom10), width="stretch", hide_index=True)

st.markdown(
    '<div class="tb-callout">📌 <b>Inequality lens:</b> Eight countries — India, Indonesia, China, the Philippines, '
    "Pakistan, Nigeria, Bangladesh, and the DR Congo — account for roughly two-thirds of the global TB burden, "
    "concentrated overwhelmingly in low- and middle-income settings.</div>",
    unsafe_allow_html=True,
)

st.caption("Source: WHO Global TB Programme — TB_burden_countries.csv")
