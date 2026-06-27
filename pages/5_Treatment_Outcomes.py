import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import check_password, load_outcomes, load_outcomes_age_sex
from utils.theme import THEME_CSS, PLOTLY_TEMPLATE

st.set_page_config(page_title="Treatment Outcomes | TB Dashboard", page_icon="💊", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

if not check_password():
    st.stop()

st.markdown('<p class="tb-eyebrow">Page 5</p>', unsafe_allow_html=True)
st.title("💊 Treatment Outcomes")
st.markdown("Success, failure, death, and lost-to-follow-up rates among TB patients starting treatment.")
st.markdown("---")

outcomes = load_outcomes()
outc_age_sex = load_outcomes_age_sex()

st.sidebar.header("Filters")
regions = ["All regions"] + sorted(outcomes["region_name"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox("WHO Region", regions)

scope = outcomes if region_sel == "All regions" else outcomes[outcomes["region_name"] == region_sel]

latest_year = scope.dropna(subset=["c_new_tsr"])["year"].max()
latest = scope[scope["year"] == latest_year]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Treatment success (new cases)", f"{latest['c_new_tsr'].mean():.1f}%", help="WHO target: 85%")
with col2:
    st.metric("Treatment success (retreatment)", f"{latest['c_ret_tsr'].mean():.1f}%")
with col3:
    st.metric("Treatment success (TB/HIV)", f"{latest['c_tbhiv_tsr'].mean():.1f}%")

st.markdown("---")

st.subheader("Treatment success rate trend by cohort type")
trend = scope.groupby("year")[["c_new_tsr", "c_ret_tsr", "c_tbhiv_tsr"]].mean().reset_index()
fig = go.Figure()
labels = {"c_new_tsr": "New cases", "c_ret_tsr": "Retreatment", "c_tbhiv_tsr": "TB/HIV co-infected"}
colors = {"c_new_tsr": "#1F5C82", "c_ret_tsr": "#2E8B8B", "c_tbhiv_tsr": "#C0392B"}
for col, label in labels.items():
    fig.add_trace(go.Scatter(x=trend["year"], y=trend[col], name=label, line=dict(color=colors[col], width=3)))
fig.add_hline(y=85, line_dash="dash", line_color="#E0A030", annotation_text="WHO target: 85%")
fig.update_layout(template=PLOTLY_TEMPLATE, height=420, margin=dict(t=10, b=10), yaxis_title="Treatment success rate (%)")
st.plotly_chart(fig, width="stretch")

st.markdown(
    '<div class="tb-callout-red">⚠️ <b>TB/HIV gap:</b> Treatment success rates among TB/HIV co-infected patients '
    "consistently lag behind new and retreatment cohorts, reflecting the compounding burden of managing two "
    "diseases simultaneously, often in resource-constrained settings.</div>",
    unsafe_allow_html=True,
)

st.markdown("---")

# --- Outcome breakdown by sex ---
st.subheader("Treatment outcomes by sex")
sex_data = outc_age_sex[(outc_age_sex["age_group"] == "a") & (outc_age_sex["sex"] != "a")]
sex_agg = sex_data.groupby("sex").agg(coh=("coh", "sum"), succ=("succ", "sum"), fail=("fail", "sum"),
                                       died=("died", "sum"), lost=("lost", "sum")).reset_index()
sex_agg["other"] = (sex_agg["coh"] - sex_agg["succ"] - sex_agg["fail"] - sex_agg["died"] - sex_agg["lost"]).clip(lower=0)
sex_agg["sex"] = sex_agg["sex"].map({"m": "Male", "f": "Female"})

st.caption(
    f"Female cohort: {sex_agg.loc[sex_agg['sex']=='Female', 'coh'].values[0]:,.0f} patients · "
    f"Male cohort: {sex_agg.loc[sex_agg['sex']=='Male', 'coh'].values[0]:,.0f} patients. "
    "Shown below as a % of each group's own cohort, since the two cohorts differ in size."
)

for col in ["succ", "fail", "died", "lost", "other"]:
    sex_agg[col] = sex_agg[col] / sex_agg["coh"] * 100

sex_long = sex_agg.melt(id_vars="sex", value_vars=["succ", "fail", "died", "lost", "other"],
                         var_name="outcome", value_name="pct")
sex_long["outcome"] = sex_long["outcome"].map(
    {"succ": "Success", "fail": "Failed", "died": "Died", "lost": "Lost to follow-up", "other": "Other/not evaluated"})

fig2 = px.bar(sex_long, x="sex", y="pct", color="outcome", barmode="group",
              text=sex_long["pct"].round(1).astype(str) + "%",
              color_discrete_sequence=["#2E8B5A", "#C0392B", "#1A1A1A", "#E0A030", "#8E44AD"])
fig2.update_traces(textposition="outside")
fig2.update_layout(template=PLOTLY_TEMPLATE, height=420, margin=dict(t=30, b=10), yaxis_title="% of cohort")
st.plotly_chart(fig2, width="stretch")

died_f = sex_agg.loc[sex_agg["sex"] == "Female", "died"].values[0]
died_m = sex_agg.loc[sex_agg["sex"] == "Male", "died"].values[0]
st.markdown(
    f'<div class="tb-callout">📌 <b>A modest sex gap in outcomes:</b> Men have a higher death rate during '
    f"treatment ({died_m:.1f}%) than women ({died_f:.1f}%), even after accounting for the larger size of the "
    "male cohort. This lines up with the broader pattern on the Demographics page, where men are also "
    "less likely to seek care promptly.</div>",
    unsafe_allow_html=True,
)

st.caption("Source: WHO Global TB Programme — TB_outcomes.csv, TB_outcomes_age_sex.csv")
