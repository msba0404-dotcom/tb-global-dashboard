import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import (
    check_password, load_burden, load_outcomes, load_age_sex,
    load_ltbi, load_budget, load_expenditure, load_outcomes_age_sex,
)
from utils.theme import THEME_CSS, PLOTLY_TEMPLATE

st.set_page_config(page_title="Summary | TB Dashboard", page_icon="🗂️", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

if not check_password():
    st.stop()

st.markdown('<p class="tb-eyebrow">Summary view</p>', unsafe_allow_html=True)
st.title("🫁 TB Global Burden — Key Findings")
st.markdown(
    "A consolidated view pulling the headline charts from across the dashboard's 8 pages. "
    "Scroll for the full set, or visit individual pages for filters and detail."
)
st.markdown("---")

# ---------- Load everything once ----------
burden = load_burden()
outcomes = load_outcomes()
age_sex = load_age_sex()
ltbi = load_ltbi()
budget = load_budget()
expenditure = load_expenditure()
outc_age_sex = load_outcomes_age_sex()

latest_year = int(burden["year"].max())
latest = burden[burden["year"] == latest_year]


def style_chart(fig, height=380, legend_bottom=False):
    fig.update_layout(template=PLOTLY_TEMPLATE, height=height, margin=dict(t=40, b=20, l=10, r=10))
    if legend_bottom:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5))
    return fig


# ============================================================
# SECTION 1 — Overview
# ============================================================
st.header("📊 Overview")

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("New cases", f"{latest['e_inc_num'].sum()/1e6:.1f}M", help=f"{latest_year}")
with k2:
    st.metric("TB deaths", f"{latest['e_mort_num'].sum()/1e3:.0f}K", help=f"{latest_year}")
with k3:
    st.metric("Avg. case fatality ratio", f"{latest['cfr_pct'].mean():.1f}%")
with k4:
    st.metric("Avg. case detection rate", f"{latest['c_cdr'].mean():.0f}%")

st.markdown("")

trend = burden.groupby("year").agg(incidence=("e_inc_num", "sum"), mortality=("e_mort_num", "sum")).reset_index()
col1, col2 = st.columns(2)
with col1:
    st.subheader("Incidence trend")
    fig_inc = go.Figure(go.Scatter(x=trend["year"], y=trend["incidence"], mode="lines+markers",
                                    line=dict(color="#1F5C82", width=3)))
    fig_inc = style_chart(fig_inc)
    fig_inc.update_layout(yaxis_title="New cases")
    st.plotly_chart(fig_inc, width="stretch")
with col2:
    st.subheader("Mortality trend")
    fig_mort = go.Figure(go.Scatter(x=trend["year"], y=trend["mortality"], mode="lines+markers",
                                     line=dict(color="#C0392B", width=3)))
    fig_mort = style_chart(fig_mort)
    fig_mort.update_layout(yaxis_title="Deaths")
    st.plotly_chart(fig_mort, width="stretch")

st.subheader("Treatment success rate over time")
outc_trend = outcomes.groupby("year")["c_new_tsr"].mean().reset_index().dropna()
fig_tsr = go.Figure()
fig_tsr.add_trace(go.Scatter(x=outc_trend["year"], y=outc_trend["c_new_tsr"], mode="lines+markers",
                              line=dict(color="#2E8B8B", width=3)))
fig_tsr.add_hline(y=85, line_dash="dash", line_color="#E0A030", annotation_text="WHO target: 85%")
fig_tsr = style_chart(fig_tsr, height=340)
fig_tsr.update_layout(yaxis_title="Treatment success rate (%)")
st.plotly_chart(fig_tsr, width="stretch")

st.markdown("---")

# ============================================================
# SECTION 2 — Geographic distribution
# ============================================================
st.header("🗺️ Geographic Distribution")
st.caption(f"Incidence per 100,000 population, {latest_year}")

map_df = latest.dropna(subset=["e_inc_100k"])
fig_map = px.choropleth(
    map_df, locations="iso3", color="e_inc_100k", hover_name="country",
    color_continuous_scale=["#EAF3F7", "#1F5C82", "#0E2A42"],
    labels={"e_inc_100k": "Incidence (per 100k)"},
)
fig_map.update_layout(
    template=PLOTLY_TEMPLATE, height=520, margin=dict(t=10, b=10, l=10, r=10),
    geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
)
st.plotly_chart(fig_map, width="stretch")

