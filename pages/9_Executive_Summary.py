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

st.set_page_config(page_title="Executive Summary | TB Dashboard", page_icon="🗂️", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

# Tighten vertical spacing specifically on this page so 13 elements can fit
# without scrolling -- this page intentionally overrides some default
# Streamlit/Plotly spacing that's fine on single-chart pages but too loose here.
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 0.5rem; }
    [data-testid="stVerticalBlock"] { gap: 0.4rem; }
    h3 { margin-top: 0.1rem !important; margin-bottom: 0.1rem !important; font-size: 1.05rem !important; }
    h4 { margin-top: 0.1rem !important; margin-bottom: 0.1rem !important; font-size: 0.92rem !important; }
    [data-testid="stMetric"] { padding: 6px 10px !important; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.68rem !important; }
    .stCaption, [data-testid="stCaptionContainer"] { font-size: 0.68rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

if not check_password():
    st.stop()

st.markdown('<p class="tb-eyebrow">Executive Summary — one-screen view</p>', unsafe_allow_html=True)
st.markdown("##### 🫁 TB Global Burden — Key Findings at a Glance")

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

# Compact chart defaults applied to every figure below
COMPACT_MARGIN = dict(t=22, b=20, l=4, r=4)
COMPACT_FONT = dict(size=10)


def style_compact(fig, height, legend_bottom=False):
    fig.update_layout(
        template=PLOTLY_TEMPLATE, height=height, margin=COMPACT_MARGIN,
        font=COMPACT_FONT, title_font=dict(size=11),
    )
    if legend_bottom:
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5,
                                       font=dict(size=8)))
    fig.update_xaxes(title_font=dict(size=9), tickfont=dict(size=8))
    fig.update_yaxes(title_font=dict(size=9), tickfont=dict(size=8))
    return fig


# ============================================================
# ROW 1 — KPI strip (Global Overview numbers, very compact)
# ============================================================
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.metric("Cases", f"{latest['e_inc_num'].sum()/1e6:.1f}M", help=f"{latest_year}")
with k2:
    st.metric("Deaths", f"{latest['e_mort_num'].sum()/1e3:.0f}K", help=f"{latest_year}")
with k3:
    st.metric("Avg CFR", f"{latest['cfr_pct'].mean():.1f}%", help="Case fatality ratio")
with k4:
    st.metric("Avg CDR", f"{latest['c_cdr'].mean():.0f}%", help="Case detection rate")
with k5:
    cov_year = ltbi.dropna(subset=['e_prevtx_hh_contacts_pct'])["year"].max()
    avg_cov = ltbi[ltbi["year"] == cov_year]["e_prevtx_hh_contacts_pct"].mean()
    st.metric("Prev. tx coverage", f"{avg_cov:.0f}%", help="Preventive treatment coverage")
with k6:
    latest_tsr_year = outcomes.dropna(subset=["c_new_tsr"])["year"].max()
    tsr_now = outcomes[outcomes["year"] == latest_tsr_year]["c_new_tsr"].mean()
    st.metric("Treatment success", f"{tsr_now:.0f}%", help="WHO target: 85%")

st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

# ============================================================
# ROW 2 — Map (left, larger) + Trends column (right)
# ============================================================
row2_col1, row2_col2 = st.columns([1.3, 1])

