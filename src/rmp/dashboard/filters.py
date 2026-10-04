"""Reusable Streamlit dashboard filters."""

from __future__ import annotations

import pandas as pd
import streamlit as st

METRIC_LABELS = {
    "median_rent": "Median Weekly Rent",
    "bonds_lodged": "New Bonds Lodged",
}


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

    if metric == "bonds_lodged":
        return "New Bonds Lodged"

    return metric_label(metric)


def series_selector(
    data: pd.DataFrame,
    *,
    key_prefix: str,
) -> tuple[str, str, str]:
    """Render geography, location and metric selectors."""
    geography_levels = sorted(
        data["geography_level"]
        .dropna()
        .unique()
    )

    geography_level = st.sidebar.selectbox(
        "Geography level",
        geography_levels,
        format_func=lambda value: (
            value.replace("_", " ").title()
        ),
        key=f"{key_prefix}_geography",
    )

    geography_data = data[
        data["geography_level"]
        == geography_level
    ]

    locations = sorted(
        geography_data["location_name"]
        .dropna()
        .unique()
    )

    location_name = st.sidebar.selectbox(
        "Location",
        locations,
        key=f"{key_prefix}_location",
    )

    location_data = geography_data[
        geography_data["location_name"]
        == location_name
    ]

    metrics = sorted(
        location_data["metric"]
        .dropna()
        .unique()
    )

    metric = st.sidebar.selectbox(
        "Metric",
        metrics,
        format_func=metric_label,
        key=f"{key_prefix}_metric",
    )

    return (
        geography_level,
        location_name,
        metric,
    )


def date_range_selector(
    data: pd.DataFrame,
    *,
    date_column: str,
    key_prefix: str,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Render explicit start and end date selectors."""
    dates = pd.to_datetime(
        data[date_column]
    ).dropna()

    minimum = dates.min()
    maximum = dates.max()

    st.sidebar.markdown("**Date range**")

    start_date = st.sidebar.date_input(
        "Start date",
        value=minimum.date(),
        min_value=minimum.date(),
        max_value=maximum.date(),
        key=f"{key_prefix}_start_date",
    )

    end_date = st.sidebar.date_input(
        "End date",
        value=maximum.date(),
        min_value=minimum.date(),
        max_value=maximum.date(),
        key=f"{key_prefix}_end_date",
    )

    start_timestamp = pd.Timestamp(start_date)
    end_timestamp = pd.Timestamp(end_date)

    if start_timestamp > end_timestamp:
        st.sidebar.error(
            "Start date must be earlier than or equal to end date."
        )
        return minimum, maximum

    return (
        start_timestamp,
        end_timestamp,
    )

def filter_series(
    data: pd.DataFrame,
    *,
    geography_level: str,
    location_name: str,
    metric: str,
) -> pd.DataFrame:
    """Filter a dataframe to one selected series."""
    return data[
        (
            data["geography_level"]
            == geography_level
        )
        & (
            data["location_name"]
            == location_name
        )
        & (
            data["metric"]
            == metric
        )
    ].copy()


def filter_date_range(
    data: pd.DataFrame,
    *,
    date_column: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    """Filter a dataframe to a selected inclusive date range."""
    dates = pd.to_datetime(
        data[date_column]
    )

    return data[
        (dates >= start_date)
        & (dates <= end_date)
    ].copy()
