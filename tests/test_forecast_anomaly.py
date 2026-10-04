"""Tests for forecast residual anomaly detection."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rmp.anomaly.forecast import (
    HIGH_THRESHOLD,
    MODERATE_THRESHOLD,
    _classify_direction,
    _classify_severity,
    detect_forecast_residual_anomalies,
    select_winner_horizon_predictions,
)


def _predictions(
    *,
    residuals: list[float],
    winner_model: str = "winner",
) -> pd.DataFrame:
    """Create synthetic rolling-origin predictions."""
    rows: list[dict[str, object]] = []

    origins = pd.date_range(
        "2025-01-01",
        periods=len(residuals),
        freq="MS",
    )

    for index, residual in enumerate(
        residuals
    ):
        origin = origins[index]
        forecast_period = (
            origin + pd.offsets.MonthBegin(1)
        )

        actual = 100.0 + residual
        predicted = 100.0

        rows.append(
            {
                "model": winner_model,
                "series_id": "series_a",
                "metric": "median_rent",
                "geography_level": "region",
                "location_id": 1,
                "location_name": "Test Region",
                "origin": origin,
                "forecast_period": forecast_period,
                "horizon_step": 1,
                "actual": actual,
                "predicted": predicted,
            }
        )

        # Losing-model row must not be used.
        rows.append(
            {
                "model": "loser",
                "series_id": "series_a",
                "metric": "median_rent",
                "geography_level": "region",
                "location_id": 1,
                "location_name": "Test Region",
                "origin": origin,
                "forecast_period": forecast_period,
                "horizon_step": 1,
                "actual": actual,
                "predicted": 999.0,
            }
        )

        # Horizon-two row must not be used.
        rows.append(
            {
                "model": winner_model,
                "series_id": "series_a",
                "metric": "median_rent",
                "geography_level": "region",
                "location_id": 1,
                "location_name": "Test Region",
                "origin": origin,
                "forecast_period": (
                    origin
                    + pd.offsets.MonthBegin(2)
                ),
                "horizon_step": 2,
                "actual": actual,
                "predicted": predicted,
            }
        )

    return pd.DataFrame(rows)


def _winners() -> pd.DataFrame:
    """Create a simple winner mapping."""
    return pd.DataFrame(
        {
            "series_id": ["series_a"],
            "metric": ["median_rent"],
            "best_model": ["winner"],
        }
    )


def test_selects_only_winner_horizon_one() -> None:
    predictions = _predictions(
        residuals=[
            1,
            2,
            1,
            2,
            1,
            2,
            1,
            2,
        ]
    )

    selected = (
        select_winner_horizon_predictions(
            predictions,
            _winners(),
        )
    )

    assert len(selected) == 8

    assert (
        selected["horizon_step"] == 1
    ).all()

    assert (
        selected["model"] == "winner"
    ).all()


def test_prediction_columns_are_validated() -> None:
    predictions = pd.DataFrame(
        {
            "series_id": ["series_a"],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing required prediction columns",
    ):
        select_winner_horizon_predictions(
            predictions,
            _winners(),
        )


def test_winner_columns_are_validated() -> None:
    predictions = _predictions(
        residuals=[1, 2, 3]
    )

    winners = pd.DataFrame(
        {
            "series_id": ["series_a"],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing required winner columns",
    ):
        select_winner_horizon_predictions(
            predictions,
            winners,
        )


def test_duplicate_winner_mapping_is_rejected() -> None:
    predictions = _predictions(
        residuals=[1, 2, 3]
    )

    winners = pd.concat(
        [
            _winners(),
            _winners(),
        ],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate series winner",
    ):
        select_winner_horizon_predictions(
            predictions,
            winners,
        )


def test_current_residual_is_excluded_from_baseline() -> None:
    residuals = [
        -2,
        -1,
        0,
        1,
        2,
        1,
        100,
    ]

    result = (
        detect_forecast_residual_anomalies(
            _predictions(
                residuals=residuals
            ),
            _winners(),
            min_prior_residuals=6,
        )
    )

    final_row = result.iloc[-1]

    expected_median = np.median(
        residuals[:6]
    )

    assert final_row[
        "residual_median"
    ] == pytest.approx(
        expected_median
    )


def test_first_residuals_are_unavailable() -> None:
    residuals = [
        -3,
        -2,
        -1,
        1,
        2,
        3,
        4,
    ]

    result = (
        detect_forecast_residual_anomalies(
            _predictions(
                residuals=residuals
            ),
            _winners(),
            min_prior_residuals=6,
        )
    )

    first_rows = result.iloc[:6]

    assert not first_rows[
        "forecast_score_available"
    ].any()

    assert (
        first_rows["forecast_severity"]
        == "unavailable"
    ).all()


def test_positive_forecast_shock_is_detected() -> None:
    residuals = [
        -3,
        -2,
        -1,
        1,
        2,
        3,
        50,
    ]

    result = (
        detect_forecast_residual_anomalies(
            _predictions(
                residuals=residuals
            ),
            _winners(),
            min_prior_residuals=6,
        )
    )

    final_row = result.iloc[-1]

    assert bool(
        final_row["forecast_is_anomaly"]
    )

    assert (
        final_row["forecast_direction"]
        == "high"
    )

    assert (
        final_row["forecast_severity"]
        == "high"
    )


def test_negative_forecast_shock_is_detected() -> None:
    residuals = [
        -3,
        -2,
        -1,
        1,
        2,
        3,
        -50,
    ]

    result = (
        detect_forecast_residual_anomalies(
            _predictions(
                residuals=residuals
            ),
            _winners(),
            min_prior_residuals=6,
        )
    )

    final_row = result.iloc[-1]

    assert bool(
        final_row["forecast_is_anomaly"]
    )

    assert (
        final_row["forecast_direction"]
        == "low"
    )

    assert (
        final_row["forecast_severity"]
        == "high"
    )


def test_residual_percentage_is_calculated() -> None:
    result = (
        detect_forecast_residual_anomalies(
            _predictions(
                residuals=[
                    -3,
                    -2,
                    -1,
                    1,
                    2,
                    3,
                    10,
                ]
            ),
            _winners(),
            min_prior_residuals=6,
        )
    )

    final_row = result.iloc[-1]

    assert final_row[
        "forecast_residual"
    ] == pytest.approx(10.0)

    assert final_row[
        "forecast_residual_pct"
    ] == pytest.approx(10.0)


def test_zero_scale_is_unavailable() -> None:
    residuals = [
        5,
        5,
        5,
        5,
        5,
        5,
        5,
    ]

    result = (
        detect_forecast_residual_anomalies(
            _predictions(
                residuals=residuals
            ),
            _winners(),
            min_prior_residuals=6,
        )
    )

    final_row = result.iloc[-1]

    assert not bool(
        final_row[
            "forecast_score_available"
        ]
    )

    assert (
        final_row["forecast_severity"]
        == "unavailable"
    )


def test_minimum_prior_residuals_is_validated() -> None:
    with pytest.raises(
        ValueError,
        match="min_prior_residuals",
    ):
        detect_forecast_residual_anomalies(
            _predictions(
                residuals=[1, 2, 3]
            ),
            _winners(),
            min_prior_residuals=2,
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