with row2_col1:
    st.markdown("#### 🗺️ Geographic distribution — incidence per 100k")
    map_df = latest.dropna(subset=["e_inc_100k"])
    fig_map = px.choropleth(
        map_df, locations="iso3", color="e_inc_100k", hover_name="country",
        color_continuous_scale=["#EAF3F7", "#1F5C82", "#0E2A42"],
    )
    fig_map.update_layout(
        template=PLOTLY_TEMPLATE, height=300, margin=dict(t=4, b=4, l=4, r=4),
        coloraxis_showscale=False,
        geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth", bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_map, width="stretch")

with row2_col2:
    st.markdown("#### 📈 Treatment success rate over time")
    outc_trend = outcomes.groupby("year")["c_new_tsr"].mean().reset_index().dropna()
    fig_tsr = go.Figure()
    fig_tsr.add_trace(go.Scatter(x=outc_trend["year"], y=outc_trend["c_new_tsr"], mode="lines",
                                  line=dict(color="#2E8B8B", width=2)))
    fig_tsr.add_hline(y=85, line_dash="dash", line_color="#E0A030", line_width=1)
    fig_tsr = style_compact(fig_tsr, 138)
    st.plotly_chart(fig_tsr, width="stretch")

    st.markdown("#### 🛡️ Preventive treatment coverage trend")
    ltbi_trend = ltbi.groupby("year")["e_prevtx_hh_contacts_pct"].mean().reset_index().dropna()
    fig_ltbi = go.Figure()
    fig_ltbi.add_trace(go.Scatter(x=ltbi_trend["year"], y=ltbi_trend["e_prevtx_hh_contacts_pct"], mode="lines",
                                   line=dict(color="#1F5C82", width=2), fill="tozeroy", fillcolor="rgba(31,92,130,0.12)"))
    fig_ltbi = style_compact(fig_ltbi, 138)
    st.plotly_chart(fig_ltbi, width="stretch")

st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

# ============================================================
# ROW 3 — Incidence + Mortality trend + Demographics (3 mini charts)
# ============================================================
row3_col1, row3_col2, row3_col3, row3_col4, row3_col5 = st.columns([1, 1, 1, 1, 1])

trend = burden.groupby("year").agg(incidence=("e_inc_num", "sum"), mortality=("e_mort_num", "sum")).reset_index()

with row3_col1:
    st.markdown("#### 📉 Incidence trend")
    fig_inc = go.Figure(go.Scatter(x=trend["year"], y=trend["incidence"], mode="lines",
                                    line=dict(color="#1F5C82", width=2), fill="tozeroy", fillcolor="rgba(31,92,130,0.12)"))
    fig_inc = style_compact(fig_inc, 160)
    st.plotly_chart(fig_inc, width="stretch")

with row3_col2:
    st.markdown("#### ⚰️ Mortality trend")
    fig_mort = go.Figure(go.Scatter(x=trend["year"], y=trend["mortality"], mode="lines",
                                     line=dict(color="#C0392B", width=2), fill="tozeroy", fillcolor="rgba(192,57,43,0.1)"))
    fig_mort = style_compact(fig_mort, 160)
    st.plotly_chart(fig_mort, width="stretch")

with row3_col3:
    st.markdown("#### 👥 Burden by sex")
    sex_data = age_sex[(age_sex["risk_factor"] == "all") & (age_sex["age_group"] == "all") & (age_sex["sex"] != "a")]
    sex_agg = sex_data.groupby("sex")["best"].sum().reset_index()
    sex_agg["sex"] = sex_agg["sex"].map({"m": "Male", "f": "Female"})
    fig_sex = px.pie(sex_agg, names="sex", values="best", color="sex",
                      color_discrete_map={"Male": "#1F5C82", "Female": "#E0A030"}, hole=0.5)
    fig_sex.update_traces(textfont_size=9, textposition="inside")
    fig_sex = style_compact(fig_sex, 160, legend_bottom=True)
    st.plotly_chart(fig_sex, width="stretch")

with row3_col4:
    st.markdown("#### ⚠️ Burden by risk factor")
    RISK_MAP = {"hiv": "HIV", "dia": "Diabetes", "alc": "Alcohol", "smk": "Smoking", "und": "Undernutr."}
    risk_data = age_sex[(age_sex["age_group"] == "all") & (age_sex["sex"] == "a") & (age_sex["risk_factor"] != "all")]
    risk_agg = risk_data.groupby("risk_factor")["best"].sum().reset_index()
    risk_agg["risk_factor"] = risk_agg["risk_factor"].map(RISK_MAP)
    risk_agg = risk_agg.sort_values("best")
    fig_risk = px.bar(risk_agg, x="best", y="risk_factor", orientation="h", color_discrete_sequence=["#2E8B8B"])
    fig_risk = style_compact(fig_risk, 160)
    fig_risk.update_layout(yaxis_title="", xaxis_title="")
    st.plotly_chart(fig_risk, width="stretch")

with row3_col5:
    st.markdown("#### 📊 Age distribution (pyramid)")
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
    fig_age = style_compact(fig_age, 160, legend_bottom=True)
    fig_age.update_layout(barmode="overlay", yaxis_title="", xaxis_title="")
    st.plotly_chart(fig_age, width="stretch")

st.markdown("<hr style='margin:2px 0;'>", unsafe_allow_html=True)

# ============================================================
# ROW 4 — Subtype outcomes %, Sex outcomes %, Funding-vs-burden, Budget vs actual
# ============================================================
row4_col1, row4_col2, row4_col3, row4_col4 = st.columns([1, 1, 1.2, 1.2])

with row4_col1:
    st.markdown("#### 🧬 Cohort outcomes (%), 2022")
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
            return {"Success": 0, "Died": 0, "Failed": 0, "Lost": 0}
        return {"Success": succ/coh*100, "Died": died/coh*100, "Failed": fail/coh*100, "Lost": lost/coh*100}

    mdr_pcts = outcome_pcts("mdr")
    xdr_pcts = outcome_pcts("xdr")
    cats = list(mdr_pcts.keys())
    fig_subtype = go.Figure()
    fig_subtype.add_trace(go.Bar(name="MDR", x=cats, y=[mdr_pcts[c] for c in cats], marker_color="#1F5C82"))
    fig_subtype.add_trace(go.Bar(name="XDR", x=cats, y=[xdr_pcts[c] for c in cats], marker_color="#C0392B"))
    fig_subtype = style_compact(fig_subtype, 175, legend_bottom=True)
    fig_subtype.update_layout(barmode="group", yaxis_title="% of cohort", xaxis_title="")
    st.plotly_chart(fig_subtype, width="stretch")

with row4_col2:
    st.markdown("#### ⚕️ Outcomes by sex (%)")
    sex_oc = outc_age_sex[(outc_age_sex["age_group"] == "a") & (outc_age_sex["sex"] != "a")]
    sex_oc_agg = sex_oc.groupby("sex").agg(coh=("coh", "sum"), succ=("succ", "sum"), fail=("fail", "sum"),
                                            died=("died", "sum"), lost=("lost", "sum")).reset_index()
    sex_oc_agg["sex"] = sex_oc_agg["sex"].map({"m": "Male", "f": "Female"})
    for col in ["succ", "fail", "died", "lost"]:
        sex_oc_agg[col] = sex_oc_agg[col] / sex_oc_agg["coh"] * 100
    sex_oc_long = sex_oc_agg.melt(id_vars="sex", value_vars=["succ", "fail", "died", "lost"],
                                   var_name="outcome", value_name="pct")
    sex_oc_long["outcome"] = sex_oc_long["outcome"].map({"succ": "Success", "fail": "Failed", "died": "Died", "lost": "Lost"})
    fig_sexoc = px.bar(sex_oc_long, x="sex", y="pct", color="outcome", barmode="group",
                        color_discrete_sequence=["#2E8B5A", "#C0392B", "#1A1A1A", "#E0A030"])
    fig_sexoc = style_compact(fig_sexoc, 175, legend_bottom=True)
    fig_sexoc.update_layout(yaxis_title="% of cohort", xaxis_title="")
    st.plotly_chart(fig_sexoc, width="stretch")

with row4_col3:
    st.markdown("#### 💰 Spend per case vs. burden, by region")
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
                               marker_color="#1F5C82", xaxis="x1", name="USD/case"))
    fig_fund.add_trace(go.Scatter(x=region_compare["total_burden"], y=region_compare["region_name"], mode="markers",
                                   marker=dict(color="#C0392B", size=9, symbol="diamond"), xaxis="x2", name="Burden"))
    fig_fund.update_layout(
        template=PLOTLY_TEMPLATE, height=185, margin=dict(t=26, b=4, l=4, r=4), font=dict(size=8),
        xaxis=dict(domain=[0, 1], side="bottom", tickfont=dict(size=7, color="#1F5C82")),
        xaxis2=dict(overlaying="x", side="top", tickfont=dict(size=7, color="#C0392B")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=7)),
    )
    fig_fund.update_yaxes(tickfont=dict(size=8))
    st.plotly_chart(fig_fund, width="stretch")

