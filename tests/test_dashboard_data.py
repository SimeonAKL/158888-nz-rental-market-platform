"""Regression tests for dashboard analytical data loaders."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import rmp.dashboard.data as dashboard_data


def _clear_cache(function) -> None:
    """Clear a Streamlit cached function when the wrapper supports it."""
    clear = getattr(function, "clear", None)

    if callable(clear):
        clear()


def test_require_file_rejects_missing_file(
    tmp_path: Path,
) -> None:
    missing = tmp_path / "missing.csv"

    with pytest.raises(
        FileNotFoundError,
        match="Dashboard data file not found",
    ):
        dashboard_data._require_file(missing)


def test_load_monthly_panel_parses_dates_and_sorts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dashboard_data,
        "ANALYTICS_DIR",
        tmp_path,
    )

    source = pd.DataFrame(
        {
            "period_date": [
                "2026-02-01",
                "2026-01-01",
                "2026-01-01",
            ],
            "series_id": [
                "series_b",
                "series_b",
                "series_a",
            ],
            "metric": [
                "median_rent",
                "median_rent",
                "bonds_lodged",
            ],
            "geography_level": [
                "region",
                "region",
                "region",
            ],
            "location_id": [2, 2, 1],
            "location_name": [
                "Wellington",
                "Wellington",
                "Auckland",
            ],
            "value": [
                620.0,
                610.0,
                1000.0,
            ],
        }
    )

    source.to_csv(
        tmp_path / "monthly_panel.csv",
        index=False,
    )

    _clear_cache(dashboard_data.load_monthly_panel)

    result = dashboard_data.load_monthly_panel()

    assert result["series_id"].tolist() == [
        "series_a",
        "series_b",
        "series_b",
    ]

    assert result["period_date"].tolist() == [
        pd.Timestamp("2026-01-01"),
        pd.Timestamp("2026-01-01"),
        pd.Timestamp("2026-02-01"),
    ]

    assert pd.api.types.is_datetime64_any_dtype(result["period_date"])


def test_load_monthly_panel_rejects_missing_required_column(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dashboard_data,
        "ANALYTICS_DIR",
        tmp_path,
    )

    source = pd.DataFrame(
        {
            "period_date": ["2026-01-01"],
            "series_id": ["series_a"],
            "metric": ["median_rent"],
            "geography_level": ["region"],
            "location_id": [1],
            "location_name": ["Auckland"],
            # value intentionally omitted
        }
    )

    source.to_csv(
        tmp_path / "monthly_panel.csv",
        index=False,
    )

    _clear_cache(dashboard_data.load_monthly_panel)

    with pytest.raises(
        ValueError,
        match="Monthly panel is missing required columns",
    ):
        dashboard_data.load_monthly_panel()


def test_load_series_winners_validates_schema_and_sorts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dashboard_data,
        "FORECASTING_DIR",
        tmp_path,
    )

    source = pd.DataFrame(
        {
            "series_id": [
                "series_b",
                "series_a",
            ],
            "metric": [
                "median_rent",
                "median_rent",
            ],
            "geography_level": [
                "region",
                "region",
            ],
            "location_id": [2, 1],
            "location_name": [
                "Wellington",
                "Auckland",
            ],
            "best_model": [
                "ets_additive_damped",
                "seasonal_naive",
            ],
            "best_mae": [20.0, 10.0],
            "best_rmse": [25.0, 15.0],
            "best_smape": [4.0, 2.0],
        }
    )

    source.to_csv(
        tmp_path / "series_model_winners.csv",
        index=False,
    )

    _clear_cache(dashboard_data.load_series_model_winners)

    result = dashboard_data.load_series_model_winners()

    assert result["series_id"].tolist() == [
        "series_a",
        "series_b",
    ]


def test_load_series_winners_rejects_invalid_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dashboard_data,
        "FORECASTING_DIR",
        tmp_path,
    )

    pd.DataFrame(
        {
            "series_id": ["series_a"],
            "best_model": ["seasonal_naive"],
        }
    ).to_csv(
        tmp_path / "series_model_winners.csv",
        index=False,
    )

    _clear_cache(dashboard_data.load_series_model_winners)

    with pytest.raises(
        ValueError,
        match="Series winner file is missing required columns",
    ):
        dashboard_data.load_series_model_winners()


def test_load_final_forward_forecasts_parses_dates_and_sorts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dashboard_data,
        "FORECASTING_DIR",
        tmp_path,
    )

    source = pd.DataFrame(
        {
            "series_id": [
                "series_b",
                "series_a",
                "series_a",
            ],
            "metric": [
                "median_rent",
                "median_rent",
                "median_rent",
            ],
            "geography_level": [
                "region",
                "region",
                "region",
            ],
            "location_id": [2, 1, 1],
            "location_name": [
                "Wellington",
                "Auckland",
                "Auckland",
            ],
            "model": [
                "ets_additive_damped",
                "seasonal_naive",
                "seasonal_naive",
            ],
            "forecast_origin": [
                "2026-07-01",
                "2026-07-01",
                "2026-07-01",
            ],
            "forecast_period": [
                "2026-08-01",
                "2026-09-01",
                "2026-08-01",
            ],
            "horizon_step": [1, 2, 1],
            "predicted": [
                620.0,
                660.0,
                650.0,
            ],
            "backtest_mae": [
                20.0,
                10.0,
                10.0,
            ],
            "backtest_rmse": [
                25.0,
                15.0,
                15.0,
            ],
            "backtest_smape": [
                4.0,
                2.0,
                2.0,
            ],
        }
    )

    source.to_csv(
        tmp_path / "final_forward_forecasts.csv",
        index=False,
    )

    _clear_cache(dashboard_data.load_final_forward_forecasts)

    result = dashboard_data.load_final_forward_forecasts()

    assert result[["series_id", "horizon_step"]].values.tolist() == [
        ["series_a", 1],
        ["series_a", 2],
        ["series_b", 1],
    ]

    assert pd.api.types.is_datetime64_any_dtype(result["forecast_origin"])

    assert pd.api.types.is_datetime64_any_dtype(result["forecast_period"])


def test_load_final_forward_forecasts_rejects_invalid_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        dashboard_data,
        "FORECASTING_DIR",
        tmp_path,
    )

    source = pd.DataFrame(
        {
            "series_id": ["series_a"],
            "forecast_origin": ["2026-07-01"],
            "forecast_period": ["2026-08-01"],
        }
    )

    source.to_csv(
        tmp_path / "final_forward_forecasts.csv",
        index=False,
    )

    _clear_cache(dashboard_data.load_final_forward_forecasts)

    with pytest.raises(
        ValueError,
        match="Final forecast file is missing required columns",
    ):
        dashboard_data.load_final_forward_forecasts()
