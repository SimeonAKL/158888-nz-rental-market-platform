"""Regression tests for anomaly coverage across analytical scopes."""

from __future__ import annotations

import pandas as pd

from rmp.anomaly.consolidate import consolidate_anomaly_outputs


def _historical_rows() -> pd.DataFrame:
    """Create historical records for two analytical series."""
    return pd.DataFrame(
        {
            "period_date": [
                "2026-01-01",
                "2026-01-01",
            ],
            "series_id": [
                "forecast_series",
                "historical_only_series",
            ],
            "metric": [
                "median_rent",
                "median_rent",
            ],
            "value": [
                600.0,
                500.0,
            ],
            "historical_score_available": [
                True,
                True,
            ],
            "historical_severity": [
                "normal",
                "normal",
            ],
            "historical_direction": [
                "normal",
                "normal",
            ],
            "historical_is_anomaly": [
                False,
                False,
            ],
            "dashboard_alert": [
                False,
                False,
            ],
            "alert_status": [
                "normal",
                "normal",
            ],
        }
    )


def _forecast_rows() -> pd.DataFrame:
    """Create a forecast record for only one analytical series."""
    return pd.DataFrame(
        {
            "forecast_period": [
                "2026-01-01",
            ],
            "series_id": [
                "forecast_series",
            ],
            "metric": [
                "median_rent",
            ],
            "model": [
                "ets_additive_damped",
            ],
            "origin": [
                "2025-12-01",
            ],
            "horizon_step": [
                1,
            ],
            "predicted": [
                590.0,
            ],
            "forecast_residual": [
                10.0,
            ],
            "forecast_residual_pct": [
                1.6949,
            ],
            "forecast_error_direction": [
                "above_forecast",
            ],
            "residual_median": [
                0.0,
            ],
            "residual_mad": [
                5.0,
            ],
            "residual_iqr": [
                8.0,
            ],
            "forecast_residual_scale": [
                7.413,
            ],
            "forecast_scale_method": [
                "mad",
            ],
            "forecast_anomaly_score": [
                1.35,
            ],
            "forecast_score_available": [
                True,
            ],
            "forecast_severity": [
                "normal",
            ],
            "forecast_direction": [
                "normal",
            ],
            "forecast_is_anomaly": [
                False,
            ],
            "forecast_practical_significance_available": [
                True,
            ],
            "forecast_practical_significance": [
                False,
            ],
            "forecast_statistical_anomaly": [
                False,
            ],
            "forecast_dashboard_alert": [
                False,
            ],
            "forecast_alert_status": [
                "normal",
            ],
        }
    )


def test_consolidation_retains_historical_only_series() -> None:
    """Historical-only analytical series must survive consolidation."""
    historical = _historical_rows()
    forecast = _forecast_rows()

    result = consolidate_anomaly_outputs(
        historical,
        forecast,
    )

    assert result["series_id"].nunique() == 2

    assert set(result["series_id"]) == {
        "forecast_series",
        "historical_only_series",
    }

    historical_only = result.loc[
        result["series_id"]
        == "historical_only_series"
    ].iloc[0]

    assert not historical_only["has_forecast_record"]
    assert (
        historical_only["detector_coverage"]
        == "historical_only"
    )
    assert (
        historical_only["overall_status"]
        == "normal"
    )


def test_forecast_series_keeps_matched_forecast_record() -> None:
    """Forecast-eligible series must retain its forecast enrichment."""
    result = consolidate_anomaly_outputs(
        _historical_rows(),
        _forecast_rows(),
    )

    forecast_series = result.loc[
        result["series_id"]
        == "forecast_series"
    ].iloc[0]

    assert forecast_series["has_forecast_record"]
    assert forecast_series["forecast_model"] == (
        "ets_additive_damped"
    )
    assert forecast_series["detector_coverage"] == "both"


def test_summary_series_count_matches_historical_scope() -> None:
    """Consolidated scope must be defined by historical analytics."""
    historical = _historical_rows()
    forecast = _forecast_rows()

    result = consolidate_anomaly_outputs(
        historical,
        forecast,
    )

    assert (
        result["series_id"].nunique()
        == historical["series_id"].nunique()
    )

    assert (
        result["series_id"].nunique()
        > forecast["series_id"].nunique()
    )
