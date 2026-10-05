"""Final validation and metadata summaries for Phase 5A anomaly outputs."""

from __future__ import annotations

import pandas as pd

from rmp.anomaly.forecast import (
    DEFAULT_HORIZON,
    DEFAULT_MIN_PRIOR_RESIDUALS,
)
from rmp.anomaly.forecast import (
    HIGH_THRESHOLD as FORECAST_HIGH_THRESHOLD,
)
from rmp.anomaly.forecast import (
    MODERATE_THRESHOLD as FORECAST_MODERATE_THRESHOLD,
)
from rmp.anomaly.forecast_practical import (
    FORECAST_BONDS_ABS_THRESHOLD,
    FORECAST_BONDS_PCT_THRESHOLD,
    FORECAST_RENT_ABS_THRESHOLD,
    FORECAST_RENT_PCT_THRESHOLD,
)
from rmp.anomaly.historical import (
    DEFAULT_BASELINE_WINDOW,
    DEFAULT_MIN_PERIODS,
    DEFAULT_SEASONAL_LAG,
)
from rmp.anomaly.historical import (
    HIGH_THRESHOLD as HISTORICAL_HIGH_THRESHOLD,
)
from rmp.anomaly.historical import (
    MODERATE_THRESHOLD as HISTORICAL_MODERATE_THRESHOLD,
)
from rmp.anomaly.practical import (
    PRACTICAL_THRESHOLDS,
)

ALLOWED_OVERALL_STATUS = {
    "normal",
    "historical_alert",
    "forecast_alert",
    "confirmed_anomaly",
    "unavailable",
}

ALLOWED_SEVERITY = {
    "normal",
    "moderate",
    "high",
    "unavailable",
}

ALLOWED_DIRECTION = {
    "normal",
    "high",
    "low",
    "mixed",
}

ALLOWED_COVERAGE = {
    "historical_only",
    "forecast_only",
    "both",
    "unavailable",
}


def _check_record(
    *,
    name: str,
    passed: bool,
    observed: object,
    expected: object,
    details: str,
) -> dict[str, object]:
    """Create one validation summary record."""
    return {
        "check_name": name,
        "passed": bool(passed),
        "observed": observed,
        "expected": expected,
        "details": details,
    }


