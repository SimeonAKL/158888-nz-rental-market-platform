"""Practical significance filtering for forecast residual anomalies."""

from __future__ import annotations

import numpy as np
import pandas as pd

FORECAST_RENT_ABS_THRESHOLD = 15.0
FORECAST_RENT_PCT_THRESHOLD = 2.0
FORECAST_BONDS_ABS_THRESHOLD = 50.0
FORECAST_BONDS_PCT_THRESHOLD = 10.0


def add_forecast_practical_significance(
    anomalies: pd.DataFrame,
) -> pd.DataFrame:
    """Add practical significance and dashboard alert fields.

    Median rent:
        abs(residual) >= 15 AND abs(residual_pct) >= 2%

    Bonds lodged:
        abs(residual) >= 50 OR abs(residual_pct) >= 10%
    """
    required_columns = {
        "metric",
        "forecast_residual",
        "forecast_residual_pct",
        "forecast_is_anomaly",
        "forecast_score_available",
    }

    missing = required_columns.difference(anomalies.columns)

    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

    result = anomalies.copy()

    result["forecast_practical_significance_available"] = (
        result["forecast_residual"].notna() & result["forecast_residual_pct"].notna()
    )

    result["forecast_practical_significance"] = False

    rent_mask = (
        result["metric"].eq("median_rent") & result["forecast_practical_significance_available"]
    )

    bonds_mask = (
        result["metric"].eq("bonds_lodged") & result["forecast_practical_significance_available"]
    )

    result.loc[
        rent_mask,
        "forecast_practical_significance",
    ] = result.loc[
        rent_mask,
        "forecast_residual",
    ].abs().ge(FORECAST_RENT_ABS_THRESHOLD) & result.loc[
        rent_mask,
        "forecast_residual_pct",
    ].abs().ge(FORECAST_RENT_PCT_THRESHOLD)

    result.loc[
        bonds_mask,
        "forecast_practical_significance",
    ] = result.loc[
        bonds_mask,
        "forecast_residual",
    ].abs().ge(FORECAST_BONDS_ABS_THRESHOLD) | result.loc[
        bonds_mask,
        "forecast_residual_pct",
    ].abs().ge(FORECAST_BONDS_PCT_THRESHOLD)

    statistical_available = result["forecast_score_available"].fillna(False).astype(bool)

    result["forecast_statistical_anomaly"] = (
        result["forecast_is_anomaly"].fillna(False).astype(bool)
    )

    result["forecast_dashboard_alert"] = (
        statistical_available
        & result["forecast_statistical_anomaly"]
        & result["forecast_practical_significance"]
    )

    result["forecast_alert_status"] = np.select(
        [
            (~statistical_available | ~result["forecast_practical_significance_available"]),
            result["forecast_dashboard_alert"],
            result["forecast_statistical_anomaly"],
        ],
        [
            "unavailable",
            "dashboard_alert",
            "statistical_only",
        ],
        default="normal",
    )

    return result
