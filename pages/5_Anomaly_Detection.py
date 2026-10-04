"""Anomaly detection page."""

from __future__ import annotations

import streamlit as st

from rmp.dashboard.data import (
    load_anomaly_summary,
)
from rmp.dashboard.filters import (
    filter_series,
    metric_label,
    series_selector,
)

st.set_page_config(
    page_title="Anomaly Detection",
    page_icon="⚠️",
    layout="wide",
)

st.title("Anomaly Detection")

st.caption(
    "Analytical alerts identify statistically unusual "
    "market movements. They do not establish causation."
)

data = load_anomaly_summary()

(
    geography_level,
    location_name,
    metric,
) = series_selector(
    data,
    key_prefix="anomaly",
)

series = filter_series(
    data,
    geography_level=geography_level,
    location_name=location_name,
    metric=metric,
).sort_values("period_date")

alerts = series[
    series["overall_dashboard_alert"]
].copy()

has_forecast_coverage = bool(
    series["has_forecast_record"]
    .fillna(False)
    .any()
)

if not has_forecast_coverage:
    st.info(
        "This series has historical anomaly coverage only. "
        "Forecast-residual anomaly detection is unavailable because "
        "the series did not enter the forecasting subset."
    )

confirmed = alerts[
    alerts["overall_status"]
    == "confirmed_anomaly"
]

high = alerts[
    alerts["overall_severity"]
    == "high"
]

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Alerts",
    len(alerts),
)

col2.metric(
    "High Severity",
    len(high),
)

col3.metric(
    "Confirmed",
    len(confirmed),
)

col4.metric(
    "Latest Status",
    (
        series.iloc[-1]["overall_status"]
        if not series.empty
        else "N/A"
    ),
)

st.subheader(
    f"{location_name} — {metric_label(metric)}"
)

chart_data = (
    series[
        [
            "period_date",
            "value",
        ]
    ]
    .set_index("period_date")
)

st.line_chart(
    chart_data,
    y="value",
    use_container_width=True,
)

st.subheader("Alert History")

if alerts.empty:
    st.success(
        "No dashboard-level anomaly alerts "
        "for this series."
    )
else:
    alert_columns = [
        "period_date",
        "value",
        "overall_status",
        "overall_severity",
        "overall_direction",
        "historical_severity",
        "historical_deviation",
        "historical_deviation_pct",
        "forecast_model",
        "predicted",
        "forecast_residual",
        "forecast_residual_pct",
        "forecast_severity",
    ]

    st.dataframe(
        alerts[
            [
                column
                for column in alert_columns
                if column in alerts.columns
            ]
        ].sort_values(
            "period_date",
            ascending=False,
        ),
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Detector Interpretation")

status_counts = (
    series[
        "overall_status"
    ]
    .value_counts()
    .rename_axis("status")
    .to_frame("observations")
)

st.bar_chart(
    status_counts,
    use_container_width=True,
)

with st.expander(
    "Methodology note"
):
    st.markdown(
        """
**Historical anomaly detector**

Uses year-on-year seasonal change with a robust
rolling median baseline and MAD/IQR scale.

**Forecast residual detector**

Uses one-step-ahead residuals from each series'
selected winner model and compares them with
previous out-of-sample residual behaviour.

**Confirmed anomaly**

Both historical and forecast practical alert
layers identify the same series-period observation.

These alerts indicate unusual analytical behaviour
only and should not be interpreted as causal claims.
"""
    )
