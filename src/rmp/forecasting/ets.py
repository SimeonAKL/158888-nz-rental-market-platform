"""Holt-Winters exponential smoothing forecasting model."""

from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

DEFAULT_SEASONAL_PERIOD = 12


def ets_forecast(
    train: pd.DataFrame,
    forecast_periods: pd.Series | pd.DatetimeIndex,
    date_column: str = "period_date",
    value_column: str = "value",
    seasonal_period: int = DEFAULT_SEASONAL_PERIOD,
) -> pd.DataFrame:
    """Fit additive damped Holt-Winters ETS and forecast future months.

    The model specification is fixed across all series and rolling origins:

    - additive trend
    - additive seasonality
    - damped trend
    - estimated initialization

    Only training observations are supplied to the model. Forecast-period
    dates contain no target values, preventing future actual observations
    from leaking into model fitting or prediction.
    """

    if seasonal_period < 1:
        raise ValueError(
            "seasonal_period must be at least 1."
        )

    required = {
        date_column,
        value_column,
    }

    missing = required.difference(
        train.columns
    )

    if missing:
        raise ValueError(
            "Missing required train columns: "
            f"{sorted(missing)}"
        )

    if train.empty:
        raise ValueError(
            "Training data cannot be empty."
        )

    data = train.copy()

    data[date_column] = pd.to_datetime(
        data[date_column]
    )

    data[value_column] = pd.to_numeric(
        data[value_column],
        errors="raise",
    )

    data = data.sort_values(
        date_column
    ).reset_index(drop=True)

    if data[date_column].duplicated().any():
        raise ValueError(
            "Training data contains duplicate periods."
        )

    if data[value_column].isna().any():
        raise ValueError(
            "Training values cannot contain NaN values."
        )

    if not np.isfinite(
        data[value_column].to_numpy(
            dtype=float
        )
    ).all():
        raise ValueError(
            "Training values must be finite."
        )

    minimum_observations = (
        2 * seasonal_period
    )

    if len(data) < minimum_observations:
        raise ValueError(
            "ETS requires at least "
            f"{minimum_observations} training observations."
        )

    expected_history = pd.date_range(
        start=data[date_column].min(),
        end=data[date_column].max(),
        freq="MS",
    )

    observed_history = pd.DatetimeIndex(
        data[date_column]
    )

    if not observed_history.equals(
        expected_history
    ):
        raise ValueError(
            "Training periods must form a complete monthly sequence."
        )

    future_dates = pd.DatetimeIndex(
        pd.to_datetime(
            forecast_periods
        )
    )

    if len(future_dates) < 1:
        raise ValueError(
            "At least one forecast period is required."
        )

    if future_dates.has_duplicates:
        raise ValueError(
            "Forecast periods contain duplicates."
        )

    expected_future = pd.date_range(
        start=(
            data[date_column].max()
            + pd.offsets.MonthBegin(1)
        ),
        periods=len(future_dates),
        freq="MS",
    )

    if not future_dates.equals(
        expected_future
    ):
        raise ValueError(
            "Forecast periods must be consecutive months "
            "immediately after the training data."
        )

    values = pd.Series(
        data[value_column].to_numpy(
            dtype=float
        ),
        index=pd.date_range(
            start=data[date_column].min(),
            periods=len(data),
            freq="MS",
        ),
        name=value_column,
    )

    model = ExponentialSmoothing(
        values,
        trend="add",
        damped_trend=True,
        seasonal="add",
        seasonal_periods=seasonal_period,
        initialization_method="estimated",
    )

    fitted = model.fit(
        optimized=True,
        remove_bias=False,
    )

    predicted = fitted.forecast(
        len(future_dates)
    )

    predictions = np.asarray(
        predicted,
        dtype=float,
    )

    if not np.isfinite(
        predictions
    ).all():
        raise ValueError(
            "ETS produced non-finite forecasts."
        )

    return pd.DataFrame(
        {
            "forecast_period": future_dates,
            "predicted": predictions,
        }
    )
