"""Tests for fixed-ETS production forward forecasts."""

from __future__ import annotations

import pandas as pd
import pytest

from rmp.forecasting import final_forecast
from rmp.forecasting.policy import (
    FORECAST_POLICY,
    PRODUCTION_MODEL,
)

SERIES_IDS = (
    "region_1_bonds_lodged",
    "region_2_bonds_lodged",
)


def make_history() -> pd.DataFrame:
    """Create complete monthly history for two forecasting series."""
    rows: list[dict[str, object]] = []

    periods = pd.date_range(
        "2022-01-01",
        periods=36,
        freq="MS",
    )

    for location_id, series_id in enumerate(
        SERIES_IDS,
        start=1,
    ):
        for period in periods:
            rows.append(
                {
                    "series_id": series_id,
                    "metric": "bonds_lodged",
                    "geography_level": "region",
                    "location_id": location_id,
                    "location_name": f"Region {location_id}",
                    "period_date": period,
                    "value": 100.0,
                }
            )

    return pd.DataFrame(rows)


def make_metrics() -> pd.DataFrame:
    """Create ETS metrics plus deliberately better XGBoost metrics."""
    rows: list[dict[str, object]] = []

    for series_id in SERIES_IDS:
        rows.append(
            {
                "model": final_forecast.ETS_MODEL,
                "series_id": series_id,
                "mae": 10.0,
                "rmse": 12.0,
                "smape": 5.0,
            }
        )

        rows.append(
            {
                "model": final_forecast.XGBOOST_MODEL,
                "series_id": series_id,
                "mae": 1.0,
                "rmse": 2.0,
                "smape": 0.5,
            }
        )

    return pd.DataFrame(rows)


def fake_ets_builder(
    history: pd.DataFrame,
    origin: pd.Timestamp,
    forecast_periods: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Return deterministic ETS forecasts without fitting statsmodels."""
    rows: list[dict[str, object]] = []

    for _, series in history.groupby(
        "series_id",
        sort=True,
    ):
        first = series.iloc[0]

        for step, forecast_period in enumerate(
            forecast_periods,
            start=1,
        ):
            rows.append(
                {
                    "model": final_forecast.ETS_MODEL,
                    "series_id": first["series_id"],
                    "metric": first["metric"],
                    "geography_level": first["geography_level"],
                    "location_id": first["location_id"],
                    "location_name": first["location_name"],
                    "forecast_origin": origin,
                    "forecast_period": forecast_period,
                    "horizon_step": step,
                    "predicted": 100.0 + step,
                }
            )

    return pd.DataFrame(
        rows,
        columns=final_forecast.MODEL_FORECAST_COLUMNS,
    )


@pytest.fixture
def patch_ets_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Replace real ETS fitting with deterministic output."""
    monkeypatch.setattr(
        final_forecast,
        "build_ets_forward_forecasts",
        fake_ets_builder,
    )


def test_production_policy_configuration() -> None:
    """Production policy should explicitly use fixed ETS."""
    assert PRODUCTION_MODEL == final_forecast.ETS_MODEL
    assert FORECAST_POLICY == "fixed_ets_v1"


def test_production_forecasts_use_ets_for_all_series(
    patch_ets_builder: None,
) -> None:
    """Every production forecast should use the fixed ETS model."""
    result = final_forecast.build_production_forward_forecasts(
        make_history(),
        make_metrics(),
    )

    assert set(result["series_id"]) == set(SERIES_IDS)

    assert set(result["model"]) == {final_forecast.ETS_MODEL}

    assert set(result["forecast_policy"]) == {FORECAST_POLICY}

    counts = result.groupby("series_id")["horizon_step"].count()

    assert counts.eq(final_forecast.DEFAULT_FORWARD_HORIZON).all()


def test_backtest_metrics_come_from_ets_not_xgboost(
    patch_ets_builder: None,
) -> None:
    """Production backtest fields must describe ETS itself."""
    result = final_forecast.build_production_forward_forecasts(
        make_history(),
        make_metrics(),
    )

    assert set(result["backtest_mae"]) == {10.0}
    assert set(result["backtest_rmse"]) == {12.0}
    assert set(result["backtest_smape"]) == {5.0}


def test_missing_ets_metrics_are_rejected(
    patch_ets_builder: None,
) -> None:
    """Every production series must have ETS backtest metrics."""
    metrics = make_metrics()

    metrics = metrics.loc[
        ~(
            (metrics["model"] == final_forecast.ETS_MODEL)
            & (metrics["series_id"] == "region_2_bonds_lodged")
        )
    ]

    with pytest.raises(
        ValueError,
        match="do not align",
    ):
        final_forecast.build_production_forward_forecasts(
            make_history(),
            metrics,
        )
