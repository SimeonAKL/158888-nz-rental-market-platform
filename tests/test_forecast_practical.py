"""Tests for forecast practical significance."""

from __future__ import annotations

import numpy as np
import pandas as pd

from rmp.anomaly.forecast_practical import (
    add_forecast_practical_significance,
)


def _row(
    *,
    metric: str,
    residual: float,
    residual_pct: float,
    anomaly: bool = True,
    score_available: bool = True,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "metric": [metric],
            "forecast_residual": [residual],
            "forecast_residual_pct": [residual_pct],
            "forecast_is_anomaly": [anomaly],
            "forecast_score_available": [score_available],
        }
    )


def test_rent_requires_absolute_and_percentage() -> None:
    frame = _row(
        metric="median_rent",
        residual=15.0,
        residual_pct=2.0,
    )

    result = add_forecast_practical_significance(frame)

    assert bool(result.iloc[0]["forecast_practical_significance"])


def test_small_rent_residual_is_filtered() -> None:
    frame = _row(
        metric="median_rent",
        residual=10.0,
        residual_pct=1.5,
    )

    result = add_forecast_practical_significance(frame)

    assert not bool(result.iloc[0]["forecast_dashboard_alert"])

    assert result.iloc[0]["forecast_alert_status"] == "statistical_only"


def test_rent_absolute_only_is_not_enough() -> None:
    frame = _row(
        metric="median_rent",
        residual=30.0,
        residual_pct=1.0,
    )

    result = add_forecast_practical_significance(frame)

    assert not bool(result.iloc[0]["forecast_practical_significance"])


def test_bonds_absolute_threshold_is_enough() -> None:
    frame = _row(
        metric="bonds_lodged",
        residual=60.0,
        residual_pct=5.0,
    )

    result = add_forecast_practical_significance(frame)

    assert bool(result.iloc[0]["forecast_practical_significance"])


def test_bonds_percentage_threshold_is_enough() -> None:
    frame = _row(
        metric="bonds_lodged",
        residual=20.0,
        residual_pct=15.0,
    )

    result = add_forecast_practical_significance(frame)

    assert bool(result.iloc[0]["forecast_practical_significance"])


def test_bonds_below_both_thresholds_is_filtered() -> None:
    frame = _row(
        metric="bonds_lodged",
        residual=40.0,
        residual_pct=8.0,
    )

    result = add_forecast_practical_significance(frame)

    assert not bool(result.iloc[0]["forecast_practical_significance"])


def test_practical_movement_without_statistical_anomaly_is_normal() -> None:
    frame = _row(
        metric="bonds_lodged",
        residual=500.0,
        residual_pct=25.0,
        anomaly=False,
    )

    result = add_forecast_practical_significance(frame)

    assert not bool(result.iloc[0]["forecast_dashboard_alert"])

    assert result.iloc[0]["forecast_alert_status"] == "normal"


def test_unavailable_score_remains_unavailable() -> None:
    frame = _row(
        metric="median_rent",
        residual=50.0,
        residual_pct=10.0,
        anomaly=False,
        score_available=False,
    )

    result = add_forecast_practical_significance(frame)

    assert result.iloc[0]["forecast_alert_status"] == "unavailable"


def test_missing_residual_is_unavailable() -> None:
    frame = _row(
        metric="median_rent",
        residual=np.nan,
        residual_pct=np.nan,
    )

    result = add_forecast_practical_significance(frame)

    assert result.iloc[0]["forecast_alert_status"] == "unavailable"
