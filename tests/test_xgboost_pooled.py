"""Tests for pooled recursive XGBoost forecasting."""

import numpy as np
import pandas as pd
import pytest

from rmp.forecasting.xgboost_pooled import (
    pooled_recursive_forecast,
    prepare_training_data,
)


def make_pooled_history(
    n_months: int = 72,
    n_series: int = 3,
) -> pd.DataFrame:
    """Create deterministic pooled regional histories."""

    dates = pd.date_range(
        "2018-01-01",
        periods=n_months,
        freq="MS",
    )

    rows = []

    for location_id in range(
        1,
        n_series + 1,
    ):
        for index, date in enumerate(dates):
            seasonal = 20.0 * np.sin(2.0 * np.pi * index / 12.0)

            value = 400.0 + (location_id * 50.0) + (index * 1.5) + seasonal

            rows.append(
                {
                    "period_date": date,
                    "series_id": (f"region_{location_id}_median_rent"),
                    "geography_level": "region",
                    "location_id": location_id,
                    "location_name": (f"Region {location_id}"),
                    "metric": "median_rent",
                    "value": value,
                }
            )

    return pd.DataFrame(rows)


def test_prepare_training_data() -> None:
    """Pooled training data should contain complete features."""

    history = make_pooled_history()

    (
        x_train,
        y_train,
        location_keys,
        feature_columns,
    ) = prepare_training_data(history)

    assert not x_train.empty
    assert len(x_train) == len(y_train)

    assert location_keys == [
        "region_1",
        "region_2",
        "region_3",
    ]

    assert "lag_12" in feature_columns
    assert "rolling_mean_12" in feature_columns
    assert "location_region_1" in feature_columns
    assert "location_region_2" in feature_columns
    assert "location_region_3" in feature_columns

    assert not x_train.isna().any().any()


def test_recursive_forecast_returns_all_series() -> None:
    """Each series should receive every forecast horizon."""

    history = make_pooled_history()

    future = pd.date_range(
        history["period_date"].max() + pd.offsets.MonthBegin(1),
        periods=6,
        freq="MS",
    )

    result = pooled_recursive_forecast(
        history,
        future,
    )

    assert len(result) == (3 * 6)

    assert result["series_id"].nunique() == 3

    assert set(result["horizon_step"]) == {
        1,
        2,
        3,
        4,
        5,
        6,
    }

    assert np.isfinite(result["predicted"]).all()


def test_recursive_forecast_is_deterministic() -> None:
    """Fixed random seed should make forecasts reproducible."""

    history = make_pooled_history()

    future = pd.date_range(
        history["period_date"].max() + pd.offsets.MonthBegin(1),
        periods=3,
        freq="MS",
    )

    first = pooled_recursive_forecast(
        history,
        future,
    )

    second = pooled_recursive_forecast(
        history,
        future,
    )

    assert first["predicted"].to_numpy() == pytest.approx(second["predicted"].to_numpy())


def test_recursive_forecast_does_not_modify_history() -> None:
    """Recursive forecasting must not mutate source history."""

    history = make_pooled_history()

    original = history.copy(deep=True)

    future = pd.date_range(
        history["period_date"].max() + pd.offsets.MonthBegin(1),
        periods=3,
        freq="MS",
    )

    pooled_recursive_forecast(
        history,
        future,
    )

    pd.testing.assert_frame_equal(
        history,
        original,
    )


def test_rejects_multiple_metrics() -> None:
    """One pooled model must represent one target metric."""

    history = make_pooled_history()

    history.loc[
        history.index[0],
        "metric",
    ] = "bonds_lodged"

    future = pd.date_range(
        history["period_date"].max() + pd.offsets.MonthBegin(1),
        periods=3,
        freq="MS",
    )

    with pytest.raises(
        ValueError,
        match="one target metric",
    ):
        prepare_training_data(history)

    with pytest.raises(
        ValueError,
        match="exactly one target metric",
    ):
        pooled_recursive_forecast(
            history,
            future,
        )


def test_rejects_nonconsecutive_future_dates() -> None:
    """Forecast dates must immediately follow the origin."""

    history = make_pooled_history()

    future = pd.date_range(
        history["period_date"].max() + pd.offsets.MonthBegin(2),
        periods=3,
        freq="MS",
    )

    with pytest.raises(
        ValueError,
        match="consecutive",
    ):
        pooled_recursive_forecast(
            history,
            future,
        )


def test_location_features_distinguish_geography_levels() -> None:
    """Equal location IDs across geography levels must remain distinct."""
    periods = pd.date_range(
        "2020-01-01",
        periods=36,
        freq="MS",
    )

    rows = []

    for geography_level, series_id, location_name in [
        (
            "region",
            "region_1_median_rent",
            "Region 1",
        ),
        (
            "territorial_authority",
            "territorial_authority_1_median_rent",
            "TA 1",
        ),
    ]:
        for index, period in enumerate(periods):
            rows.append(
                {
                    "period_date": period,
                    "series_id": series_id,
                    "geography_level": geography_level,
                    "location_id": 1,
                    "location_name": location_name,
                    "metric": "median_rent",
                    "value": 500.0 + index,
                }
            )

    history = pd.DataFrame(rows)

    _, _, location_keys, feature_columns = prepare_training_data(history)

    assert set(location_keys) == {
        "region_1",
        "territorial_authority_1",
    }

    assert "location_region_1" in feature_columns
    assert "location_territorial_authority_1" in feature_columns
