"""Regression tests for reusable dashboard filtering logic."""

from __future__ import annotations

import pandas as pd

from rmp.dashboard.filters import (
    _ordered_metrics,
    filter_date_range,
    filter_series,
    geography_label,
    metric_axis_label,
    metric_label,
)


def test_metric_labels_are_user_facing() -> None:
    assert metric_label("median_rent") == "Median Weekly Rent"
    assert metric_label("bonds_lodged") == "New Bonds Lodged"
    assert metric_label("custom_metric") == "Custom Metric"

    assert metric_axis_label("median_rent") == "Median Weekly Rent (NZD)"
    assert metric_axis_label("bonds_lodged") == "New Bonds Lodged"

    assert geography_label("territorial_authority") == "Territorial Authority"


def test_ordered_metrics_prioritises_known_metrics() -> None:
    result = _ordered_metrics(
        [
            "z_metric",
            "bonds_lodged",
            "a_metric",
            "median_rent",
        ]
    )

    assert result == [
        "median_rent",
        "bonds_lodged",
        "a_metric",
        "z_metric",
    ]


def test_filter_series_returns_only_requested_series() -> None:
    data = pd.DataFrame(
        {
            "geography_level": [
                "region",
                "region",
                "territorial_authority",
                "region",
            ],
            "location_name": [
                "Auckland",
                "Auckland",
                "Auckland",
                "Wellington",
            ],
            "metric": [
                "median_rent",
                "bonds_lodged",
                "median_rent",
                "median_rent",
            ],
            "value": [
                650.0,
                1200.0,
                700.0,
                620.0,
            ],
        }
    )

    result = filter_series(
        data,
        geography_level="region",
        location_name="Auckland",
        metric="median_rent",
    )

    assert len(result) == 1
    assert result.iloc[0]["value"] == 650.0

    # The function must return an independent copy.
    result.loc[result.index[0], "value"] = 999.0
    assert data.iloc[0]["value"] == 650.0


def test_filter_series_can_return_empty_dataframe() -> None:
    data = pd.DataFrame(
        {
            "geography_level": ["region"],
            "location_name": ["Auckland"],
            "metric": ["median_rent"],
            "value": [650.0],
        }
    )

    result = filter_series(
        data,
        geography_level="region",
        location_name="Christchurch",
        metric="median_rent",
    )

    assert result.empty


def test_filter_date_range_is_inclusive() -> None:
    data = pd.DataFrame(
        {
            "period_date": [
                "2026-01-01",
                "2026-02-01",
                "2026-03-01",
                "2026-04-01",
            ],
            "value": [1, 2, 3, 4],
        }
    )

    result = filter_date_range(
        data,
        date_column="period_date",
        start_date=pd.Timestamp("2026-02-01"),
        end_date=pd.Timestamp("2026-03-01"),
    )

    assert result["value"].tolist() == [2, 3]


def test_filter_date_range_accepts_string_backed_dates() -> None:
    data = pd.DataFrame(
        {
            "forecast_period": [
                "2026-08-01",
                "2026-09-01",
                "2026-10-01",
            ],
            "predicted": [650.0, 655.0, 660.0],
        }
    )

    result = filter_date_range(
        data,
        date_column="forecast_period",
        start_date=pd.Timestamp("2026-09-01"),
        end_date=pd.Timestamp("2026-10-01"),
    )

    assert result["predicted"].tolist() == [655.0, 660.0]
