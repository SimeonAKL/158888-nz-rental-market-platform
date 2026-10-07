"""Historical analytics dashboard page."""

from __future__ import annotations

import calendar
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from rmp.dashboard.data import (
    load_monthly_panel,
    load_monthly_seasonality,
)
from rmp.dashboard.filters import (
    date_range_selector,
    filter_date_range,
    filter_series,
    geography_label,
    metric_axis_label,
    metric_label,
    series_selector,
)
from rmp.dashboard.formatters import (
    format_percentage,
    format_value,
)
from rmp.dashboard.layout import (
    inject_home_styles,
    render_card_header,
    render_filter_header,
    render_footer,
    render_legend,
    render_page_hero,
    render_series_header,
    render_source_note,
    render_stat_card,
    render_top_navigation,
    tone_for,
)

# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Historical Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_home_styles()
render_top_navigation(
    active_page="Historical Analytics",
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

HERO_IMAGE_PATH = PROJECT_ROOT / "assets" / "auckland_skyline.jpg"


# ---------------------------------------------------------------------
# Chart palette
# ---------------------------------------------------------------------

BLUE = "#1769ff"
LIGHT_BLUE = "#9cc4ff"
PALE_BLUE = "#c7dcff"
WARM = "#e8833a"

LABEL_COLOR = "#71809c"
TITLE_COLOR = "#52617e"
TICK_COLOR = "#d7dfeb"
GRID_COLOR = "#edf1f7"

MONTH_ORDER = list(calendar.month_abbr)[1:]

MONTHS_PER_YEAR = 12

MIN_YEARS_FOR_ANNUAL_CHART = 2


# ---------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------

render_page_hero(
    "Historical Analytics",
    (
        "Long-run trends, annual movements, "
        "and typical seasonal patterns for "
        "each Region and Territorial Authority."
    ),
    HERO_IMAGE_PATH,
)


# ---------------------------------------------------------------------
# Data and filters
# ---------------------------------------------------------------------

panel = load_monthly_panel()

seasonality = load_monthly_seasonality()


with st.container(
    key="filters_historical",
):
    render_filter_header(
        "Series Selection",
        ("Choose a geography, location, indicator, and the period to analyse."),
    )

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
        geography_level=(geography_level),
        location_name=location_name,
        metric=metric,
    ).sort_values("period_date")

    if full_series.empty:
        st.warning("No historical data is available for this selection.")
        st.stop()

    (
        start_date,
        end_date,
    ) = date_range_selector(
        full_series,
        date_column="period_date",
        key_prefix="historical",
        default_years=None,
    )


# ---------------------------------------------------------------------
# Derived historical features
# ---------------------------------------------------------------------
#
# These are calculated before the date filter so that rolling
# statistics at the beginning of a shortened selection can use
# observations immediately preceding the selected period.

full_series = full_series.reset_index(drop=True)

year_ago = (
    full_series[
        [
            "period_date",
            "value",
        ]
    ]
    .assign(
        period_date=lambda data: (
            data["period_date"]
            + pd.DateOffset(
                months=12,
            )
        )
    )
    .rename(
        columns={
            "value": ("value_year_ago"),
        }
    )
)

full_series = full_series.merge(
    year_ago,
    on="period_date",
    how="left",
)

full_series = full_series.assign(
    rolling_12m=(
        full_series["value"]
        .rolling(
            12,
            min_periods=12,
        )
        .mean()
    ),
    mom_pct=(full_series["value"].pct_change() * 100),
    yoy_pct=((full_series["value"] / full_series["value_year_ago"] - 1) * 100),
)


# ---------------------------------------------------------------------
# Selected period
# ---------------------------------------------------------------------

series = filter_date_range(
    full_series,
    date_column="period_date",
    start_date=start_date,
    end_date=end_date,
).sort_values("period_date")

if series.empty:
    st.warning("No observations are available for the selected period.")
    st.stop()


axis_label = metric_axis_label(metric)

series_start = pd.Timestamp(series["period_date"].min())

series_end = pd.Timestamp(series["period_date"].max())


# ---------------------------------------------------------------------
# Headline statistics
# ---------------------------------------------------------------------

period_average = float(series["value"].mean())

max_row = series.loc[series["value"].idxmax()]

min_row = series.loc[series["value"].idxmin()]


# ---------------------------------------------------------------------
# Annualised growth
# ---------------------------------------------------------------------
#
# Prefer valid 12-month rolling averages because they smooth
# single-month seasonality. Use the first and last valid rolling
# averages inside the selected period.
#
# Only fall back to monthly endpoints when the selected period
# does not contain enough rolling-average observations.

valid_rolling = (
    series[
        [
            "period_date",
            "rolling_12m",
        ]
    ]
    .dropna(
        subset=[
            "rolling_12m",
        ]
    )
    .sort_values("period_date")
)

