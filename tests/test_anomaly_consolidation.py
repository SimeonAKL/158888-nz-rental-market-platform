"""Tests for anomaly output consolidation."""

from __future__ import annotations

import pandas as pd
import pytest

from rmp.anomaly.consolidate import (
    consolidate_anomaly_outputs,
)


def _historical(
    *,
    dashboard_alert: bool = False,
    severity: str = "normal",
    direction: str = "normal",
    score_available: bool = True,
) -> pd.DataFrame:
    """Create a minimal historical anomaly record."""
    return pd.DataFrame(
        {
            "period_date": [
                "2026-01-01"
            ],
            "series_id": [
                "region_1_median_rent"
            ],
            "metric": [
                "median_rent"
            ],
            "value": [
                600.0
            ],
            "historical_score_available": [
                score_available
            ],
            "historical_severity": [
                severity
            ],
            "historical_direction": [
                direction
            ],
            "historical_is_anomaly": [
                dashboard_alert
            ],
            "dashboard_alert": [
                dashboard_alert
            ],
            "alert_status": [
                (
                    "dashboard_alert"
                    if dashboard_alert
                    else (
                        "normal"
                        if score_available
                        else "unavailable"
                    )
                )
            ],
        }
    )


def _forecast(
    *,
    dashboard_alert: bool = False,
    severity: str = "normal",
    error_direction: str = "on_forecast",
    score_available: bool = True,
) -> pd.DataFrame:
    """Create a minimal forecast anomaly record."""
    return pd.DataFrame(
        {
            "forecast_period": [
                "2026-01-01"
            ],
            "series_id": [
                "region_1_median_rent"
            ],
            "metric": [
                "median_rent"
            ],
            "model": [
                "ets_additive_damped"
            ],
            "origin": [
                "2025-12-01"
            ],
            "horizon_step": [
                1
            ],
            "predicted": [
                580.0
            ],
            "forecast_residual": [
                20.0
            ],
            "forecast_residual_pct": [
                3.45
            ],
            "forecast_error_direction": [
                error_direction
            ],
            "residual_median": [
                0.0
            ],
            "residual_mad": [
                5.0
            ],
            "residual_iqr": [
                8.0
            ],
            "forecast_residual_scale": [
                7.4
            ],
            "forecast_scale_method": [
                "mad"
            ],
            "forecast_anomaly_score": [
                3.0
                if dashboard_alert
                else 0.5
            ],
            "forecast_score_available": [
                score_available
            ],
            "forecast_severity": [
                severity
            ],
            "forecast_direction": [
                (
                    "high"
                    if dashboard_alert
                    else "normal"
                )
            ],
            "forecast_is_anomaly": [
                dashboard_alert
            ],
            "forecast_practical_significance_available": [
                True
            ],
            "forecast_practical_significance": [
                dashboard_alert
            ],
            "forecast_statistical_anomaly": [
                dashboard_alert
            ],
            "forecast_dashboard_alert": [
                dashboard_alert
            ],
            "forecast_alert_status": [
                (
                    "dashboard_alert"
                    if dashboard_alert
                    else (
                        "normal"
                        if score_available
                        else "unavailable"
                    )
                )
            ],
        }
    )


def test_normal_when_both_detectors_normal() -> None:
    result = consolidate_anomaly_outputs(
        _historical(),
        _forecast(),
    )

    row = result.iloc[0]

    assert (
        row["overall_status"]
        == "normal"
    )
    assert (
        row["overall_severity"]
        == "normal"
    )
    assert not bool(
        row["overall_dashboard_alert"]
    )


def test_historical_alert_status() -> None:
    result = consolidate_anomaly_outputs(
        _historical(
            dashboard_alert=True,
            severity="moderate",
            direction="high",
        ),
        _forecast(),
    )

    row = result.iloc[0]

    assert (
        row["overall_status"]
        == "historical_alert"
    )
    assert (
        row["overall_severity"]
        == "moderate"
    )
    assert (
        row["overall_direction"]
        == "high"
    )


def test_forecast_alert_status() -> None:
    result = consolidate_anomaly_outputs(
        _historical(),
        _forecast(
            dashboard_alert=True,
            severity="high",
            error_direction="below_forecast",
        ),
    )

    row = result.iloc[0]

    assert (
        row["overall_status"]
        == "forecast_alert"
    )
    assert (
        row["overall_severity"]
        == "high"
    )
    assert (
        row["overall_direction"]
        == "low"
    )


def test_confirmed_anomaly_same_direction() -> None:
    result = consolidate_anomaly_outputs(
        _historical(
            dashboard_alert=True,
            severity="moderate",
            direction="high",
        ),
        _forecast(
            dashboard_alert=True,
            severity="high",
            error_direction="above_forecast",
        ),
    )

    row = result.iloc[0]

    assert (
        row["overall_status"]
        == "confirmed_anomaly"
    )
    assert (
        row["overall_severity"]
        == "high"
    )
    assert (
        row["overall_direction"]
        == "high"
    )


def test_confirmed_anomaly_mixed_direction() -> None:
    result = consolidate_anomaly_outputs(
        _historical(
            dashboard_alert=True,
            severity="high",
            direction="high",
        ),
        _forecast(
            dashboard_alert=True,
            severity="moderate",
            error_direction="below_forecast",
        ),
    )

    row = result.iloc[0]

    assert (
        row["overall_status"]
        == "confirmed_anomaly"
    )
    assert (
        row["overall_direction"]
        == "mixed"
    )


def test_unavailable_when_both_detectors_unavailable() -> None:
    result = consolidate_anomaly_outputs(
        _historical(
            score_available=False,
        ),
        _forecast(
            score_available=False,
        ),
    )

    row = result.iloc[0]

    assert (
        row["overall_status"]
        == "unavailable"
    )
    assert (
        row["overall_severity"]
        == "unavailable"
    )
    assert (
        row["detector_coverage"]
        == "unavailable"
    )


def test_historical_only_can_still_be_normal() -> None:
    forecast = _forecast().iloc[0:0]

    result = consolidate_anomaly_outputs(
        _historical(),
        forecast,
    )

    row = result.iloc[0]

    assert (
        row["detector_coverage"]
        == "historical_only"
    )
    assert (
        row["overall_status"]
        == "normal"
    )


def test_forecast_fields_are_attached() -> None:
    result = consolidate_anomaly_outputs(
        _historical(),
        _forecast(),
    )

    row = result.iloc[0]

    assert bool(
        row["has_forecast_record"]
    )

    assert (
        row["forecast_model"]
        == "ets_additive_damped"
    )

    assert row["predicted"] == pytest.approx(
        580.0
    )


def test_duplicate_historical_records_are_rejected() -> None:
    historical = pd.concat(
        [
            _historical(),
            _historical(),
        ],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate historical",
    ):
        consolidate_anomaly_outputs(
            historical,
            _forecast(),
        )


def test_duplicate_forecast_records_are_rejected() -> None:
    forecast = pd.concat(
        [
            _forecast(),
            _forecast(),
        ],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate forecast",
    ):
        consolidate_anomaly_outputs(
            _historical(),
            forecast,
        )


def test_metric_mismatch_is_rejected() -> None:
    forecast = _forecast()
    forecast["metric"] = "bonds_lodged"

    with pytest.raises(
        ValueError,
        match="metric mismatch",
    ):
        consolidate_anomaly_outputs(
            _historical(),
            forecast,
        )
