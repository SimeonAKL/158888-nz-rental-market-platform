"""NZ Rental Market Analytics and Forecasting Platform."""

from __future__ import annotations

import streamlit as st

from rmp.dashboard.data import (
    load_anomaly_summary,
    load_series_catalog,
)

st.set_page_config(
    page_title="NZ Rental Market Analytics",
    page_icon="🏠",
    layout="wide",
)

st.title(
    "New Zealand Rental Market Analytics "
    "and Forecasting Platform"
)

st.caption(
    "Regional rental market analytics, "
    "forecast evaluation, and anomaly detection."
)

catalog = load_series_catalog()
anomalies = load_anomaly_summary()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Series",
    f"{catalog['series_id'].nunique():,}",
)

col2.metric(
    "Historical observations",
    f"{len(anomalies):,}",
)

col3.metric(
    "Overall alerts",
    f"{int(anomalies['overall_dashboard_alert'].sum()):,}",
)

col4.metric(
    "Confirmed anomalies",
    f"{int((anomalies['overall_status'] == 'confirmed_anomaly').sum()):,}",
)

st.divider()

st.subheader("Platform")

st.markdown(
    """
This platform analyses official New Zealand rental-market
data and provides:

- **Market Overview** — latest indicators and recent market movement.
- **Historical Analytics** — long-run trends and monthly seasonality.
- **Forecasting** — rolling-origin forecast evaluation and selected models.
- **Model Performance** — comparison of Seasonal Naive, ETS and XGBoost.
- **Anomaly Detection** — historical and forecast-residual analytical alerts.

Use the navigation menu to open each dashboard page.
"""
)

st.info(
    "Anomaly indicators identify statistically unusual "
    "market movements. They should not be interpreted "
    "as evidence of a specific causal event."
)
