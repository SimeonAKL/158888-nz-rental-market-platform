"""Historical analytics dashboard page."""

from __future__ import annotations

import calendar

import streamlit as st

from rmp.dashboard.data import (
    load_monthly_panel,
    load_monthly_seasonality,
)
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
    page_title="Historical Analytics",
    page_icon="📈",
    layout="wide",
)

st.title("Historical Analytics")

panel = load_monthly_panel()
seasonality = load_monthly_seasonality()

(
    geography_level,
    location_name,
    metric,
) = series_selector(
    panel,
    key_prefix="historical",
)

full_series = filter_series(
    panel,
    geography_level=geography_level,
    location_name=location_name,
    metric=metric,
).sort_values("period_date")

if full_series.empty:
    st.warning("No historical data available.")
    st.stop()

(
    start_date,
    end_date,
) = date_range_selector(
    full_series,
    date_column="period_date",
    key_prefix="historical",
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

seasonal = filter_series(
    seasonality,
    geography_level=geography_level,
    location_name=location_name,
    metric=metric,
).sort_values("month")

st.subheader(
    f"{location_name} — "
    f"{metric_label(metric)}"
)

st.caption(
    f"Historical view: "
    f"{series['period_date'].min():%b %Y} "
    f"to "
    f"{series['period_date'].max():%b %Y}"
)

st.subheader("Long-run Trend")

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

if not seasonal.empty:
    seasonal = seasonal.copy()

    seasonal["month_name"] = (
        seasonal["month"]
        .astype(int)
        .map(
            lambda month: (
                calendar.month_abbr[month]
            )
        )
    )

    peak = seasonal.loc[
        seasonal["median_value"].idxmax()
    ]

    low = seasonal.loc[
        seasonal["median_value"].idxmin()
    ]

    seasonal_mean = (
        seasonal["median_value"].mean()
    )

    seasonal_spread_pct = None

    if seasonal_mean != 0:
        seasonal_spread_pct = (
            (
                peak["median_value"]
                - low["median_value"]
            )
            / seasonal_mean
            * 100
        )

    st.subheader("Monthly Seasonality")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Typical Peak Month",
        peak["month_name"],
        format_value(
            peak["median_value"],
            metric,
        ),
    )

    col2.metric(
        "Typical Lowest Month",
        low["month_name"],
        format_value(
            low["median_value"],
            metric,
        ),
    )

    col3.metric(
        "Peak-to-Low Spread",
        format_percentage(
            seasonal_spread_pct,
            signed=False,
        ),
    )

    seasonality_chart = (
        seasonal[
            [
                "month_name",
                "median_value",
            ]
        ]
        .rename(
            columns={
                "month_name": "Month",
                "median_value": (
                    metric_axis_label(metric)
                ),
            }
        )
        .set_index("Month")
    )

    st.bar_chart(
        seasonality_chart,
        use_container_width=True,
    )

    st.caption(
        "Monthly seasonality is summarised "
        "using the historical median value "
        "for each calendar month."
    )

    with st.expander(
        "Seasonality statistics",
        expanded=False,
    ):
        seasonal_display = (
            seasonal[
                [
                    "month_name",
                    "median_value",
                    "mean_value",
                    "minimum_value",
                    "maximum_value",
                    "n_observations",
                ]
            ]
            .rename(
                columns={
                    "month_name": "Month",
                    "median_value": "Median",
                    "mean_value": "Mean",
                    "minimum_value": "Minimum",
                    "maximum_value": "Maximum",
                    "n_observations": (
                        "Observations"
                    ),
                }
            )
        )

        st.dataframe(
            seasonal_display,
            use_container_width=True,
            hide_index=True,
        )

if series["is_provisional"].fillna(False).any():
    st.warning(
        "The current source snapshot is marked as provisional "
        "by Tenancy Services during the Bond Hub migration period. "
        "Historical observations are shown as published in this "
        "snapshot and may be revised in future source releases."
    )

with st.expander(
    "Historical observations",
    expanded=False,
):
    historical_display = (
        series[
            [
                "period_date",
                "value",
            ]
        ]
        .rename(
            columns={
                "period_date": "Period",
                "value": metric_axis_label(
                    metric
                ),
            }
        )
        .sort_values(
            "Period",
            ascending=False,
        )
    )

    st.dataframe(
        historical_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Period": st.column_config.DateColumn(
                "Period",
                format="MMM YYYY",
            ),
        },
    )
