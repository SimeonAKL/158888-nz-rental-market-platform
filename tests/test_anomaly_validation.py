"""Tests for final anomaly validation."""

from __future__ import annotations

import pandas as pd
import pytest

from rmp.anomaly.validation import (
    build_anomaly_metadata,
    validate_anomaly_summary,
)


def _summary() -> pd.DataFrame:
    """Create a logically consistent summary dataset."""
    return pd.DataFrame(
        {
            "period_date": [
                "2026-01-01",
                "2026-02-01",
                "2026-03-01",
                "2026-04-01",
                "2026-05-01",
            ],
            "series_id": [
                "series_a",
                "series_a",
                "series_a",
                "series_a",
                "series_a",
            ],
            "metric": [
                "median_rent",
                "median_rent",
                "median_rent",
                "median_rent",
                "median_rent",
            ],
            "value": [
                500.0,
                510.0,
                520.0,
                530.0,
                540.0,
            ],
            "historical_detector_available": [
                True,
                True,
                True,
                True,
                False,
            ],
            "forecast_detector_available": [
                False,
                True,
                True,
                True,
                False,
            ],
            "historical_dashboard_alert": [
                False,
                True,
                False,
                True,
                False,
            ],
            "forecast_dashboard_alert": [
                False,
                False,
                True,
                True,
                False,
            ],
            "overall_dashboard_alert": [
                False,
                True,
                True,
                True,
                False,
            ],
            "overall_status": [
                "normal",
                "historical_alert",
                "forecast_alert",
                "confirmed_anomaly",
                "unavailable",
            ],
            "overall_severity": [
                "normal",
                "moderate",
                "high",
                "high",
                "unavailable",
            ],
            "overall_direction": [
                "normal",
                "high",
                "low",
                "mixed",
                "normal",
            ],
            "detector_coverage": [
                "historical_only",
                "both",
                "both",
                "both",
                "unavailable",
            ],
            "has_forecast_record": [
                False,
                True,
                True,
                True,
                False,
            ],
        }
    )


def test_valid_summary_passes_all_checks() -> None:
    validation = validate_anomaly_summary(_summary())

    assert validation["passed"].all()


def test_duplicate_series_period_fails() -> None:
    frame = _summary()

    duplicate = pd.concat(
        [
            frame,
            frame.iloc[[0]],
        ],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="unique_series_period",
    ):
        validate_anomaly_summary(duplicate)


def test_invalid_status_fails() -> None:
    frame = _summary()
    frame.loc[
        0,
        "overall_status",
    ] = "invalid_status"

    with pytest.raises(
        ValueError,
        match="valid_overall_status",
    ):
        validate_anomaly_summary(frame)


def test_overall_alert_union_is_validated() -> None:
    frame = _summary()

    frame.loc[
        0,
        "overall_dashboard_alert",
    ] = True

    with pytest.raises(
        ValueError,
        match="overall_alert_union",
    ):
        validate_anomaly_summary(frame)


def test_confirmed_requires_both_alerts() -> None:
    frame = _summary()

    frame.loc[
        1,
        "overall_status",
    ] = "confirmed_anomaly"

    with pytest.raises(
        ValueError,
        match="confirmed_anomaly_logic",
    ):
        validate_anomaly_summary(frame)


def test_unavailable_requires_no_detector() -> None:
    frame = _summary()

    frame.loc[
        0,
        "overall_status",
    ] = "unavailable"

    with pytest.raises(
        ValueError,
        match="unavailable_status_logic",
    ):
        validate_anomaly_summary(frame)


def test_detector_coverage_is_validated() -> None:
    frame = _summary()

    frame.loc[
        0,
        "detector_coverage",
    ] = "both"

    with pytest.raises(
        ValueError,
        match="detector_coverage_logic",
    ):
        validate_anomaly_summary(frame)


def test_alert_requires_alert_severity() -> None:
    frame = _summary()

    frame.loc[
        1,
        "overall_severity",
    ] = "normal"

    with pytest.raises(
        ValueError,
        match="alert_severity_consistency",
    ):
        validate_anomaly_summary(frame)


def test_metadata_contains_core_sections() -> None:
    metadata = build_anomaly_metadata(_summary())

    categories = set(metadata["category"])

    assert {
        "dataset",
        "historical_detector",
        "historical_practical",
        "forecast_detector",
        "forecast_practical",
        "outputs",
    }.issubset(categories)


def test_metadata_counts_outputs() -> None:
    metadata = build_anomaly_metadata(_summary())

    values = metadata.set_index(
        [
            "category",
            "item",
        ]
    )["value"]

    assert (
        int(
            values.loc[
                (
                    "outputs",
                    "historical_dashboard_alerts",
                )
            ]
        )
        == 2
    )

    assert (
        int(
            values.loc[
                (
                    "outputs",
                    "forecast_dashboard_alerts",
                )
            ]
        )
        == 2
    )

    assert (
        int(
            values.loc[
                (
                    "outputs",
                    "confirmed_anomalies",
                )
            ]
        )
        == 1
    )

    assert (
        int(
            values.loc[
                (
                    "outputs",
                    "overall_dashboard_alerts",
                )
            ]
        )
        == 3
    )
