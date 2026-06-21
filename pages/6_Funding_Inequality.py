import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import check_password, load_budget, load_expenditure, load_burden
from utils.theme import THEME_CSS, PLOTLY_TEMPLATE

st.set_page_config(page_title="Funding & Inequality | TB Dashboard", page_icon="💰", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

if not check_password():
    st.stop()

st.markdown('<p class="tb-eyebrow">Page 6</p>', unsafe_allow_html=True)
st.title("💰 Funding & Inequality")
st.markdown("Budget vs. actual expenditure gaps, funding sources, and the relationship between TB burden and country income.")
st.markdown("---")

budget = load_budget()
expenditure = load_expenditure()
burden = load_burden()

st.sidebar.header("Filters")
regions = ["All regions"] + sorted(budget["g_whoregion"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox("WHO Region", regions)

b_scope = budget if region_sel == "All regions" else budget[budget["g_whoregion"] == region_sel]
e_scope = expenditure if region_sel == "All regions" else expenditure[expenditure["g_whoregion"] == region_sel]

latest_b_year = b_scope.dropna(subset=["budget_tot"])["year"].max()
latest_e_year = e_scope.dropna(subset=["exp_tot"])["year"].max()

col1, col2, col3 = st.columns(3)
with col1:
    bt = b_scope[b_scope["year"] == latest_b_year]["budget_tot"].sum()
    st.metric("Total budgeted", f"${bt/1e6:.0f}M", help=f"{int(latest_b_year)}")
with col2:
    et = e_scope[e_scope["year"] == latest_e_year]["exp_tot"].sum()
    st.metric("Total spent", f"${et/1e6:.0f}M", help=f"{int(latest_e_year)}")
with col3:
    rep_rate = e_scope["exp_tot"].notna().mean() * 100
    st.metric("Countries reporting expenditure", f"{rep_rate:.0f}%", help="Data completeness — a signal in itself")

st.markdown(
    '<div class="tb-callout">📌 <b>Reporting gap as inequality signal:</b> Roughly 40% of countries do not report '
    "complete TB expenditure data. Missing reporting is itself disproportionately concentrated in lower-capacity "
    "health systems — the countries that most need funding scrutiny are often the hardest to scrutinize.</div>",
    unsafe_allow_html=True,
)

st.markdown("---")

# --- Funding source breakdown ---
st.subheader("Funding sources")
fund_cols = ["rcvd_tot_domestic", "rcvd_tot_gf", "rcvd_tot_usaid", "rcvd_tot_grnt"]
fund_labels = {"rcvd_tot_domestic": "Domestic government", "rcvd_tot_gf": "Global Fund",
               "rcvd_tot_usaid": "USAID", "rcvd_tot_grnt": "Other grants"}
latest_exp = e_scope[e_scope["year"] == latest_e_year]
fund_sum = latest_exp[fund_cols].sum().reset_index()
fund_sum.columns = ["source", "amount"]
fund_sum["source"] = fund_sum["source"].map(fund_labels)

fig = px.pie(fund_sum, names="source", values="amount", hole=0.45,
             color_discrete_sequence=["#1F5C82", "#2E8B8B", "#E0A030", "#8E44AD"])
fig.update_layout(template=PLOTLY_TEMPLATE, height=400, margin=dict(t=10, b=10))
st.plotly_chart(fig, width="stretch")

st.markdown("---")

# --- Budget vs actual by country (top funded) ---
st.subheader("Budget vs. actual expenditure — top 15 countries by budget")
merged = b_scope[b_scope["year"] == latest_b_year][["country", "budget_tot"]].merge(
    e_scope[e_scope["year"] == latest_e_year][["country", "exp_tot"]], on="country", how="inner"
).dropna()
top15 = merged.nlargest(15, "budget_tot")

fig2 = go.Figure()
fig2.add_trace(go.Bar(name="Budgeted", x=top15["country"], y=top15["budget_tot"], marker_color="#1F5C82"))
fig2.add_trace(go.Bar(name="Actually spent", x=top15["country"], y=top15["exp_tot"], marker_color="#E0A030"))
fig2.update_layout(template=PLOTLY_TEMPLATE, barmode="group", height=440, margin=dict(t=10, b=10),
                    yaxis_title="USD", xaxis_tickangle=-40)
st.plotly_chart(fig2, width="stretch")

st.markdown("---")

# --- Burden vs population (proxy for income-tier inequality) ---
st.subheader("TB burden vs. population size — by region")
latest_burden_year = burden["year"].max()
lb = burden[burden["year"] == latest_burden_year].dropna(subset=["e_pop_num", "e_inc_100k", "e_inc_num", "region_name"])
lb = lb[lb["e_inc_num"] > 0]
fig3 = px.scatter(lb, x="e_pop_num", y="e_inc_100k", color="region_name", size="e_inc_num",
                   hover_name="country", log_x=True,
                   labels={"e_pop_num": "Population (log scale)", "e_inc_100k": "Incidence per 100k"},
                   color_discrete_sequence=["#1F5C82", "#2E8B8B", "#E0A030", "#C0392B", "#8E44AD", "#5A6B78"])
fig3.update_layout(template=PLOTLY_TEMPLATE, height=460, margin=dict(t=10, b=10))
st.plotly_chart(fig3, width="stretch")

st.caption("Source: WHO Global TB Programme — TB_budget.csv, TB_expenditure_utilisation.csv, TB_burden_countries.csv")
