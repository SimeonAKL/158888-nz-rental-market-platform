"""Shared layout helpers for the Streamlit dashboard."""

from __future__ import annotations

import base64
import html
import math
from pathlib import Path

import streamlit as st

HOME_HERO_IMAGE_PATH = (
    Path(__file__).resolve().parents[3]
    / "assets"
    / "auckland_skyline.jpg"
)

PAGE_MAX_WIDTH = "1280px"
PAGE_MAX_WIDTH_XL = "1500px"


_BASE_CSS = """
<style>
/* ============================================================
   Design tokens
   ============================================================ */

:root {
    --brand-blue: #1769ff;
    --brand-blue-2: #2f80ed;
    --brand-blue-dark: #0b2f89;
    --brand-text: #102047;
    --heading-text: #15264d;
    --muted-text: #64728f;
    --soft-text: #7b88a4;
    --positive: #13864a;
    --negative: #cc4545;
    --card-border: rgba(38, 91, 170, 0.10);
    --card-border-hover: rgba(23, 105, 255, 0.20);
    --card-bg: linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(247, 250, 255, 0.96));
    --card-shadow: 0 8px 22px rgba(24, 48, 94, 0.05), 0 1px 2px rgba(24, 48, 94, 0.03);
    --card-shadow-hover: 0 13px 28px rgba(24, 48, 94, 0.08), 0 2px 4px rgba(24, 48, 94, 0.03);
}

/* ============================================================
   Streamlit chrome: hide header, toolbar, sidebar, footer
   ============================================================ */

header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stHeaderActionElements"],
[data-testid="stAppDeployButton"],
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"] {
    display: none !important;
}

#MainMenu,
footer {
    visibility: hidden;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* ============================================================
   App background
   ============================================================ */

.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(23, 105, 255, 0.08), transparent 22%),
        radial-gradient(circle at 92% 8%, rgba(82, 167, 255, 0.10), transparent 18%),
        linear-gradient(180deg, #f7f9ff 0%, #f3f6fc 100%);
}

/* ============================================================
   Page width (single source of truth)
   ============================================================ */

[data-testid="stMainBlockContainer"] {
    max-width: __PAGE_MAX_WIDTH__ !important;
    width: 100% !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding: 1.6rem 3rem 3rem 3rem !important;
}

@media (min-width: 1800px) {
    [data-testid="stMainBlockContainer"] {
        max-width: __PAGE_MAX_WIDTH_XL__ !important;
    }
}

@media (max-width: 1200px) {
    [data-testid="stMainBlockContainer"] {
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
}

@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"] {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
}

/* Column spacing */
div[data-testid="stHorizontalBlock"] {
    gap: 0.9rem;
}

/* ============================================================
   Top navigation
   ============================================================ */

.st-key-top_nav_shell {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 0 0 0.9rem 0;
    margin-bottom: 1.4rem;
    border-bottom: 1px solid rgba(24, 48, 94, 0.09);
}

/* Prevent Markdown margins from pushing the brand out of alignment */
.st-key-top_nav_shell .stMarkdown,
.st-key-top_nav_shell [data-testid="stMarkdownContainer"] {
    margin: 0 !important;
    padding: 0 !important;
}

.st-key-top_nav_shell [data-testid="stHorizontalBlock"] {
    gap: 0.45rem;
}

/* Brand */
.brand-box {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    min-height: 52px;
}

.brand-icon {
    width: 50px;
    height: 50px;
    flex-shrink: 0;
    border-radius: 14px;
    background: linear-gradient(135deg, #dcebff 0%, #eef5ff 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    box-shadow: inset 0 0 0 1px rgba(23, 105, 255, 0.08);
}

.brand-title {
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--brand-text);
    line-height: 1.05;
    letter-spacing: -0.02em;
}

.brand-subtitle {
    color: var(--muted-text);
    font-size: 0.88rem;
    margin-top: 0.12rem;
}

/* Nav buttons: hug their text and center in the column */
.st-key-top_nav_shell div.stButton {
    display: flex;
    justify-content: center;
}

.st-key-top_nav_shell div.stButton > button {
    min-height: 2.55rem;
    border-radius: 999px !important;
    padding: 0 1.3rem !important;
    transition: background 0.16s ease, color 0.16s ease;
}

.st-key-top_nav_shell div.stButton > button p {
    font-size: 0.98rem;
    font-weight: 600;
    white-space: nowrap;
}

/* Inactive item */
.st-key-top_nav_shell button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid transparent !important;
    color: #53617f !important;
    box-shadow: none !important;
}

.st-key-top_nav_shell button[kind="secondary"]:hover {
    background: rgba(23, 105, 255, 0.07) !important;
    color: var(--brand-blue) !important;
}

/* Active item */
.st-key-top_nav_shell button[kind="primary"] {
    background: linear-gradient(135deg, var(--brand-blue) 0%, var(--brand-blue-2) 100%) !important;
    border: 1px solid transparent !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(23, 105, 255, 0.20) !important;
}

/* Keyboard focus */
.st-key-top_nav_shell div.stButton > button:focus-visible {
    outline: 2px solid var(--brand-blue) !important;
    outline-offset: 2px;
}

@media (max-width: 900px) {
    .brand-icon {
        width: 44px;
        height: 44px;
        font-size: 1.4rem;
    }

    .brand-title {
        font-size: 1.2rem;
    }
}

/* ============================================================
   General buttons (outside the nav)
   ============================================================ */

div.stButton > button {
    border-radius: 12px;
    min-height: 2.6rem;
    font-weight: 600;
}

/* ============================================================
   Home hero
   ============================================================ */

.hero-card {
    position: relative;
    overflow: hidden;
    border-radius: 24px;
    min-height: 270px;
    padding: 2.15rem;
    margin-bottom: 1.65rem;
    background:
        linear-gradient(90deg, rgba(255,255,255,0.88) 0%, rgba(255,255,255,0.74) 38%, rgba(255,255,255,0.10) 100%),
        url('__HERO_IMAGE__');
    background-size: cover;
    background-position: center 64%;
    border: 1px solid rgba(23, 105, 255, 0.08);
    box-shadow:
        0 14px 34px rgba(24, 48, 94, 0.08),
        0 2px 6px rgba(24, 48, 94, 0.03);
}

.hero-card::before {
    content: "";
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 18% 22%, rgba(23, 105, 255, 0.12), transparent 22%);
    pointer-events: none;
}

.hero-content {
    position: relative;
    max-width: 760px;
    z-index: 1;
}

.hero-chip {
    display: inline-block;
    padding: 0.38rem 0.8rem;
    border-radius: 999px;
    background: rgba(23, 105, 255, 0.10);
    color: var(--brand-blue-dark);
    font-size: 0.82rem;
    font-weight: 700;
    margin-bottom: 1rem;
}

.hero-title {
    max-width: 690px;
    font-size: 2.25rem;
    font-weight: 900;
    color: var(--brand-text);
    line-height: 1.08;
    letter-spacing: -0.025em;
    margin-bottom: 0.7rem;
}

.hero-subtitle {
    max-width: 690px;
    font-size: 1rem;
    color: #31446f;
    line-height: 1.65;
}

@media (max-width: 1100px) {
    .hero-title {
        font-size: 1.9rem;
    }
}

/* ============================================================
   Section headings (Home)
   ============================================================ */

.section-title {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    font-size: 1.48rem;
    line-height: 1.25;
    font-weight: 800;
    letter-spacing: -0.018em;
    color: var(--brand-text);
    margin-top: 0.45rem;
    margin-bottom: 0.28rem;
}

.section-title::before {
    content: "";
    display: inline-block;
    width: 5px;
    height: 25px;
    border-radius: 999px;
    background: linear-gradient(180deg, var(--brand-blue) 0%, #58a5ff 100%);
}

.section-caption {
    margin-left: 0.72rem;
    margin-bottom: 1rem;
    color: #73809d;
    font-size: 0.91rem;
    line-height: 1.5;
}

/* ============================================================
   KPI cards (Home)
   ============================================================ */

.metric-card {
    position: relative;
    overflow: hidden;
    min-height: 150px;
    padding: 1.28rem 1.25rem;
    border-radius: 20px;
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    box-shadow: var(--card-shadow);
}

.metric-card::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, var(--brand-blue), #67adff);
    opacity: 0.82;
}

.metric-label {
    color: #657493;
    font-size: 0.86rem;
    font-weight: 700;
    margin-bottom: 0.72rem;
}

.metric-value {
    color: var(--brand-text);
    font-size: 2.05rem;
    font-weight: 900;
    line-height: 1;
    letter-spacing: -0.025em;
    margin-bottom: 0.62rem;
}

.metric-note {
    color: var(--soft-text);
    font-size: 0.82rem;
    line-height: 1.52;
}

/* ============================================================
   Module cards: st.container(border=True, key="module_xxx")
   ============================================================ */

[class*="st-key-module_"] {
    border-radius: 20px !important;
    border: 1px solid var(--card-border) !important;
    background: var(--card-bg) !important;
    padding: 1.3rem 1.4rem !important;
    box-shadow: var(--card-shadow);
    transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

[class*="st-key-module_"]:hover {
    border-color: var(--card-border-hover) !important;
    box-shadow: var(--card-shadow-hover);
}

[class*="st-key-module_"] h3 {
    color: var(--heading-text) !important;
    font-size: 1.2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.015em;
    padding: 0 0 0.3rem 0 !important;
}

[class*="st-key-module_"] p {
    color: var(--muted-text);
    font-size: 0.93rem;
    line-height: 1.55;
}

/* ============================================================
   Page links
   ============================================================ */

div[data-testid="stPageLink"] a {
    width: fit-content;
    border-radius: 10px;
    padding: 0.5rem 0.75rem;
    background: #f1f6ff;
    border: 1px solid rgba(23, 105, 255, 0.11);
    color: #195bc4;
    font-size: 0.88rem;
    font-weight: 700;
    text-decoration: none;
    transition: background 0.18s ease;
}

div[data-testid="stPageLink"] a:hover {
    background: #e6f0ff;
}

/* ============================================================
   Scope panels (Home)
   ============================================================ */

.soft-panel {
    min-height: 142px;
    border-radius: 20px;
    padding: 1.2rem 1.25rem;
    margin-top: 0.25rem;
    margin-bottom: 1rem;
    border: 1px solid var(--card-border);
    background: var(--card-bg);
    box-shadow: var(--card-shadow);
}

.small-heading {
    color: var(--heading-text);
    font-size: 1.05rem;
    font-weight: 800;
    margin-bottom: 0.6rem;
}

.small-text {
    color: #6d7a96;
    font-size: 0.89rem;
    line-height: 1.58;
}

/* ============================================================
   Interpretation note (Home)
   ============================================================ */

.notice-box {
    border-radius: 18px;
    padding: 1.05rem 1.2rem;
    background: linear-gradient(90deg, rgba(23, 105, 255, 0.075), rgba(75, 154, 255, 0.035));
    border: 1px solid rgba(23, 105, 255, 0.11);
    color: #425475;
    font-size: 0.94rem;
    line-height: 1.6;
}

/* ============================================================
   Shared analysis-page components
   ============================================================ */

/* Page hero (image set inline by render_page_hero) */
.page-hero {
    min-height: 190px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 2rem 2.2rem;
    margin-bottom: 0.4rem;
    border-radius: 24px;
    background-size: cover;
    background-position: center 60%;
    border: 1px solid rgba(23, 105, 255, 0.08);
    box-shadow:
        0 14px 34px rgba(24, 48, 94, 0.08),
        0 2px 6px rgba(24, 48, 94, 0.03);
}

.page-hero-title {
    color: var(--brand-text);
    font-size: 2.3rem;
    font-weight: 900;
    line-height: 1.05;
    letter-spacing: -0.035em;
    margin-bottom: 0.5rem;
}

.page-hero-caption {
    color: #31446f;
    font-size: 0.98rem;
    line-height: 1.6;
    max-width: 620px;
}

/* Filter card: st.container(key="filters_xxx") */
[class*="st-key-filters_"] {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 20px;
    padding: 1.15rem 1.3rem 1rem 1.3rem;
    box-shadow: var(--card-shadow);
}

[class*="st-key-filters_"] label p {
    color: #53617f;
    font-size: 0.82rem;
    font-weight: 700;
}

.filter-title {
    color: var(--heading-text);
    font-size: 1rem;
    font-weight: 800;
    margin-bottom: 0.15rem;
}

.filter-caption {
    color: var(--soft-text);
    font-size: 0.83rem;
    margin-bottom: 0.4rem;
}

/* Selected series header */
.series-card {
    padding: 1.15rem 1.4rem;
    border-radius: 20px;
    background: linear-gradient(110deg, rgba(232, 242, 255, 0.95) 0%, rgba(255, 255, 255, 0.98) 100%);
    border: 1px solid rgba(23, 105, 255, 0.10);
    border-left: 5px solid var(--brand-blue);
}

.series-title {
    color: var(--brand-text);
    font-size: 1.45rem;
    font-weight: 850;
    letter-spacing: -0.02em;
    margin-bottom: 0.25rem;
}

.series-meta {
    color: #6d7a96;
    font-size: 0.87rem;
}

/* Provisional source note */
.source-note {
    border-radius: 14px;
    padding: 0.7rem 1rem;
    background: rgba(255, 193, 7, 0.08);
    border: 1px solid rgba(209, 154, 0, 0.16);
    color: #6b5824;
    font-size: 0.84rem;
    line-height: 1.5;
}

/* Stat cards */
.stat-card {
    position: relative;
    overflow: hidden;
    min-height: 138px;
    padding: 1.15rem 1.2rem;
    border-radius: 19px;
    border: 1px solid var(--card-border);
    background: var(--card-bg);
    box-shadow: var(--card-shadow);
}

.stat-card::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    width: 100%;
    height: 4px;
    background: linear-gradient(90deg, var(--brand-blue), #67adff);
}

/* Flat variant for stats nested inside a content card */
.stat-card.flat {
    min-height: 112px;
    border-radius: 16px;
    background: #f7faff;
    border-color: rgba(38, 91, 170, 0.09);
    box-shadow: none;
}

.stat-card.flat::before {
    display: none;
}

.stat-label {
    color: #657493;
    font-size: 0.82rem;
    font-weight: 700;
    margin-bottom: 0.6rem;
}

.stat-value {
    color: var(--brand-text);
    font-size: 1.8rem;
    font-weight: 900;
    line-height: 1.05;
    letter-spacing: -0.025em;
}

.stat-card.flat .stat-value {
    font-size: 1.45rem;
}

.stat-value.positive {
    color: var(--positive);
}

.stat-value.negative {
    color: var(--negative);
}

.stat-note {
    color: var(--soft-text);
    font-size: 0.79rem;
    line-height: 1.45;
    margin-top: 0.5rem;
}

/* Content cards: st.container(key="card_xxx") */
[class*="st-key-card_"] {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid var(--card-border);
    border-radius: 22px;
    padding: 1.25rem 1.4rem;
    box-shadow: var(--card-shadow);
    margin-top: 0.4rem;
}

.card-title {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    color: var(--brand-text);
    font-size: 1.3rem;
    font-weight: 850;
    letter-spacing: -0.018em;
    margin-bottom: 0.2rem;
}

.card-title::before {
    content: "";
    width: 4px;
    height: 21px;
    border-radius: 999px;
    background: linear-gradient(180deg, var(--brand-blue), #63adff);
}

.card-caption {
    color: #7885a0;
    font-size: 0.85rem;
    line-height: 1.5;
    margin-left: 0.65rem;
    margin-bottom: 0.5rem;
}

/* Chart legend */
.chart-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 1.4rem;
    color: #64728f;
    font-size: 0.82rem;
    margin-left: 0.65rem;
}

.chart-legend span {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
}

.chart-legend .swatch {
    display: inline-block;
    width: 22px;
    border-radius: 999px;
}

/* Download buttons: st.container(key="download_xxx") */
[class*="st-key-download_"] div.stDownloadButton {
    display: flex;
    justify-content: flex-end;
}

[class*="st-key-download_"] button {
    border-radius: 10px !important;
}

/* Tables inside content cards */
[class*="st-key-card_"] [data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}

@media (max-width: 900px) {
    .page-hero {
        padding: 1.5rem 1.4rem;
    }

    .page-hero-title {
        font-size: 1.9rem;
    }
}

/* ============================================================
   Reduced motion
   ============================================================ */

@media (prefers-reduced-motion: reduce) {
    * {
        transition: none !important;
    }
}
</style>
"""


