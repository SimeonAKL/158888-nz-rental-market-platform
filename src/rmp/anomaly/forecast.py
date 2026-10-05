"""Forecast-residual anomaly detection.

This module identifies observations whose one-step-ahead forecast residual is
unusual relative to the winner model's previous out-of-sample residuals.

Only rolling-origin, horizon-one predictions from the selected series-level
winner model are used. The current residual is excluded from its own baseline,
so anomaly scoring does not use future residual information.

The method is retrospective analytical anomaly detection. It does not imply
that an unusual forecast residual has a known causal explanation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MAD_SCALE_FACTOR = 0.6745
IQR_NORMAL_SCALE = 1.349

DEFAULT_HORIZON = 1
DEFAULT_MIN_PRIOR_RESIDUALS = 6

MODERATE_THRESHOLD = 2.5
HIGH_THRESHOLD = 3.5


def _median_absolute_deviation(values: pd.Series) -> float:
    """Return median absolute deviation."""
    median = values.median()
    return float((values - median).abs().median())


def _interquartile_range(values: pd.Series) -> float:
    """Return interquartile range."""
    return float(values.quantile(0.75) - values.quantile(0.25))


def _classify_severity(score: float | None) -> str:
    """Classify forecast anomaly severity."""
    if score is None or pd.isna(score):
        return "unavailable"

    absolute_score = abs(float(score))

    if absolute_score >= HIGH_THRESHOLD:
        return "high"

    if absolute_score >= MODERATE_THRESHOLD:
        return "moderate"

    return "normal"


def _classify_direction(score: float | None) -> str:
    """Classify direction of forecast deviation."""
    if score is None or pd.isna(score):
        return "unavailable"

    if score >= MODERATE_THRESHOLD:
        return "high"

    if score <= -MODERATE_THRESHOLD:
        return "low"

    return "normal"


def select_winner_horizon_predictions(
    predictions: pd.DataFrame,
    winners: pd.DataFrame,
    *,
    horizon: int = DEFAULT_HORIZON,
) -> pd.DataFrame:
    """Select horizon-one predictions from each series winner model.

    Parameters
    ----------
    predictions:
        Unified Phase 4 rolling-origin prediction output.
    winners:
        Phase 4 series-level model winner output.
    horizon:
        Forecast horizon to retain. Phase 5 anomaly detection uses horizon 1.

    Returns
    -------
    pandas.DataFrame
        Winner-model predictions for the requested horizon.
    """
    prediction_required = {
        "model",
        "series_id",
        "metric",
        "origin",
        "forecast_period",
        "horizon_step",
        "actual",
        "predicted",
    }

    winner_required = {
        "series_id",
        "metric",
        "best_model",
    }

    missing_predictions = prediction_required.difference(predictions.columns)

    if missing_predictions:
        missing = ", ".join(sorted(missing_predictions))
        raise ValueError(f"Missing required prediction columns: {missing}")

    missing_winners = winner_required.difference(winners.columns)

    if missing_winners:
        missing = ", ".join(sorted(missing_winners))
        raise ValueError(f"Missing required winner columns: {missing}")

    winner_map = winners[
        [
            "series_id",
            "metric",
            "best_model",
        ]
    ].copy()

    duplicated_winners = winner_map.duplicated(
        subset=[
            "series_id",
            "metric",
        ],
        keep=False,
    )

    if duplicated_winners.any():
        raise ValueError("Duplicate series winner mappings found.")

    selected = predictions.loc[predictions["horizon_step"].eq(horizon)].copy()

    selected = selected.merge(
        winner_map,
        on=[
            "series_id",
            "metric",
        ],
        how="inner",
        validate="many_to_one",
    )

    selected = selected.loc[selected["model"].eq(selected["best_model"])].copy()

    if selected.empty:
        raise ValueError("No winner-model horizon predictions were found.")

    selected["origin"] = pd.to_datetime(selected["origin"])

    selected["forecast_period"] = pd.to_datetime(selected["forecast_period"])

    duplicated_predictions = selected.duplicated(
        subset=[
            "series_id",
            "forecast_period",
        ],
        keep=False,
    )

    if duplicated_predictions.any():
        raise ValueError("Duplicate winner-model series-period predictions found.")

    return selected.sort_values(
        [
            "series_id",
            "forecast_period",
        ],
        kind="stable",
    ).reset_index(drop=True)


def detect_forecast_residual_anomalies(
    predictions: pd.DataFrame,
    winners: pd.DataFrame,
    *,
    horizon: int = DEFAULT_HORIZON,
    min_prior_residuals: int = DEFAULT_MIN_PRIOR_RESIDUALS,
) -> pd.DataFrame:
    """Detect anomalies in winner-model forecast residuals.

    The residual is defined as::

        residual = actual - predicted

    A positive residual means the actual observation was above the forecast.
    A negative residual means the actual observation was below the forecast.

    Each residual is evaluated against only previous out-of-sample residuals
    from the same series and selected winner model.

    MAD is the primary robust scale estimate. IQR is used when MAD is zero.

    Parameters
    ----------
    predictions:
        Phase 4 unified rolling-origin predictions.
    winners:
        Phase 4 series-level winner model mapping.
    horizon:
        Forecast horizon to analyse. Defaults to one-step-ahead.
    min_prior_residuals:
        Minimum number of earlier residuals required before scoring.

    Returns
    -------
    pandas.DataFrame
        Winner-model horizon-one predictions plus residual anomaly fields.
    """
    if horizon < 1:
        raise ValueError("horizon must be at least 1")

    if min_prior_residuals < 3:
        raise ValueError("min_prior_residuals must be at least 3")

    result = select_winner_horizon_predictions(
        predictions,
        winners,
        horizon=horizon,
    )

    result["actual"] = pd.to_numeric(
        result["actual"],
        errors="coerce",
    )

    result["predicted"] = pd.to_numeric(
        result["predicted"],
        errors="coerce",
    )

    result["forecast_residual"] = result["actual"] - result["predicted"]

    result["forecast_residual_pct"] = np.where(
        result["predicted"].notna() & result["predicted"].ne(0),
        (result["forecast_residual"] / result["predicted"] * 100.0),
        np.nan,
    )

    result["forecast_error_direction"] = np.select(
        [
            result["forecast_residual"].gt(0),
            result["forecast_residual"].lt(0),
        ],
        [
            "above_forecast",
            "below_forecast",
        ],
        default="on_forecast",
    )

    # Exclude the current residual from its own baseline.
    prior_residuals = result.groupby(
        "series_id",
        sort=False,
    )["forecast_residual"].shift(1)

    grouped_prior = prior_residuals.groupby(
        result["series_id"],
        sort=False,
    )

    result["residual_median"] = grouped_prior.transform(
        lambda values: values.expanding(min_periods=min_prior_residuals).median()
    )

    result["residual_mad"] = grouped_prior.transform(
        lambda values: values.expanding(min_periods=min_prior_residuals).apply(
            _median_absolute_deviation,
            raw=False,
        )
    )

    result["residual_iqr"] = grouped_prior.transform(
        lambda values: values.expanding(min_periods=min_prior_residuals).apply(
            _interquartile_range,
            raw=False,
        )
    )

    mad_available = result["residual_mad"].notna() & result["residual_mad"].gt(0)

    iqr_available = ~mad_available & result["residual_iqr"].notna() & result["residual_iqr"].gt(0)

    result["forecast_scale_method"] = np.select(
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

    result["forecast_residual_scale"] = np.nan

    result.loc[
        mad_available,
        "forecast_residual_scale",
    ] = (
        result.loc[
            mad_available,
            "residual_mad",
        ]
        / MAD_SCALE_FACTOR
    )

    result.loc[
        iqr_available,
        "forecast_residual_scale",
    ] = (
        result.loc[
            iqr_available,
            "residual_iqr",
        ]
        / IQR_NORMAL_SCALE
    )

    score_available = (
        result["forecast_residual"].notna()
        & result["residual_median"].notna()
        & result["forecast_residual_scale"].notna()
        & result["forecast_residual_scale"].gt(0)
    )

    result["forecast_anomaly_score"] = np.where(
        score_available,
        (result["forecast_residual"] - result["residual_median"])
        / result["forecast_residual_scale"],
        np.nan,
    )

    result["forecast_score_available"] = score_available

    result["forecast_severity"] = result["forecast_anomaly_score"].map(_classify_severity)

    result["forecast_direction"] = result["forecast_anomaly_score"].map(_classify_direction)

    result["forecast_is_anomaly"] = result["forecast_severity"].isin(
        {
            "moderate",
            "high",
        }
    )

    result["forecast_anomaly_horizon"] = horizon

    result["minimum_prior_residuals"] = min_prior_residuals

    return result
