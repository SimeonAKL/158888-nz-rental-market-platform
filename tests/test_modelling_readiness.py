"""Tests for modelling-readiness checks."""

import pandas as pd

from rmp.analytics.modelling_readiness import (
    build_modelling_readiness,
)


def make_inputs():
    """Create representative Phase 3 inputs."""

    dates = pd.date_range(
        "2015-01-01",
        periods=120,
        freq="MS",
    )

    panel = pd.DataFrame(
        {
            "period_date": list(dates) + list(dates),
            "series_id": (["series_a"] * 120 + ["series_b"] * 120),
            "metric": (["median_rent"] * 120 + ["bonds_lodged"] * 120),
            "value": list(range(120)) + list(range(120)),
        }
    )

    catalog = pd.DataFrame(
        {
            "series_id": [
                "series_a",
                "series_b",
            ],
            "n_observations": [
                120,
                120,
            ],
            "missing_months": [
                0,
                0,
            ],
            "continuous_months": [
                120,
                120,
            ],
            "eligible_for_forecasting": [
                True,
                True,
            ],
        }
    )

    quality = pd.DataFrame(
        {
            "series_id": [
                "series_a",
                "series_b",
            ],
            "status": [
                "PASS",
                "PASS",
            ],
        }
    )

    return panel, catalog, quality


def test_ready_dataset() -> None:
    """Eligible high-quality series should be modelling-ready."""

    panel, catalog, quality = make_inputs()

    result = build_modelling_readiness(
        panel,
        catalog,
        quality,
    )

    row = result.iloc[0]

    assert bool(row["dataset_ready"])

    assert row["n_series"] == 2
    assert row["complete_series"] == 2

    assert row["forecast_eligible_series"] == 2

    assert row["quality_pass_series"] == 2

    assert row["eligible_quality_pass_series"] == 2

    assert row["minimum_eligible_continuous_months"] == 120

    assert row["required_continuous_months"] == 77

    assert bool(row["rolling_origin_ready"])

    assert bool(row["feature_history_ready"])


def test_ineligible_series_does_not_block_ready_subset() -> None:
    """Analytics-only series should not block a valid forecast subset."""

    panel, catalog, quality = make_inputs()

    catalog.loc[
        catalog["series_id"] == "series_b",
        "missing_months",
    ] = 1

    catalog.loc[
        catalog["series_id"] == "series_b",
        "continuous_months",
    ] = 50

    catalog.loc[
        catalog["series_id"] == "series_b",
        "eligible_for_forecasting",
    ] = False

    result = build_modelling_readiness(
        panel,
        catalog,
        quality,
    )

    row = result.iloc[0]

    assert bool(row["dataset_ready"])

    assert row["n_series"] == 2
    assert row["complete_series"] == 1

    assert row["forecast_eligible_series"] == 1

    assert row["eligible_quality_pass_series"] == 1

    assert row["minimum_eligible_continuous_months"] == 120

    assert bool(row["rolling_origin_ready"])


def test_failed_quality_not_ready() -> None:
    """Failed quality in an eligible series should prevent readiness."""

    panel, catalog, quality = make_inputs()

    quality.loc[
        quality["series_id"] == "series_b",
        "status",
    ] = "FAIL"

    result = build_modelling_readiness(
        panel,
        catalog,
        quality,
    )

    row = result.iloc[0]

    assert not bool(row["dataset_ready"])

    assert row["forecast_eligible_series"] == 2

    assert row["eligible_quality_pass_series"] == 1


def test_no_forecast_eligible_series_not_ready() -> None:
    """Dataset should not be ready when no series can be forecast."""

    panel, catalog, quality = make_inputs()

    catalog["eligible_for_forecasting"] = False

    catalog["continuous_months"] = 50

    result = build_modelling_readiness(
        panel,
        catalog,
        quality,
    )

    row = result.iloc[0]

    assert not bool(row["dataset_ready"])

    assert row["forecast_eligible_series"] == 0

    assert row["minimum_eligible_continuous_months"] == 0

    assert not bool(row["rolling_origin_ready"])
