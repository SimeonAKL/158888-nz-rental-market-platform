"""Tests for rolling-origin evaluation splits."""

import pandas as pd
import pytest

from rmp.forecasting.splits import (
    generate_rolling_origins,
    slice_rolling_origin,
)


def make_periods(
    n_months: int = 120,
) -> pd.DatetimeIndex:
    """Create a complete monthly date sequence."""

    return pd.date_range(
        "2016-01-01",
        periods=n_months,
        freq="MS",
    )


def test_generate_requested_origins() -> None:
    """Generator should return the requested number of origins."""

    splits = generate_rolling_origins(
        make_periods(),
        forecast_horizon=6,
        n_origins=12,
        min_history_months=60,
    )

    assert len(splits) == 12


def test_latest_origin_uses_final_horizon() -> None:
    """Latest split should reserve final six months for testing."""

    periods = make_periods()

    splits = generate_rolling_origins(
        periods,
        forecast_horizon=6,
        n_origins=12,
        min_history_months=60,
    )

    latest = splits[-1]

    assert (
        latest.origin
        == periods[-7]
    )

    assert (
        latest.test_start
        == periods[-6]
    )

    assert (
        latest.test_end
        == periods[-1]
    )


def test_origins_are_monthly_and_chronological() -> None:
    """Origins should advance exactly one month at a time."""

    splits = generate_rolling_origins(
        make_periods(),
        forecast_horizon=6,
        n_origins=12,
        min_history_months=60,
    )

    origins = pd.DatetimeIndex(
        split.origin
        for split in splits
    )

    expected = pd.date_range(
        origins.min(),
        origins.max(),
        freq="MS",
    )

    assert origins.equals(expected)


def test_slice_rolling_origin() -> None:
    """Train and test windows should respect the origin."""

    periods = make_periods()

    data = pd.DataFrame(
        {
            "period_date": periods,
            "value": range(
                len(periods)
            ),
        }
    )

    split = generate_rolling_origins(
        periods,
        forecast_horizon=6,
        n_origins=1,
        min_history_months=60,
    )[0]

    train, test = slice_rolling_origin(
        data,
        split,
    )

    assert (
        train["period_date"].max()
        == split.origin
    )

    assert len(test) == 6

    assert (
        test["period_date"].min()
        == split.test_start
    )

    assert (
        test["period_date"].max()
        == split.test_end
    )


def test_rejects_missing_month() -> None:
    """Incomplete monthly histories should be rejected."""

    periods = make_periods().delete(10)

    with pytest.raises(
        ValueError,
        match="complete monthly sequence",
    ):
        generate_rolling_origins(
            periods,
            forecast_horizon=6,
            n_origins=12,
            min_history_months=60,
        )


def test_rejects_insufficient_history() -> None:
    """Series shorter than history plus horizon should fail."""

    periods = make_periods(
        n_months=60
    )

    with pytest.raises(
        ValueError,
        match="Insufficient history",
    ):
        generate_rolling_origins(
            periods,
            forecast_horizon=6,
            n_origins=12,
            min_history_months=60,
        )
