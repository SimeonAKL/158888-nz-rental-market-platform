"""Tests for leakage-safe forecasting features."""

import pandas as pd
import pytest

from rmp.forecasting.features import (
    add_calendar_features,
    add_lag_features,
    add_rolling_features,
    build_forecasting_features,
)


@pytest.fixture
def sample_series() -> pd.DataFrame:
    """Create a deterministic monthly series."""

    dates = pd.date_range(
        "2020-01-01",
        periods=15,
        freq="MS",
    )

    return pd.DataFrame(
        {
            "period_date": dates,
            "series_id": ["region_2_median_rent"] * 15,
            "value": list(range(1, 16)),
        }
    )


def test_calendar_features(
    sample_series: pd.DataFrame,
) -> None:
    """Calendar features should match observation dates."""

    result = add_calendar_features(sample_series)

    first = result.iloc[0]

    assert first["month"] == 1
    assert first["quarter"] == 1
    assert first["year"] == 2020


def test_lag_one_uses_previous_value(
    sample_series: pd.DataFrame,
) -> None:
    """lag_1 must contain the previous month's value."""

    result = add_lag_features(
        sample_series,
        lags=(1,),
    )

    assert pd.isna(result.iloc[0]["lag_1"])

    assert result.iloc[1]["lag_1"] == 1

    assert result.iloc[2]["lag_1"] == 2


def test_lag_twelve(
    sample_series: pd.DataFrame,
) -> None:
    """lag_12 should represent the same month one year earlier."""

    result = add_lag_features(
        sample_series,
        lags=(12,),
    )

    assert pd.isna(result.iloc[11]["lag_12"])

    assert result.iloc[12]["lag_12"] == 1


def test_rolling_mean_excludes_current_target(
    sample_series: pd.DataFrame,
) -> None:
    """Rolling mean must use only observations before t."""

    result = add_rolling_features(
        sample_series,
        windows=(3,),
    )

    # At month 4, prior values are 1, 2, 3.
    assert result.iloc[3]["rolling_mean_3"] == pytest.approx(2.0)

    # It must not include current value 4.
    assert result.iloc[3]["rolling_mean_3"] != pytest.approx(3.0)


def test_rolling_requires_full_history(
    sample_series: pd.DataFrame,
) -> None:
    """Rolling features should require a complete prior window."""

    result = add_rolling_features(
        sample_series,
        windows=(3,),
    )

    assert pd.isna(result.iloc[0]["rolling_mean_3"])

    assert pd.isna(result.iloc[1]["rolling_mean_3"])

    assert pd.isna(result.iloc[2]["rolling_mean_3"])

    assert not pd.isna(result.iloc[3]["rolling_mean_3"])


def test_build_forecasting_features(
    sample_series: pd.DataFrame,
) -> None:
    """Complete feature builder should create all core features."""

    result = build_forecasting_features(sample_series)

    expected_columns = {
        "lag_1",
        "lag_2",
        "lag_3",
        "lag_6",
        "lag_12",
        "rolling_mean_3",
        "rolling_mean_6",
        "rolling_mean_12",
        "month",
        "quarter",
        "year",
    }

    assert expected_columns.issubset(result.columns)


def test_rejects_invalid_lag(
    sample_series: pd.DataFrame,
) -> None:
    """Zero or negative lags should be rejected."""

    with pytest.raises(
        ValueError,
        match="at least 1",
    ):
        add_lag_features(
            sample_series,
            lags=(0,),
        )
