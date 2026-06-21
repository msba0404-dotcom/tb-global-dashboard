"""
Shared visual theme for the TB Global Burden Dashboard.
Palette: WHO-report inspired deep navy/teal, restrained accent of amber for risk callouts.
"""

THEME_CSS = """
<style>
    :root {
        --tb-navy: #0E2A42;
        --tb-blue: #1F5C82;
        --tb-teal: #2E8B8B;
        --tb-amber: #E0A030;
        --tb-red: #C0392B;
        --tb-bg: #F7F9FA;
        --tb-card: #FFFFFF;
    }

    .stApp {
        background-color: var(--tb-bg);
    }

    h1, h2, h3 {
        color: var(--tb-navy) !important;
        font-family: 'Georgia', serif;
    }

    p, li, span, label, .stMarkdown, [data-testid="stMarkdownContainer"] {
        color: #1A1A1A;
    }

    [data-testid="stCaptionContainer"] {
        color: #5A6B78 !important;
    }

    [data-testid="stMetricValue"] {
        font-family: 'Georgia', serif;
        color: var(--tb-navy);
    }

    [data-testid="stMetricLabel"] {
        color: #5A6B78;
        font-weight: 500;
        text-transform: uppercase;
        font-size: 0.78rem;
        letter-spacing: 0.04em;
    }

    [data-testid="stMetric"] {
        background-color: var(--tb-card);
        border: 1px solid #E2E8EC;
        border-left: 4px solid var(--tb-teal);
        border-radius: 6px;
        padding: 14px 16px;
    }

    .tb-eyebrow {
        color: var(--tb-teal);
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 0.8rem;
        margin-bottom: -8px;
    }

    .tb-callout {
        background-color: #FFF7E8;
        border-left: 4px solid var(--tb-amber);
        padding: 14px 18px;
        border-radius: 4px;
        margin: 10px 0;
    }

    .tb-callout-red {
        background-color: #FDECEA;
        border-left: 4px solid var(--tb-red);
        padding: 14px 18px;
        border-radius: 4px;
        margin: 10px 0;
    }

    section[data-testid="stSidebar"] {
        background-color: var(--tb-navy);
    }

    section[data-testid="stSidebar"] * {
        color: #E8EEF2 !important;
    }

    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
        background-color: #1A3F5C;
    }

    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] * {
        color: white !important;
    }

    /* Dropdown options menu renders outside the sidebar, at document root */
    div[data-baseweb="popover"] li {
        color: #1A1A1A !important;
        background-color: white !important;
    }

    div[data-baseweb="popover"] li:hover {
        background-color: #EBF3FB !important;
    }

    hr {
        border-top: 1px solid #D8E0E5;
    }
</style>
"""

PLOTLY_TEMPLATE = "plotly_white"
COLOR_SEQUENCE = ["#1F5C82", "#2E8B8B", "#E0A030", "#C0392B", "#5A6B78", "#8E44AD"]
RISK_COLORS = {
    "On track": "#2E8B5A",
    "Moderate progress": "#2E8B8B",
    "Slow progress": "#E0A030",
    "Worsening": "#C0392B",
}