"""Market overview dashboard page."""

from __future__ import annotations

import base64
import html
from pathlib import Path
from textwrap import dedent

import altair as alt
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
from rmp.dashboard.layout import (
    HOME_HERO_IMAGE,
    inject_home_styles,
    render_top_navigation,
)

# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Market Overview",
    page_icon="📊",
    layout="wide",
)

inject_home_styles()
render_top_navigation(active_page="Overview")


# ---------------------------------------------------------------------
# Hero image
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OVERVIEW_HERO_PATH = PROJECT_ROOT / "assets" / "overview_hero.jpg"


def hero_image_source() -> str:
    """Return local hero image or shared fallback image."""
    if not OVERVIEW_HERO_PATH.exists():
        return HOME_HERO_IMAGE

    encoded = base64.b64encode(OVERVIEW_HERO_PATH.read_bytes()).decode("ascii")

    return f"data:image/jpeg;base64,{encoded}"


OVERVIEW_HERO_IMAGE = hero_image_source()


# ---------------------------------------------------------------------
# Overview-specific styles
# ---------------------------------------------------------------------

st.markdown(
    f"""
<style>
/* ============================================================
   Overview Hero
   ============================================================ */

.overview-hero {{
    position: relative;
    overflow: hidden;

    min-height: 190px;

    border-radius: 24px;

    padding: 2rem 2.1rem;
    margin-bottom: 1.45rem;

    background:
        linear-gradient(
            90deg,
            rgba(255, 255, 255, 0.97) 0%,
            rgba(255, 255, 255, 0.91) 43%,
            rgba(255, 255, 255, 0.25) 100%
        ),
        url('{OVERVIEW_HERO_IMAGE}');

    background-size: cover;
    background-position: center;

    border:
        1px solid rgba(23, 105, 255, 0.08);

    box-shadow:
        0 12px 30px rgba(24, 48, 94, 0.07),
        0 2px 5px rgba(24, 48, 94, 0.03);
}}

.overview-hero-content {{
    position: relative;
    z-index: 1;
    max-width: 720px;
}}

.overview-hero-chip {{
    display: inline-block;

    padding: 0.36rem 0.75rem;
    margin-bottom: 0.85rem;

    border-radius: 999px;

    background:
        rgba(23, 105, 255, 0.10);

    color: var(--brand-blue-dark);

    font-size: 0.78rem;
    font-weight: 700;
}}

.overview-hero-title {{
    color: var(--brand-text);

    font-size: 2.25rem;
    font-weight: 900;

    line-height: 1.06;
    letter-spacing: -0.035em;

    margin-bottom: 0.55rem;
}}

.overview-hero-caption {{
    color: #536783;

    font-size: 0.98rem;
    line-height: 1.6;

    max-width: 680px;
}}


/* ============================================================
   Filter Card
   ============================================================ */

.st-key-overview_filters {{
    background: var(--card-bg);

    border:
        1px solid var(--card-border);

    border-radius: 21px;

    padding:
        1.15rem 1.3rem 1rem 1.3rem;

    margin-bottom: 1.3rem;

    box-shadow: var(--card-shadow);
}}

.overview-filter-title {{
    color: var(--heading-text);

    font-size: 1.05rem;
    font-weight: 800;

    margin-bottom: 0.15rem;
}}

.overview-filter-caption {{
    color: var(--soft-text);

    font-size: 0.84rem;

    margin-bottom: 0.75rem;
}}


/* ============================================================
   Selected Series
   ============================================================ */

.overview-series-card {{
    position: relative;

    padding:
        1.25rem 1.45rem
        1.25rem 1.65rem;

    margin-bottom: 0.9rem;

    border-radius: 20px;

    border:
        1px solid
        rgba(23, 105, 255, 0.10);

    background:
        linear-gradient(
            110deg,
            rgba(239, 246, 255, 0.96),
            rgba(255, 255, 255, 0.97)
        );

    box-shadow: var(--card-shadow);
}}

.overview-series-card::before {{
    content: "";

    position: absolute;

    left: 0;
    top: 18px;
    bottom: 18px;

    width: 5px;

    border-radius: 999px;

    background:
        linear-gradient(
            180deg,
            var(--brand-blue),
            #64adff
        );
}}

.overview-series-title {{
    color: var(--brand-text);

    font-size: 1.48rem;
    font-weight: 850;

    line-height: 1.2;
    letter-spacing: -0.02em;

    margin-bottom: 0.28rem;
}}

.overview-series-meta {{
    color: #6d7a96;

    font-size: 0.87rem;
}}


/* ============================================================
   Source Note
   ============================================================ */

.overview-source-note {{
    border-radius: 16px;

    padding: 0.85rem 1rem;

    margin-bottom: 1rem;

    background:
        linear-gradient(
            90deg,
            rgba(255, 193, 7, 0.075),
            rgba(255, 241, 197, 0.13)
        );

    border:
        1px solid
        rgba(209, 154, 0, 0.14);

    color: #6a5727;

    font-size: 0.84rem;
    line-height: 1.5;
}}


/* ============================================================
   KPI Cards
   ============================================================ */

.overview-kpi {{
    position: relative;
    overflow: hidden;

    min-height: 142px;

    padding: 1.15rem 1.2rem;

    border-radius: 19px;

    border:
        1px solid var(--card-border);

    background: var(--card-bg);

    box-shadow: var(--card-shadow);
}}

.overview-kpi::before {{
    content: "";

    position: absolute;

    top: 0;
    left: 0;

    width: 100%;
    height: 4px;

    background:
        linear-gradient(
            90deg,
            var(--brand-blue),
            #67adff
        );
}}

.overview-kpi-label {{
    color: #657493;

    font-size: 0.82rem;
    font-weight: 700;

    margin-bottom: 0.62rem;
}}

.overview-kpi-value {{
    color: var(--brand-text);

    font-size: 1.85rem;
    font-weight: 900;

    line-height: 1.05;

    letter-spacing: -0.025em;
}}

.overview-kpi-value.positive {{
    color: #13864a;
}}

.overview-kpi-value.negative {{
    color: #cc4545;
}}

.overview-kpi-note {{
    color: var(--soft-text);

    font-size: 0.78rem;
    line-height: 1.45;

    margin-top: 0.55rem;
}}


/* ============================================================
   Main Content Cards
   ============================================================ */

.st-key-overview_trend_card,
.st-key-overview_summary_card,
.st-key-overview_recent_card {{
    background:
        rgba(255, 255, 255, 0.96);

    border:
        1px solid var(--card-border);

    border-radius: 22px;

    padding: 1.25rem 1.4rem;

    box-shadow: var(--card-shadow);

    margin-top: 1.1rem;
    margin-bottom: 1.15rem;
}}

.overview-card-title {{
    display: flex;
    align-items: center;

    gap: 0.65rem;

    color: var(--brand-text);

    font-size: 1.35rem;
    font-weight: 850;

    letter-spacing: -0.018em;

    margin-bottom: 0.2rem;
}}

.overview-card-title::before {{
    content: "";

    width: 4px;
    height: 21px;

    border-radius: 999px;

    background:
        linear-gradient(
            180deg,
            var(--brand-blue),
            #63adff
        );
}}

.overview-card-caption {{
    color: #7885a0;

    font-size: 0.84rem;
    line-height: 1.5;

    margin-left: 0.65rem;
    margin-bottom: 0.7rem;
}}


/* ============================================================
   Summary Cards
   ============================================================ */

.overview-summary-stat {{
    min-height: 120px;

    padding: 1rem 1.05rem;

    border-radius: 17px;

    background:
        linear-gradient(
            145deg,
            #f7faff,
            #ffffff
        );

    border:
        1px solid
        rgba(38, 91, 170, 0.09);
}}

.overview-summary-label {{
    color: #6c7995;

    font-size: 0.79rem;
    font-weight: 700;

    margin-bottom: 0.45rem;
}}

.overview-summary-value {{
    color: var(--brand-text);

    font-size: 1.5rem;
    font-weight: 850;

    line-height: 1.1;
}}

.overview-summary-value.positive {{
    color: #13864a;
}}

.overview-summary-value.negative {{
    color: #cc4545;
}}

.overview-summary-note {{
    color: #7c89a3;

    font-size: 0.76rem;

    margin-top: 0.45rem;
}}


/* ============================================================
   Recent Observations
   ============================================================ */

.st-key-overview_recent_card
[data-testid="stDataFrame"] {{
    border-radius: 14px;

    overflow: hidden;
}}

.st-key-overview_download
div.stDownloadButton {{
    display: flex;

    justify-content: flex-end;
}}

.st-key-overview_download
button {{
    border-radius: 10px !important;

    min-height: 2.5rem;
}}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# HTML helper
# ---------------------------------------------------------------------


def render_html(
    content: str,
) -> None:
    """Render dashboard HTML without Markdown parsing."""
    st.html(dedent(content).strip())


# ---------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------


def percentage_class(
    value: float | None,
) -> str:
    """Return directional CSS class."""
    if value is None or pd.isna(value):
        return ""

    if value > 0:
        return "positive"

    if value < 0:
        return "negative"

    return ""


def percentage_note(
    value: float | None,
    *,
    positive_text: str,
    negative_text: str,
) -> str:
    """Return short directional interpretation."""
    if value is None or pd.isna(value):
        return "Comparison unavailable"

    if value > 0:
        return positive_text

    if value < 0:
        return negative_text

    return "No change"


# ---------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------

render_html(
    """
    <div class="overview-hero">

        <div class="overview-hero-content">

            <div class="overview-hero-chip">
                Rental market snapshot
            </div>

            <div class="overview-hero-title">
                Market Overview
            </div>

            <div class="overview-hero-caption">
                Explore recent rental-market conditions,
                short-term movements, and historical context
                across New Zealand Regions and
                Territorial Authorities.
            </div>

        </div>

    </div>
    """
)


# ---------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------

panel = load_monthly_panel()


# ---------------------------------------------------------------------
# Inline filters
# ---------------------------------------------------------------------

with st.container(
    key="overview_filters",
):
    render_html(
        """
        <div class="overview-filter-title">
            Market Selection
        </div>

        <div class="overview-filter-caption">
            Choose a geography, location, market indicator,
            and analysis period.
        </div>
        """
    )

    (
        geography_level,
        location_name,
        metric,
    ) = series_selector(
        panel,
        key_prefix="overview",
        use_sidebar=False,
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
        use_sidebar=False,
        default_years=10,
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
    st.warning("No observations are available for the selected date range.")
    st.stop()


# ---------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------

latest = series.iloc[-1]

latest_date = pd.Timestamp(latest["period_date"])

latest_value = float(latest["value"])

history_to_latest = full_series[full_series["period_date"] <= latest_date].sort_values(
    "period_date"
)


# Month-on-month
mom_change = None

if len(history_to_latest) >= 2:
    previous_value = float(history_to_latest.iloc[-2]["value"])

    if previous_value != 0:
        mom_change = (latest_value - previous_value) / previous_value * 100


# Year-on-year
yoy_change = None

target_yoy_period = latest_date - pd.DateOffset(months=12)

yoy_row = full_series[full_series["period_date"] == target_yoy_period]

if not yoy_row.empty:
    yoy_value = float(yoy_row.iloc[0]["value"])

    if yoy_value != 0:
        yoy_change = (latest_value - yoy_value) / yoy_value * 100


# Selected-period average
period_average = float(series["value"].mean())


# Period boundaries
series_start = pd.Timestamp(series["period_date"].min())

series_end = pd.Timestamp(series["period_date"].max())


# Period change
period_change = None

first_value = float(series.iloc[0]["value"])

if first_value != 0:
    period_change = (latest_value - first_value) / first_value * 100


# Minimum
minimum_index = series["value"].idxmin()

minimum_value = float(
    series.loc[
        minimum_index,
        "value",
    ]
)

minimum_date = pd.Timestamp(
    series.loc[
        minimum_index,
        "period_date",
    ]
)


# Maximum
maximum_index = series["value"].idxmax()

maximum_value = float(
    series.loc[
        maximum_index,
        "value",
    ]
)

maximum_date = pd.Timestamp(
    series.loc[
        maximum_index,
        "period_date",
    ]
)


# Geography label
geography_display = (
    "Territorial Authority" if geography_level == "territorial_authority" else "Region"
)


# ---------------------------------------------------------------------
# Selected series
# ---------------------------------------------------------------------

render_html(
    f"""
    <div class="overview-series-card">

        <div class="overview-series-title">
            {html.escape(str(location_name))}
            — {html.escape(metric_label(metric))}
        </div>

        <div class="overview-series-meta">
            {html.escape(geography_display)}
            &nbsp;•&nbsp;
            Selected period:
            {series_start:%b %Y}
            –
            {series_end:%b %Y}
        </div>

    </div>
    """
)


# ---------------------------------------------------------------------
# Source status
# ---------------------------------------------------------------------

if series["source_snapshot_provisional"].fillna(False).any():
    render_html(
        """
        <div class="overview-source-note">

            <strong>Source status:</strong>

            The current source snapshot is marked as
            provisional by Tenancy Services during the
            Bond Hub migration period. Historical observations
            are shown as published in this snapshot and may
            be revised in future source releases.

        </div>
        """
    )


# ---------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------

kpi_data = [
    (
        "Latest Observed Value",
        format_value(
            latest_value,
            metric,
        ),
        "",
        (f"Latest observation · {latest_date:%b %Y}"),
    ),
    (
        "Month-on-Month",
        format_percentage(
            mom_change,
        ),
        percentage_class(
            mom_change,
        ),
        percentage_note(
            mom_change,
            positive_text=("Increase from previous month"),
            negative_text=("Decrease from previous month"),
        ),
    ),
    (
        "Year-on-Year",
        format_percentage(
            yoy_change,
        ),
        percentage_class(
            yoy_change,
        ),
        percentage_note(
            yoy_change,
            positive_text=("Increase from the same month one year earlier"),
            negative_text=("Decrease from the same month one year earlier"),
        ),
    ),
    (
        "Selected Period Average",
        format_value(
            period_average,
            metric,
        ),
        "",
        (f"Average across {len(series):,} monthly observations"),
    ),
]

kpi_columns = st.columns(4)

for column, (
    label,
    value,
    css_class,
    note,
) in zip(
    kpi_columns,
    kpi_data,
):
    with column:
        render_html(
            f"""
            <div class="overview-kpi">

                <div class="overview-kpi-label">
                    {html.escape(label)}
                </div>

                <div
                    class="overview-kpi-value
                    {html.escape(css_class)}"
                >
                    {html.escape(str(value))}
                </div>

                <div class="overview-kpi-note">
                    {html.escape(str(note))}
                </div>

            </div>
            """
        )


# ---------------------------------------------------------------------
# Historical trend
# ---------------------------------------------------------------------

chart_data = series[
    [
        "period_date",
        "value",
    ]
].copy()

chart_data["rolling_12m"] = (
    chart_data["value"]
    .rolling(
        window=12,
        min_periods=12,
    )
    .mean()
)

with st.container(
    key="overview_trend_card",
):
    render_html(
        f"""
        <div class="overview-card-title">
            Historical Trend
        </div>

        <div class="overview-card-caption">
            Monthly observations and 12-month rolling average
            for {html.escape(metric_label(metric))},
            {series_start:%b %Y} – {series_end:%b %Y}.
        </div>
        """
    )

    monthly_line = (
        alt.Chart(chart_data)
        .mark_line(
            color="#83bfff",
            strokeWidth=1.4,
            opacity=0.72,
        )
        .encode(
            x=alt.X(
                "period_date:T",
                title=None,
                axis=alt.Axis(
                    format="%Y",
                    tickCount=10,
                    labelColor="#71809c",
                    tickColor="#d7dfeb",
                    grid=False,
                ),
            ),
            y=alt.Y(
                "value:Q",
                title=metric_axis_label(metric),
                scale=alt.Scale(
                    zero=False,
                ),
                axis=alt.Axis(
                    labelColor="#71809c",
                    titleColor="#52617e",
                    gridColor="#edf1f7",
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
                    title="Monthly Value",
                    format=",.1f",
                ),
            ],
        )
    )

    rolling_line = (
        alt.Chart(chart_data)
        .mark_line(
            color="#1769ff",
            strokeWidth=3,
        )
        .encode(
            x=alt.X(
                "period_date:T",
                title=None,
            ),
            y=alt.Y(
                "rolling_12m:Q",
                title=metric_axis_label(metric),
            ),
            tooltip=[
                alt.Tooltip(
                    "period_date:T",
                    title="Period",
                    format="%b %Y",
                ),
                alt.Tooltip(
                    "rolling_12m:Q",
                    title="12-Month Average",
                    format=",.1f",
                ),
            ],
        )
    )

    latest_point = (
        alt.Chart(chart_data.tail(1))
        .mark_circle(
            color="#0b57d0",
            size=85,
        )
        .encode(
            x=alt.X(
                "period_date:T",
                title=None,
            ),
            y=alt.Y(
                "value:Q",
                title=metric_axis_label(metric),
            ),
            tooltip=[
                alt.Tooltip(
                    "period_date:T",
                    title="Latest Period",
                    format="%b %Y",
                ),
                alt.Tooltip(
                    "value:Q",
                    title="Latest Value",
                    format=",.1f",
                ),
            ],
        )
    )

    trend_chart = (monthly_line + rolling_line + latest_point).properties(
        height=370,
    )

    st.altair_chart(
        trend_chart.interactive(
            bind_y=False,
        ),
        width="stretch",
    )

    legend_col1, legend_col2 = st.columns(
        [1.2, 4],
    )

    with legend_col1:
        st.caption("Monthly observations")

    with legend_col2:
        st.caption("12-month rolling average")


# ---------------------------------------------------------------------
# Selected period summary
# ---------------------------------------------------------------------

with st.container(
    key="overview_summary_card",
):
    render_html(
        """
        <div class="overview-card-title">
            Selected Period Summary
        </div>

        <div class="overview-card-caption">
            Key descriptive statistics for the selected
            analysis window.
        </div>
        """
    )

    summary_data = [
        (
            "Minimum",
            format_value(
                minimum_value,
                metric,
            ),
            f"{minimum_date:%b %Y}",
            "",
        ),
        (
            "Maximum",
            format_value(
                maximum_value,
                metric,
            ),
            f"{maximum_date:%b %Y}",
            "",
        ),
        (
            "Period Change",
            format_percentage(
                period_change,
            ),
            (f"{series_start:%b %Y} → {series_end:%b %Y}"),
            percentage_class(
                period_change,
            ),
        ),
    ]

    summary_columns = st.columns(3)

    for column, (
        label,
        value,
        note,
        css_class,
    ) in zip(
        summary_columns,
        summary_data,
    ):
        with column:
            render_html(
                f"""
                <div class="overview-summary-stat">

                    <div class="overview-summary-label">
                        {html.escape(label)}
                    </div>

                    <div
                        class="overview-summary-value
                        {html.escape(css_class)}"
                    >
                        {html.escape(str(value))}
                    </div>

                    <div class="overview-summary-note">
                        {html.escape(str(note))}
                    </div>

                </div>
                """
            )


# ---------------------------------------------------------------------
# Recent observations
# ---------------------------------------------------------------------

recent_source = series[
    [
        "period_date",
        "value",
    ]
].copy()

recent_source["month_on_month"] = recent_source["value"].pct_change().mul(100)

recent = recent_source.tail(12).sort_values(
    "period_date",
    ascending=False,
)

display = pd.DataFrame(
    {
        "Period": (recent["period_date"].dt.strftime("%b %Y")),
        metric_axis_label(metric): [
            format_value(
                value,
                metric,
            )
            for value in recent["value"]
        ],
        "Month-on-Month": [
            format_percentage(
                value,
            )
            for value in recent["month_on_month"]
        ],
    }
)

with st.container(
    key="overview_recent_card",
):
    title_col, button_col = st.columns(
        [4, 1],
        vertical_alignment="center",
    )

    with title_col:
        render_html(
            """
            <div class="overview-card-title">
                Recent Observations
            </div>

            <div class="overview-card-caption">
                The 12 most recent monthly observations
                within the selected analysis period.
            </div>
            """
        )

    with (
        button_col,
        st.container(
            key="overview_download",
        ),
    ):
        csv_data = (
            recent[
                [
                    "period_date",
                    "value",
                    "month_on_month",
                ]
            ]
            .rename(
                columns={
                    "period_date": "period",
                    "value": "value",
                    "month_on_month": ("month_on_month_pct"),
                }
            )
            .to_csv(
                index=False,
            )
            .encode("utf-8")
        )

        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=(f"overview_{geography_level}_{metric}.csv"),
            mime="text/csv",
            width="stretch",
        )

    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
    )
