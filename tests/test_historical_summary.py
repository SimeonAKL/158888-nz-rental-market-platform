"""Tests for historical modelling-readiness summaries."""

import pandas as pd
import pytest

from rmp.analytics.historical_summary import (
    build_historical_summary,
    build_monthly_seasonality_summary,
    build_recent_history_summary,
)


@pytest.fixture
def sample_panel() -> pd.DataFrame:
    """Create a deterministic monthly forecasting series."""

    dates = pd.date_range(
        "2020-01-01",
        periods=24,
        freq="MS",
    )

    values = list(
        range(100, 124)
    )

    return pd.DataFrame(
        {
            "period_date": dates,
            "series_id": [
                "region_2_median_rent"
            ]
            * 24,
            "geography_level": [
                "region"
            ]
            * 24,
            "location_id": [2] * 24,
            "location_name": [
                "Auckland Region"
            ]
            * 24,
            "metric": [
                "median_rent"
            ]
            * 24,
            "value": values,
            "is_provisional": [
                True
            ]
            * 24,
            "source_snapshot_id": [
                4
            ]
            * 24,
        }
    )


def test_build_historical_summary(
    sample_panel: pd.DataFrame,
) -> None:
    """Historical summary should calculate core statistics."""

    summary = build_historical_summary(
        sample_panel
    )

    assert len(summary) == 1

    row = summary.iloc[0]

    assert row["series_id"] == (
        "region_2_median_rent"
    )

    assert row["n_observations"] == 24

    assert row["latest_value"] == pytest.approx(
        123.0
    )

    assert row["change_1m"] == pytest.approx(
        1.0
    )

    assert row["change_12m"] == pytest.approx(
        12.0
    )

    expected_pct_change = (
        (123 - 111)
        / 111
        * 100
    )

    assert row["pct_change_12m"] == pytest.approx(
        expected_pct_change
    )


def test_historical_summary_mean_and_median(
    sample_panel: pd.DataFrame,
) -> None:
    """Mean and median should match source values."""

    summary = build_historical_summary(
        sample_panel
    )

    row = summary.iloc[0]

    expected_mean = sample_panel[
        "value"
    ].mean()

    expected_median = sample_panel[
        "value"
    ].median()

    assert row["mean"] == pytest.approx(
        expected_mean
    )

    assert row["median"] == pytest.approx(
        expected_median
    )


def test_monthly_seasonality_summary(
    sample_panel: pd.DataFrame,
) -> None:
    """Seasonality summary should produce one row per month."""

    summary = (
        build_monthly_seasonality_summary(
            sample_panel
        )
    )

    assert len(summary) == 12

    january = summary.loc[
        summary["month"] == 1
    ].iloc[0]

    assert january[
        "n_observations"
    ] == 2

    assert january[
        "mean_value"
    ] == pytest.approx(
        (100 + 112)
        / 2
    )


def test_recent_history_summary(
    sample_panel: pd.DataFrame,
) -> None:
    """Recent summary should use only the requested window."""

    summary = build_recent_history_summary(
        sample_panel,
        recent_months=6,
    )

    row = summary.iloc[0]

    assert row[
        "recent_observations"
    ] == 6

    assert row[
        "recent_start_period"
    ] == pd.Timestamp(
        "2021-07-01"
    )

    assert row[
        "recent_end_period"
    ] == pd.Timestamp(
        "2021-12-01"
    )

    assert row[
        "recent_mean"
    ] == pytest.approx(
        sum(
            range(118, 124)
        )
        / 6
    )


def test_recent_history_rejects_invalid_months(
    sample_panel: pd.DataFrame,
) -> None:
    """Recent-month window must be positive."""

    with pytest.raises(
        ValueError,
        match="at least 1",
    ):
        build_recent_history_summary(
            sample_panel,
            recent_months=0,
        )


def test_summary_rejects_missing_columns(
    sample_panel: pd.DataFrame,
) -> None:
    """Missing required input columns should fail."""

    invalid = sample_panel.drop(
        columns=["metric"]
    )

    with pytest.raises(
        ValueError,
        match="Missing required",
    ):
        build_historical_summary(
            invalid
        )
