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


def add_region_names(df):
    """Attach a human-readable region_name column derived from g_whoregion, if present."""
    if "g_whoregion" in df.columns:
        df = df.copy()
        df["region_name"] = df["g_whoregion"].map(WHO_REGION_NAMES)
    return df


# Human-readable labels for raw WHO column codes, used whenever a dataframe is displayed
# directly to the user (e.g. in st.dataframe tables). Charts use explicit axis titles
# instead, but any table or selectbox built from raw column names should run through this.
COLUMN_LABELS = {
    "e_inc_100k": "Incidence rate (per 100k)",
    "e_inc_100k_lo": "Incidence rate, lower bound (per 100k)",
    "e_inc_100k_hi": "Incidence rate, upper bound (per 100k)",
    "e_inc_num": "Estimated new cases",
    "e_inc_num_lo": "Estimated new cases, lower bound",
    "e_inc_num_hi": "Estimated new cases, upper bound",
    "e_mort_100k": "Mortality rate (per 100k)",
    "e_mort_num": "Estimated deaths",
    "e_mort_exc_tbhiv_num": "Estimated deaths (excluding TB/HIV)",
    "e_mort_tbhiv_num": "Estimated deaths (TB/HIV co-infected)",
    "e_inc_tbhiv_100k": "TB/HIV incidence rate (per 100k)",
    "e_inc_tbhiv_num": "Estimated TB/HIV co-infected cases",
    "e_tbhiv_prct": "% of TB cases HIV-positive",
    "c_cdr": "Case detection rate (%)",
    "c_newinc_100k": "Case notification rate (per 100k)",
    "cfr_pct": "Case fatality ratio (%)",
    "e_pop_num": "Population",
    "e_rr_pct_new": "% resistant, new cases",
    "e_rr_pct_ret": "% resistant, retreatment cases",
    "e_inc_rr_num": "Estimated RR-TB cases",
    "e_prevtx_hh_contacts_pct": "Preventive treatment coverage (%)",
    "e_prevtx_eligible": "Eligible for preventive treatment",
    "e_prevtx_kids_pct": "% of eligible who are children under 5",
    "e_hh_contacts": "Estimated household contacts",
    "budget_tot": "Total budgeted (USD)",
    "exp_tot": "Total spent (USD)",
    "c_new_tsr": "Treatment success rate, new cases (%)",
    "c_ret_tsr": "Treatment success rate, retreatment (%)",
    "c_tbhiv_tsr": "Treatment success rate, TB/HIV (%)",
    "country": "Country",
    "g_whoregion": "WHO Region",
    "region_name": "WHO Region",
    "year": "Year",
    "iso3": "Country code",
}


def relabel(df, columns=None):
    """Return a copy of df with display-friendly column names, for use right before
    showing a dataframe to the user. Pass `columns` to relabel only a subset."""
    cols = columns if columns is not None else df.columns
    rename_map = {c: COLUMN_LABELS.get(c, c) for c in cols}
    return df.rename(columns=rename_map)


@st.cache_data
def load_burden():
    df = pd.read_csv(os.path.join(DATA_DIR, "TB_burden_countries_20260615.csv"), low_memory=False)
    return add_region_names(df)


@st.cache_data
def load_notifications():
    df = pd.read_csv(os.path.join(DATA_DIR, "TB_notifications_20260615.csv"), low_memory=False)
    return add_region_names(df)


@st.cache_data
def load_outcomes():
    df = pd.read_csv(os.path.join(DATA_DIR, "TB_outcomes_20260615.csv"), low_memory=False)
    return add_region_names(df)


@st.cache_data
def load_mdr():
    df = pd.read_csv(os.path.join(DATA_DIR, "MDR_RR_TB_burden_estimates_20260615.csv"), low_memory=False)
    return add_region_names(df)


@st.cache_data
def load_age_sex():
    df = pd.read_csv(os.path.join(DATA_DIR, "TB_burden_age_sex_20260615.csv"), low_memory=False)
    df["region_name"] = None
    return df


@st.cache_data
def load_outcomes_age_sex():
    df = pd.read_csv(os.path.join(DATA_DIR, "TB_outcomes_age_sex_20260615.csv"), low_memory=False)
    return add_region_names(df)


@st.cache_data
def load_budget():
    df = pd.read_csv(os.path.join(DATA_DIR, "TB_budget_20260615.csv"), low_memory=False)
    return add_region_names(df)


@st.cache_data
def load_expenditure():
    df = pd.read_csv(os.path.join(DATA_DIR, "TB_expenditure_utilisation_20260615.csv"), low_memory=False)
    return add_region_names(df)


@st.cache_data
def load_ltbi():
    df = pd.read_csv(os.path.join(DATA_DIR, "LTBI_estimates_20260615.csv"), low_memory=False)
    return add_region_names(df)


@st.cache_data
def load_dr_surveillance():
    df = pd.read_csv(os.path.join(DATA_DIR, "TB_dr_surveillance_20260615.csv"), low_memory=False)
    return add_region_names(df)


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
