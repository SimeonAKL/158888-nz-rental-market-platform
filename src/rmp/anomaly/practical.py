"""Practical significance filtering for anomaly outputs.

Statistical anomaly detection and practical significance answer different
questions:

- Statistical anomaly:
  Is the observation unusual relative to its historical distribution?

- Practical significance:
  Is the magnitude of the deviation large enough to be operationally useful
  as a dashboard alert?

Practical significance does not replace the statistical anomaly result.
Both are retained in the processed output.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PracticalThreshold:
    """Metric-specific practical significance thresholds."""

    minimum_absolute_deviation: float
    minimum_percentage_deviation: float


PRACTICAL_THRESHOLDS: dict[str, PracticalThreshold] = {
    "median_rent": PracticalThreshold(
        minimum_absolute_deviation=15.0,
        minimum_percentage_deviation=3.0,
    ),
    "bonds_lodged": PracticalThreshold(
        minimum_absolute_deviation=25.0,
        minimum_percentage_deviation=20.0,
    ),
}


def _get_threshold(
    metric: str,
) -> PracticalThreshold | None:
    """Return practical threshold configuration for a metric."""
    return PRACTICAL_THRESHOLDS.get(metric)


def add_practical_significance(
    anomalies: pd.DataFrame,
    *,
    metric_col: str = "metric",
    deviation_col: str = "historical_deviation",
    deviation_pct_col: str = "historical_deviation_pct",
    anomaly_col: str = "historical_is_anomaly",
    score_available_col: str = "historical_score_available",
) -> pd.DataFrame:
    """Add practical significance and dashboard-alert fields.

    An observation is practically significant when both its absolute
    deviation and percentage deviation meet the configured metric-specific
    thresholds.

    A dashboard alert requires both:

    1. statistical anomaly status; and
    2. practical significance.

    Observations without an available statistical anomaly score remain
    unavailable even if deviation values can otherwise be calculated.
    """
    required_columns = {
        metric_col,
        deviation_col,
        deviation_pct_col,
        anomaly_col,
        score_available_col,
    }

    missing_columns = required_columns.difference(anomalies.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    result = anomalies.copy()

    result["practical_abs_threshold"] = np.nan
    result["practical_pct_threshold"] = np.nan

    result["practical_significance_available"] = False
    result["practical_significance"] = False

    for metric, threshold in PRACTICAL_THRESHOLDS.items():
        metric_mask = result[metric_col].eq(metric)

        result.loc[
            metric_mask,
            "practical_abs_threshold",
        ] = threshold.minimum_absolute_deviation

        result.loc[
            metric_mask,
            "practical_pct_threshold",
        ] = threshold.minimum_percentage_deviation

        available = metric_mask & result[deviation_col].notna() & result[deviation_pct_col].notna()

        result.loc[
            available,
            "practical_significance_available",
        ] = True

        significant = (
            available
            & result[deviation_col].abs().ge(threshold.minimum_absolute_deviation)
            & result[deviation_pct_col].abs().ge(threshold.minimum_percentage_deviation)
        )

        result.loc[
            significant,
            "practical_significance",
        ] = True

    result["statistical_anomaly"] = result[anomaly_col].fillna(False).astype(bool)

    statistical_available = result[score_available_col].fillna(False).astype(bool)

    result["dashboard_alert"] = (
        statistical_available & result["statistical_anomaly"] & result["practical_significance"]
    )

    result["alert_status"] = np.select(
        [
            (~statistical_available | ~result["practical_significance_available"]),
            result["dashboard_alert"],
            result["statistical_anomaly"],
        ],
        [
            "unavailable",
            "dashboard_alert",
            "statistical_only",
        ],
        default="normal",
    )

    return result