# ---------------------------------------------------------------------
# Styles and navigation
# ---------------------------------------------------------------------


def inject_home_styles() -> None:
    """Inject shared CSS for all dashboard pages."""

    home_hero_image = (
        _image_data_uri(str(HOME_HERO_IMAGE_PATH))
        or ""
    )

    css = (
        _BASE_CSS.replace("__HERO_IMAGE__", home_hero_image)
        .replace("__PAGE_MAX_WIDTH_XL__", PAGE_MAX_WIDTH_XL)
        .replace("__PAGE_MAX_WIDTH__", PAGE_MAX_WIDTH)
    )

    st.markdown(
        css,
        unsafe_allow_html=True,
    )

NAV_ITEMS = [
    ("Home", "app.py"),
    ("Overview", "pages/1_Overview.py"),
    ("Historical Analytics", "pages/2_Historical_Analytics.py"),
    ("Forecasting", "pages/3_Forecasting.py"),
    ("Model Performance", "pages/4_Model_Performance.py"),
    ("Anomaly Detection", "pages/5_Anomaly_Detection.py"),
]


def render_top_navigation(active_page: str) -> None:
    """Render a top navigation bar for the dashboard."""

    with st.container(key="top_nav_shell"):
        brand_col, *nav_cols = st.columns(
            [2.9, 1.1, 1.2, 1.6, 1.45, 1.5, 1.55],
            vertical_alignment="center",
        )

        with brand_col:
            render_html(
                """
                <div class="brand-box">
                    <div class="brand-icon">🏠</div>
                    <div>
                        <div class="brand-title">NZ Rental Market</div>
                        <div class="brand-subtitle">Analytics &amp; Forecasting Platform</div>
                    </div>
                </div>
                """
            )

        for column, (label, target) in zip(nav_cols, NAV_ITEMS):
            with column:
                button_type = "primary" if label == active_page else "secondary"
                if st.button(
                    label,
                    key=f"topnav_{label}",
                    type=button_type,
                ):
                    st.switch_page(target)