def validate_anomaly_summary(
    summary: pd.DataFrame,
) -> pd.DataFrame:
    """Validate consolidated anomaly output invariants.

    The checks focus on structural and logical consistency. They do not
    recalibrate anomaly thresholds or alter any anomaly classifications.

    Returns
    -------
    pandas.DataFrame
        One row per validation check.

    Raises
    ------
    ValueError
        If one or more validation checks fail.
    """
    required_columns = {
        "period_date",
        "series_id",
        "metric",
        "value",
        "historical_detector_available",
        "forecast_detector_available",
        "historical_dashboard_alert",
        "forecast_dashboard_alert",
        "overall_dashboard_alert",
        "overall_status",
        "overall_severity",
        "overall_direction",
        "detector_coverage",
        "has_forecast_record",
    }

    missing = required_columns.difference(summary.columns)

    if missing:
        raise ValueError("Missing required anomaly summary columns: " + ", ".join(sorted(missing)))

    df = summary.copy()

    df["period_date"] = pd.to_datetime(df["period_date"])

    historical_available = df["historical_detector_available"].fillna(False).astype(bool)

    forecast_available = df["forecast_detector_available"].fillna(False).astype(bool)

    historical_alert = df["historical_dashboard_alert"].fillna(False).astype(bool)

    forecast_alert = df["forecast_dashboard_alert"].fillna(False).astype(bool)

    overall_alert = df["overall_dashboard_alert"].fillna(False).astype(bool)

    records: list[dict[str, object]] = []

    duplicate_count = int(
        df.duplicated(
            subset=[
                "series_id",
                "period_date",
            ],
            keep=False,
        ).sum()
    )

    records.append(
        _check_record(
            name="unique_series_period",
            passed=duplicate_count == 0,
            observed=duplicate_count,
            expected=0,
            details=("Each series-period must appear exactly once."),
        )
    )

    invalid_status = int((~df["overall_status"].isin(ALLOWED_OVERALL_STATUS)).sum())

    records.append(
        _check_record(
            name="valid_overall_status",
            passed=invalid_status == 0,
            observed=invalid_status,
            expected=0,
            details=("Overall status must use the approved status vocabulary."),
        )
    )

    invalid_severity = int((~df["overall_severity"].isin(ALLOWED_SEVERITY)).sum())

    records.append(
        _check_record(
            name="valid_overall_severity",
            passed=invalid_severity == 0,
            observed=invalid_severity,
            expected=0,
            details=("Overall severity must be normal, moderate, high, or unavailable."),
        )
    )

    invalid_direction = int((~df["overall_direction"].isin(ALLOWED_DIRECTION)).sum())

    records.append(
        _check_record(
            name="valid_overall_direction",
            passed=invalid_direction == 0,
            observed=invalid_direction,
            expected=0,
            details=("Overall direction must use the approved direction vocabulary."),
        )
    )

    invalid_coverage = int((~df["detector_coverage"].isin(ALLOWED_COVERAGE)).sum())

    records.append(
        _check_record(
            name="valid_detector_coverage",
            passed=invalid_coverage == 0,
            observed=invalid_coverage,
            expected=0,
            details=("Detector coverage must use the approved coverage vocabulary."),
        )
    )

    expected_overall_alert = historical_alert | forecast_alert

    alert_mismatch = int((overall_alert != expected_overall_alert).sum())

    records.append(
        _check_record(
            name="overall_alert_union",
            passed=alert_mismatch == 0,
            observed=alert_mismatch,
            expected=0,
            details=("Overall dashboard alert must equal historical OR forecast alert."),
        )
    )

    confirmed_expected = historical_alert & forecast_alert

    confirmed_actual = df["overall_status"] == "confirmed_anomaly"

    confirmed_mismatch = int((confirmed_actual != confirmed_expected).sum())

    records.append(
        _check_record(
            name="confirmed_anomaly_logic",
            passed=confirmed_mismatch == 0,
            observed=confirmed_mismatch,
            expected=0,
            details=("Confirmed anomaly requires both dashboard alert types."),
        )
    )

    historical_only_status = df["overall_status"] == "historical_alert"

    historical_only_expected = historical_alert & ~forecast_alert

    historical_status_mismatch = int((historical_only_status != historical_only_expected).sum())

    records.append(
        _check_record(
            name="historical_alert_logic",
            passed=historical_status_mismatch == 0,
            observed=historical_status_mismatch,
            expected=0,
            details=("Historical alert status requires historical alert only."),
        )
    )

    forecast_only_status = df["overall_status"] == "forecast_alert"

    forecast_only_expected = forecast_alert & ~historical_alert

    forecast_status_mismatch = int((forecast_only_status != forecast_only_expected).sum())

    records.append(
        _check_record(
            name="forecast_alert_logic",
            passed=forecast_status_mismatch == 0,
            observed=forecast_status_mismatch,
            expected=0,
            details=("Forecast alert status requires forecast alert only."),
        )
    )

    no_detector_available = ~historical_available & ~forecast_available

    unavailable_status = df["overall_status"] == "unavailable"

    unavailable_mismatch = int((unavailable_status != no_detector_available).sum())

    records.append(
        _check_record(
            name="unavailable_status_logic",
            passed=unavailable_mismatch == 0,
            observed=unavailable_mismatch,
            expected=0,
            details=("Overall status is unavailable only when neither detector is available."),
        )
    )

    normal_expected = (
        (historical_available | forecast_available) & ~historical_alert & ~forecast_alert
    )

    normal_actual = df["overall_status"] == "normal"

    normal_mismatch = int((normal_actual != normal_expected).sum())

    records.append(
        _check_record(
            name="normal_status_logic",
            passed=normal_mismatch == 0,
            observed=normal_mismatch,
            expected=0,
            details=("Normal requires detector coverage and no active dashboard alert."),
        )
    )

    expected_coverage = pd.Series(
        "unavailable",
        index=df.index,
        dtype="object",
    )

    expected_coverage.loc[historical_available & ~forecast_available] = "historical_only"

    expected_coverage.loc[~historical_available & forecast_available] = "forecast_only"

    expected_coverage.loc[historical_available & forecast_available] = "both"

    coverage_mismatch = int((df["detector_coverage"] != expected_coverage).sum())

    records.append(
        _check_record(
            name="detector_coverage_logic",
            passed=coverage_mismatch == 0,
            observed=coverage_mismatch,
            expected=0,
            details=("Detector coverage must match historical and forecast availability."),
        )
    )

    alert_severity_invalid = int(
        (
            overall_alert
            & ~df["overall_severity"].isin(
                {
                    "moderate",
                    "high",
                }
            )
        ).sum()
    )

    records.append(
        _check_record(
            name="alert_severity_consistency",
            passed=alert_severity_invalid == 0,
            observed=alert_severity_invalid,
            expected=0,
            details=("Every dashboard alert must have moderate or high severity."),
        )
    )

    non_alert_severity_invalid = int(
        ((df["overall_status"] == "normal") & df["overall_severity"].ne("normal")).sum()
    )

    records.append(
        _check_record(
            name="normal_severity_consistency",
            passed=non_alert_severity_invalid == 0,
            observed=non_alert_severity_invalid,
            expected=0,
            details=("Normal observations must have normal overall severity."),
        )
    )

    unavailable_severity_invalid = int(
        ((df["overall_status"] == "unavailable") & df["overall_severity"].ne("unavailable")).sum()
    )

    records.append(
        _check_record(
            name="unavailable_severity_consistency",
            passed=unavailable_severity_invalid == 0,
            observed=unavailable_severity_invalid,
            expected=0,
            details=("Unavailable observations must have unavailable overall severity."),
        )
    )

    forecast_without_record = int(
        (forecast_available & ~df["has_forecast_record"].fillna(False).astype(bool)).sum()
    )

    records.append(
        _check_record(
            name="forecast_availability_requires_record",
            passed=forecast_without_record == 0,
            observed=forecast_without_record,
            expected=0,
            details=("Forecast detector availability requires a matched forecast record."),
        )
    )

    validation = pd.DataFrame(records)

    if not validation["passed"].all():
        failed = validation.loc[
            ~validation["passed"],
            "check_name",
        ].tolist()

        raise ValueError("Anomaly summary validation failed: " + ", ".join(failed))

    return validation


