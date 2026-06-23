import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import check_password, load_ltbi, relabel
from utils.theme import THEME_CSS, PLOTLY_TEMPLATE

st.set_page_config(page_title="Latent TB & Prevention | TB Dashboard", page_icon="🛡️", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

if not check_password():
    st.stop()

st.markdown('<p class="tb-eyebrow">Page 7</p>', unsafe_allow_html=True)
st.title("🛡️ Latent TB & Prevention")
st.markdown("Household contact tracing and preventive treatment (TPT) coverage — who is being reached, and who is left behind.")
st.markdown("---")

ltbi = load_ltbi()

st.sidebar.header("Filters")
regions = ["All regions"] + sorted(ltbi["region_name"].dropna().unique().tolist())
region_sel = st.sidebar.selectbox("WHO Region", regions)

scope = ltbi if region_sel == "All regions" else ltbi[ltbi["region_name"] == region_sel]
latest_year = scope.dropna(subset=["e_prevtx_hh_contacts_pct"])["year"].max()
latest = scope[scope["year"] == latest_year]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Avg. preventive treatment coverage", f"{latest['e_prevtx_hh_contacts_pct'].mean():.0f}%",
               help="% of household contacts who received TB preventive treatment")
with col2:
    st.metric("Eligible for preventive treatment", f"{latest['e_prevtx_eligible'].sum()/1e6:.1f}M",
               help=f"{int(latest_year)}")
with col3:
    st.metric("Children under 5 among eligible", f"{latest['e_prevtx_kids_pct'].mean():.0f}%")

st.markdown("---")

st.subheader("Preventive treatment coverage trend")
trend = scope.groupby("year")["e_prevtx_hh_contacts_pct"].mean().reset_index().dropna()
fig = go.Figure()
fig.add_trace(go.Scatter(x=trend["year"], y=trend["e_prevtx_hh_contacts_pct"], mode="lines+markers",
                          line=dict(color="#2E8B8B", width=3), fill="tozeroy", fillcolor="rgba(46,139,139,0.1)"))
fig.update_layout(template=PLOTLY_TEMPLATE, height=380, margin=dict(t=10, b=10), yaxis_title="Coverage (%)")
st.plotly_chart(fig, width="stretch")

st.markdown(
    '<div class="tb-callout">📌 <b>The prevention gap:</b> Household contacts of TB patients are at significantly '
    "elevated risk of developing the disease themselves. Low preventive treatment coverage in many countries means "
    "millions of at-risk individuals, including young children, are not being protected before they ever fall ill."
    "</div>",
    unsafe_allow_html=True,
)

st.markdown("---")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader(f"Top 10 countries — eligible population ({int(latest_year)})")
    top10 = latest.nlargest(10, "e_prevtx_eligible")[["country", "e_prevtx_eligible"]].reset_index(drop=True)
    st.dataframe(relabel(top10), width="stretch", hide_index=True)

with col_b:
    st.subheader(f"Bottom 10 countries — coverage % ({int(latest_year)})")
    bottom10 = latest[latest["e_prevtx_hh_contacts_pct"] > 0].nsmallest(
        10, "e_prevtx_hh_contacts_pct")[["country", "e_prevtx_hh_contacts_pct"]].reset_index(drop=True)
    st.dataframe(relabel(bottom10), width="stretch", hide_index=True)

st.caption("Source: WHO Global TB Programme — LTBI_estimates.csv")
