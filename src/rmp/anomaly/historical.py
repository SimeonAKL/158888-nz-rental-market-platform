"""Historical anomaly detection for monthly rental-market series.

The detector evaluates unusual year-on-year movements rather than raw
monthly levels. This controls for recurring annual seasonality in monthly
rental-market data.

For observation t:

1. seasonal_change = x[t] - x[t-12]
2. The current seasonal change is excluded from its own baseline.
3. A rolling median of previous seasonal changes defines the expected
   year-on-year movement.
4. MAD is the primary robust scale estimate.
5. IQR is used as a robust fallback when MAD is zero.
6. The resulting robust score is classified as normal, moderate, or high.

The output identifies analytical alerts only. It does not provide causal
explanations for unusual market movements.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MAD_SCALE_FACTOR = 0.6745
IQR_NORMAL_SCALE = 1.349

DEFAULT_SEASONAL_LAG = 12
DEFAULT_BASELINE_WINDOW = 36
DEFAULT_MIN_PERIODS = 24

MODERATE_THRESHOLD = 2.5
HIGH_THRESHOLD = 3.5


def _median_absolute_deviation(values: pd.Series) -> float:
    """Return median absolute deviation for a rolling window."""
    median = values.median()
    return float((values - median).abs().median())


def _interquartile_range(values: pd.Series) -> float:
    """Return interquartile range for a rolling window."""
    return float(values.quantile(0.75) - values.quantile(0.25))


def _classify_severity(score: float | None) -> str:
    """Classify an anomaly score by absolute magnitude."""
    if score is None or pd.isna(score):
        return "unavailable"

    absolute_score = abs(float(score))

    if absolute_score >= HIGH_THRESHOLD:
        return "high"

    if absolute_score >= MODERATE_THRESHOLD:
        return "moderate"

    return "normal"


def _classify_direction(score: float | None) -> str:
    """Classify the direction of an anomaly score."""
    if score is None or pd.isna(score):
        return "unavailable"

    if score >= MODERATE_THRESHOLD:
        return "high"

    if score <= -MODERATE_THRESHOLD:
        return "low"

    return "normal"


def detect_historical_anomalies(
    panel: pd.DataFrame,
    *,
    seasonal_lag: int = DEFAULT_SEASONAL_LAG,
    baseline_window: int = DEFAULT_BASELINE_WINDOW,
    min_periods: int = DEFAULT_MIN_PERIODS,
    series_col: str = "series_id",
    period_col: str = "period_date",
    value_col: str = "value",
) -> pd.DataFrame:
    """Detect unusual historical movements in monthly time series.

    The method compares each observation with the corresponding observation
    one seasonal cycle earlier and evaluates that year-on-year change against
    previous year-on-year changes.

    Parameters
    ----------
    panel:
        Long-format monthly analytical dataset.
    seasonal_lag:
        Seasonal period in observations. Twelve is used for monthly data.
    baseline_window:
        Maximum number of previous seasonal changes used for the robust
        baseline.
    min_periods:
        Minimum previous seasonal changes required before a score is
        calculated.
    series_col:
        Column identifying an individual time series.
    period_col:
        Monthly observation date.
    value_col:
        Numeric value being analysed.

    Returns
    -------
    pandas.DataFrame
        Original observations plus historical anomaly diagnostics.
    """
    required_columns = {
        series_col,
        period_col,
        value_col,
    }
    missing_columns = required_columns.difference(panel.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    if seasonal_lag < 1:
        raise ValueError("seasonal_lag must be at least 1")

    if baseline_window < 2:
        raise ValueError("baseline_window must be at least 2")

    if min_periods < 2:
        raise ValueError("min_periods must be at least 2")

    if min_periods > baseline_window:
        raise ValueError("min_periods cannot exceed baseline_window")

    result = panel.copy()

    result[period_col] = pd.to_datetime(result[period_col])
    result[value_col] = pd.to_numeric(
        result[value_col],
        errors="coerce",
    )

    result = result.sort_values(
        [series_col, period_col],
        kind="stable",
    ).reset_index(drop=True)

    duplicated = result.duplicated(
        subset=[series_col, period_col],
        keep=False,
    )

    if duplicated.any():
        raise ValueError("Duplicate series-period observations found in historical anomaly input.")

    grouped_values = result.groupby(
        series_col,
        sort=False,
    )[value_col]

    result["seasonal_reference"] = grouped_values.shift(seasonal_lag)

    result["seasonal_change"] = result[value_col] - result["seasonal_reference"]

    # Exclude the current seasonal change from its own
    # historical baseline.
    prior_changes = result.groupby(
        series_col,
        sort=False,
    )["seasonal_change"].shift(1)

    grouped_prior_changes = prior_changes.groupby(
        result[series_col],
        sort=False,
    )

    result["historical_change_expected"] = grouped_prior_changes.transform(
        lambda values: values.rolling(
            window=baseline_window,
            min_periods=min_periods,
        ).median()
    )

    result["historical_mad"] = grouped_prior_changes.transform(
        lambda values: values.rolling(
            window=baseline_window,
            min_periods=min_periods,
        ).apply(
            _median_absolute_deviation,
            raw=False,
        )
    )

    result["historical_iqr"] = grouped_prior_changes.transform(
        lambda values: values.rolling(
            window=baseline_window,
            min_periods=min_periods,
        ).apply(
            _interquartile_range,
            raw=False,
        )
    )

    result["historical_expected"] = (
        result["seasonal_reference"] + result["historical_change_expected"]
    )

    result["historical_deviation"] = result[value_col] - result["historical_expected"]

    result["historical_deviation_pct"] = np.where(
        result["historical_expected"].notna() & result["historical_expected"].ne(0),
        (result["historical_deviation"] / result["historical_expected"] * 100.0),
        np.nan,
    )

    mad_available = result["historical_mad"].notna() & result["historical_mad"].gt(0)

    iqr_available = (
        ~mad_available & result["historical_iqr"].notna() & result["historical_iqr"].gt(0)
    )

    result["historical_scale_method"] = np.select(
        [
            mad_available,
            iqr_available,
        ],
        [
            "mad",
            "iqr",
        ],
        default="unavailable",
    )

    result["historical_scale"] = np.nan

    result.loc[
        mad_available,
        "historical_scale",
    ] = (
        result.loc[
            mad_available,
            "historical_mad",
        ]
        / MAD_SCALE_FACTOR
    )

    result.loc[
        iqr_available,
        "historical_scale",
    ] = (
        result.loc[
            iqr_available,
            "historical_iqr",
        ]
        / IQR_NORMAL_SCALE
    )

    score_available = (
        result[value_col].notna()
        & result["historical_expected"].notna()
        & result["historical_scale"].notna()
        & result["historical_scale"].gt(0)
    )

    result["historical_score"] = np.where(
        score_available,
        (result["historical_deviation"] / result["historical_scale"]),
        np.nan,
    )

    result["historical_score_available"] = score_available

    result["historical_severity"] = result["historical_score"].map(_classify_severity)

    result["historical_direction"] = result["historical_score"].map(_classify_direction)

    result["historical_is_anomaly"] = result["historical_severity"].isin({"moderate", "high"})

    result["seasonal_lag"] = seasonal_lag
    result["baseline_window"] = baseline_window
    result["minimum_baseline_observations"] = min_periods

    return result