annualised_growth = None

growth_basis = "monthly values"

growth_start_date = series_start

growth_end_date = series_end

first_level = float(series.iloc[0]["value"])

last_level = float(series.iloc[-1]["value"])


if len(valid_rolling) >= 2:
    rolling_start = valid_rolling.iloc[0]

    rolling_end = valid_rolling.iloc[-1]

    growth_start_date = pd.Timestamp(rolling_start["period_date"])

    growth_end_date = pd.Timestamp(rolling_end["period_date"])

    first_level = float(rolling_start["rolling_12m"])

    last_level = float(rolling_end["rolling_12m"])

    growth_basis = "12-month averages"


years_span = (growth_end_date - growth_start_date).days / 365.25


if years_span >= 1 and first_level > 0 and last_level > 0:
    annualised_growth = ((last_level / first_level) ** (1 / years_span) - 1) * 100


# ---------------------------------------------------------------------
# Selected series header
# ---------------------------------------------------------------------

render_series_header(
    (f"{location_name} — {metric_label(metric)}"),
    (
        f"{geography_label(geography_level)}"
        "  •  "
        f"{series_start:%b %Y}"
        " – "
        f"{series_end:%b %Y}"
        "  •  "
        f"{len(series):,} monthly observations"
    ),
)


if series["source_snapshot_provisional"].fillna(False).any():
    render_source_note()


# ---------------------------------------------------------------------
# Headline cards
# ---------------------------------------------------------------------

stat_specs = [
    (
        "Period Average",
        format_value(
            period_average,
            metric,
        ),
        (f"Mean of {len(series):,} months"),
        "",
    ),
    (
        "Annualised Growth",
        format_percentage(annualised_growth),
        (f"Compound rate from {growth_basis}"),
        tone_for(annualised_growth),
    ),
    (
        "Highest",
        format_value(
            max_row["value"],
            metric,
        ),
        (f"{max_row['period_date']:%b %Y}"),
        "",
    ),
    (
        "Lowest",
        format_value(
            min_row["value"],
            metric,
        ),
        (f"{min_row['period_date']:%b %Y}"),
        "",
    ),
]


for column, (
    label,
    value,
    note,
    tone,
) in zip(
    st.columns(4),
    stat_specs,
):
    with column:
        render_stat_card(
            label,
            value,
            note,
            tone,
        )


# ---------------------------------------------------------------------
# Long-run trend
# ---------------------------------------------------------------------

