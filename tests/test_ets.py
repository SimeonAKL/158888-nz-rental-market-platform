"""Tests for Holt-Winters ETS forecasting."""

import numpy as np
import pandas as pd
import pytest

from rmp.forecasting.ets import (
    ets_forecast,
)


def make_training_series(
    n_months: int = 72,
) -> pd.DataFrame:
    """Create deterministic monthly trend and seasonal data."""

    dates = pd.date_range(
        "2018-01-01",
        periods=n_months,
        freq="MS",
    )

    seasonal_pattern = np.array(
        [
            -20.0,
            -15.0,
            -10.0,
            -5.0,
            0.0,
            5.0,
            10.0,
            15.0,
            20.0,
            10.0,
            0.0,
            -10.0,
        ]
    )

    values = []

    for index in range(n_months):
        trend = 500.0 + (2.0 * index)

        seasonal = seasonal_pattern[index % 12]

        values.append(trend + seasonal)

    return pd.DataFrame(
        {
            "period_date": dates,
            "value": values,
        }
    )


def make_forecast_periods(
    train: pd.DataFrame,
    horizon: int = 6,
) -> pd.DatetimeIndex:
    """Create consecutive months immediately after training."""

    return pd.date_range(
        train["period_date"].max() + pd.offsets.MonthBegin(1),
        periods=horizon,
        freq="MS",
    )


def test_ets_returns_requested_horizon() -> None:
    """ETS should return one prediction per forecast month."""

    train = make_training_series()

    periods = make_forecast_periods(train)

    result = ets_forecast(
        train,
        periods,
    )

    assert len(result) == 6

    assert pd.DatetimeIndex(result["forecast_period"]).equals(periods)

    assert np.isfinite(result["predicted"]).all()


def test_ets_is_deterministic() -> None:
    """Repeated fits on identical data should give identical forecasts."""

    train = make_training_series()

    periods = make_forecast_periods(train)

    first = ets_forecast(
        train,
        periods,
    )

    second = ets_forecast(
        train,
        periods,
    )

    assert first["predicted"].to_numpy() == pytest.approx(second["predicted"].to_numpy())


def test_ets_does_not_modify_training_data() -> None:
    """Forecasting should not mutate the supplied training frame."""

    train = make_training_series()

    original = train.copy(deep=True)

    periods = make_forecast_periods(train)

    ets_forecast(
        train,
        periods,
    )

    pd.testing.assert_frame_equal(
        train,
        original,
    )


def test_ets_rejects_insufficient_history() -> None:
    """At least two complete seasonal cycles are required."""

    train = make_training_series(n_months=23)

    periods = make_forecast_periods(train)

    with pytest.raises(
        ValueError,
        match="at least 24",
    ):
        ets_forecast(
            train,
            periods,
        )


def test_ets_rejects_missing_month() -> None:
    """Training history must be a complete monthly sequence."""

    train = make_training_series()

    train = train.drop(index=10).reset_index(drop=True)

    periods = make_forecast_periods(train)

    with pytest.raises(
        ValueError,
        match="complete monthly sequence",
    ):
        ets_forecast(
            train,
            periods,
        )


def test_ets_rejects_nonconsecutive_forecast_periods() -> None:
    """Forecast dates must immediately follow training."""

    train = make_training_series()

    periods = pd.date_range(
        train["period_date"].max() + pd.offsets.MonthBegin(2),
        periods=6,
        freq="MS",
    )

    with pytest.raises(
        ValueError,
        match="consecutive months",
    ):
        ets_forecast(
            train,
            periods,
        )


def test_ets_rejects_invalid_seasonal_period() -> None:
    """Seasonal period must be positive."""

    train = make_training_series()

    periods = make_forecast_periods(train)

    with pytest.raises(
        ValueError,
        match="at least 1",
    ):
        ets_forecast(
            train,
            periods,
            seasonal_period=0,
        )