st.markdown("---")

# ============================================================
# SECTION 3 — Demographics
# ============================================================
st.header("👥 Demographics")
st.caption(f"Age, sex, and risk factor breakdown — {age_sex['year'].iloc[0]} snapshot")

col3, col4, col5 = st.columns(3)
with col3:
    st.subheader("Burden by sex")
    sex_data = age_sex[(age_sex["risk_factor"] == "all") & (age_sex["age_group"] == "all") & (age_sex["sex"] != "a")]
    sex_agg = sex_data.groupby("sex")["best"].sum().reset_index()
    sex_agg["sex"] = sex_agg["sex"].map({"m": "Male", "f": "Female"})
    fig_sex = px.pie(sex_agg, names="sex", values="best", color="sex",
                      color_discrete_map={"Male": "#1F5C82", "Female": "#E0A030"}, hole=0.45)
    fig_sex = style_chart(fig_sex, height=360)
    st.plotly_chart(fig_sex, width="stretch")

with col4:
    st.subheader("Burden by risk factor")
    RISK_MAP = {"hiv": "HIV", "dia": "Diabetes", "alc": "Alcohol use", "smk": "Smoking", "und": "Undernutrition"}
    risk_data = age_sex[(age_sex["age_group"] == "all") & (age_sex["sex"] == "a") & (age_sex["risk_factor"] != "all")]
    risk_agg = risk_data.groupby("risk_factor")["best"].sum().reset_index()
    risk_agg["risk_factor"] = risk_agg["risk_factor"].map(RISK_MAP)
    risk_agg = risk_agg.sort_values("best")
    fig_risk = px.bar(risk_agg, x="best", y="risk_factor", orientation="h", color_discrete_sequence=["#2E8B8B"])
    fig_risk = style_chart(fig_risk, height=360)
    fig_risk.update_layout(xaxis_title="Estimated cases", yaxis_title="")
    st.plotly_chart(fig_risk, width="stretch")

with col5:
    st.subheader("Age distribution (pyramid)")
    fine_ages = ["0-4", "5-14", "15-24", "25-34", "35-44", "45-54", "55-64", "65plus"]
    age_data = age_sex[(age_sex["risk_factor"] == "all") & (age_sex["sex"] != "a") & (age_sex["age_group"].isin(fine_ages))]
    age_agg = age_data.groupby(["age_group", "sex"])["best"].sum().reset_index()
    age_agg["sex"] = age_agg["sex"].map({"m": "Male", "f": "Female"})
    age_agg["age_group"] = age_agg["age_group"].astype("category").cat.set_categories(fine_ages, ordered=True)
    age_agg = age_agg.sort_values("age_group")
    age_agg.loc[age_agg["sex"] == "Male", "best"] *= -1

    fig_age = go.Figure()
    for sex_name, color in [("Female", "#E0A030"), ("Male", "#1F5C82")]:
        d = age_agg[age_agg["sex"] == sex_name]
        fig_age.add_trace(go.Bar(y=d["age_group"], x=d["best"], name=sex_name, orientation="h",
                                  marker_color=color))
    fig_age = style_chart(fig_age, height=360, legend_bottom=True)
    fig_age.update_layout(barmode="overlay", xaxis_title="Estimated cases (Male ← | → Female)", yaxis_title="")
    st.plotly_chart(fig_age, width="stretch")

st.markdown("---")

# ============================================================
# SECTION 4 — Disease subtypes & treatment outcomes
# ============================================================
st.header("🧬 Disease Subtypes & Treatment Outcomes")

