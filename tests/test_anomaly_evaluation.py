"""Tests for anomaly-detector evaluation evidence."""

from __future__ import annotations

import numpy as np
import pandas as pd

from rmp.anomaly.evaluation import (
    evaluate_historical_threshold_sensitivity,
    evaluate_synthetic_historical_injection,
    evaluate_transition_period,
    transition_period_mask,
)


def test_synthetic_injection_recovers_both_shocks() -> None:
    result = evaluate_synthetic_historical_injection()

    assert len(result) == 2
    assert result["passed"].all()
    assert result["detected_anomaly"].all()
    assert set(result["observed_direction"]) == {
        "high",
        "low",
    }
    assert np.isfinite(result["score"]).all()


def test_threshold_sensitivity_is_valid() -> None:
    result = evaluate_historical_threshold_sensitivity()

    assert len(result) == 5
    assert result["threshold"].tolist() == [
        2.0,
        2.5,
        3.0,
        3.5,
        4.0,
    ]

    assert result["injection_recovery_rate"].between(
        0.0,
        1.0,
    ).all()

    assert result["background_alert_rate"].between(
        0.0,
        1.0,
    ).all()

    assert result["background_alerts"].is_monotonic_decreasing


def test_transition_period_mask_uses_documented_boundaries() -> None:
    dates = pd.Series(
        pd.to_datetime(
            [
                "2024-12-01",
                "2025-01-01",
                "2026-07-01",
                "2026-12-01",
                "2027-01-01",
            ]
        )
    )

    result = transition_period_mask(dates)

    assert result.tolist() == [
        False,
        True,
        True,
        True,
        False,
    ]


def test_transition_evaluation_uses_equal_length_windows() -> None:
    dates = pd.date_range(
        "2023-06-01",
        "2026-07-01",
        freq="MS",
    )

    frame = pd.DataFrame(
        {
            "period_date": dates,
            "historical_score_available": True,
            "historical_is_anomaly": False,
            "dashboard_alert": False,
        }
    )

    frame.loc[
        frame["period_date"].eq(pd.Timestamp("2024-06-01")),
        "historical_is_anomaly",
    ] = True

    frame.loc[
        frame["period_date"].eq(pd.Timestamp("2025-06-01")),
        "historical_is_anomaly",
    ] = True

    result = evaluate_transition_period(frame)

    assert len(result) == 2
    assert result["months"].tolist() == [
        19,
        19,
    ]
    assert result["rows"].tolist() == [
        19,
        19,
    ]

    assert result["period"].tolist() == [
        "pre_transition_comparison",
        "bond_hub_transition",
    ]

    assert result["start_date"].tolist() == [
        pd.Timestamp("2023-06-01"),
        pd.Timestamp("2025-01-01"),
    ]

    assert result["end_date"].tolist() == [
        pd.Timestamp("2024-12-01"),
        pd.Timestamp("2026-07-01"),
    ]