with row4_col4:
    st.markdown("#### 📑 Budget vs. actual, top 15")
    latest_b_year = budget.dropna(subset=["budget_tot"])["year"].max()
    latest_e_year = expenditure.dropna(subset=["exp_tot"])["year"].max()
    merged = budget[budget["year"] == latest_b_year][["country", "budget_tot"]].merge(
        expenditure[expenditure["year"] == latest_e_year][["country", "exp_tot"]], on="country", how="inner"
    ).dropna()
    top15 = merged.nlargest(15, "budget_tot")
    fig_budget = go.Figure()
    fig_budget.add_trace(go.Bar(name="Budget", x=top15["country"], y=top15["budget_tot"], marker_color="#1F5C82"))
    fig_budget.add_trace(go.Bar(name="Spent", x=top15["country"], y=top15["exp_tot"], marker_color="#E0A030"))
    fig_budget = style_compact(fig_budget, 185, legend_bottom=True)
    fig_budget.update_layout(barmode="group", yaxis_title="", xaxis_title="")
    fig_budget.update_xaxes(tickangle=-55, tickfont=dict(size=6))
    st.plotly_chart(fig_budget, width="stretch")

st.caption(
    "Executive summary view — condensed from the Overview, Geographic Map, Demographics, Disease Subtypes, "
    "Treatment Outcomes, Funding & Inequality, and Latent TB & Prevention pages. See those pages for filters, "
    "full detail, and source notes."
)
