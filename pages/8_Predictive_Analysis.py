import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import check_password, load_burden, load_mdr, load_expenditure, compute_endtb_progress
from utils.theme import THEME_CSS, PLOTLY_TEMPLATE, RISK_COLORS

st.set_page_config(page_title="Predictive Analysis | TB Dashboard", page_icon="🔮", layout="wide")
st.markdown(THEME_CSS, unsafe_allow_html=True)

if not check_password():
    st.stop()

st.markdown('<p class="tb-eyebrow">Page 8 · Bonus component</p>', unsafe_allow_html=True)
st.title("🔮 Predictive Analysis")
st.markdown(
    "Forecasting future TB incidence and classifying countries by their risk of missing the "
    "**WHO End TB Strategy 2030 target** (an 80% reduction in incidence from the 2015 baseline)."
)
st.markdown("---")

burden = load_burden()
mdr = load_mdr()
expenditure = load_expenditure()
progress = compute_endtb_progress()

tab1, tab2 = st.tabs(["📈 Incidence Forecasting", "🎯 End TB 2030 Risk Classifier"])

# ============== TAB 1: FORECASTING ==============
with tab1:
    st.subheader("Forecast TB incidence by country (to 2030)")
    st.markdown(
        "Select a country to see its historical incidence trend and a simple forward projection."
    )

    countries = sorted(burden["country"].unique().tolist())
    default_idx = countries.index("India") if "India" in countries else 0
    country_sel = st.selectbox("Select a country", countries, index=default_idx)

    st.markdown("")  # spacing so the chart title below doesn't sit flush under the dropdown

    country_df = burden[burden["country"] == country_sel][["year", "e_inc_100k"]].dropna().sort_values("year")

    if len(country_df) < 5:
        st.warning("Not enough historical data to forecast this country.")
    else:
        X = country_df["year"].values.reshape(-1, 1)
        y = country_df["e_inc_100k"].values

        model = LinearRegression()
        model.fit(X, y)

        future_years = np.arange(country_df["year"].max() + 1, 2031).reshape(-1, 1)
        future_preds = model.predict(future_years) if len(future_years) > 0 else np.array([])

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=country_df["year"], y=country_df["e_inc_100k"], mode="lines+markers",
                                  name="Historical", line=dict(color="#1F5C82", width=3)))
        if len(future_years) > 0:
            fig.add_trace(go.Scatter(x=future_years.flatten(), y=future_preds, mode="lines+markers",
                                      name="Forecast (linear trend)", line=dict(color="#E0A030", width=3, dash="dash")))

        baseline_2015 = country_df[country_df["year"] == 2015]["e_inc_100k"]
        if len(baseline_2015) > 0 and baseline_2015.values[0] > 0:
            target_val = baseline_2015.values[0] * 0.2
            fig.add_hline(y=target_val, line_dash="dot", line_color="#2E8B5A",
                          annotation_text=f"2030 target ({target_val:.1f} per 100k)")

        fig.update_layout(template=PLOTLY_TEMPLATE, height=440, margin=dict(t=50, b=10),
                          yaxis_title="Incidence per 100,000", xaxis_title="Year",
                          title=dict(text=f"{country_sel}: incidence trend & linear forecast", y=0.97))
        st.plotly_chart(fig, width="stretch")

        if len(future_preds) > 0:
            pred_2030 = future_preds[-1] if future_years.flatten()[-1] == 2030 else model.predict([[2030]])[0]
            st.markdown(
                f'<div class="tb-callout">📌 <b>Linear projection:</b> Based on the 2000–{int(country_df["year"].max())} '
                f"trend, {country_sel}'s incidence rate is projected to reach approximately "
                f"<b>{max(pred_2030, 0):.1f} per 100,000</b> by 2030. This is a simple linear extrapolation and "
                "does not account for policy changes, outbreaks, or health system shocks.</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="tb-callout-red">⚠️ <b>This is illustrative trend-fitting, not a tested forecasting model.</b> '
            "The line is a single linear regression fit on this country's full history, with no train/test split "
            "and no accuracy evaluation against held-out years. It is meant to show the direction and pace of the "
            "current trend, not to be read as a validated prediction. (The classifier in the next tab, by contrast, "
            "<i>is</i> evaluated on held-out data — see its accuracy score there.)</div>",
            unsafe_allow_html=True,
        )

        st.caption(
            "Method: Ordinary least squares linear regression on historical incidence (e_inc_100k) vs. year. "
            "A simple, transparent baseline forecast — more advanced models (e.g. Prophet, ARIMA) could improve accuracy "
            "but require more tuning per country."
        )