# ---------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------


def render_html(content: str) -> None:
    """Render HTML through Streamlit Markdown.

    Every line is stripped and blank lines are removed, so indented
    templates are never turned into Markdown code blocks.
    """
    lines = (line.strip() for line in content.splitlines())
    st.markdown(
        "\n".join(line for line in lines if line),
        unsafe_allow_html=True,
    )


def tone_for(value: float | None) -> str:
    """Return 'positive', 'negative' or '' for a signed change."""
    if value is None or math.isnan(value):
        return ""
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return ""


@st.cache_data(show_spinner=False)
def _image_data_uri(path_str: str) -> str | None:
    """Return a base64 data URI for a local image, or None if missing."""
    path = Path(path_str)
    if not path.exists():
        return None
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


# ---------------------------------------------------------------------
# Shared analysis-page components
# ---------------------------------------------------------------------


def render_page_hero(
    title: str,
    caption: str,
    image_path: Path | None = None,
) -> None:
    """Render a page hero with a background image.

    Uses the local image when it exists, otherwise the Home hero image.
    """
    source = _image_data_uri(str(image_path)) if image_path else None
    source = (
        source
        or _image_data_uri(str(HOME_HERO_IMAGE_PATH))
        or ""
    )

    render_html(
        f"""
        <div class="page-hero" style="background-image:
        linear-gradient(90deg, rgba(255,255,255,0.90) 0%, rgba(255,255,255,0.78) 42%, rgba(255,255,255,0.12) 100%),
        url('{source}');">
            <div class="page-hero-title">{html.escape(title)}</div>
            <div class="page-hero-caption">{html.escape(caption)}</div>
        </div>
        """
    )