col6, col7 = st.columns(2)
with col6:
    st.subheader("MDR-TB vs. XDR-TB outcomes (% of cohort)")
    if 2022 in outcomes["year"].values:
        oc_year_val = 2022
    else:
        oc_year_val = outcomes.dropna(subset=["mdr_coh"])["year"].max()
    oc_year = outcomes[outcomes["year"] == oc_year_val]

    def outcome_pcts(prefix):
        coh = oc_year[f"{prefix}_coh"].sum()
        succ = oc_year[f"{prefix}_succ"].sum()
        died = oc_year[f"{prefix}_died"].sum()
        fail = oc_year[f"{prefix}_fail"].sum()
        lost = oc_year[f"{prefix}_lost"].sum()
        if coh == 0:
            return {"Success": 0, "Died": 0, "Failed": 0, "Lost to follow-up": 0}
        return {"Success": succ/coh*100, "Died": died/coh*100, "Failed": fail/coh*100, "Lost to follow-up": lost/coh*100}

    mdr_pcts = outcome_pcts("mdr")
    xdr_pcts = outcome_pcts("xdr")
    cats = list(mdr_pcts.keys())
    fig_subtype = go.Figure()
    fig_subtype.add_trace(go.Bar(name="MDR-TB", x=cats, y=[mdr_pcts[c] for c in cats], marker_color="#1F5C82",
                                  text=[f"{mdr_pcts[c]:.1f}%" for c in cats], textposition="outside"))
    fig_subtype.add_trace(go.Bar(name="XDR-TB", x=cats, y=[xdr_pcts[c] for c in cats], marker_color="#C0392B",
                                  text=[f"{xdr_pcts[c]:.1f}%" for c in cats], textposition="outside"))
    fig_subtype = style_chart(fig_subtype, height=400, legend_bottom=True)
    fig_subtype.update_layout(barmode="group", yaxis_title="% of cohort")
    st.plotly_chart(fig_subtype, width="stretch")
    st.caption(f"Cohort year: {int(oc_year_val)}. XDR-TB shows a notably higher failure rate despite its smaller cohort size.")

with col7:
    st.subheader("Treatment outcomes by sex (% of cohort)")
    sex_oc = outc_age_sex[(outc_age_sex["age_group"] == "a") & (outc_age_sex["sex"] != "a")]
    sex_oc_agg = sex_oc.groupby("sex").agg(coh=("coh", "sum"), succ=("succ", "sum"), fail=("fail", "sum"),
                                            died=("died", "sum"), lost=("lost", "sum")).reset_index()
    sex_oc_agg["sex"] = sex_oc_agg["sex"].map({"m": "Male", "f": "Female"})
    for col in ["succ", "fail", "died", "lost"]:
        sex_oc_agg[col] = sex_oc_agg[col] / sex_oc_agg["coh"] * 100
    sex_oc_long = sex_oc_agg.melt(id_vars="sex", value_vars=["succ", "fail", "died", "lost"],
                                   var_name="outcome", value_name="pct")
    sex_oc_long["outcome"] = sex_oc_long["outcome"].map(
        {"succ": "Success", "fail": "Failed", "died": "Died", "lost": "Lost to follow-up"})
    fig_sexoc = px.bar(sex_oc_long, x="sex", y="pct", color="outcome", barmode="group",
                        text=sex_oc_long["pct"].round(1).astype(str) + "%",
                        color_discrete_sequence=["#2E8B5A", "#C0392B", "#1A1A1A", "#E0A030"])
    fig_sexoc.update_traces(textposition="outside")
    fig_sexoc = style_chart(fig_sexoc, height=400, legend_bottom=True)
    fig_sexoc.update_layout(yaxis_title="% of cohort")
    st.plotly_chart(fig_sexoc, width="stretch")

st.markdown("---")

# ============================================================
# SECTION 5 — Funding & inequality
# ============================================================
st.header("💰 Funding & Inequality")

st.subheader("Spend per TB case vs. burden, by region")
latest_exp_year = expenditure["year"].max()
exp_latest = expenditure[expenditure["year"] == latest_exp_year][["country", "region_name", "exp_tot"]]
burden_latest = burden[burden["year"] == latest_year][["country", "region_name", "e_inc_num"]]
per_case = exp_latest.merge(burden_latest[["country", "e_inc_num"]], on="country", how="inner").dropna()
per_case = per_case[per_case["e_inc_num"] > 0]
per_case["spend_per_case"] = per_case["exp_tot"] / per_case["e_inc_num"]
region_compare = per_case.groupby("region_name")["spend_per_case"].median().reset_index()
region_burden = burden_latest.groupby("region_name")["e_inc_num"].sum().reset_index().rename(columns={"e_inc_num": "total_burden"})
region_compare = region_compare.merge(region_burden, on="region_name", how="left").sort_values("spend_per_case")

