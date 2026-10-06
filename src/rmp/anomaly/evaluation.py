"""Evaluation utilities for anomaly-detector performance evidence."""

from __future__ import annotations

import pandas as pd

BOND_HUB_TRANSITION_START = pd.Timestamp("2025-01-01")
BOND_HUB_TRANSITION_END = pd.Timestamp("2026-12-31")


def transition_period_mask(
    dates: pd.Series,
) -> pd.Series:
    """Return rows within the documented 2025-2026 Bond Hub transition period."""
    values = pd.to_datetime(dates)

    return values.between(
        BOND_HUB_TRANSITION_START,
        BOND_HUB_TRANSITION_END,
        inclusive="both",
    )


def build_synthetic_historical_panel(
    *,
    shock: float,
    n_years: int = 8,
) -> pd.DataFrame:
    """Build a deterministic monthly series with one injected final shock."""
    periods = pd.date_range(
        "2018-01-01",
        periods=n_years * 12,
        freq="MS",
    )

    values: list[float] = []

    for index, period in enumerate(periods):
        seasonal_component = float(period.month)
        trend_component = index * 0.5

        # Add deterministic non-seasonal variation so year-on-year
        # changes retain a realistic, non-degenerate robust scale.
        irregular_pattern = (
            0.0,
            3.0,
            -2.0,
            4.0,
            -1.0,
            2.0,
            -3.0,
        )
        irregular_component = irregular_pattern[index % len(irregular_pattern)]

        values.append(
            500.0
            + seasonal_component
            + trend_component
            + irregular_component
        )

    values[-1] += shock

    return pd.DataFrame(
        {
            "period_date": periods,
            "series_id": ["synthetic_series"] * len(periods),
            "metric": ["median_rent"] * len(periods),
            "geography_level": ["synthetic"] * len(periods),
            "location_id": ["synthetic"] * len(periods),
            "location_name": ["Synthetic Series"] * len(periods),
            "value": values,
        }
    )


def evaluate_synthetic_historical_injection() -> pd.DataFrame:
    """Evaluate recovery of deterministic positive and negative injected shocks."""
    from rmp.anomaly.historical import detect_historical_anomalies

    scenarios = [
        ("positive_shock", 150.0),
        ("negative_shock", -150.0),
    ]

    records: list[dict[str, object]] = []

    for scenario, shock in scenarios:
        panel = build_synthetic_historical_panel(
            shock=shock,
        )

        result = detect_historical_anomalies(panel)

        final_row = result.iloc[-1]

        historical_scale = float(final_row["historical_scale"])

        if historical_scale <= 1e-6:
            raise ValueError(
                "Synthetic evaluation produced a degenerate historical scale."
            )

        expected_direction = "high" if shock > 0 else "low"

        detected = bool(final_row["historical_is_anomaly"])
        observed_direction = str(final_row["historical_direction"])

        records.append(
            {
                "evaluation": "synthetic_injection",
                "scenario": scenario,
                "shock_value": shock,
                "expected_anomaly": True,
                "detected_anomaly": detected,
                "expected_direction": expected_direction,
                "observed_direction": observed_direction,
                "severity": str(final_row["historical_severity"]),
                "score": float(final_row["historical_score"]),
                "passed": (
                    detected
                    and observed_direction == expected_direction
                ),
            }
        )

    return pd.DataFrame(records)


def evaluate_historical_threshold_sensitivity() -> pd.DataFrame:
    """Evaluate injection recovery and background alert rates across thresholds."""
    from rmp.anomaly.historical import detect_historical_anomalies

    thresholds = (
        2.0,
        2.5,
        3.0,
        3.5,
        4.0,
    )

    clean_result = detect_historical_anomalies(
        build_synthetic_historical_panel(shock=0.0)
    )

    clean_scores = (
        clean_result.loc[
            clean_result["historical_score_available"],
            "historical_score",
        ]
        .abs()
        .dropna()
    )

    injected_scores: list[float] = []

    for shock in (150.0, -150.0):
        injected_result = detect_historical_anomalies(
            build_synthetic_historical_panel(shock=shock)
        )

        injected_score = float(
            injected_result.iloc[-1]["historical_score"]
        )

        injected_scores.append(abs(injected_score))

    records: list[dict[str, object]] = []

    for threshold in thresholds:
        recovered = sum(
            score >= threshold
            for score in injected_scores
        )

        background_alerts = int(
            clean_scores.ge(threshold).sum()
        )

        background_count = len(clean_scores)

        background_alert_rate = (
            background_alerts / background_count
            if background_count
            else 0.0
        )

        records.append(
            {
                "evaluation": "threshold_sensitivity",
                "threshold": threshold,
                "injected_cases": len(injected_scores),
                "injected_recovered": recovered,
                "injection_recovery_rate": (
                    recovered / len(injected_scores)
                ),
                "background_scored_observations": background_count,
                "background_alerts": background_alerts,
                "background_alert_rate": background_alert_rate,
            }
        )

    return pd.DataFrame(records)