def render_filter_header(title: str, caption: str) -> None:
    """Render the heading inside a filter card."""
    render_html(
        f"""
        <div class="filter-title">{html.escape(title)}</div>
        <div class="filter-caption">{html.escape(caption)}</div>
        """
    )


def render_series_header(title: str, meta: str) -> None:
    """Render the selected-series banner."""
    render_html(
        f"""
        <div class="series-card">
            <div class="series-title">{html.escape(title)}</div>
            <div class="series-meta">{html.escape(meta)}</div>
        </div>
        """
    )


PROVISIONAL_NOTE = (
    "Tenancy Services marks the current snapshot as provisional during the "
    "Bond Hub migration. Figures may be revised in future releases."
)


def render_source_note(text: str = PROVISIONAL_NOTE) -> None:
    """Render the provisional-data notice."""
    render_html(
        f"""
        <div class="source-note">
            <strong>Provisional data:</strong> {html.escape(text)}
        </div>
        """
    )


def render_stat_card(
    label: str,
    value: str,
    note: str = "",
    tone: str = "",
    *,
    flat: bool = False,
) -> None:
    """Render a single statistic card."""
    card_class = "stat-card flat" if flat else "stat-card"
    note_html = f'<div class="stat-note">{html.escape(note)}</div>' if note else ""
    render_html(
        f"""
        <div class="{card_class}">
            <div class="stat-label">{html.escape(label)}</div>
            <div class="stat-value {html.escape(tone)}">{html.escape(value)}</div>
            {note_html}
        </div>
        """
    )