fig_fund = go.Figure()
fig_fund.add_trace(go.Bar(x=region_compare["spend_per_case"], y=region_compare["region_name"], orientation="h",
                           marker_color="#1F5C82", xaxis="x1", name="Median USD spent per TB case"))
fig_fund.add_trace(go.Scatter(x=region_compare["total_burden"], y=region_compare["region_name"], mode="markers",
                               marker=dict(color="#C0392B", size=14, symbol="diamond"), xaxis="x2",
                               name="Total estimated TB cases"))
fig_fund.update_layout(
    template=PLOTLY_TEMPLATE, height=420, margin=dict(t=90, b=20, l=10, r=10),
    xaxis=dict(title="Median USD spent per TB case", domain=[0, 1], side="bottom",
               title_font=dict(color="#1F5C82"), tickfont=dict(color="#1F5C82")),
    xaxis2=dict(title="Total estimated TB cases", overlaying="x", side="top",
                title_font=dict(color="#C0392B"), tickfont=dict(color="#C0392B")),
    legend=dict(orientation="h", yanchor="bottom", y=1.22, xanchor="center", x=0.5),
)
st.plotly_chart(fig_fund, width="stretch")

low_region = region_compare.iloc[0]
high_region = region_compare.iloc[-1]
gap_multiple = high_region["spend_per_case"] / low_region["spend_per_case"] if low_region["spend_per_case"] > 0 else None
if gap_multiple:
    st.markdown(
        f'<div class="tb-callout-red">⚠️ <b>The gap:</b> {high_region["region_name"]} spends roughly '
        f'<b>{gap_multiple:.0f}x more per TB case</b> than {low_region["region_name"]} — while carrying far less '
        "of the actual disease burden.</div>",
        unsafe_allow_html=True,
    )

st.markdown("")
st.subheader("Budget vs. actual expenditure — top 15 countries by budget")
latest_b_year = budget.dropna(subset=["budget_tot"])["year"].max()
latest_e_year = expenditure.dropna(subset=["exp_tot"])["year"].max()
merged = budget[budget["year"] == latest_b_year][["country", "budget_tot"]].merge(
    expenditure[expenditure["year"] == latest_e_year][["country", "exp_tot"]], on="country", how="inner"
).dropna()
top15 = merged.nlargest(15, "budget_tot")
fig_budget = go.Figure()
fig_budget.add_trace(go.Bar(name="Budgeted", x=top15["country"], y=top15["budget_tot"], marker_color="#1F5C82"))
fig_budget.add_trace(go.Bar(name="Actually spent", x=top15["country"], y=top15["exp_tot"], marker_color="#E0A030"))
fig_budget = style_chart(fig_budget, height=440, legend_bottom=True)
fig_budget.update_layout(barmode="group", yaxis_title="USD", xaxis_tickangle=-40)
st.plotly_chart(fig_budget, width="stretch")

st.markdown("---")

# ============================================================
# SECTION 6 — Latent TB & Prevention
# ============================================================
st.header("🛡️ Latent TB & Prevention")
st.subheader("Preventive treatment coverage trend")
ltbi_trend = ltbi.groupby("year")["e_prevtx_hh_contacts_pct"].mean().reset_index().dropna()
fig_ltbi = go.Figure()
fig_ltbi.add_trace(go.Scatter(x=ltbi_trend["year"], y=ltbi_trend["e_prevtx_hh_contacts_pct"], mode="lines+markers",
                               line=dict(color="#2E8B8B", width=3), fill="tozeroy", fillcolor="rgba(46,139,139,0.1)"))
fig_ltbi = style_chart(fig_ltbi, height=360)
fig_ltbi.update_layout(yaxis_title="Coverage (%)")
st.plotly_chart(fig_ltbi, width="stretch")

st.caption(
    "Summary view — condensed from the Overview, Geographic Map, Demographics, Disease Subtypes, "
    "Treatment Outcomes, Funding & Inequality, and Latent TB & Prevention pages. Visit individual pages "
    "for region/year filters and full source notes."
)
