import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import check_password, load_mdr, load_outcomes, load_burden
from utils.theme import THEME_CSS, PLOTLY_TEMPLATE

st.set_page_config(page_title="Disease Subtypes | TB Dashboard", page_icon="🧬", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

if not check_password():
    st.stop()

st.markdown('<p class="tb-eyebrow">Page 4</p>', unsafe_allow_html=True)
st.title("🧬 Disease Subtypes: Drug-Resistant TB")
st.markdown("Multidrug-resistant (MDR) and extensively drug-resistant (XDR) TB burden and outcomes.")
st.markdown("---")

mdr = load_mdr()
outcomes = load_outcomes()
burden = load_burden()

st.sidebar.header("Filters")
regions = ["All regions"] + sorted(mdr["g_whoregion"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox("WHO Region", regions)

scope = mdr if region_sel == "All regions" else mdr[mdr["g_whoregion"] == region_sel]

col1, col2, col3 = st.columns(3)
latest_year = scope["year"].max()
latest = scope[scope["year"] == latest_year]
with col1:
    st.metric("RR/MDR-TB cases", f"{latest['e_inc_rr_num'].sum()/1e3:.0f}K", help=f"Estimated incident RR-TB cases, {int(latest_year)}")
with col2:
    st.metric("Avg. % resistant (new cases)", f"{latest['e_rr_pct_new'].mean():.1f}%")
with col3:
    st.metric("Avg. % resistant (retreatment)", f"{latest['e_rr_pct_ret'].mean():.1f}%")

st.markdown("---")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("RR-TB incidence trend")
    trend = scope.groupby("year")["e_inc_rr_num"].sum().reset_index()
    fig = px.area(trend, x="year", y="e_inc_rr_num", color_discrete_sequence=["#C0392B"])
    fig.update_layout(template=PLOTLY_TEMPLATE, height=380, margin=dict(t=10, b=10),
                       yaxis_title="Estimated RR-TB cases")
    st.plotly_chart(fig, width="stretch")

with col_b:
    st.subheader("Resistance: new vs. retreatment cases")
    trend2 = scope.groupby("year")[["e_rr_pct_new", "e_rr_pct_ret"]].mean().reset_index()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=trend2["year"], y=trend2["e_rr_pct_new"], name="New cases",
                               line=dict(color="#1F5C82", width=3)))
    fig2.add_trace(go.Scatter(x=trend2["year"], y=trend2["e_rr_pct_ret"], name="Retreatment cases",
                               line=dict(color="#E0A030", width=3)))
    fig2.update_layout(template=PLOTLY_TEMPLATE, height=380, margin=dict(t=10, b=10),
                        yaxis_title="% resistant to rifampicin")
    st.plotly_chart(fig2, width="stretch")

st.markdown(
    '<div class="tb-callout-red">⚠️ <b>Treatment access gap:</b> Globally, only about 2 in 5 people with '
    "drug-resistant TB access appropriate treatment — leaving the majority of MDR/RR-TB cases untreated or "
    "treated with regimens unlikely to succeed.</div>",
    unsafe_allow_html=True,
)

st.markdown("---")

# --- MDR/XDR treatment outcomes ---
st.subheader("MDR-TB vs. XDR-TB treatment outcomes")
outc_scope = outcomes if region_sel == "All regions" else outcomes[outcomes["g_whoregion"] == region_sel]
latest_outc_year = outc_scope.dropna(subset=["mdr_coh"])["year"].max()
oc = outc_scope[outc_scope["year"] == latest_outc_year]

def outcome_summary(prefix):
    coh = oc[f"{prefix}_coh"].sum()
    succ = oc[f"{prefix}_succ"].sum()
    died = oc[f"{prefix}_died"].sum()
    fail = oc[f"{prefix}_fail"].sum()
    lost = oc[f"{prefix}_lost"].sum()
    other = max(coh - succ - died - fail - lost, 0)
    return {"Success": succ, "Died": died, "Failed": fail, "Lost to follow-up": lost, "Other/not evaluated": other}

mdr_summary = outcome_summary("mdr")
xdr_summary = outcome_summary("xdr")

fig3 = go.Figure()
categories = list(mdr_summary.keys())
fig3.add_trace(go.Bar(name="MDR-TB", x=categories, y=list(mdr_summary.values()), marker_color="#1F5C82"))
fig3.add_trace(go.Bar(name="XDR-TB", x=categories, y=list(xdr_summary.values()), marker_color="#C0392B"))
fig3.update_layout(template=PLOTLY_TEMPLATE, barmode="group", height=400, margin=dict(t=10, b=10),
                    yaxis_title="Patients", title=f"Cohort outcomes, {int(latest_outc_year)}")
st.plotly_chart(fig3, width="stretch")

st.caption("Source: WHO Global TB Programme — MDR_RR_TB_burden_estimates.csv, TB_outcomes.csv")