def evaluate_transition_period(
    historical_anomalies: pd.DataFrame,
) -> pd.DataFrame:
    """Compare anomaly-alert rates during the documented transition period."""
    required_columns = {
        "period_date",
        "historical_score_available",
        "historical_is_anomaly",
        "dashboard_alert",
    }

    missing = required_columns.difference(historical_anomalies.columns)

    if missing:
        raise ValueError(
            "Missing required transition-evaluation columns: "
            + ", ".join(sorted(missing))
        )

    df = historical_anomalies.copy()
    df["period_date"] = pd.to_datetime(df["period_date"])

    dataset_end = df["period_date"].max()
    transition_end = min(
        dataset_end,
        BOND_HUB_TRANSITION_END,
    )

    transition_months = (
        (transition_end.year - BOND_HUB_TRANSITION_START.year) * 12
        + transition_end.month
        - BOND_HUB_TRANSITION_START.month
        + 1
    )

    comparison_end = BOND_HUB_TRANSITION_START - pd.offsets.MonthBegin(1)
    comparison_start = (
        comparison_end
        - pd.offsets.MonthBegin(transition_months - 1)
    )

    periods = (
        (
            "pre_transition_comparison",
            comparison_start,
            comparison_end,
        ),
        (
            "bond_hub_transition",
            BOND_HUB_TRANSITION_START,
            transition_end,
        ),
    )

    records: list[dict[str, object]] = []

    for period_name, start_date, end_date in periods:
        subset = df.loc[
            df["period_date"].between(
                start_date,
                end_date,
                inclusive="both",
            )
        ]

        scored = subset[
            subset["historical_score_available"]
            .fillna(False)
            .astype(bool)
        ]

        scored_count = len(scored)

        statistical_alerts = int(
            scored["historical_is_anomaly"]
            .fillna(False)
            .sum()
        )

        dashboard_alerts = int(
            subset["dashboard_alert"]
            .fillna(False)
            .sum()
        )

        records.append(
            {
                "evaluation": "transition_period",
                "period": period_name,
                "start_date": start_date,
                "end_date": end_date,
                "months": transition_months,
                "rows": len(subset),
                "scored_observations": scored_count,
                "statistical_anomalies": statistical_alerts,
                "statistical_anomaly_rate": (
                    statistical_alerts / scored_count
                    if scored_count
                    else 0.0
                ),
                "dashboard_alerts": dashboard_alerts,
                "dashboard_alert_rate": (
                    dashboard_alerts / scored_count
                    if scored_count
                    else 0.0
                ),
            }
        )

    return pd.DataFrame(records)


def validate_anomaly_evaluation_summary(
    summary: pd.DataFrame,
) -> pd.DataFrame:
    """Validate the unified anomaly-evaluation evidence output."""
    required_columns = {
        "evaluation_group",
        "evaluation",
    }

    missing = required_columns.difference(summary.columns)

    if missing:
        raise ValueError(
            "Missing required anomaly-evaluation columns: "
            + ", ".join(sorted(missing))
        )

    expected_groups = {
        "synthetic_injection",
        "threshold_sensitivity",
        "transition_period",
    }

    observed_groups = set(
        summary["evaluation_group"]
        .dropna()
        .astype(str)
    )

    if observed_groups != expected_groups:
        raise ValueError(
            "Unexpected anomaly-evaluation groups: "
            f"{sorted(observed_groups)}"
        )

    synthetic = summary.loc[
        summary["evaluation_group"].eq(
            "synthetic_injection"
        )
    ]

    if len(synthetic) != 2:
        raise ValueError(
            "Synthetic-injection evaluation must contain exactly 2 rows."
        )

    if not synthetic["passed"].fillna(False).astype(bool).all():
        raise ValueError(
            "Synthetic-injection evaluation contains a failed scenario."
        )

    sensitivity = summary.loc[
        summary["evaluation_group"].eq(
            "threshold_sensitivity"
        )
    ].sort_values("threshold")

    if len(sensitivity) != 5:
        raise ValueError(
            "Threshold-sensitivity evaluation must contain exactly 5 rows."
        )

    if not sensitivity["injection_recovery_rate"].between(
        0.0,
        1.0,
    ).all():
        raise ValueError(
            "Invalid injection recovery rate."
        )

    if not sensitivity["background_alert_rate"].between(
        0.0,
        1.0,
    ).all():
        raise ValueError(
            "Invalid background alert rate."
        )

    transition = summary.loc[
        summary["evaluation_group"].eq(
            "transition_period"
        )
    ]

    if len(transition) != 2:
        raise ValueError(
            "Transition-period evaluation must contain exactly 2 rows."
        )

    if transition["months"].nunique() != 1:
        raise ValueError(
            "Transition and comparison windows must have equal length."
        )

    return summary
