"""Anomaly detection dashboard page."""

from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from rmp.dashboard.data import (
    load_anomaly_summary,
)
from rmp.dashboard.filters import (
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
)

# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Anomaly Detection",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_home_styles()

render_top_navigation(
    active_page="Anomaly Detection",
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

HERO_IMAGE_PATH = PROJECT_ROOT / "assets" / "auckland_skyline.jpg"


# ---------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------

BLUE = "#1769ff"
LIGHT_BLUE = "#92c3ff"

MODERATE_COLOR = "#f0a23b"
HIGH_COLOR = "#df4d4d"
BOTH_COLOR = "#7a5af8"

LABEL_COLOR = "#71809c"
TITLE_COLOR = "#52617e"
GRID_COLOR = "#edf1f7"
TICK_COLOR = "#d7dfeb"


STATUS_LABELS = {
    "normal": "Normal",
    "historical_alert": ("Historical Alert"),
    "forecast_alert": ("Forecast Alert"),
    "confirmed_anomaly": ("Both Detectors Flagged"),
    "unavailable": "Unavailable",
}


SEVERITY_LABELS = {
    "normal": "Normal",
    "moderate": "Moderate",
    "high": "High",
    "unavailable": "Unavailable",
}


DIRECTION_LABELS = {
    "positive": "Above Expected",
    "negative": "Below Expected",
    "up": "Above Expected",
    "down": "Below Expected",
    "high": "Above Expected",
    "low": "Below Expected",
}


MODEL_LABELS = {
    "seasonal_naive": ("Seasonal Naive"),
    "ets_additive_damped": ("ETS (Additive Damped)"),
    "xgboost_pooled_recursive": ("XGBoost (Pooled Recursive)"),
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def status_label(
    status: object,
) -> str:
    """Return user-facing anomaly status."""
    if pd.isna(status):
        return "Unavailable"

    value = str(status)

    return STATUS_LABELS.get(
        value,
        value.replace(
            "_",
            " ",
        ).title(),
    )


def severity_label(
    severity: object,
) -> str:
    """Return user-facing severity label."""
    if pd.isna(severity):
        return "Unavailable"

    value = str(severity)

    return SEVERITY_LABELS.get(
        value,
        value.replace(
            "_",
            " ",
        ).title(),
    )


def direction_label(
    direction: object,
) -> str:
    """Return user-facing anomaly direction."""
    if pd.isna(direction):
        return "N/A"

    value = str(direction)

    return DIRECTION_LABELS.get(
        value,
        value.replace(
            "_",
            " ",
        ).title(),
    )


def model_label(
    model: object,
) -> str:
    """Return user-facing forecast model name."""
    if pd.isna(model):
        return "N/A"

    value = str(model)

    return MODEL_LABELS.get(
        value,
        value.replace(
            "_",
            " ",
        ).title(),
    )


def safe_bool_series(
    frame: pd.DataFrame,
    column: str,
) -> pd.Series:
    """Return a Boolean series even when a column is absent."""
    if column not in frame.columns:
        return pd.Series(
            False,
            index=frame.index,
        )

    return frame[column].fillna(False).astype(bool)


def format_optional_value(
    value: object,
    metric: str,
) -> str:
    """Format optional market values."""
    if pd.isna(value):
        return "N/A"

    return format_value(
        float(value),
        metric,
    )


def format_optional_percentage(
    value: object,
) -> str:
    """Format optional percentage values."""
    if pd.isna(value):
        return "N/A"

    return format_percentage(float(value))


# ---------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------

render_page_hero(
    "Anomaly Detection",
    (
        "Identify statistically unusual rental-market "
        "movements using historical seasonal behaviour "
        "and forecast-residual evidence."
    ),
    HERO_IMAGE_PATH,
)


# ---------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------

try:
    data = load_anomaly_summary()

except (
    FileNotFoundError,
    ValueError,
) as exc:
    st.error(str(exc))
    st.stop()


# ---------------------------------------------------------------------
# Series selection
# ---------------------------------------------------------------------

with st.container(
    key="filters_anomaly",
):
    render_filter_header(
        "Anomaly Selection",
        (
            "Choose a geography, location, and market "
            "indicator to review historical alerts and "
            "detector coverage."
        ),
    )

    (
        geography_level,
        location_name,
        metric,
    ) = series_selector(
        data,
        key_prefix="anomaly",
    )


# ---------------------------------------------------------------------
# Selected series
# ---------------------------------------------------------------------

series = (
    filter_series(
        data,
        geography_level=(geography_level),
        location_name=location_name,
        metric=metric,
    )
    .sort_values("period_date")
    .reset_index(drop=True)
)

if series.empty:
    st.warning("No anomaly-analysis data are available for this selection.")
    st.stop()


axis_label = metric_axis_label(metric)

series_start = pd.Timestamp(series["period_date"].min())

series_end = pd.Timestamp(series["period_date"].max())


alert_mask = safe_bool_series(
    series,
    "overall_dashboard_alert",
)

alerts = series.loc[alert_mask].copy()


has_forecast_coverage = bool(
    safe_bool_series(
        series,
        "has_forecast_record",
    ).any()
)


# ---------------------------------------------------------------------
# Series header
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


if (
    "source_snapshot_provisional" in series.columns
    and series["source_snapshot_provisional"].fillna(False).any()
):
    render_source_note()


# ---------------------------------------------------------------------
# Detector coverage
# ---------------------------------------------------------------------

if not has_forecast_coverage:
    st.info(
        "**Historical anomaly coverage only.** "
        "This series remains available for historical "
        "anomaly detection but is outside the "
        "forecast-eligible modelling subset, so "
        "forecast-residual anomaly detection is not "
        "available for this series."
    )


# ---------------------------------------------------------------------
# Headline statistics
# ---------------------------------------------------------------------

high_alerts = (
    alerts.loc[alerts["overall_severity"] == "high"]
    if "overall_severity" in alerts.columns
    else alerts.iloc[0:0]
)


both_flagged = (
    alerts.loc[alerts["overall_status"] == "confirmed_anomaly"]
    if "overall_status" in alerts.columns
    else alerts.iloc[0:0]
)


if alerts.empty:
    latest_alert_text = "None"

    latest_alert_note = "No dashboard-level alerts"

else:
    latest_alert_row = alerts.sort_values("period_date").iloc[-1]

    latest_alert_date = pd.Timestamp(latest_alert_row["period_date"])

    latest_alert_text = latest_alert_date.strftime("%b %Y")

    latest_alert_note = (
        status_label(latest_alert_row["overall_status"])
        if "overall_status" in latest_alert_row.index
        else "Alert"
    )


headline_specs = [
    (
        "Total Alerts",
        f"{len(alerts):,}",
        ("Dashboard-level alerts in the full series"),
    ),
    (
        "High Severity",
        f"{len(high_alerts):,}",
        ("Alerts classified as high severity"),
    ),
    (
        "Both Detectors Flagged",
        f"{len(both_flagged):,}",
        ("Same period flagged by historical and forecast detectors"),
    ),
    (
        "Latest Alert",
        latest_alert_text,
        latest_alert_note,
    ),
]


for column, (
    label,
    value,
    note,
) in zip(
    st.columns(4),
    headline_specs,
):
    with column:
        render_stat_card(
            label,
            value,
            note,
        )


# ---------------------------------------------------------------------
# Historical series with anomaly markers
# ---------------------------------------------------------------------

with st.container(
    key="card_anomaly_history",
):
    render_card_header(
        "Historical Series and Anomaly Alerts",
        (
            "Monthly observations with dashboard-level "
            "anomaly markers. Alert markers indicate "
            "statistically unusual analytical behaviour "
            "rather than confirmed causal events."
        ),
    )

    render_legend(
        [
            (
                "Observed series",
                LIGHT_BLUE,
                2,
            ),
            (
                "Moderate alert",
                MODERATE_COLOR,
                8,
            ),
            (
                "High alert",
                HIGH_COLOR,
                8,
            ),
            (
                "Both detectors flagged",
                BOTH_COLOR,
                8,
            ),
        ]
    )

    chart_data = series[
        [
            "period_date",
            "value",
        ]
    ].copy()

    base_line = (
        alt.Chart(chart_data)
        .mark_line(
            color=LIGHT_BLUE,
            strokeWidth=1.8,
        )
        .encode(
            x=alt.X(
                "period_date:T",
                title=None,
                axis=alt.Axis(
                    format="%Y",
                    grid=False,
                    labelColor=(LABEL_COLOR),
                    tickColor=(TICK_COLOR),
                ),
            ),
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
    )

    if not alerts.empty:
        alert_points = alerts[
            [
                column
                for column in [
                    "period_date",
                    "value",
                    "overall_status",
                    "overall_severity",
                    "overall_direction",
                ]
                if column in alerts.columns
            ]
        ].copy()

        def alert_category(
            row: pd.Series,
        ) -> str:
            """Return chart alert category."""
            if row.get("overall_status") == "confirmed_anomaly":
                return "Both detectors flagged"

            if row.get("overall_severity") == "high":
                return "High"

            return "Moderate"

        alert_points["alert_category"] = alert_points.apply(
            alert_category,
            axis=1,
        )

        alert_points["status_label"] = (
            alert_points["overall_status"].map(status_label)
            if "overall_status" in alert_points.columns
            else "Alert"
        )

        alert_points["severity_label"] = (
            alert_points["overall_severity"].map(severity_label)
            if "overall_severity" in alert_points.columns
            else "N/A"
        )

        alert_points["direction_label"] = (
            alert_points["overall_direction"].map(direction_label)
            if "overall_direction" in alert_points.columns
            else "N/A"
        )

        marker_layer = (
            alt.Chart(alert_points)
            .mark_circle(
                size=95,
                stroke="white",
                strokeWidth=1.2,
            )
            .encode(
                x=alt.X(
                    "period_date:T",
                    title=None,
                ),
                y=alt.Y(
                    "value:Q",
                    title=axis_label,
                ),
                color=alt.Color(
                    "alert_category:N",
                    scale=alt.Scale(
                        domain=[
                            "Moderate",
                            "High",
                            ("Both detectors flagged"),
                        ],
                        range=[
                            MODERATE_COLOR,
                            HIGH_COLOR,
                            BOTH_COLOR,
                        ],
                    ),
                    legend=None,
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
                    alt.Tooltip(
                        "status_label:N",
                        title="Alert Type",
                    ),
                    alt.Tooltip(
                        "severity_label:N",
                        title="Severity",
                    ),
                    alt.Tooltip(
                        "direction_label:N",
                        title="Direction",
                    ),
                ],
            )
        )

        history_chart = base_line + marker_layer

    else:
        history_chart = base_line

    st.altair_chart(
        history_chart.properties(height=380)
        .interactive(bind_y=False)
        .configure_view(strokeWidth=0),
        width="stretch",
    )

    if alerts.empty:
        st.success("No dashboard-level anomaly alerts were identified for this series.")

    else:
        st.caption(
            f"{len(alerts):,} dashboard-level alerts "
            f"were identified between "
            f"{alerts['period_date'].min():%b %Y} "
            f"and {alerts['period_date'].max():%b %Y}."
        )


# ---------------------------------------------------------------------
# Alert history
# ---------------------------------------------------------------------

with st.container(
    key="card_anomaly_alert_history",
):
    render_card_header(
        "Alert History",
        ("Dashboard-level anomaly observations, newest first."),
    )

    if alerts.empty:
        st.info("There are no alert records to display for this series.")

    else:
        recent_alerts = alerts.sort_values(
            "period_date",
            ascending=False,
        ).copy()

        display = pd.DataFrame()

        display["Period"] = recent_alerts["period_date"].dt.strftime("%b %Y")

        display[axis_label] = [
            format_optional_value(
                value,
                metric,
            )
            for value in recent_alerts["value"]
        ]

        if "overall_status" in recent_alerts.columns:
            display["Alert Type"] = recent_alerts["overall_status"].map(status_label)

        if "overall_severity" in recent_alerts.columns:
            display["Severity"] = recent_alerts["overall_severity"].map(severity_label)

        if "overall_direction" in recent_alerts.columns:
            display["Direction"] = recent_alerts["overall_direction"].map(direction_label)

        if "historical_deviation_pct" in recent_alerts.columns:
            display["Historical Deviation"] = [
                format_optional_percentage(value)
                for value in recent_alerts["historical_deviation_pct"]
            ]

        if "forecast_model" in recent_alerts.columns:
            display["Forecast Model"] = recent_alerts["forecast_model"].map(model_label)

        if "predicted" in recent_alerts.columns:
            display["Predicted"] = [
                format_optional_value(
                    value,
                    metric,
                )
                for value in recent_alerts["predicted"]
            ]

        if "forecast_residual_pct" in recent_alerts.columns:
            display["Forecast Residual"] = [
                format_optional_percentage(value)
                for value in recent_alerts["forecast_residual_pct"]
            ]

        # Presentation-only styling for analytical anomaly alerts.
        # A detector flag does not confirm a real-world market event.
        def alert_status_style(value: object) -> str:
            label = str(value).strip().lower()

            if "both detectors" in label:
                return "color: #7754bf; font-weight: 600"

            if "alert" in label or "flagged" in label:
                return "color: #a56817; font-weight: 600"

            if label == "normal":
                return "color: #13864a"

            return "color: #7b88a4"

        def deviation_style(value: object) -> str:
            """Colour signed deviations without implying severity."""
            value_text = (
                str(value)
                .strip()
                .replace("%", "")
                .replace(",", "")
                .replace("−", "-")
            )

            try:
                numeric_value = float(value_text)
            except (TypeError, ValueError):
                return "color: #7b88a4"

            if numeric_value > 0:
                return "color: #1769ff"

            if numeric_value < 0:
                return "color: #cc4545"

            return "color: #7b88a4"

        styled_alerts = display.style

        # Style the actual dashboard alert labels.
        if "Alert Type" in display.columns:
            styled_alerts = styled_alerts.map(
                alert_status_style,
                subset=["Alert Type"],
            )

        if "Severity" in display.columns:
            def severity_style(value: object) -> str:
                label = str(value).strip().lower()

                if label == "high":
                    return "color: #cc4545; font-weight: 600"

                if label == "moderate":
                    return "color: #a56817; font-weight: 600"

                return "color: #7b88a4"

            styled_alerts = styled_alerts.map(
                severity_style,
                subset=["Severity"],
            )

        deviation_columns = [
            column
            for column in [
                "Historical Deviation",
                "Forecast Residual",
            ]
            if column in display.columns
        ]

        if deviation_columns:
            styled_alerts = styled_alerts.map(
                deviation_style,
                subset=deviation_columns,
            )

        if "Predicted" in display.columns:
            styled_alerts = styled_alerts.map(
                lambda value: (
                    "color: #7b88a4"
                    if str(value).strip().upper() in {"N/A", "—", "", "NAN"}
                    else "color: #1769ff; font-weight: 600"
                ),
                subset=["Predicted"],
            )

        alert_table_height = min(
            430,
            (len(display) + 1) * 35 + 3,
        )

        st.dataframe(
            styled_alerts,
            width="stretch",
            hide_index=True,
            height=alert_table_height,
        )


# ---------------------------------------------------------------------
# Detector coverage and status distribution
# ---------------------------------------------------------------------

with st.container(
    key="card_anomaly_status",
):
    render_card_header(
        "Detector Coverage and Status Distribution",
        ("Distribution of dashboard anomaly statuses across the selected historical series."),
    )

    st.caption(
        "Unavailable indicates periods where an anomaly "
        "score could not yet be produced, such as early-history "
        "warm-up periods or unavailable forecast-residual coverage. "
        "It does not necessarily indicate missing market observations."
    )

    status_counts = (
        series["overall_status"]
        .fillna("unavailable")
        .value_counts()
        .rename_axis("status")
        .reset_index(name="observations")
    )

    status_counts["status_label"] = status_counts["status"].map(status_label)

    status_order = [
        "Normal",
        "Historical Alert",
        "Forecast Alert",
        "Both Detectors Flagged",
        "Unavailable",
    ]

    status_chart = (
        alt.Chart(status_counts)
        .mark_bar(
            cornerRadiusEnd=6,
            color=BLUE,
        )
        .encode(
            y=alt.Y(
                "status_label:N",
                title=None,
                sort=status_order,
                axis=alt.Axis(
                    labelColor=(LABEL_COLOR),
                    tickColor=(TICK_COLOR),
                    labelLimit=180,
                ),
            ),
            x=alt.X(
                "observations:Q",
                title="Monthly Observations",
                axis=alt.Axis(
                    labelColor=(LABEL_COLOR),
                    titleColor=(TITLE_COLOR),
                    gridColor=(GRID_COLOR),
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "status_label:N",
                    title="Status",
                ),
                alt.Tooltip(
                    "observations:Q",
                    title="Observations",
                    format=",",
                ),
            ],
        )
        .properties(height=250)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(
        status_chart,
        width="stretch",
    )

    coverage_specs = [
        (
            "Historical Detector",
            "Available",
            ("Historical seasonal anomaly coverage"),
        ),
        (
            "Forecast-Residual Detector",
            ("Available" if has_forecast_coverage else "Not Available"),
            ("Depends on forecast-eligible model coverage"),
        ),
        (
            "Both-Detector Flags",
            f"{len(both_flagged):,}",
            ("Periods flagged by both analytical detector paths"),
        ),
    ]

    for column, (
        label,
        value,
        note,
    ) in zip(
        st.columns(3),
        coverage_specs,
    ):
        with column:
            render_stat_card(
                label,
                value,
                note,
                flat=True,
            )


# ---------------------------------------------------------------------
# Interpretation
# ---------------------------------------------------------------------

with st.container(
    key="card_anomaly_interpretation",
):
    render_card_header(
        "How to Interpret Anomaly Alerts",
        (
            "Anomaly signals identify unusual analytical "
            "patterns, not explanations for why those "
            "patterns occurred."
        ),
    )

    st.info(
        "**Moderate** and **High** indicate the strength "
        "of the statistical alert relative to the detector "
        "baseline. **Both Detectors Flagged** means that the "
        "historical anomaly detector and the forecast-residual "
        "detector both generated dashboard-level alerts for "
        "the same series-period. This does not establish that "
        "a real-world event caused the movement."
    )


# ---------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------

with st.expander(
    "Anomaly Detection Methodology",
    expanded=True,
):
    st.markdown(
        """
### Historical anomaly detector

The historical detector evaluates **year-on-year seasonal
change** against a robust rolling historical baseline.

The expected change is estimated using prior seasonal
behaviour, with robust dispersion based on **MAD/IQR**
rather than assuming normally distributed movements.

Statistical thresholds are combined with practical
significance rules so that small numerical deviations do
not automatically become dashboard alerts.

### Forecast-residual detector

For forecast-eligible series, the forecast detector uses
the **one-step-ahead residual** from the research-layer
selected winner model.

The current residual is compared with the series' previous
out-of-sample residual behaviour using an expanding robust
baseline. The current residual is excluded from the
baseline used to evaluate itself.

### Both Detectors Flagged

A period is shown as **Both Detectors Flagged** when both
the historical detector and forecast-residual detector
produce dashboard-level alerts for the same series-period.

This label refers only to agreement between two analytical
detector paths. It is **not causal confirmation** and does
not establish that a particular economic, policy, migration,
housing, or market event caused the observed movement.

### Coverage

All analytical series can retain historical anomaly
coverage where the required historical information is
available.

Forecast-residual anomaly detection is available only for
series included in the forecast-eligible modelling subset.

A historical-only series is therefore not treated as an
error or failed series; it simply does not have the second
detector path.

**Unavailable** status at a particular period means that
an anomaly score could not yet be produced for that
detector context. This can occur during early-history
warm-up periods or where forecast-residual coverage does
not exist. It does not necessarily mean the underlying
market observation is missing.
"""
    )


render_footer()
