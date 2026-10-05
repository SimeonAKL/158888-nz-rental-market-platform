"""Reusable Streamlit dashboard filters."""

from __future__ import annotations

import pandas as pd
import streamlit as st

METRIC_LABELS = {
    "median_rent": "Median Weekly Rent",
    "bonds_lodged": "New Bonds Lodged",
}

# Display order in the indicator dropdown.
# Unknown metrics follow alphabetically.
METRIC_ORDER = [
    "median_rent",
    "bonds_lodged",
]


def metric_label(metric: str) -> str:
    """Return a human-readable metric label."""
    return METRIC_LABELS.get(
        metric,
        metric.replace("_", " ").title(),
    )


def metric_axis_label(metric: str) -> str:
    """Return a user-facing chart axis label."""
    if metric == "median_rent":
        return "Median Weekly Rent (NZD)"

    return metric_label(metric)


def geography_label(value: str) -> str:
    """Return a human-readable geography level label."""
    return value.replace(
        "_",
        " ",
    ).title()


def _ordered_metrics(
    metrics: list[str],
) -> list[str]:
    """Sort metrics by configured order, then alphabetically."""
    known = [metric for metric in METRIC_ORDER if metric in metrics]

    others = sorted(metric for metric in metrics if metric not in METRIC_ORDER)

    return known + others


def _slots(
    count: int,
    use_sidebar: bool,
) -> list:
    """Return sidebar slots or side-by-side columns."""
    if use_sidebar:
        return [st.sidebar] * count

    return list(st.columns(count))


# ---------------------------------------------------------------------
# Series selector
# ---------------------------------------------------------------------


def series_selector(
    data: pd.DataFrame,
    *,
    key_prefix: str,
    use_sidebar: bool = False,
) -> tuple[str, str, str]:
    """Render geography, location and indicator selectors."""

    (
        geography_slot,
        location_slot,
        metric_slot,
    ) = _slots(
        3,
        use_sidebar,
    )

    geography_levels = sorted(data["geography_level"].dropna().unique())

    geography_level = geography_slot.selectbox(
        "Geography level",
        geography_levels,
        format_func=geography_label,
        key=f"{key_prefix}_geography",
    )

    geography_data = data[data["geography_level"] == geography_level]

    locations = sorted(geography_data["location_name"].dropna().unique())

    location_name = location_slot.selectbox(
        "Location",
        locations,
        key=f"{key_prefix}_location",
    )

    location_data = geography_data[geography_data["location_name"] == location_name]

    metrics = _ordered_metrics(list(location_data["metric"].dropna().unique()))

    metric = metric_slot.selectbox(
        "Indicator",
        metrics,
        format_func=metric_label,
        key=f"{key_prefix}_metric",
    )

    return (
        geography_level,
        location_name,
        metric,
    )


# ---------------------------------------------------------------------
# Period selector
# ---------------------------------------------------------------------


def date_range_selector(
    data: pd.DataFrame,
    *,
    date_column: str,
    key_prefix: str,
    use_sidebar: bool = False,
    default_years: int | None = None,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Render a month-range slider.

    Parameters
    ----------
    default_years:
        When provided, the initial range covers approximately
        the latest N years. When omitted, the full available
        history is selected.
    """

    months = sorted(pd.to_datetime(data[date_column]).dropna().unique())

    months = [pd.Timestamp(month) for month in months]

    if not months:
        raise ValueError("No dates available for the period selector.")

    if len(months) == 1:
        return (
            months[0],
            months[0],
        )

    first = months[0]
    last = months[-1]

    default_start = first

    if default_years is not None:
        cutoff = last - pd.DateOffset(
            years=default_years,
        )

        default_start = next(
            (month for month in months if month >= cutoff),
            first,
        )

    target = st.sidebar if use_sidebar else st

    if default_years is None:
        guidance = (
            "Default view: full available history. "
            "Adjust the range below to focus on "
            "a shorter period."
        )
    else:
        guidance = (
            f"Default view: latest {default_years} years. "
            "Adjust the range below to explore earlier "
            "or shorter periods."
        )

    target.caption(guidance)

    start, end = target.select_slider(
        "Analysis period",
        options=months,
        value=(
            default_start,
            last,
        ),
        format_func=lambda month: month.strftime("%b %Y"),
        key=f"{key_prefix}_period",
    )

    return (
        pd.Timestamp(start),
        pd.Timestamp(end),
    )


# ---------------------------------------------------------------------
# Data filters
# ---------------------------------------------------------------------


def filter_series(
    data: pd.DataFrame,
    *,
    geography_level: str,
    location_name: str,
    metric: str,
) -> pd.DataFrame:
    """Filter a dataframe to one selected series."""

    mask = (
        (data["geography_level"] == geography_level)
        & (data["location_name"] == location_name)
        & (data["metric"] == metric)
    )

    return data[mask].copy()


def filter_date_range(
    data: pd.DataFrame,
    *,
    date_column: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    """Filter a dataframe to an inclusive date range."""

    dates = pd.to_datetime(data[date_column])

    return data[(dates >= start_date) & (dates <= end_date)].copy()
