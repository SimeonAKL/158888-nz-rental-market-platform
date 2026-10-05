"""Seasonal naive forecasting baseline."""

from __future__ import annotations

import pandas as pd

DEFAULT_SEASONAL_PERIOD = 12


def seasonal_naive_forecast(
    train: pd.DataFrame,
    test: pd.DataFrame,
    date_column: str = "period_date",
    value_column: str = "value",
    seasonal_period: int = DEFAULT_SEASONAL_PERIOD,
) -> pd.DataFrame:
    """Forecast each test observation using the value one season earlier.

    For monthly data with ``seasonal_period=12``:

        forecast(t) = observed(t - 12 months)

    Reference values are taken strictly from the training set. This ensures
    that future observed values cannot leak into the forecast.
    """

    if seasonal_period < 1:
        raise ValueError("seasonal_period must be at least 1.")

    required = {
        date_column,
        value_column,
    }

    missing_train = required.difference(train.columns)
    missing_test = required.difference(test.columns)

    if missing_train:
        raise ValueError(f"Missing required train columns: {sorted(missing_train)}")

    if missing_test:
        raise ValueError(f"Missing required test columns: {sorted(missing_test)}")

    if train.empty:
        raise ValueError("Training data cannot be empty.")

    if test.empty:
        raise ValueError("Test data cannot be empty.")

    train_data = train.copy()
    test_data = test.copy()

    train_data[date_column] = pd.to_datetime(train_data[date_column])
    test_data[date_column] = pd.to_datetime(test_data[date_column])

    train_data = train_data.sort_values(date_column).reset_index(drop=True)

    test_data = test_data.sort_values(date_column).reset_index(drop=True)

    if train_data[date_column].duplicated().any():
        raise ValueError("Training data contains duplicate periods.")

    if test_data[date_column].duplicated().any():
        raise ValueError("Test data contains duplicate periods.")

    history = train_data.set_index(date_column)[value_column]

    rows: list[dict[str, object]] = []

    for horizon_step, row in enumerate(
        test_data.itertuples(index=False),
        start=1,
    ):
        forecast_period = pd.Timestamp(getattr(row, date_column))

        actual = float(getattr(row, value_column))

        reference_period = forecast_period - pd.DateOffset(months=seasonal_period)

        if reference_period not in history.index:
            raise ValueError(
                "Seasonal reference period "
                f"{reference_period.date()} "
                "is not available in the training data."
            )

        predicted = float(history.loc[reference_period])

        error = actual - predicted

        rows.append(
            {
                "forecast_period": forecast_period,
                "reference_period": reference_period,
                "horizon_step": horizon_step,
                "actual": actual,
                "predicted": predicted,
                "error": error,
                "absolute_error": abs(error),
                "squared_error": error**2,
            }
        )

    return pd.DataFrame(rows)