with st.container(
    key="card_historical_trend",
):
    render_card_header(
        "Long-run Trend",
        (
            f"Monthly {metric_label(metric)} "
            "with a 12-month rolling average, "
            f"{series_start:%b %Y}"
            " – "
            f"{series_end:%b %Y}. "
            "Drag to pan, scroll to zoom."
        ),
    )

    render_legend(
        [
            (
                "Monthly value",
                LIGHT_BLUE,
                2,
            ),
            (
                "12-month average",
                BLUE,
                4,
            ),
        ]
    )

    x_time = alt.X(
        "period_date:T",
        title=None,
        axis=alt.Axis(
            format="%Y",
            tickCount="year",
            labelOverlap=True,
            grid=False,
            labelColor=(LABEL_COLOR),
            tickColor=(TICK_COLOR),
        ),
    )

    trend_base = alt.Chart(series)

    monthly_line = trend_base.mark_line(
        color=LIGHT_BLUE,
        strokeWidth=1.4,
    ).encode(
        x=x_time,
        y=alt.Y(
            "value:Q",
            title=axis_label,
            scale=alt.Scale(zero=False),
            axis=alt.Axis(
                labelColor=(LABEL_COLOR),
                titleColor=(TITLE_COLOR),
                gridColor=(GRID_COLOR),
            ),
        ),
        tooltip=[
            alt.Tooltip(
                "period_date:T",
                title="Period",
                format="%b %Y",
            ),
            alt.Tooltip(
                "value:Q",
                title=axis_label,
                format=",.1f",
            ),
        ],
    )

    rolling_line = (
        trend_base.transform_filter("isValid(datum.rolling_12m)")
        .mark_line(
            color=BLUE,
            strokeWidth=2.8,
        )
        .encode(
            x="period_date:T",
            y=alt.Y(
                "rolling_12m:Q",
                title=axis_label,
            ),
            tooltip=[
                alt.Tooltip(
                    "period_date:T",
                    title="Period",
                    format="%b %Y",
                ),
                alt.Tooltip(
                    "rolling_12m:Q",
                    title=("12-month average"),
                    format=",.1f",
                ),
            ],
        )
    )

    trend_chart = (
        (monthly_line + rolling_line)
        .interactive(bind_y=False)
        .properties(height=380)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(
        trend_chart,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Annual averages
# ---------------------------------------------------------------------

annual = (
    series.assign(year=(series["period_date"].dt.year))
    .groupby(
        "year",
        as_index=False,
    )
    .agg(
        average=(
            "value",
            "mean",
        ),
        months=(
            "value",
            "size",
        ),
    )
)

full_year = annual["months"] >= MONTHS_PER_YEAR

annual["coverage"] = np.where(
    full_year,
    "Full year",
    "Partial year",
)

annual["yoy_pct"] = annual["average"].pct_change() * 100

previous_full_year = full_year.shift(fill_value=False)

annual.loc[
    ~(full_year & previous_full_year),
    "yoy_pct",
] = np.nan


if len(annual) >= MIN_YEARS_FOR_ANNUAL_CHART:
    with st.container(
        key="card_historical_annual",
    ):
        render_card_header(
            "Annual Averages",
            (
                "Calendar-year averages within the "
                "selected period. Lighter bars cover "
                "fewer than 12 months."
            ),
        )

        render_legend(
            [
                (
                    "Full year",
                    BLUE,
                    10,
                ),
                (
                    "Partial year",
                    PALE_BLUE,
                    10,
                ),
            ]
        )

        annual_chart = (
            alt.Chart(annual)
            .mark_bar(
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4,
            )
            .encode(
                x=alt.X(
                    "year:O",
                    title=None,
                    axis=alt.Axis(
                        labelAngle=0,
                        labelOverlap=True,
                        labelColor=(LABEL_COLOR),
                        tickColor=(TICK_COLOR),
                    ),
                ),
                y=alt.Y(
                    "average:Q",
                    title=(f"Average {axis_label}"),
                    axis=alt.Axis(
                        labelColor=(LABEL_COLOR),
                        titleColor=(TITLE_COLOR),
                        gridColor=(GRID_COLOR),
                    ),
                ),
                color=alt.Color(
                    "coverage:N",
                    scale=alt.Scale(
                        domain=[
                            "Full year",
                            "Partial year",
                        ],
                        range=[
                            BLUE,
                            PALE_BLUE,
                        ],
                    ),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip(
                        "year:O",
                        title="Year",
                    ),
                    alt.Tooltip(
                        "average:Q",
                        title="Average",
                        format=",.1f",
                    ),
                    alt.Tooltip(
                        "months:Q",
                        title=("Months of data"),
                    ),
                    alt.Tooltip(
                        "yoy_pct:Q",
                        title=("Change vs previous year (%)"),
                        format="+.1f",
                    ),
                ],
            )
            .properties(height=300)
            .configure_view(strokeWidth=0)
        )

        st.altair_chart(
            annual_chart,
            width="stretch",
        )


# ---------------------------------------------------------------------
# Monthly seasonality
# ---------------------------------------------------------------------

seasonal = filter_series(
    seasonality,
    geography_level=(geography_level),
    location_name=(location_name),
    metric=metric,
)


if not seasonal.empty:
    seasonal = seasonal.assign(month=(seasonal["month"].astype(int))).sort_values("month")

    seasonal["month_name"] = seasonal["month"].map(lambda month: calendar.month_abbr[month])

    seasonal_mean = float(seasonal["median_value"].mean())

    if seasonal_mean:
        seasonal["deviation_pct"] = (seasonal["median_value"] / seasonal_mean - 1) * 100
    else:
        seasonal["deviation_pct"] = np.nan

    peak = seasonal.loc[seasonal["median_value"].idxmax()]

    low = seasonal.loc[seasonal["median_value"].idxmin()]

    spread_pct = None

    if seasonal_mean:
        spread_pct = (peak["median_value"] - low["median_value"]) / seasonal_mean * 100

    with st.container(
        key="card_historical_seasonality",
    ):
        render_card_header(
            "Monthly Seasonality",
            (
                "Typical calendar-month pattern based "
                "on full-history monthly medians. "
                "This section uses the complete historical "
                "series, not only the selected period."
            ),
        )

        season_specs = [
            (
                "Typical Peak Month",
                calendar.month_name[int(peak["month"])],
                (f"Full-history median {format_value(peak['median_value'], metric)}"),
            ),
            (
                "Typical Lowest Month",
                calendar.month_name[int(low["month"])],
                (f"Full-history median {format_value(low['median_value'], metric)}"),
            ),
            (
                "Peak-to-Low Spread",
                format_percentage(
                    spread_pct,
                    signed=False,
                ),
                ("Gap between peak and low, relative to the average month"),
            ),
        ]

        for column, (
            label,
            value,
            note,
        ) in zip(
            st.columns(3),
            season_specs,
        ):
            with column:
                render_stat_card(
                    label,
                    value,
                    note,
                    flat=True,
                )

        render_legend(
            [
                (
                    "Above average month",
                    BLUE,
                    10,
                ),
                (
                    "Below average month",
                    WARM,
                    10,
                ),
            ]
        )

        seasonal_bars = (
            alt.Chart(seasonal)
            .mark_bar(cornerRadiusEnd=4)
            .encode(
                x=alt.X(
                    "month_name:N",
                    sort=MONTH_ORDER,
                    title=None,
                    axis=alt.Axis(
                        labelAngle=0,
                        labelColor=(LABEL_COLOR),
                        tickColor=(TICK_COLOR),
                    ),
                ),
                y=alt.Y(
                    "deviation_pct:Q",
                    title=("% vs average month"),
                    axis=alt.Axis(
                        format="+.1f",
                        labelColor=(LABEL_COLOR),
                        titleColor=(TITLE_COLOR),
                        gridColor=(GRID_COLOR),
                    ),
                ),
                color=alt.condition(
                    ("datum.deviation_pct >= 0"),
                    alt.value(BLUE),
                    alt.value(WARM),
                ),
                tooltip=[
                    alt.Tooltip(
                        "month_name:N",
                        title="Month",
                    ),
                    alt.Tooltip(
                        "median_value:Q",
                        title=("Full-history median"),
                        format=",.1f",
                    ),
                    alt.Tooltip(
                        "deviation_pct:Q",
                        title=("% vs average month"),
                        format="+.1f",
                    ),
                    alt.Tooltip(
                        "n_observations:Q",
                        title=("Historical observations"),
                    ),
                ],
            )
        )

        zero_rule = (
            alt.Chart(
                pd.DataFrame(
                    {
                        "y": [0],
                    }
                )
            )
            .mark_rule(
                color="#9aa6bf",
                strokeWidth=1,
            )
            .encode(y="y:Q")
        )

        st.altair_chart(
            (seasonal_bars + zero_rule).properties(height=300).configure_view(strokeWidth=0),
            width="stretch",
        )

        with st.expander(
            "Monthly statistics",
            expanded=False,
        ):
            seasonal_display = pd.DataFrame(
                {
                    "Month": (seasonal["month_name"]),
                    "Median": [
                        format_value(
                            value,
                            metric,
                        )
                        for value in seasonal["median_value"]
                    ],
                    "Mean": [
                        format_value(
                            value,
                            metric,
                        )
                        for value in seasonal["mean_value"]
                    ],
                    "Minimum": [
                        format_value(
                            value,
                            metric,
                        )
                        for value in seasonal["minimum_value"]
                    ],
                    "Maximum": [
                        format_value(
                            value,
                            metric,
                        )
                        for value in seasonal["maximum_value"]
                    ],
                    "Observations": (seasonal["n_observations"].astype(int)),
                }
            )

            st.dataframe(
                seasonal_display,
                width="stretch",
                hide_index=True,
                height=((len(seasonal_display) + 1) * 35 + 3),
            )


# ---------------------------------------------------------------------
# Historical observations
# ---------------------------------------------------------------------

with st.container(
    key="card_historical_table",
):
    (
        title_col,
        button_col,
    ) = st.columns(
        [4, 1],
        vertical_alignment="center",
    )

    with title_col:
        render_card_header(
            "Historical Observations",
            (f"All {len(series):,} months in the selected period, newest first."),
        )

    with (
        button_col,
        st.container(
            key="download_historical",
        ),
    ):
        csv_data = (
            series[
                [
                    "period_date",
                    "value",
                    "mom_pct",
                    "yoy_pct",
                ]
            ]
            .assign(period_date=lambda data: data["period_date"].dt.strftime("%Y-%m"))
            .rename(
                columns={
                    "period_date": "period",
                    "mom_pct": ("month_on_month_pct"),
                    "yoy_pct": ("year_on_year_pct"),
                }
            )
            .round(2)
            .to_csv(index=False)
            .encode("utf-8")
        )

        location_slug = (
            str(location_name)
            .lower()
            .replace(
                " ",
                "_",
            )
        )

        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=(f"historical_{location_slug}_{metric}.csv"),
            mime="text/csv",
            width="stretch",
        )

    recent_first = series.sort_values(
        "period_date",
        ascending=False,
    )

    table = pd.DataFrame(
        {
            "Period": (recent_first["period_date"].dt.strftime("%b %Y")),
            axis_label: [
                format_value(
                    value,
                    metric,
                )
                for value in recent_first["value"]
            ],
            "Month-on-Month": [format_percentage(value) for value in recent_first["mom_pct"]],
            "Year-on-Year": [format_percentage(value) for value in recent_first["yoy_pct"]],
        }
    )

    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        height=430,
    )


render_footer()
