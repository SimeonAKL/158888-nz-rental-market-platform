"""Market overview dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from rmp.dashboard.data import load_monthly_panel
from rmp.dashboard.filters import (
    date_range_selector,
    filter_date_range,
    filter_series,
    metric_axis_label,
    metric_label,
    series_selector,
)
from rmp.dashboard.formatters import (
    format_percentage,
    format_value,
)

st.set_page_config(
    page_title="Market Overview",
    page_icon="📊",
    layout="wide",
)

st.title("Market Overview")

panel = load_monthly_panel()

(
    geography_level,
    location_name,
    metric,
) = series_selector(
    panel,
    key_prefix="overview",
)

full_series = filter_series(
    panel,
    geography_level=geography_level,
    location_name=location_name,
    metric=metric,
).sort_values("period_date")

if full_series.empty:
    st.warning("No data available.")
    st.stop()

(
    start_date,
    end_date,
) = date_range_selector(
    full_series,
    date_column="period_date",
    key_prefix="overview",
)

series = filter_date_range(
    full_series,
    date_column="period_date",
    start_date=start_date,
    end_date=end_date,
).sort_values("period_date")

if series.empty:
    st.warning(
        "No observations are available "
        "for the selected date range."
    )
    st.stop()

latest = series.iloc[-1]
latest_date = latest["period_date"]
latest_value = latest["value"]

history_to_latest = full_series[
    full_series["period_date"]
    <= latest_date
].sort_values("period_date")

previous_value = None
mom_change = None

if len(history_to_latest) >= 2:
    previous_value = (
        history_to_latest.iloc[-2]["value"]
    )

    if previous_value != 0:
        mom_change = (
            (
                latest_value
                - previous_value
            )
            / previous_value
            * 100
        )

yoy_change = None

target_yoy_period = (
    pd.Timestamp(latest_date)
    - pd.DateOffset(months=12)
)

yoy_row = full_series[
    full_series["period_date"]
    == target_yoy_period
]

if not yoy_row.empty:
    yoy_value = yoy_row.iloc[0]["value"]

    if yoy_value != 0:
        yoy_change = (
            (
                latest_value
                - yoy_value
            )
            / yoy_value
            * 100
        )

period_average = series["value"].mean()

st.subheader(
    f"{location_name} — "
    f"{metric_label(metric)}"
)

st.caption(
    f"Selected period: "
    f"{series['period_date'].min():%b %Y} "
    f"to "
    f"{series['period_date'].max():%b %Y}"
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Latest Value",
    format_value(
        latest_value,
        metric,
    ),
    help=(
        f"Latest observation: "
        f"{latest_date:%B %Y}"
    ),
)

col2.metric(
    "Month-on-Month",
    format_percentage(
        mom_change
    ),
)

col3.metric(
    "Year-on-Year",
    format_percentage(
        yoy_change
    ),
)

col4.metric(
    "Period Average",
    format_value(
        period_average,
        metric,
    ),
)

st.subheader("Historical Trend")

trend = (
    series[
        [
            "period_date",
            "value",
        ]
    ]
    .rename(
        columns={
            "period_date": "Period",
            "value": metric_axis_label(metric),
        }
    )
    .set_index("Period")
)

st.line_chart(
    trend,
    use_container_width=True,
)

if series["is_provisional"].fillna(False).any():
    st.warning(
        "The current source snapshot is marked as provisional "
        "by Tenancy Services during the Bond Hub migration period. "
        "Historical observations are shown as published in this "
        "snapshot and may be revised in future source releases."
    )

st.subheader("Selected Period Summary")

summary_col1, summary_col2, summary_col3 = (
    st.columns(3)
)

summary_col1.metric(
    "Observations",
    f"{len(series):,}",
)

summary_col2.metric(
    "Minimum",
    format_value(
        series["value"].min(),
        metric,
    ),
)

summary_col3.metric(
    "Maximum",
    format_value(
        series["value"].max(),
        metric,
    ),
)

with st.expander(
    "Recent observations",
    expanded=False,
):
    display = (
        series[
            [
                "period_date",
                "value",
            ]
        ]
        .tail(24)
        .sort_values(
            "period_date",
            ascending=False,
        )
        .rename(
            columns={
                "period_date": "Period",
                "value": metric_axis_label(
                    metric
                ),
            }
        )
    )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Period": st.column_config.DateColumn(
                "Period",
                format="MMM YYYY",
            ),
        },
    )
