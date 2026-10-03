"""Leakage-safe forecasting feature engineering."""

from __future__ import annotations

import pandas as pd

DEFAULT_LAGS = (
    1,
    2,
    3,
    6,
    12,
)

DEFAULT_ROLLING_WINDOWS = (
    3,
    6,
    12,
)


def add_calendar_features(
    df: pd.DataFrame,
    date_column: str = "period_date",
) -> pd.DataFrame:
    """Add calendar features derived from the forecast month."""

    result = df.copy()

    if date_column not in result.columns:
        raise ValueError(
            f"Missing date column: {date_column}"
        )

    result[date_column] = pd.to_datetime(
        result[date_column]
    )

    result["month"] = result[date_column].dt.month
    result["quarter"] = result[date_column].dt.quarter
    result["year"] = result[date_column].dt.year

    return result


def add_lag_features(
    df: pd.DataFrame,
    value_column: str = "value",
    group_column: str = "series_id",
    lags: tuple[int, ...] = DEFAULT_LAGS,
) -> pd.DataFrame:
    """Add leakage-safe lag features within each series."""

    result = df.copy()

    required = {
        value_column,
        group_column,
        "period_date",
    }

    missing = required.difference(result.columns)

    if missing:
        raise ValueError(
            "Missing required lag columns: "
            f"{sorted(missing)}"
        )

    result = result.sort_values(
        [
            group_column,
            "period_date",
        ]
    ).copy()

    grouped = result.groupby(
        group_column,
        sort=False,
    )[value_column]

    for lag in lags:
        if lag < 1:
            raise ValueError(
                "Lag values must be at least 1."
            )

        result[f"lag_{lag}"] = grouped.shift(lag)

    return result


def add_rolling_features(
    df: pd.DataFrame,
    value_column: str = "value",
    group_column: str = "series_id",
    windows: tuple[int, ...] = DEFAULT_ROLLING_WINDOWS,
) -> pd.DataFrame:
    """Add leakage-safe rolling mean features.

    The target value is shifted by one month before calculating
    each rolling mean. This prevents the current month's target
    from leaking into its own predictor values.
    """

    result = df.copy()

    required = {
        value_column,
        group_column,
        "period_date",
    }

    missing = required.difference(result.columns)

    if missing:
        raise ValueError(
            "Missing required rolling columns: "
            f"{sorted(missing)}"
        )

    result = result.sort_values(
        [
            group_column,
            "period_date",
        ]
    ).copy()

    for window in windows:
        if window < 1:
            raise ValueError(
                "Rolling windows must be at least 1."
            )

        result[f"rolling_mean_{window}"] = (
            result.groupby(
                group_column,
                sort=False,
            )[value_column]
            .transform(
                lambda series, window=window: (
                    series.shift(1)
                    .rolling(
                        window=window,
                        min_periods=window,
                    )
                    .mean()
                )
            )
        )

    return result


def build_forecasting_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Build the complete leakage-safe forecasting feature set."""

    result = df.copy()

    result = add_calendar_features(result)
    result = add_lag_features(result)
    result = add_rolling_features(result)

    return result.sort_values(
        [
            "series_id",
            "period_date",
        ]
    ).reset_index(drop=True)
