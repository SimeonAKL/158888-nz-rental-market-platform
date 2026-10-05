"""Forecast evaluation metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _as_float_arrays(
    y_true,
    y_pred,
) -> tuple[np.ndarray, np.ndarray]:
    """Convert observed and predicted values to float arrays."""

    actual = np.asarray(
        y_true,
        dtype=float,
    )

    predicted = np.asarray(
        y_pred,
        dtype=float,
    )

    if actual.shape != predicted.shape:
        raise ValueError("y_true and y_pred must have the same shape.")

    if actual.size == 0:
        raise ValueError("Metric inputs cannot be empty.")

    if np.isnan(actual).any() or np.isnan(predicted).any():
        raise ValueError("Metric inputs cannot contain NaN values.")

    return actual, predicted


def mae(
    y_true,
    y_pred,
) -> float:
    """Mean absolute error."""

    actual, predicted = _as_float_arrays(
        y_true,
        y_pred,
    )

    return float(np.mean(np.abs(actual - predicted)))


def rmse(
    y_true,
    y_pred,
) -> float:
    """Root mean squared error."""

    actual, predicted = _as_float_arrays(
        y_true,
        y_pred,
    )

    return float(np.sqrt(np.mean(np.square(actual - predicted))))


def smape(
    y_true,
    y_pred,
) -> float:
    """Symmetric mean absolute percentage error.

    Returns sMAPE as a percentage between 0 and 200.

    Terms where both actual and predicted are zero contribute
    zero error rather than causing division by zero.
    """

    actual, predicted = _as_float_arrays(
        y_true,
        y_pred,
    )

    denominator = np.abs(actual) + np.abs(predicted)

    numerator = 2.0 * np.abs(actual - predicted)

    terms = np.divide(
        numerator,
        denominator,
        out=np.zeros_like(
            numerator,
            dtype=float,
        ),
        where=denominator != 0,
    )

    return float(np.mean(terms) * 100.0)


def calculate_forecast_metrics(
    y_true,
    y_pred,
) -> dict[str, float]:
    """Calculate all core project forecasting metrics."""

    return {
        "mae": mae(
            y_true,
            y_pred,
        ),
        "rmse": rmse(
            y_true,
            y_pred,
        ),
        "smape": smape(
            y_true,
            y_pred,
        ),
    }


def calculate_metrics_frame(
    y_true,
    y_pred,
) -> pd.DataFrame:
    """Return core forecasting metrics as a one-row dataframe."""

    metrics = calculate_forecast_metrics(
        y_true,
        y_pred,
    )

    return pd.DataFrame([metrics])
