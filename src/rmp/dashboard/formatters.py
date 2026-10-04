"""Formatting helpers for dashboard values."""

from __future__ import annotations

import math

MODEL_LABELS = {
    "seasonal_naive": "Seasonal Naive",
    "ets_additive_damped": "ETS (Additive Damped)",
    "xgboost_pooled_recursive": (
        "XGBoost (Pooled Recursive)"
    ),
}


def format_value(
    value: float | None,
    metric: str,
) -> str:
    """Format a metric value for display."""
    if value is None:
        return "N/A"

    try:
        if math.isnan(float(value)):
            return "N/A"
    except (TypeError, ValueError):
        pass

    if metric == "median_rent":
        return f"${float(value):,.0f}"

    if metric == "bonds_lodged":
        return f"{float(value):,.0f}"

    return f"{float(value):,.2f}"


def format_percentage(
    value: float | None,
    *,
    signed: bool = True,
) -> str:
    """Format a percentage value."""
    if value is None:
        return "N/A"

    try:
        if math.isnan(float(value)):
            return "N/A"
    except (TypeError, ValueError):
        return "N/A"

    if signed:
        return f"{float(value):+.1f}%"

    return f"{float(value):.1f}%"


def model_label(model: str) -> str:
    """Return a human-readable forecasting model label."""
    return MODEL_LABELS.get(
        model,
        model.replace("_", " ").title(),
    )