def render_card_header(title: str, caption: str = "") -> None:
    """Render a content-card title and optional caption."""
    caption_html = f'<div class="card-caption">{html.escape(caption)}</div>' if caption else ""
    render_html(
        f"""
        <div class="card-title">{html.escape(title)}</div>
        {caption_html}
        """
    )


def render_legend(items: list[tuple[str, str, int]]) -> None:
    """Render a chart legend from (label, colour, swatch height in px)."""
    spans = "".join(
        f'<span><i class="swatch" style="background:{color};height:{height}px"></i>'
        f"{html.escape(label)}</span>"
        for label, color, height in items
    )
    render_html(f'<div class="chart-legend">{spans}</div>')

def render_footer() -> None:
    """Render the shared dashboard footer."""

    st.html(
        """
        <style>
        .rmp-footer {
            position: relative;
            overflow: hidden;
            margin-top: 1.8rem;
            margin-bottom: 0.6rem;
            padding: 1.35rem 1.4rem 1.2rem;
            border-radius: 18px;

            background:
                linear-gradient(
                    135deg,
                    #2f80ed 0%,
                    #2563eb 55%,
                    #315fd6 100%
                );

            border:
                1px solid rgba(255, 255, 255, 0.16);

            box-shadow:
                0 10px 24px rgba(37, 99, 235, 0.14),
                inset 0 1px 0 rgba(255, 255, 255, 0.18);

            text-align: center;
        }

        .rmp-footer::before {
            content: "";
            position: absolute;
            inset: 0;

            background:
                radial-gradient(
                    circle at 20% 0%,
                    rgba(255, 255, 255, 0.18),
                    transparent 28%
                ),
                radial-gradient(
                    circle at 85% 100%,
                    rgba(255, 255, 255, 0.08),
                    transparent 24%
                );

            pointer-events: none;
        }

        .rmp-footer-title,
        .rmp-footer-project,
        .rmp-footer-author,
        .rmp-footer-meta {
            position: relative;
            z-index: 1;
        }

        .rmp-footer-title {
            color: #ffffff;
            font-size: 1.28rem;
            font-weight: 800;
            letter-spacing: -0.015em;
            line-height: 1.2;
            margin-bottom: 0.45rem;
        }

        .rmp-footer-project {
            color: rgba(255, 255, 255, 0.92);
            font-size: 0.96rem;
            font-weight: 600;
            line-height: 1.45;
            margin-bottom: 0.18rem;
        }

        .rmp-footer-author {
            color: #BFDBFE;
            font-size: 0.84rem;
            font-weight: 500;
            line-height: 1.4;
            margin-bottom: 0.30rem;
        }

        .rmp-footer-meta {
            color: rgba(255, 255, 255, 0.78);
            font-size: 0.78rem;
            font-weight: 500;
            line-height: 1.4;
        }

        @media (max-width: 700px) {
            .rmp-footer {
                margin-top: 1.4rem;
                padding: 1rem 0.9rem;
                border-radius: 14px;
            }

            .rmp-footer-title {
                font-size: 1.02rem;
            }

            .rmp-footer-project {
                font-size: 0.82rem;
            }

            .rmp-footer-author {
                font-size: 0.76rem;
            }

            .rmp-footer-meta {
                font-size: 0.72rem;
            }
        }
        </style>

        <div class="rmp-footer">
            <div class="rmp-footer-title">
                NZ Rental Market Analytics &amp; Forecasting Platform
            </div>

            <div class="rmp-footer-project">
                Massey University ·
                158888 Information Technology Professional Project
            </div>

            <div class="rmp-footer-author">
                Developed by Simeon Zhang
            </div>

            <div class="rmp-footer-meta">
                Data source: Tenancy Services / MBIE
                &nbsp;·&nbsp;
                Analytical and educational use
            </div>
        </div>
        """
    )