def build_anomaly_metadata(
    summary: pd.DataFrame,
) -> pd.DataFrame:
    """Build reproducibility metadata for Phase 5A."""
    df = summary.copy()

    df["period_date"] = pd.to_datetime(df["period_date"])

    historical_alerts = int(df["historical_dashboard_alert"].sum())

    forecast_alerts = int(df["forecast_dashboard_alert"].sum())

    overall_alerts = int(df["overall_dashboard_alert"].sum())

    confirmed = int((df["overall_status"] == "confirmed_anomaly").sum())

    historical_rent = PRACTICAL_THRESHOLDS["median_rent"]

    historical_bonds = PRACTICAL_THRESHOLDS["bonds_lodged"]

    metadata: list[tuple[str, str, object]] = [
        (
            "dataset",
            "rows",
            len(df),
        ),
        (
            "dataset",
            "series",
            df["series_id"].nunique(),
        ),
        (
            "dataset",
            "periods",
            df["period_date"].nunique(),
        ),
        (
            "dataset",
            "start_period",
            df["period_date"].min().date(),
        ),
        (
            "dataset",
            "end_period",
            df["period_date"].max().date(),
        ),
        (
            "dataset",
            "forecast_records",
            int(df["has_forecast_record"].sum()),
        ),
        (
            "historical_detector",
            "seasonal_lag",
            DEFAULT_SEASONAL_LAG,
        ),
        (
            "historical_detector",
            "baseline_window",
            DEFAULT_BASELINE_WINDOW,
        ),
        (
            "historical_detector",
            "minimum_baseline_observations",
            DEFAULT_MIN_PERIODS,
        ),
        (
            "historical_detector",
            "moderate_threshold",
            HISTORICAL_MODERATE_THRESHOLD,
        ),
        (
            "historical_detector",
            "high_threshold",
            HISTORICAL_HIGH_THRESHOLD,
        ),
        (
            "historical_practical",
            "median_rent_absolute_threshold",
            historical_rent.minimum_absolute_deviation,
        ),
        (
            "historical_practical",
            "median_rent_percentage_threshold",
            historical_rent.minimum_percentage_deviation,
        ),
        (
            "historical_practical",
            "bonds_absolute_threshold",
            historical_bonds.minimum_absolute_deviation,
        ),
        (
            "historical_practical",
            "bonds_percentage_threshold",
            historical_bonds.minimum_percentage_deviation,
        ),
        (
            "forecast_detector",
            "horizon",
            DEFAULT_HORIZON,
        ),
        (
            "forecast_detector",
            "minimum_prior_residuals",
            DEFAULT_MIN_PRIOR_RESIDUALS,
        ),
        (
            "forecast_detector",
            "moderate_threshold",
            FORECAST_MODERATE_THRESHOLD,
        ),
        (
            "forecast_detector",
            "high_threshold",
            FORECAST_HIGH_THRESHOLD,
        ),
        (
            "forecast_practical",
            "median_rent_absolute_threshold",
            FORECAST_RENT_ABS_THRESHOLD,
        ),
        (
            "forecast_practical",
            "median_rent_percentage_threshold",
            FORECAST_RENT_PCT_THRESHOLD,
        ),
        (
            "forecast_practical",
            "bonds_absolute_threshold",
            FORECAST_BONDS_ABS_THRESHOLD,
        ),
        (
            "forecast_practical",
            "bonds_percentage_threshold",
            FORECAST_BONDS_PCT_THRESHOLD,
        ),
        (
            "outputs",
            "historical_dashboard_alerts",
            historical_alerts,
        ),
        (
            "outputs",
            "forecast_dashboard_alerts",
            forecast_alerts,
        ),
        (
            "outputs",
            "confirmed_anomalies",
            confirmed,
        ),
        (
            "outputs",
            "overall_dashboard_alerts",
            overall_alerts,
        ),
        (
            "outputs",
            "overall_high",
            int((df["overall_severity"] == "high").sum()),
        ),
        (
            "outputs",
            "overall_moderate",
            int((df["overall_severity"] == "moderate").sum()),
        ),
        (
            "outputs",
            "overall_unavailable",
            int((df["overall_status"] == "unavailable").sum()),
        ),
    ]

    return pd.DataFrame(
        metadata,
        columns=[
            "category",
            "item",
            "value",
        ],
    )