# ============== TAB 2: RISK CLASSIFIER ==============
with tab2:
    st.subheader("Which countries are at risk of missing the 2030 target?")

    st.markdown(
        "Countries are classified into four categories based on their incidence change since the 2015 baseline:"
    )
    legend_cols = st.columns(4)
    for col, (cat, color) in zip(legend_cols, RISK_COLORS.items()):
        col.markdown(f"<span style='color:{color}; font-size:1.3rem;'>●</span> **{cat}**", unsafe_allow_html=True)

    st.markdown("---")

    dist = progress["risk_category"].value_counts().reindex(list(RISK_COLORS.keys())).reset_index()
    dist.columns = ["risk_category", "count"]

    col_a, col_b = st.columns([1, 2])
    with col_a:
        fig_pie = px.pie(dist, names="risk_category", values="count", color="risk_category",
                          color_discrete_map=RISK_COLORS, hole=0.45)
        fig_pie.update_layout(template=PLOTLY_TEMPLATE, height=360, margin=dict(t=10, b=10), showlegend=False)
        st.plotly_chart(fig_pie, width="stretch")
        st.metric("Countries on track for 80% reduction", f"{(progress['risk_category']=='On track').sum()} / {len(progress)}")

    with col_b:
        st.markdown("**Map: progress toward the 2030 target**")
        fig_map = px.choropleth(progress, locations="iso3", color="risk_category", hover_name="country",
                                 color_discrete_map=RISK_COLORS,
                                 hover_data={"pct_change": ":.1f"})
        fig_map.update_layout(template=PLOTLY_TEMPLATE, height=380, margin=dict(t=10, b=10),
                              geo=dict(showframe=False, projection_type="natural earth"))
        st.plotly_chart(fig_map, width="stretch")

    st.markdown(
        '<div class="tb-callout-red">⚠️ <b>Key finding:</b> Only a small share of countries have achieved the '
        "trajectory needed to hit WHO's 80% incidence reduction target by 2030. Most countries are making "
        "moderate or slow progress, and roughly one in five are seeing incidence actually <b>increase</b> since "
        "2015.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.subheader("Predictive model: classifying country risk")

    st.markdown(
        '<div class="tb-callout">📌 <b>How this prediction actually works:</b> This is <b>supervised</b> learning, '
        "not unsupervised — but the labels aren't handed to us by WHO; we derive them ourselves. First, we "
        "calculate each country's real % change in incidence from 2015 to today and sort it into one of the four "
        "risk categories using the fixed rule shown above (this part is just arithmetic, not a model). "
        "<b>Then</b> we train a Random Forest to predict <i>that label</i> using a different set of features "
        "— population, TB/HIV %, case detection rate, case fatality ratio, drug resistance %, and TB expenditure "
        "— none of which is the incidence change itself. So the model isn't told the answer; it has to infer the "
        "risk category from country characteristics that are conceptually separate from the outcome being "
        "predicted.</div>",
        unsafe_allow_html=True,
    )

    # Build feature set
    latest_year = burden["year"].max()
    feats = burden[burden["year"] == latest_year][
        ["country", "iso3", "e_pop_num", "e_tbhiv_prct", "c_cdr", "cfr_pct"]
    ]
    mdr_latest = mdr[mdr["year"] == mdr["year"].max()][["country", "e_rr_pct_new"]]
    exp_latest = expenditure[expenditure["year"] == expenditure["year"].max()][["country", "exp_tot"]]

    model_df = feats.merge(mdr_latest, on="country", how="left").merge(exp_latest, on="country", how="left")
    model_df = model_df.merge(progress[["country", "risk_category"]], on="country", how="inner")

    feature_cols = ["e_pop_num", "e_tbhiv_prct", "c_cdr", "cfr_pct", "e_rr_pct_new", "exp_tot"]
    model_df_clean = model_df.dropna(subset=feature_cols + ["risk_category"])

    if len(model_df_clean) < 30:
        st.warning("Not enough complete cases to train a reliable classifier with current data.")
    else:
        X = model_df_clean[feature_cols]
        y = model_df_clean["risk_category"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

        clf = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42, class_weight="balanced")
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        acc = accuracy_score(y_test, y_pred)

        col_c, col_d = st.columns([1, 1])
        with col_c:
            st.metric("Model accuracy (held-out test set)", f"{acc*100:.0f}%")
            st.caption(f"Trained on {len(X_train)} countries, tested on {len(X_test)}.")

            importance = pd.DataFrame({
                "feature": ["Population", "TB/HIV %", "Case detection rate", "Case fatality ratio",
                            "Drug resistance %", "TB expenditure"],
                "importance": clf.feature_importances_
            }).sort_values("importance", ascending=True)
            fig_imp = px.bar(importance, x="importance", y="feature", orientation="h",
                              color_discrete_sequence=["#1F5C82"])
            fig_imp.update_layout(template=PLOTLY_TEMPLATE, height=300, margin=dict(t=10, b=10),
                                  xaxis_title="Feature importance", yaxis_title="")
            st.plotly_chart(fig_imp, width="stretch")

        with col_d:
            st.markdown("**What drives the prediction?**")
            st.markdown(
                """
                The Random Forest classifier uses six country-level indicators to predict which of the
                four risk categories a country falls into:
                - **Case detection rate** and **case fatality ratio** — health system capacity signals
                - **TB/HIV co-infection %** and **drug resistance %** — disease severity factors
                - **TB expenditure** — funding-side inequality signal
                - **Population** — scale control

                This is a transparent, interpretable baseline model. With more complete funding and
                socioeconomic data (e.g. GDP per capita, health spending as % of GDP), classification
                accuracy could likely be improved further.
                """
            )

        st.caption(
            "Method: Random Forest classifier (scikit-learn), 200 trees, balanced class weights to handle "
            "the uneven distribution of risk categories. Train/test split: 75/25, stratified by risk category."
        )

st.caption("Source: WHO Global TB Programme — TB_burden_countries.csv, MDR_RR_TB_burden_estimates.csv, TB_expenditure_utilisation.csv")
