"""Tests for the final production-forecast runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

SCRIPT_PATH = Path("scripts/build_final_forecasts.py")


def load_runner_module():
    """Load the runner script as an isolated Python module."""
    spec = importlib.util.spec_from_file_location(
        "build_final_forecasts_runner",
        SCRIPT_PATH,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load build_final_forecasts.py.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def test_runner_uses_metrics_and_production_builder(
    tmp_path,
    monkeypatch,
) -> None:
    """Runner should use metrics_by_series and fixed-policy builder."""
    module = load_runner_module()

    panel_path = tmp_path / "monthly_panel.csv"
    catalog_path = tmp_path / "series_catalog.csv"
    metrics_path = tmp_path / "metrics_by_series.csv"
    output_path = tmp_path / "final_forward_forecasts.csv"

    pd.DataFrame(
        {
            "period_date": ["2026-07-01"],
            "series_id": ["series_1"],
            "metric": ["median_rent"],
            "geography_level": ["region"],
            "location_id": [1],
            "location_name": ["Test Region"],
            "value": [600.0],
        }
    ).to_csv(
        panel_path,
        index=False,
    )

    pd.DataFrame(
        {
            "series_id": ["series_1"],
            "continuous_start": ["2020-01-01"],
            "eligible_for_forecasting": [True],
        }
    ).to_csv(
        catalog_path,
        index=False,
    )

    pd.DataFrame(
        {
            "model": ["ets_additive_damped"],
            "series_id": ["series_1"],
            "mae": [10.0],
            "rmse": [12.0],
            "smape": [5.0],
        }
    ).to_csv(
        metrics_path,
        index=False,
    )

    monkeypatch.setattr(
        module,
        "PANEL_PATH",
        panel_path,
    )
    monkeypatch.setattr(
        module,
        "CATALOG_PATH",
        catalog_path,
    )
    monkeypatch.setattr(
        module,
        "METRICS_PATH",
        metrics_path,
    )
    monkeypatch.setattr(
        module,
        "OUTPUT_PATH",
        output_path,
    )

    observed: dict[str, object] = {}

    def fake_select_forecasting_series(
        panel: pd.DataFrame,
        catalog: pd.DataFrame,
    ) -> pd.DataFrame:
        observed["panel_rows"] = len(panel)
        observed["catalog_rows"] = len(catalog)

        return panel.copy()

    def fake_build_production_forward_forecasts(
        history: pd.DataFrame,
        metrics_by_series: pd.DataFrame,
        horizon: int,
    ) -> pd.DataFrame:
        observed["history_rows"] = len(history)
        observed["metric_models"] = set(metrics_by_series["model"])
        observed["horizon"] = horizon

        return pd.DataFrame(
            {
                "series_id": ["series_1"],
                "metric": ["median_rent"],
                "geography_level": ["region"],
                "location_id": [1],
                "location_name": ["Test Region"],
                "model": ["ets_additive_damped"],
                "forecast_origin": [pd.Timestamp("2026-07-01")],
                "forecast_period": [pd.Timestamp("2026-08-01")],
                "horizon_step": [1],
                "predicted": [610.0],
                "backtest_mae": [10.0],
                "backtest_rmse": [12.0],
                "backtest_smape": [5.0],
                "forecast_policy": ["fixed_ets_v1"],
            }
        )

    monkeypatch.setattr(
        module,
        "select_forecasting_series",
        fake_select_forecasting_series,
    )

    monkeypatch.setattr(
        module,
        "build_production_forward_forecasts",
        fake_build_production_forward_forecasts,
    )

    module.main()

    assert output_path.exists()

    result = pd.read_csv(output_path)

    assert len(result) == 1
    assert set(result["model"]) == {"ets_additive_damped"}
    assert set(result["forecast_policy"]) == {"fixed_ets_v1"}

    assert observed == {
        "panel_rows": 1,
        "catalog_rows": 1,
        "history_rows": 1,
        "metric_models": {"ets_additive_damped"},
        "horizon": 6,
    }
