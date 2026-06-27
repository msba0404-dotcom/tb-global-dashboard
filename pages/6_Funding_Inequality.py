import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import check_password, load_budget, load_expenditure, load_burden, relabel
from utils.theme import THEME_CSS, PLOTLY_TEMPLATE

st.set_page_config(page_title="Funding & Inequality | TB Dashboard", page_icon="💰", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

if not check_password():
    st.stop()

st.markdown('<p class="tb-eyebrow">Page 6</p>', unsafe_allow_html=True)
st.title("💰 Funding & Inequality")
st.markdown(
    "Budget vs. actual expenditure gaps, funding sources, and how much is spent **per TB case** "
    "across regions and countries — the comparison that actually reveals inequality, since raw "
    "dollar totals mostly just reflect country size."
)
st.markdown("---")

budget = load_budget()
expenditure = load_expenditure()
burden = load_burden()

st.sidebar.header("Filters")
regions = ["All regions"] + sorted(budget["region_name"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox("WHO Region", regions)

b_scope = budget if region_sel == "All regions" else budget[budget["region_name"] == region_sel]
e_scope = expenditure if region_sel == "All regions" else expenditure[expenditure["region_name"] == region_sel]

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

# --- THE KEY INEQUALITY METRIC: spending per TB case, by region ---
st.subheader("The real inequality measure: spending per TB case vs. burden, by region")
st.markdown(
    "Total dollars spent mostly reflects how large or wealthy a country is — not whether its "
    "TB response is well-funded relative to its actual disease burden. Dividing total expenditure "
    "by the number of estimated TB cases gives a fairer, size-independent comparison — and placing it "
    "next to each region's actual case burden shows whether funding and need line up."
)

latest_exp_year = expenditure["year"].max()
latest_burden_year = burden["year"].max()

exp_latest = expenditure[expenditure["year"] == latest_exp_year][["country", "region_name", "exp_tot"]]
burden_latest = burden[burden["year"] == latest_burden_year][["country", "region_name", "e_inc_num"]]

per_case = exp_latest.merge(burden_latest[["country", "e_inc_num"]], on="country", how="inner").dropna()
per_case = per_case[per_case["e_inc_num"] > 0]
per_case["spend_per_case"] = per_case["exp_tot"] / per_case["e_inc_num"]

region_compare = per_case.groupby("region_name")["spend_per_case"].median().reset_index()
region_burden = burden_latest.groupby("region_name")["e_inc_num"].sum().reset_index().rename(columns={"e_inc_num": "total_burden"})
region_compare = region_compare.merge(region_burden, on="region_name", how="left")
region_compare = region_compare.sort_values("spend_per_case")

fig_region = go.Figure()
fig_region.add_trace(go.Bar(
    x=region_compare["spend_per_case"], y=region_compare["region_name"], orientation="h",
    name="Median USD spent per TB case", marker_color="#1F5C82",
    xaxis="x1",
))
fig_region.add_trace(go.Scatter(
    x=region_compare["total_burden"], y=region_compare["region_name"],
    name="Total estimated TB cases", mode="markers",
    marker=dict(color="#C0392B", size=14, symbol="diamond"),
    xaxis="x2",
))
fig_region.update_layout(
    template=PLOTLY_TEMPLATE, height=440, margin=dict(t=90, b=10),
    xaxis=dict(title="Median USD spent per TB case", domain=[0, 1], side="bottom",
               title_font=dict(color="#1F5C82"), tickfont=dict(color="#1F5C82")),
    xaxis2=dict(title="Total estimated TB cases", overlaying="x", side="top",
                title_font=dict(color="#C0392B"), tickfont=dict(color="#C0392B")),
    legend=dict(orientation="h", yanchor="bottom", y=1.22, xanchor="center", x=0.5),
)
st.plotly_chart(fig_region, width="stretch")
st.caption(
    "Blue bars (bottom axis): median spending per case. Red diamonds (top axis): total disease burden. "
    "The regions with the longest blue bars should, in a fairly-funded world, also be the regions with the "
    "most red diamonds — instead, it's often the reverse."
)

low_region = region_compare.iloc[0]
high_region = region_compare.iloc[-1]
gap_multiple = high_region["spend_per_case"] / low_region["spend_per_case"] if low_region["spend_per_case"] > 0 else None

if gap_multiple:
    st.markdown(
        f'<div class="tb-callout-red">⚠️ <b>The gap:</b> {high_region["region_name"]} spends roughly '
        f'<b>{gap_multiple:.0f}x more per TB case</b> than {low_region["region_name"]} '
        f"(${high_region['spend_per_case']:,.0f} vs. ${low_region['spend_per_case']:,.0f} per case). "
        "This is the core funding inequality the dashboard is built to surface — the regions carrying "
        "the heaviest TB burden are also the most poorly resourced to fight it.</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

col_x, col_y = st.columns(2)
with col_x:
    st.subheader("Top 10 — highest spend per case")
    top10_pc = per_case.nlargest(10, "spend_per_case")[["country", "spend_per_case"]].reset_index(drop=True)
    top10_pc["spend_per_case"] = top10_pc["spend_per_case"].round(0)
    st.dataframe(relabel(top10_pc).rename(columns={"spend_per_case": "USD per case"}), width="stretch", hide_index=True)
with col_y:
    st.subheader("Bottom 10 — lowest spend per case")
    bottom10_pc = per_case[per_case["spend_per_case"] > 0].nsmallest(10, "spend_per_case")[["country", "spend_per_case"]].reset_index(drop=True)
    bottom10_pc["spend_per_case"] = bottom10_pc["spend_per_case"].round(1)
    st.dataframe(relabel(bottom10_pc).rename(columns={"spend_per_case": "USD per case"}), width="stretch", hide_index=True)

st.caption(
    "Method: total TB expenditure (exp_tot) ÷ estimated new TB cases (e_inc_num), most recent year available "
    "for each. A handful of very small countries/territories show extreme outlier values (e.g. one TB case and "
    "a fixed minimum program cost) — region-level medians are used above specifically to reduce the influence "
    "of these outliers."
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
st.markdown(
    '<div class="tb-callout">📌 <b>Why this matters for inequality:</b> Countries reliant on external donors '
    "(Global Fund, USAID, other grants) rather than domestic government funding are more exposed to funding "
    "cuts or shifting donor priorities — a structural vulnerability that wealthier countries, funded almost "
    "entirely domestically, do not face.</div>",
    unsafe_allow_html=True,
)

st.markdown("---")

# --- Budget vs actual by country (top funded) ---
st.subheader("Budget vs. actual expenditure — top 15 countries by budget")
st.caption("Shown for the largest TB programs by budget size (a scale comparison) — see the per-case analysis above for the inequality comparison.")
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

st.caption("Source: WHO Global TB Programme — TB_budget.csv, TB_expenditure_utilisation.csv, TB_burden_countries.csv")