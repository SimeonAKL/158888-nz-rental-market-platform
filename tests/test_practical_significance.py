"""Tests for practical anomaly significance."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rmp.anomaly.practical import (
    PRACTICAL_THRESHOLDS,
    add_practical_significance,
)


def _row(
    *,
    metric: str,
    deviation: float,
    deviation_pct: float,
    statistical_anomaly: bool = True,
    score_available: bool = True,
) -> pd.DataFrame:
    """Create a one-row anomaly frame."""
    return pd.DataFrame(
        {
            "metric": [metric],
            "historical_deviation": [
                deviation
            ],
            "historical_deviation_pct": [
                deviation_pct
            ],
            "historical_is_anomaly": [
                statistical_anomaly
            ],
            "historical_score_available": [
                score_available
            ],
        }
    )


def test_required_columns_are_validated() -> None:
    frame = pd.DataFrame(
        {
            "metric": ["median_rent"],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing required columns",
    ):
        add_practical_significance(frame)


def test_rent_practical_thresholds() -> None:
    threshold = PRACTICAL_THRESHOLDS[
        "median_rent"
    ]

    assert (
        threshold.minimum_absolute_deviation
        == 15.0
    )
    assert (
        threshold.minimum_percentage_deviation
        == 3.0
    )


def test_bonds_practical_thresholds() -> None:
    threshold = PRACTICAL_THRESHOLDS[
        "bonds_lodged"
    ]

    assert (
        threshold.minimum_absolute_deviation
        == 25.0
    )
    assert (
        threshold.minimum_percentage_deviation
        == 20.0
    )


def test_small_rent_deviation_is_statistical_only() -> None:
    frame = _row(
        metric="median_rent",
        deviation=10.0,
        deviation_pct=6.0,
    )

    result = add_practical_significance(
        frame
    )

    row = result.iloc[0]

    assert bool(
        row["statistical_anomaly"]
    )

    assert not bool(
        row["practical_significance"]
    )

    assert not bool(
        row["dashboard_alert"]
    )

    assert (
        row["alert_status"]
        == "statistical_only"
    )


def test_rent_requires_absolute_and_percentage_thresholds() -> None:
    absolute_only = _row(
        metric="median_rent",
        deviation=20.0,
        deviation_pct=2.0,
    )

    percentage_only = _row(
        metric="median_rent",
        deviation=10.0,
        deviation_pct=8.0,
    )

    result_absolute = (
        add_practical_significance(
            absolute_only
        )
    )

    result_percentage = (
        add_practical_significance(
            percentage_only
        )
    )

    assert not bool(
        result_absolute.iloc[0][
            "practical_significance"
        ]
    )

    assert not bool(
        result_percentage.iloc[0][
            "practical_significance"
        ]
    )


def test_significant_rent_anomaly_becomes_dashboard_alert() -> None:
    frame = _row(
        metric="median_rent",
        deviation=25.0,
        deviation_pct=5.0,
    )

    result = add_practical_significance(
        frame
    )

    row = result.iloc[0]

    assert bool(
        row["practical_significance"]
    )

    assert bool(
        row["dashboard_alert"]
    )

    assert (
        row["alert_status"]
        == "dashboard_alert"
    )


def test_negative_deviation_uses_absolute_magnitude() -> None:
    frame = _row(
        metric="median_rent",
        deviation=-25.0,
        deviation_pct=-5.0,
    )

    result = add_practical_significance(
        frame
    )

    assert bool(
        result.iloc[0][
            "practical_significance"
        ]
    )


def test_bond_deviation_requires_both_thresholds() -> None:
    frame = _row(
        metric="bonds_lodged",
        deviation=100.0,
        deviation_pct=10.0,
    )

    result = add_practical_significance(
        frame
    )

    assert not bool(
        result.iloc[0][
            "practical_significance"
        ]
    )


def test_significant_bond_anomaly_becomes_dashboard_alert() -> None:
    frame = _row(
        metric="bonds_lodged",
        deviation=300.0,
        deviation_pct=25.0,
    )

    result = add_practical_significance(
        frame
    )

    assert bool(
        result.iloc[0][
            "dashboard_alert"
        ]
    )


def test_practical_movement_without_statistical_anomaly_is_not_alert() -> None:
    frame = _row(
        metric="median_rent",
        deviation=100.0,
        deviation_pct=20.0,
        statistical_anomaly=False,
    )

    result = add_practical_significance(
        frame
    )

    row = result.iloc[0]

    assert bool(
        row["practical_significance"]
    )

    assert not bool(
        row["dashboard_alert"]
    )

    assert (
        row["alert_status"]
        == "normal"
    )


def test_missing_deviation_is_unavailable() -> None:
    frame = _row(
        metric="median_rent",
        deviation=np.nan,
        deviation_pct=np.nan,
    )

    result = add_practical_significance(
        frame
    )

    row = result.iloc[0]

    assert not bool(
        row[
            "practical_significance_available"
        ]
    )

    assert not bool(
        row["dashboard_alert"]
    )

    assert (
        row["alert_status"]
        == "unavailable"
    )


def test_unknown_metric_is_unavailable() -> None:
    frame = _row(
        metric="unknown_metric",
        deviation=1000.0,
        deviation_pct=100.0,
    )

    result = add_practical_significance(
        frame
    )

    row = result.iloc[0]

    assert not bool(
        row[
            "practical_significance_available"
        ]
    )

    assert (
        row["alert_status"]
        == "unavailable"
    )


def test_threshold_boundary_is_inclusive() -> None:
    frame = _row(
        metric="median_rent",
        deviation=15.0,
        deviation_pct=3.0,
    )

    result = add_practical_significance(
        frame
    )

    assert bool(
        result.iloc[0][
            "practical_significance"
        ]
    )


def test_unavailable_statistical_score_is_unavailable() -> None:
    frame = _row(
        metric="median_rent",
        deviation=25.0,
        deviation_pct=5.0,
        statistical_anomaly=False,
        score_available=False,
    )

    result = add_practical_significance(
        frame
    )

    row = result.iloc[0]

    assert not bool(
        row["dashboard_alert"]
    )

    assert (
        row["alert_status"]
        == "unavailable"
    )
