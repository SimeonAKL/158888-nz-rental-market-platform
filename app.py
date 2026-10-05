"""NZ Rental Market Analytics and Forecasting Platform."""

from __future__ import annotations

import streamlit as st

from rmp.dashboard.data import (
    load_anomaly_summary,
    load_final_forward_forecasts,
    load_series_catalog,
)
from rmp.dashboard.layout import (
    inject_home_styles,
    render_top_navigation,
)

st.set_page_config(
    page_title="Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_home_styles()
render_top_navigation(active_page="Home")

catalog = load_series_catalog()
anomalies = load_anomaly_summary()

total_series = catalog["series_id"].nunique()
historical_observations = len(anomalies)
overall_alerts = int(anomalies["overall_dashboard_alert"].sum())
both_detectors_flagged = int((anomalies["overall_status"] == "confirmed_anomaly").sum())

final_forecasts = load_final_forward_forecasts()

forecast_series = final_forecasts["series_id"].nunique()

# ---------------------------------------------------------------------
# Hero section
# ---------------------------------------------------------------------

st.markdown(
    """
<div class="hero-card">
    <div class="hero-content">
        <div class="hero-chip">Official New Zealand rental-market dashboard</div>
        <div class="hero-title">
            New Zealand Rental Market Analytics and Forecasting Platform
        </div>
        <div class="hero-subtitle">
            Explore official rental-market data across Regions and Territorial
            Authorities, compare historical patterns, review model performance,
            assess anomaly signals, and examine six-month forward forecasts.
        </div>
    </div>
</div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------
# KPI section
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section-title">Platform Snapshot</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-caption">A high-level summary of the current analytical and modelling coverage.</div>',
    unsafe_allow_html=True,
)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-label">Analytical Series</div>
    <div class="metric-value">{total_series:,}</div>
    <div class="metric-note">
        Total Region and Territorial Authority time series available for analytical exploration.
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-label">Historical Observations</div>
    <div class="metric-value">{historical_observations:,}</div>
    <div class="metric-note">
        Monthly observations represented in the consolidated analytical anomaly dataset.
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

with kpi3:
    forecast_text = f"{forecast_series:,}" if forecast_series is not None else "N/A"
    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-label">Forecast-Covered Series</div>
    <div class="metric-value">{forecast_text}</div>
    <div class="metric-note">
        Series included in the forecast-eligible modelling subset for final forward forecasting.
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

with kpi4:
    st.markdown(
        f"""
<div class="metric-card">
    <div class="metric-label">Both Detectors Flagged</div>
    <div class="metric-value">{both_detectors_flagged:,}</div>
    <div class="metric-note">
        Periods simultaneously flagged by the historical and forecast-residual detector paths.
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")

# ---------------------------------------------------------------------
# Module cards
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section-title">Explore the Platform</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-caption">Navigate through the dashboard modules to analyse market conditions, historical trends, forecasts, model evidence, and anomaly signals.</div>',
    unsafe_allow_html=True,
)

row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1, st.container(border=True):
    st.markdown("### 📊 Overview")
    st.write(
        "Review current rental-market indicators and recent movements "
        "for Regions and Territorial Authorities."
    )
    st.page_link(
        "pages/1_Overview.py",
        label="Open Overview",
        icon="➡️",
    )

with row1_col2, st.container(border=True):
    st.markdown("### 📈 Historical Analytics")
    st.write(
        "Explore long-run trends, historical observations, and "
        "monthly seasonality across the analytical series."
    )
    st.page_link(
        "pages/2_Historical_Analytics.py",
        label="Open Historical Analytics",
        icon="➡️",
    )

with row1_col3, st.container(border=True):
    st.markdown("### 🔮 Forecasting")
    st.write(
        "View six-month forward forecasts produced using the fixed "
        "ETS production model for each forecast-eligible series."
    )
    st.page_link(
        "pages/3_Forecasting.py",
        label="Open Forecasting",
        icon="➡️",
    )

row2_col1, row2_col2 = st.columns(2)

with row2_col1, st.container(border=True):
    st.markdown("### 🧠 Model Performance")
    st.write(
        "Compare Seasonal Naive, ETS, and XGBoost using rolling-origin "
        "validation and standard forecast-error metrics."
    )
    st.page_link(
        "pages/4_Model_Performance.py",
        label="Open Model Performance",
        icon="➡️",
    )

with row2_col2, st.container(border=True):
    st.markdown("### ⚠️ Anomaly Detection")
    st.write(
        "Investigate statistically unusual market movements identified "
        "through historical and forecast-residual detector paths."
    )
    st.page_link(
        "pages/5_Anomaly_Detection.py",
        label="Open Anomaly Detection",
        icon="➡️",
    )

st.markdown("")

# ---------------------------------------------------------------------
# Scope panels
# ---------------------------------------------------------------------

st.markdown(
    '<div class="section-title">Coverage and Methodology</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-caption">A concise summary of platform scope, data coverage, and modelling approach.</div>',
    unsafe_allow_html=True,
)

scope1, scope2, scope3 = st.columns(3)

with scope1:
    st.markdown(
        """
<div class="soft-panel">
    <div class="small-heading">🗺️ Geographic Coverage</div>
    <div class="small-text">
        The platform covers New Zealand Regions and valid Territorial Authorities,
        supporting national, regional, and local rental-market comparison.
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

with scope2:
    st.markdown(
        """
<div class="soft-panel">
    <div class="small-heading">📉 Market Indicators</div>
    <div class="small-text">
        Core monthly indicators include median weekly rent and new bond lodgements,
        providing complementary views of market pricing and activity.
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

with scope3:
    st.markdown(
        """
<div class="soft-panel">
    <div class="small-heading">🤖 Forecasting Approach</div>
    <div class="small-text">
        Forecasting combines Seasonal Naive, ETS additive damped, and pooled
        recursive XGBoost, evaluated using rolling-origin validation.
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

note1, note2 = st.columns(2)

with note1:
    st.markdown(
        """
<div class="soft-panel">
    <div class="small-heading">📚 Official Data Sources</div>
    <div class="small-text">
        Analytical outputs are based on official New Zealand rental-market data,
        including Tenancy Services market-rent and rental-bond information.
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

with note2:
    st.markdown(
        f"""
<div class="soft-panel">
    <div class="small-heading">🚨 Analytical Alerts</div>
    <div class="small-text">
        The current anomaly pipeline contains <strong>{overall_alerts:,}</strong>
        dashboard alerts, including periods highlighted by historical and
        forecast-residual detector logic.
    </div>
</div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")

st.markdown(
    """
<div class="notice-box">
    <strong>Interpretation note:</strong> Forecasts are model-based estimates rather than
    guaranteed future outcomes. Anomaly indicators identify statistically unusual market
    movements and should not be interpreted as proof of a specific causal event.
</div>
    """,
    unsafe_allow_html=True,
)
