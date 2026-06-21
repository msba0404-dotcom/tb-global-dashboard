import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import check_password, load_age_sex
from utils.theme import THEME_CSS, PLOTLY_TEMPLATE, COLOR_SEQUENCE

st.set_page_config(page_title="Demographics | TB Dashboard", page_icon="👥", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

if not check_password():
    st.stop()

st.markdown('<p class="tb-eyebrow">Page 3 · 2024 snapshot</p>', unsafe_allow_html=True)
st.title("👥 Demographics: Age, Sex & Risk Factors")
st.markdown(
    "TB burden by age group, sex, and risk factor. **Note:** this dataset provides a single-year (2024) "
    "demographic snapshot, not a multi-year time series."
)
st.markdown("---")

df = load_age_sex()

st.sidebar.header("Filters")
regions = ["All countries"] + sorted(df["country"].unique().tolist())
country_sel = st.sidebar.selectbox("Country (optional)", regions)

AGE_ORDER = ["0-4", "5-9", "5-14", "10-14", "0-14", "15-19", "15-24", "20-24", "25-34",
             "35-44", "45-54", "55-64", "65plus", "15plus", "18plus", "all"]
SEX_MAP = {"a": "All", "f": "Female", "m": "Male"}
RISK_MAP = {"all": "All TB", "hiv": "HIV", "dia": "Diabetes", "alc": "Alcohol use",
            "smk": "Smoking", "und": "Undernutrition"}

scope = df if country_sel == "All countries" else df[df["country"] == country_sel]

# ---- Sex disparity (global or country) ----
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Burden by sex")
    sex_data = scope[(scope["risk_factor"] == "all") & (scope["age_group"] == "all") & (scope["sex"] != "a")]
    sex_agg = sex_data.groupby("sex")["best"].sum().reset_index()
    sex_agg["sex"] = sex_agg["sex"].map(SEX_MAP)
    fig = px.pie(sex_agg, names="sex", values="best", color="sex",
                 color_discrete_map={"Male": "#1F5C82", "Female": "#E0A030"}, hole=0.45)
    fig.update_layout(template=PLOTLY_TEMPLATE, height=340, margin=dict(t=10, b=10))
    st.plotly_chart(fig, width="stretch")

with col2:
    st.subheader("Burden by risk factor")
    risk_data = scope[(scope["age_group"] == "all") & (scope["sex"] == "a") & (scope["risk_factor"] != "all")]
    risk_agg = risk_data.groupby("risk_factor")["best"].sum().reset_index()
    risk_agg["risk_factor"] = risk_agg["risk_factor"].map(RISK_MAP)
    risk_agg = risk_agg.sort_values("best", ascending=True)
    fig2 = px.bar(risk_agg, x="best", y="risk_factor", orientation="h", color_discrete_sequence=["#2E8B8B"])
    fig2.update_layout(template=PLOTLY_TEMPLATE, height=340, margin=dict(t=10, b=10),
                        xaxis_title="Estimated TB cases attributable", yaxis_title="")
    st.plotly_chart(fig2, width="stretch")

st.markdown("---")

# ---- Age pyramid ----
st.subheader("Age distribution of TB incidence")
fine_ages = ["0-4", "5-14", "15-24", "25-34", "35-44", "45-54", "55-64", "65plus"]
age_data = scope[(scope["risk_factor"] == "all") & (scope["sex"] != "a") & (scope["age_group"].isin(fine_ages))]
age_agg = age_data.groupby(["age_group", "sex"])["best"].sum().reset_index()
age_agg["sex"] = age_agg["sex"].map(SEX_MAP)
age_agg["age_group"] = age_agg["age_group"].astype("category").cat.set_categories(fine_ages, ordered=True)
age_agg = age_agg.sort_values("age_group")
age_agg.loc[age_agg["sex"] == "Male", "best"] *= -1

fig3 = go.Figure()
for sex_name, color in [("Female", "#E0A030"), ("Male", "#1F5C82")]:
    d = age_agg[age_agg["sex"] == sex_name]
    fig3.add_trace(go.Bar(y=d["age_group"], x=d["best"], name=sex_name, orientation="h",
                           marker_color=color))
fig3.update_layout(template=PLOTLY_TEMPLATE, height=420, barmode="overlay", margin=dict(t=10, b=10),
                    xaxis_title="Estimated cases (Male ← | → Female)", yaxis_title="Age group")
st.plotly_chart(fig3, width="stretch")

st.markdown(
    '<div class="tb-callout">📌 <b>Gender gap:</b> WHO estimates that approximately 54% of people who develop TB '
    "globally are men, compared to 35% women and 11% children — a disparity driven by both biological and "
    "behavioral/structural factors, including men's lower likelihood of seeking care.</div>",
    unsafe_allow_html=True,
)

st.caption("Source: WHO Global TB Programme — TB_burden_age_sex.csv (2024 estimates)")
