# Tuberculosis (TB) Global Burden Dashboard

A Streamlit dashboard analyzing global TB burden, inequality, drug resistance, and progress
toward WHO's End TB Strategy 2030 target. Built for MSBA382 – Healthcare Analytics.

## Password

The landing page is password-protected. Current password: **tb2026**
(Change it in `utils/data_loader.py`, in the `check_password()` function.)

## Pages

1. **Overview & KPIs** — global incidence/mortality trends, treatment success
2. **Geographic Map** — choropleth maps by country and year
3. **Demographics** — age, sex, and risk factor breakdowns (2024 snapshot)
4. **Disease Subtypes** — MDR-TB / XDR-TB burden and outcomes
5. **Treatment Outcomes** — success/failure/death rates by cohort and sex
6. **Funding & Inequality** — budget vs. actual expenditure, funding sources
7. **Latent TB & Prevention** — household contact tracing, preventive treatment coverage
8. **Predictive Analysis** — incidence forecasting (linear regression) + End TB 2030 risk
   classifier (Random Forest)

## Run locally

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Deploy to Streamlit Community Cloud

1. Create a new GitHub repository (e.g. `tb-global-dashboard`)
2. Upload all files in this folder, preserving the structure:
   ```
   tb-dashboard/
   ├── Home.py
   ├── pages/
   ├── utils/
   ├── data/
   ├── requirements.txt
   └── README.md
   ```
3. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub
4. Click "New app" → select your repository → set main file to `Home.py`
5. Click "Deploy" — you'll get a public URL like `https://your-app-name.streamlit.app`

## Data source

World Health Organization, Global Tuberculosis Programme.
https://www.who.int/teams/global-tuberculosis-programme/data

All 10 CSV files in `data/` were downloaded directly from the WHO portal (no registration
required) and are used as-is, with cleaning/aggregation handled at runtime in `utils/data_loader.py`.
