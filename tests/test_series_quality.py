"""Tests for Phase 3 time-series quality summaries."""

import pandas as pd

from rmp.analytics.series_quality import (
    build_quality_summary,
    build_series_catalog,
)


def make_panel() -> pd.DataFrame:
    """Create a small complete monthly panel."""

    dates = pd.date_range(
        "2020-01-01",
        periods=60,
        freq="MS",
    )

    return pd.DataFrame(
        {
            "period_date": dates,
            "series_id": ["region_2_median_rent"] * 60,
            "geography_level": ["region"] * 60,
            "location_id": [2] * 60,
            "location_name": ["Auckland Region"] * 60,
            "metric": ["median_rent"] * 60,
            "value": list(range(500, 560)),
            "source_snapshot_provisional": [True] * 60,
            "source_snapshot_id": [4] * 60,
        }
    )


def test_series_catalog_60_month_series_not_eligible() -> None:
    """A complete 60-month series is insufficient for full evaluation."""

    panel = make_panel()

    catalog = build_series_catalog(panel)

    row = catalog.iloc[0]

    assert row["n_observations"] == 60
    assert row["expected_observations"] == 60
    assert row["missing_months"] == 0
    assert row["null_values"] == 0
    assert row["completeness_rate"] == 1.0
    assert not bool(row["eligible_for_forecasting"])


def test_series_catalog_77_month_series_is_eligible() -> None:
    """A complete 77-month series should support full evaluation."""

    periods = pd.date_range(
        "2020-01-01",
        periods=77,
        freq="MS",
    )

    panel = pd.DataFrame(
        {
            "series_id": ["region_1_median_rent"] * len(periods),
            "period_date": periods,
            "geography_level": ["region"] * len(periods),
            "location_id": [1] * len(periods),
            "location_name": ["Test Region"] * len(periods),
            "metric": ["median_rent"] * len(periods),
            "value": [500.0] * len(periods),
            "source_snapshot_provisional": [False] * len(periods),
        }
    )

    catalog = build_series_catalog(panel)

    row = catalog.iloc[0]

    assert row["continuous_months"] == 77
    assert row["missing_months"] == 0
    assert bool(row["eligible_for_forecasting"])


def test_catalog_detects_missing_month() -> None:
    """Missing calendar months should be detected."""

    panel = make_panel().drop(index=10)

    catalog = build_series_catalog(panel)

    row = catalog.iloc[0]

    assert row["missing_months"] == 1
    assert not bool(row["eligible_for_forecasting"])


def test_quality_summary_passes_clean_series() -> None:
    """Clean values should receive PASS status."""

    panel = make_panel()

    summary = build_quality_summary(panel)

    row = summary.iloc[0]

    assert row["duplicate_periods"] == 0
    assert row["null_values"] == 0
    assert row["negative_values"] == 0
    assert row["zero_values"] == 0
    assert bool(row["source_snapshot_provisional"])
    assert "provisional_observations" not in summary.columns
    assert row["status"] == "PASS"


def test_quality_summary_detects_negative_value() -> None:
    """Negative values should fail validation."""

    panel = make_panel()

    panel.loc[
        panel.index[0],
        "value",
    ] = -1

    summary = build_quality_summary(panel)

    row = summary.iloc[0]

    assert row["negative_values"] == 1
    assert row["status"] == "FAIL"
