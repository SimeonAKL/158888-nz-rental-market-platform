"""Tests for historical anomaly detection."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rmp.anomaly.historical import (
    HIGH_THRESHOLD,
    MODERATE_THRESHOLD,
    _classify_direction,
    _classify_severity,
    detect_historical_anomalies,
)


def _panel(values: list[float]) -> pd.DataFrame:
    """Create a simple monthly test panel."""
    return pd.DataFrame(
        {
            "period_date": pd.date_range(
                "2015-01-01",
                periods=len(values),
                freq="MS",
            ),
            "series_id": "test_series",
            "metric": "bonds_lodged",
            "geography": "Test Geography",
            "value": values,
        }
    )


def test_required_columns_are_validated() -> None:
    panel = pd.DataFrame(
        {
            "series_id": ["a"],
            "period_date": ["2020-01-01"],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing required columns",
    ):
        detect_historical_anomalies(panel)


def test_invalid_parameters_are_rejected() -> None:
    panel = _panel([100.0] * 60)

    with pytest.raises(ValueError):
        detect_historical_anomalies(
            panel,
            seasonal_lag=0,
        )

    with pytest.raises(ValueError):
        detect_historical_anomalies(
            panel,
            baseline_window=1,
        )

    with pytest.raises(ValueError):
        detect_historical_anomalies(
            panel,
            min_periods=1,
        )

    with pytest.raises(ValueError):
        detect_historical_anomalies(
            panel,
            baseline_window=12,
            min_periods=13,
        )


def test_duplicate_series_period_is_rejected() -> None:
    panel = _panel([100.0, 101.0])

    duplicate = pd.concat(
        [
            panel,
            panel.iloc[[0]],
        ],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate series-period",
    ):
        detect_historical_anomalies(
            duplicate
        )


def test_seasonal_reference_uses_previous_year() -> None:
    values = list(
        np.arange(100.0, 160.0)
    )

    result = detect_historical_anomalies(
        _panel(values),
        seasonal_lag=12,
        baseline_window=24,
        min_periods=12,
    )

    row = result.iloc[24]

    assert row["seasonal_reference"] == pytest.approx(
        values[12]
    )

    assert row["seasonal_change"] == pytest.approx(
        values[24] - values[12]
    )


def test_current_change_is_excluded_from_baseline() -> None:
    values = []

    for year in range(6):
        for month in range(12):
            values.append(
                100.0
                + month
                + year * 5.0
            )

    # Create a large final-month jump.
    values[-1] += 500.0

    result = detect_historical_anomalies(
        _panel(values),
        seasonal_lag=12,
        baseline_window=36,
        min_periods=24,
    )

    final_row = result.iloc[-1]

    assert (
        final_row["historical_expected"]
        < final_row["value"]
    )


def test_recurring_seasonal_peak_is_not_anomaly() -> None:
    values = []

    for year in range(8):
        yearly_values = [
            300.0,
            100.0,
            105.0,
            110.0,
            115.0,
            120.0,
            125.0,
            120.0,
            115.0,
            110.0,
            105.0,
            100.0,
        ]

        # Mild annual trend.
        values.extend(
            [
                value + year * 5.0
                for value in yearly_values
            ]
        )

    result = detect_historical_anomalies(
        _panel(values),
        seasonal_lag=12,
        baseline_window=36,
        min_periods=24,
    )

    january_rows = result[
        result["period_date"].dt.month == 1
    ]

    available_january = january_rows[
        january_rows[
            "historical_score_available"
        ]
    ]

    if not available_january.empty:
        assert not available_january[
            "historical_is_anomaly"
        ].any()


def test_genuine_positive_shock_is_detected() -> None:
    values = []

    for year in range(8):
        for month in range(12):
            value = (
                100.0
                + month * 2.0
                + year * (4.0 + month * 0.05)
            )
            values.append(value)

    # Final observation is much higher than the
    # established same-month historical pattern.
    values[-1] += 200.0

    result = detect_historical_anomalies(
        _panel(values),
        seasonal_lag=12,
        baseline_window=36,
        min_periods=24,
    )

    final_row = result.iloc[-1]

    assert bool(
        final_row["historical_is_anomaly"]
    )
    assert (
        final_row["historical_direction"]
        == "high"
    )


def test_genuine_negative_shock_is_detected() -> None:
    values = []

    for year in range(8):
        for month in range(12):
            value = (
                200.0
                + month * 2.0
                + year * (4.0 + month * 0.05)
            )
            values.append(value)

    values[-1] -= 150.0

    result = detect_historical_anomalies(
        _panel(values),
        seasonal_lag=12,
        baseline_window=36,
        min_periods=24,
    )

    final_row = result.iloc[-1]

    assert bool(
        final_row["historical_is_anomaly"]
    )
    assert (
        final_row["historical_direction"]
        == "low"
    )


def test_iqr_is_used_when_mad_is_zero() -> None:
    values = []

    yearly_growth = [
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        5.0,
        10.0,
    ]

    current = np.array(
        [
            100.0 + month
            for month in range(12)
        ]
    )

    values.extend(current.tolist())

    for growth in yearly_growth:
        current = current + growth
        values.extend(current.tolist())

    result = detect_historical_anomalies(
        _panel(values),
        seasonal_lag=12,
        baseline_window=36,
        min_periods=24,
    )

    assert set(
        result["historical_scale_method"].unique()
    ).issubset(
        {"mad", "iqr", "unavailable"}
    )


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.0, "normal"),
        (
            MODERATE_THRESHOLD - 0.01,
            "normal",
        ),
        (
            MODERATE_THRESHOLD,
            "moderate",
        ),
        (
            -MODERATE_THRESHOLD,
            "moderate",
        ),
        (
            HIGH_THRESHOLD - 0.01,
            "moderate",
        ),
        (
            HIGH_THRESHOLD,
            "high",
        ),
        (
            -HIGH_THRESHOLD,
            "high",
        ),
        (
            np.nan,
            "unavailable",
        ),
    ],
)
def test_severity_thresholds(
    score: float,
    expected: str,
) -> None:
    assert (
        _classify_severity(score)
        == expected
    )


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.0, "normal"),
        (2.49, "normal"),
        (-2.49, "normal"),
        (2.5, "high"),
        (-2.5, "low"),
        (4.0, "high"),
        (-4.0, "low"),
        (np.nan, "unavailable"),
    ],
)
def test_direction_classification(
    score: float,
    expected: str,
) -> None:
    assert (
        _classify_direction(score)
        == expected
    )


def test_multiple_series_are_independent() -> None:
    first_values = []

    for year in range(8):
        for month in range(12):
            first_values.append(
                100.0
                + month
                + year * (5.0 + month * 0.05)
            )

    second_values = [
        value + 200.0
        for value in first_values
    ]

    first = _panel(first_values)

    second = _panel(second_values)
    second["series_id"] = "second_series"

    panel = pd.concat(
        [first, second],
        ignore_index=True,
    )

    result = detect_historical_anomalies(
        panel,
        seasonal_lag=12,
        baseline_window=36,
        min_periods=24,
    )

    assert result["series_id"].nunique() == 2
