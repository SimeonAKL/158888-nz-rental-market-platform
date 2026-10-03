"""Rolling-origin time-series evaluation splits."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

DEFAULT_FORECAST_HORIZON = 6
DEFAULT_N_ORIGINS = 12
DEFAULT_MIN_HISTORY_MONTHS = 60


@dataclass(frozen=True)
class RollingOriginSplit:
    """A single rolling-origin evaluation window."""

    origin: pd.Timestamp
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    horizon: int


def generate_rolling_origins(
    periods: pd.Series | pd.DatetimeIndex,
    forecast_horizon: int = DEFAULT_FORECAST_HORIZON,
    n_origins: int = DEFAULT_N_ORIGINS,
    min_history_months: int = DEFAULT_MIN_HISTORY_MONTHS,
) -> list[RollingOriginSplit]:
    """Generate expanding-window rolling-origin splits.

    The origin is the final month available to the training set.
    The test window contains the following ``forecast_horizon`` months.

    Parameters
    ----------
    periods:
        Monthly observation dates for one time series.
    forecast_horizon:
        Number of months to forecast after each origin.
    n_origins:
        Maximum number of evaluation origins.
    min_history_months:
        Minimum number of training observations required.

    Returns
    -------
    list[RollingOriginSplit]
        Chronologically ordered evaluation splits.
    """

    if forecast_horizon < 1:
        raise ValueError(
            "forecast_horizon must be at least 1."
        )

    if n_origins < 1:
        raise ValueError(
            "n_origins must be at least 1."
        )

    if min_history_months < 1:
        raise ValueError(
            "min_history_months must be at least 1."
        )

    dates = pd.DatetimeIndex(
        pd.to_datetime(periods)
    ).sort_values()

    if dates.has_duplicates:
        raise ValueError(
            "Periods contain duplicate monthly observations."
        )

    if len(dates) < (
        min_history_months
        + forecast_horizon
    ):
        raise ValueError(
            "Insufficient history for rolling-origin evaluation."
        )

    expected = pd.date_range(
        start=dates.min(),
        end=dates.max(),
        freq="MS",
    )

    if not dates.equals(expected):
        raise ValueError(
            "Periods must form a complete monthly sequence."
        )

    latest_origin_index = (
        len(dates)
        - forecast_horizon
        - 1
    )

    earliest_allowed_index = (
        min_history_months
        - 1
    )

    available_origins = (
        latest_origin_index
        - earliest_allowed_index
        + 1
    )

    actual_n_origins = min(
        n_origins,
        available_origins,
    )

    first_origin_index = (
        latest_origin_index
        - actual_n_origins
        + 1
    )

    splits: list[RollingOriginSplit] = []

    for origin_index in range(
        first_origin_index,
        latest_origin_index + 1,
    ):
        origin = dates[origin_index]

        test_start_index = (
            origin_index + 1
        )

        test_end_index = (
            origin_index
            + forecast_horizon
        )

        splits.append(
            RollingOriginSplit(
                origin=origin,
                train_start=dates[0],
                train_end=origin,
                test_start=dates[
                    test_start_index
                ],
                test_end=dates[
                    test_end_index
                ],
                horizon=forecast_horizon,
            )
        )

    return splits


def slice_rolling_origin(
    series: pd.DataFrame,
    split: RollingOriginSplit,
    date_column: str = "period_date",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return train and test data for one split."""

    if date_column not in series.columns:
        raise ValueError(
            f"Missing date column: {date_column}"
        )

    data = series.copy()

    data[date_column] = pd.to_datetime(
        data[date_column]
    )

    train = data.loc[
        data[date_column]
        <= split.train_end
    ].copy()

    test = data.loc[
        (
            data[date_column]
            >= split.test_start
        )
        & (
            data[date_column]
            <= split.test_end
        )
    ].copy()

    train = train.sort_values(
        date_column
    ).reset_index(drop=True)

    test = test.sort_values(
        date_column
    ).reset_index(drop=True)

    if len(test) != split.horizon:
        raise ValueError(
            "Test window does not contain "
            f"{split.horizon} observations."
        )

    return train, test
