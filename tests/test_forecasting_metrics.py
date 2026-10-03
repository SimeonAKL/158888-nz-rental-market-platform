"""Tests for forecasting evaluation metrics."""

import math

import pytest

from rmp.forecasting.metrics import (
    calculate_forecast_metrics,
    mae,
    rmse,
    smape,
)


def test_mae() -> None:
    """MAE should calculate mean absolute error."""

    result = mae(
        [100, 200, 300],
        [110, 190, 330],
    )

    assert result == pytest.approx(
        50 / 3
    )


def test_rmse() -> None:
    """RMSE should calculate root mean squared error."""

    result = rmse(
        [100, 200, 300],
        [110, 190, 330],
    )

    expected = math.sqrt(
        (
            10**2
            + 10**2
            + 30**2
        )
        / 3
    )

    assert result == pytest.approx(
        expected
    )


def test_smape_perfect_forecast() -> None:
    """Perfect forecasts should have zero sMAPE."""

    result = smape(
        [100, 200, 300],
        [100, 200, 300],
    )

    assert result == pytest.approx(
        0.0
    )


def test_smape_handles_both_zero() -> None:
    """Actual=prediction=0 should contribute zero error."""

    result = smape(
        [0, 100],
        [0, 110],
    )

    expected = (
        (
            0
            + (
                2
                * 10
                / 210
            )
        )
        / 2
        * 100
    )

    assert result == pytest.approx(
        expected
    )


def test_calculate_forecast_metrics() -> None:
    """All project metrics should be returned."""

    result = calculate_forecast_metrics(
        [100, 200],
        [110, 180],
    )

    assert set(result) == {
        "mae",
        "rmse",
        "smape",
    }


def test_metrics_reject_different_shapes() -> None:
    """Actual and forecast arrays must have equal shape."""

    with pytest.raises(
        ValueError,
        match="same shape",
    ):
        mae(
            [1, 2, 3],
            [1, 2],
        )
