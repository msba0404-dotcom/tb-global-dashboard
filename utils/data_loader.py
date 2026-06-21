"""
Shared data loading utilities for the TB Global Burden Dashboard.
All functions are cached with st.cache_data so files are read once per session.
"""

import pandas as pd
import streamlit as st
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

WHO_REGION_NAMES = {
    "AFR": "Africa",
    "AMR": "Americas",
    "EMR": "Eastern Mediterranean",
    "EUR": "Europe",
    "SEA": "South-East Asia",
    "WPR": "Western Pacific",
}


@st.cache_data
def load_burden():
    df = pd.read_csv(os.path.join(DATA_DIR, "TB_burden_countries_20260615.csv"), low_memory=False)
    df["region_name"] = df["g_whoregion"].map(WHO_REGION_NAMES)
    return df


@st.cache_data
def load_notifications():
    return pd.read_csv(os.path.join(DATA_DIR, "TB_notifications_20260615.csv"), low_memory=False)


@st.cache_data
def load_outcomes():
    return pd.read_csv(os.path.join(DATA_DIR, "TB_outcomes_20260615.csv"), low_memory=False)


@st.cache_data
def load_mdr():
    return pd.read_csv(os.path.join(DATA_DIR, "MDR_RR_TB_burden_estimates_20260615.csv"), low_memory=False)


@st.cache_data
def load_age_sex():
    df = pd.read_csv(os.path.join(DATA_DIR, "TB_burden_age_sex_20260615.csv"), low_memory=False)
    df["region_name"] = None
    return df


@st.cache_data
def load_outcomes_age_sex():
    return pd.read_csv(os.path.join(DATA_DIR, "TB_outcomes_age_sex_20260615.csv"), low_memory=False)


@st.cache_data
def load_budget():
    return pd.read_csv(os.path.join(DATA_DIR, "TB_budget_20260615.csv"), low_memory=False)


@st.cache_data
def load_expenditure():
    return pd.read_csv(os.path.join(DATA_DIR, "TB_expenditure_utilisation_20260615.csv"), low_memory=False)


@st.cache_data
def load_ltbi():
    return pd.read_csv(os.path.join(DATA_DIR, "LTBI_estimates_20260615.csv"), low_memory=False)


@st.cache_data
def load_dr_surveillance():
    return pd.read_csv(os.path.join(DATA_DIR, "TB_dr_surveillance_20260615.csv"), low_memory=False)


@st.cache_data
def load_data_dictionary():
    return pd.read_csv(os.path.join(DATA_DIR, "TB_data_dictionary_20260615.csv"), low_memory=False)


@st.cache_data
def compute_endtb_progress():
    """
    Computes 2015 -> latest year % change in incidence per 100k for each country,
    and classifies progress toward the WHO End TB Strategy 2030 target
    (80% reduction in incidence from the 2015 baseline).
    """
    df = load_burden()
    latest_year = df["year"].max()

    base = df[df["year"] == 2015][["country", "iso3", "g_whoregion", "region_name", "e_inc_100k"]].rename(
        columns={"e_inc_100k": "inc_2015"}
    )
    latest = df[df["year"] == latest_year][["country", "iso3", "e_inc_100k", "e_pop_num"]].rename(
        columns={"e_inc_100k": "inc_latest"}
    )

    m = base.merge(latest, on=["country", "iso3"], how="inner")
    # Exclude zero/NaN baselines -- can't compute meaningful % change
    m = m[(m["inc_2015"] > 0) & m["inc_2015"].notna() & m["inc_latest"].notna()].copy()
    m["pct_change"] = (m["inc_latest"] - m["inc_2015"]) / m["inc_2015"] * 100
    m["target_2030_value"] = m["inc_2015"] * 0.2  # 80% reduction target

    def risk_cat(pct):
        if pct <= -50:
            return "On track"
        elif pct <= -20:
            return "Moderate progress"
        elif pct <= 0:
            return "Slow progress"
        else:
            return "Worsening"

    m["risk_category"] = m["pct_change"].apply(risk_cat)
    m["latest_year"] = latest_year
    return m


def check_password():
    """Simple password gate for the dashboard landing page."""
    PASSWORD = "tb2026"

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown("### 🔒 Restricted Access")
    pwd = st.text_input("Enter password to access the dashboard", type="password")
    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")
    return False
