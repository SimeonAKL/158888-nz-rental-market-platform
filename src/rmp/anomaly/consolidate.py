"""Consolidation of historical and forecast anomaly outputs.

The consolidated anomaly dataset provides one dashboard-ready record per
historical series-period observation.

Historical anomaly results define the full analytical time axis. Forecast
residual anomaly diagnostics are attached where winner-model, horizon-one
rolling-origin predictions are available.

Overall alert status is based on dashboard-level alerts rather than raw
statistical anomaly flags.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

SEVERITY_RANK = {
    "unavailable": -1,
    "normal": 0,
    "moderate": 1,
    "high": 2,
}


def _overall_severity(
    historical_alert: bool,
    historical_severity: str | None,
    forecast_alert: bool,
    forecast_severity: str | None,
    any_available: bool,
) -> str:
    """Return overall severity from active dashboard alerts."""
    if not any_available:
        return "unavailable"

    active_severities: list[str] = []

    if historical_alert:
        active_severities.append(
            str(historical_severity)
        )

    if forecast_alert:
        active_severities.append(
            str(forecast_severity)
        )

    if not active_severities:
        return "normal"

    return max(
        active_severities,
        key=lambda value: SEVERITY_RANK.get(
            value,
            -1,
        ),
    )


def consolidate_anomaly_outputs(
    historical: pd.DataFrame,
    forecast: pd.DataFrame,
) -> pd.DataFrame:
    """Combine historical and forecast anomaly outputs.

    Parameters
    ----------
    historical:
        Historical anomaly output from Phase 5A.2 / 5A.2.1.
    forecast:
        Forecast residual anomaly output from Phase 5A.3 / 5A.3.1.

    Returns
    -------
    pandas.DataFrame
        Dashboard-ready anomaly summary.
    """
    historical_required = {
        "period_date",
        "series_id",
        "metric",
        "historical_score_available",
        "historical_severity",
        "historical_direction",
        "historical_is_anomaly",
        "dashboard_alert",
        "alert_status",
    }

    forecast_required = {
        "forecast_period",
        "series_id",
        "metric",
        "model",
        "predicted",
        "forecast_residual",
        "forecast_residual_pct",
        "forecast_error_direction",
        "forecast_anomaly_score",
        "forecast_score_available",
        "forecast_severity",
        "forecast_direction",
        "forecast_is_anomaly",
        "forecast_dashboard_alert",
        "forecast_alert_status",
    }

    missing_historical = (
        historical_required.difference(
            historical.columns
        )
    )

    if missing_historical:
        raise ValueError(
            "Missing required historical columns: "
            + ", ".join(
                sorted(missing_historical)
            )
        )

    missing_forecast = (
        forecast_required.difference(
            forecast.columns
        )
    )

    if missing_forecast:
        raise ValueError(
            "Missing required forecast columns: "
            + ", ".join(
                sorted(missing_forecast)
            )
        )

    historical_result = historical.copy()
    forecast_result = forecast.copy()

    historical_result["period_date"] = (
        pd.to_datetime(
            historical_result["period_date"]
        )
    )

    forecast_result["forecast_period"] = (
        pd.to_datetime(
            forecast_result["forecast_period"]
        )
    )

    historical_duplicates = (
        historical_result.duplicated(
            subset=[
                "series_id",
                "period_date",
            ],
            keep=False,
        )
    )

    if historical_duplicates.any():
        raise ValueError(
            "Duplicate historical series-period "
            "observations found."
        )

    forecast_duplicates = (
        forecast_result.duplicated(
            subset=[
                "series_id",
                "forecast_period",
            ],
            keep=False,
        )
    )

    if forecast_duplicates.any():
        raise ValueError(
            "Duplicate forecast series-period "
            "observations found."
        )

    forecast_columns = [
        "series_id",
        "forecast_period",
        "metric",
        "model",
        "origin",
        "horizon_step",
        "predicted",
        "forecast_residual",
        "forecast_residual_pct",
        "forecast_error_direction",
        "residual_median",
        "residual_mad",
        "residual_iqr",
        "forecast_residual_scale",
        "forecast_scale_method",
        "forecast_anomaly_score",
        "forecast_score_available",
        "forecast_severity",
        "forecast_direction",
        "forecast_is_anomaly",
        "forecast_practical_significance_available",
        "forecast_practical_significance",
        "forecast_statistical_anomaly",
        "forecast_dashboard_alert",
        "forecast_alert_status",
    ]

    forecast_columns = [
        column
        for column in forecast_columns
        if column in forecast_result.columns
    ]

    forecast_subset = forecast_result[
        forecast_columns
    ].copy()

    forecast_subset = forecast_subset.rename(
        columns={
            "forecast_period": "period_date",
            "metric": "forecast_metric",
            "model": "forecast_model",
        }
    )

    result = historical_result.merge(
        forecast_subset,
        on=[
            "series_id",
            "period_date",
        ],
        how="left",
        validate="one_to_one",
    )

    metric_mismatch = (
        result["forecast_metric"].notna()
        & result["metric"].ne(
            result["forecast_metric"]
        )
    )

    if metric_mismatch.any():
        raise ValueError(
            "Historical and forecast metric mismatch "
            "found after consolidation."
        )

    result["has_forecast_record"] = (
        result["forecast_metric"].notna()
    )

    result[
        "historical_dashboard_alert"
    ] = (
        result["dashboard_alert"]
        .fillna(False)
        .astype(bool)
    )

    result[
        "forecast_dashboard_alert"
    ] = (
        result[
            "forecast_dashboard_alert"
        ]
        .fillna(False)
        .astype(bool)
    )

    result[
        "historical_detector_available"
    ] = (
        result[
            "historical_score_available"
        ]
        .fillna(False)
        .astype(bool)
    )

    result[
        "forecast_detector_available"
    ] = (
        result[
            "forecast_score_available"
        ]
        .fillna(False)
        .astype(bool)
    )

    historical_available = result[
        "historical_detector_available"
    ]

    forecast_available = result[
        "forecast_detector_available"
    ]

    result["detector_coverage"] = np.select(
        [
            historical_available
            & forecast_available,
            historical_available
            & ~forecast_available,
            ~historical_available
            & forecast_available,
        ],
        [
            "both",
            "historical_only",
            "forecast_only",
        ],
        default="unavailable",
    )

    historical_alert = result[
        "historical_dashboard_alert"
    ]

    forecast_alert = result[
        "forecast_dashboard_alert"
    ]

    any_available = (
        historical_available
        | forecast_available
    )

    result["overall_status"] = np.select(
        [
            ~any_available,
            historical_alert
            & forecast_alert,
            historical_alert,
            forecast_alert,
        ],
        [
            "unavailable",
            "confirmed_anomaly",
            "historical_alert",
            "forecast_alert",
        ],
        default="normal",
    )

    result["overall_dashboard_alert"] = (
        historical_alert
        | forecast_alert
    )

    result["overall_severity"] = [
        _overall_severity(
            bool(hist_alert),
            hist_severity,
            bool(fc_alert),
            fc_severity,
            bool(available),
        )
        for (
            hist_alert,
            hist_severity,
            fc_alert,
            fc_severity,
            available,
        ) in zip(
            historical_alert,
            result["historical_severity"],
            forecast_alert,
            result["forecast_severity"],
            any_available,
            strict=True,
        )
    ]

    result["overall_direction"] = np.select(
        [
            historical_alert
            & forecast_alert
            & result[
                "historical_direction"
            ].eq(
                result[
                    "forecast_error_direction"
                ].map(
                    {
                        "above_forecast": "high",
                        "below_forecast": "low",
                        "on_forecast": "normal",
                    }
                )
            ),
            historical_alert
            & forecast_alert,
            historical_alert,
            forecast_alert,
        ],
        [
            result["historical_direction"],
            "mixed",
            result["historical_direction"],
            result[
                "forecast_error_direction"
            ].map(
                {
                    "above_forecast": "high",
                    "below_forecast": "low",
                    "on_forecast": "normal",
                }
            ),
        ],
        default="normal",
    )

    result = result.drop(
        columns=[
            "forecast_metric",
        ]
    )

    return result.sort_values(
        [
            "series_id",
            "period_date",
        ],
        kind="stable",
    ).reset_index(drop=True)
