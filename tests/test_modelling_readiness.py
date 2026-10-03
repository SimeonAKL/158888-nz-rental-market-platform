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
            "period_date": list(dates)
            + list(dates),
            "series_id": (
                ["series_a"] * 120
                + ["series_b"] * 120
            ),
            "metric": (
                ["median_rent"] * 120
                + ["bonds_lodged"] * 120
            ),
            "value": list(range(120))
            + list(range(120)),
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
    """Complete high-quality series should be modelling-ready."""

    panel, catalog, quality = make_inputs()

    result = build_modelling_readiness(
        panel,
        catalog,
        quality,
    )

    row = result.iloc[0]

    assert bool(
        row["dataset_ready"]
    )

    assert row["n_series"] == 2
    assert row["complete_series"] == 2
    assert (
        row["forecast_eligible_series"]
        == 2
    )
    assert row["quality_pass_series"] == 2
    assert bool(
        row["rolling_origin_ready"]
    )
    assert bool(
        row["feature_history_ready"]
    )


def test_incomplete_series_not_ready() -> None:
    """Missing months should prevent readiness."""

    panel, catalog, quality = make_inputs()

    catalog.loc[
        catalog["series_id"] == "series_b",
        "missing_months",
    ] = 1

    catalog.loc[
        catalog["series_id"] == "series_b",
        "eligible_for_forecasting",
    ] = False

    result = build_modelling_readiness(
        panel,
        catalog,
        quality,
    )

    assert not bool(
        result.iloc[0]["dataset_ready"]
    )


def test_failed_quality_not_ready() -> None:
    """A failed quality series should prevent readiness."""

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

    assert not bool(
        result.iloc[0]["dataset_ready"]
    )
