"""Production-path tests for final forward forecasting."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from rmp.forecasting import final_forecast


def _history() -> pd.DataFrame:
    """Return two simple modelling series with stable metadata."""
    periods = pd.date_range(
        "2024-01-01",
        periods=24,
        freq="MS",
    )

    rows: list[dict[str, object]] = []

    for series_id, metric, location_id, location_name, base in [
        (
            "series_a",
            "median_rent",
            1,
            "Auckland",
            500.0,
        ),
        (
            "series_b",
            "bonds_lodged",
            2,
            "Wellington",
            1000.0,
        ),
    ]:
        for offset, period in enumerate(periods):
            rows.append(
                {
                    "series_id": series_id,
                    "metric": metric,
                    "geography_level": "region",
                    "location_id": location_id,
                    "location_name": location_name,
                    "period_date": period,
                    "value": base + offset,
                }
            )

    return pd.DataFrame(rows)


def _single_series_history() -> pd.DataFrame:
    history = _history()

    return history.loc[history["series_id"] == "series_a"].copy()


def _model_frame(
    model: str,
    origin: pd.Timestamp,
    forecast_periods: pd.DatetimeIndex,
    *,
    predicted: list[float] | None = None,
) -> pd.DataFrame:
    if predicted is None:
        predicted = [
            600.0 + step
            for step in range(
                1,
                len(forecast_periods) + 1,
            )
        ]

    rows = []

    for step, (
        forecast_period,
        prediction,
    ) in enumerate(
        zip(
            forecast_periods,
            predicted,
            strict=True,
        ),
        start=1,
    ):
        rows.append(
            {
                "model": model,
                "series_id": "series_a",
                "metric": "median_rent",
                "geography_level": "region",
                "location_id": 1,
                "location_name": "Auckland",
                "forecast_origin": origin,
                "forecast_period": forecast_period,
                "horizon_step": step,
                "predicted": prediction,
            }
        )

    return pd.DataFrame(
        rows,
        columns=final_forecast.MODEL_FORECAST_COLUMNS,
    )


def test_build_ets_forward_forecasts_preserves_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history = _history()

    origin = pd.Timestamp("2025-12-01")

    forecast_periods = pd.date_range(
        "2026-01-01",
        periods=2,
        freq="MS",
    )

    def fake_ets_forecast(
        series: pd.DataFrame,
        periods: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        series_id = series["series_id"].iloc[0]

        base = 600.0 if series_id == "series_a" else 1100.0

        return pd.DataFrame(
            {
                "forecast_period": periods,
                "predicted": [
                    base,
                    base + 1.0,
                ],
            }
        )

    monkeypatch.setattr(
        final_forecast,
        "ets_forecast",
        fake_ets_forecast,
    )

    result = final_forecast.build_ets_forward_forecasts(
        history,
        origin,
        forecast_periods,
    )

    assert len(result) == 4

    assert set(result["series_id"]) == {
        "series_a",
        "series_b",
    }

    assert set(result["model"]) == {final_forecast.ETS_MODEL}

    assert set(result["forecast_origin"]) == {origin}

    assert result.groupby("series_id")["horizon_step"].apply(list).to_dict() == {
        "series_a": [1, 2],
        "series_b": [1, 2],
    }


def test_build_ets_forward_forecasts_wraps_model_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history = _single_series_history()

    origin = pd.Timestamp("2025-12-01")

    forecast_periods = pd.date_range(
        "2026-01-01",
        periods=2,
        freq="MS",
    )

    def failing_ets_forecast(
        series: pd.DataFrame,
        periods: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        del series, periods
        raise ValueError("model failed")

    monkeypatch.setattr(
        final_forecast,
        "ets_forecast",
        failing_ets_forecast,
    )

    with pytest.raises(
        RuntimeError,
        match="Final ETS forecasting failed for series_a",
    ):
        final_forecast.build_ets_forward_forecasts(
            history,
            origin,
            forecast_periods,
        )


def test_build_xgboost_forward_forecasts_runs_by_metric(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history = _history()

    origin = pd.Timestamp("2025-12-01")

    forecast_periods = pd.date_range(
        "2026-01-01",
        periods=2,
        freq="MS",
    )

    observed_metrics: list[str] = []

    def fake_pooled_recursive_forecast(
        metric_data: pd.DataFrame,
        periods: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        metric = str(metric_data["metric"].iloc[0])

        observed_metrics.append(metric)

        rows = []

        for series_id, series in metric_data.groupby("series_id"):
            first = series.iloc[0]

            for step, period in enumerate(
                periods,
                start=1,
            ):
                rows.append(
                    {
                        "series_id": series_id,
                        "metric": first["metric"],
                        "geography_level": (first["geography_level"]),
                        "location_id": (first["location_id"]),
                        "location_name": (first["location_name"]),
                        "forecast_period": period,
                        "horizon_step": step,
                        "predicted": float(100.0 + step),
                    }
                )

        return pd.DataFrame(rows)

    monkeypatch.setattr(
        final_forecast,
        "pooled_recursive_forecast",
        fake_pooled_recursive_forecast,
    )

    result = final_forecast.build_xgboost_forward_forecasts(
        history,
        origin,
        forecast_periods,
    )

    assert sorted(observed_metrics) == [
        "bonds_lodged",
        "median_rent",
    ]

    assert len(result) == 4

    assert set(result["model"]) == {final_forecast.XGBOOST_MODEL}

    assert set(result["forecast_origin"]) == {origin}


def test_build_xgboost_forward_forecasts_wraps_model_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history = _single_series_history()

    origin = pd.Timestamp("2025-12-01")

    forecast_periods = pd.date_range(
        "2026-01-01",
        periods=2,
        freq="MS",
    )

    def failing_forecast(
        metric_data: pd.DataFrame,
        periods: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        del metric_data, periods
        raise ValueError("model failed")

    monkeypatch.setattr(
        final_forecast,
        "pooled_recursive_forecast",
        failing_forecast,
    )

    with pytest.raises(
        RuntimeError,
        match=("Final pooled XGBoost forecasting failed for median_rent"),
    ):
        final_forecast.build_xgboost_forward_forecasts(
            history,
            origin,
            forecast_periods,
        )


def test_build_all_model_forward_forecasts_combines_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history = _single_series_history()

    def seasonal_builder(
        data: pd.DataFrame,
        origin: pd.Timestamp,
        periods: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        del data
        return _model_frame(
            final_forecast.SEASONAL_NAIVE_MODEL,
            origin,
            periods,
        )

    def ets_builder(
        data: pd.DataFrame,
        origin: pd.Timestamp,
        periods: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        del data
        return _model_frame(
            final_forecast.ETS_MODEL,
            origin,
            periods,
        )

    def xgb_builder(
        data: pd.DataFrame,
        origin: pd.Timestamp,
        periods: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        del data
        return _model_frame(
            final_forecast.XGBOOST_MODEL,
            origin,
            periods,
        )

    monkeypatch.setattr(
        final_forecast,
        "build_seasonal_naive_forward_forecasts",
        seasonal_builder,
    )

    monkeypatch.setattr(
        final_forecast,
        "build_ets_forward_forecasts",
        ets_builder,
    )

    monkeypatch.setattr(
        final_forecast,
        "build_xgboost_forward_forecasts",
        xgb_builder,
    )

    result = final_forecast.build_all_model_forward_forecasts(
        history,
        horizon=2,
    )

    assert len(result) == 6

    assert set(result["model"]) == {
        final_forecast.SEASONAL_NAIVE_MODEL,
        final_forecast.ETS_MODEL,
        final_forecast.XGBOOST_MODEL,
    }

    assert set(result["forecast_origin"]) == {pd.Timestamp("2025-12-01")}

    assert set(result["forecast_period"]) == {
        pd.Timestamp("2026-01-01"),
        pd.Timestamp("2026-02-01"),
    }


def test_build_all_model_forward_forecasts_rejects_duplicate_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history = _single_series_history()

    def duplicate_seasonal(
        data: pd.DataFrame,
        origin: pd.Timestamp,
        periods: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        del data

        frame = _model_frame(
            final_forecast.SEASONAL_NAIVE_MODEL,
            origin,
            periods,
        )

        return pd.concat(
            [
                frame,
                frame.iloc[[0]],
            ],
            ignore_index=True,
        )

    monkeypatch.setattr(
        final_forecast,
        "build_seasonal_naive_forward_forecasts",
        duplicate_seasonal,
    )

    monkeypatch.setattr(
        final_forecast,
        "build_ets_forward_forecasts",
        lambda data, origin, periods: _model_frame(
            final_forecast.ETS_MODEL,
            origin,
            periods,
        ),
    )

    monkeypatch.setattr(
        final_forecast,
        "build_xgboost_forward_forecasts",
        lambda data, origin, periods: _model_frame(
            final_forecast.XGBOOST_MODEL,
            origin,
            periods,
        ),
    )

    with pytest.raises(
        ValueError,
        match="Forward forecasts contain duplicate keys",
    ):
        final_forecast.build_all_model_forward_forecasts(
            history,
            horizon=2,
        )


def test_build_all_model_forward_forecasts_rejects_non_finite_predictions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history = _single_series_history()

    monkeypatch.setattr(
        final_forecast,
        "build_seasonal_naive_forward_forecasts",
        lambda data, origin, periods: _model_frame(
            final_forecast.SEASONAL_NAIVE_MODEL,
            origin,
            periods,
        ),
    )

    monkeypatch.setattr(
        final_forecast,
        "build_ets_forward_forecasts",
        lambda data, origin, periods: _model_frame(
            final_forecast.ETS_MODEL,
            origin,
            periods,
        ),
    )

    def non_finite_xgb(
        data: pd.DataFrame,
        origin: pd.Timestamp,
        periods: pd.DatetimeIndex,
    ) -> pd.DataFrame:
        del data

        return _model_frame(
            final_forecast.XGBOOST_MODEL,
            origin,
            periods,
            predicted=[
                np.inf,
                700.0,
            ],
        )

    monkeypatch.setattr(
        final_forecast,
        "build_xgboost_forward_forecasts",
        non_finite_xgb,
    )

    with pytest.raises(
        ValueError,
        match="Forward forecasts contain non-finite predictions",
    ):
        final_forecast.build_all_model_forward_forecasts(
            history,
            horizon=2,
        )


def test_winner_selection_rejects_unsupported_model() -> None:
    forecasts = _model_frame(
        final_forecast.SEASONAL_NAIVE_MODEL,
        pd.Timestamp("2025-12-01"),
        pd.date_range(
            "2026-01-01",
            periods=2,
            freq="MS",
        ),
    )

    winners = pd.DataFrame(
        {
            "series_id": ["series_a"],
            "best_model": ["unsupported_model"],
            "best_mae": [10.0],
            "best_rmse": [15.0],
            "best_smape": [2.0],
        }
    )

    with pytest.raises(
        ValueError,
        match="Unsupported winner models",
    ):
        final_forecast.select_winner_forward_forecasts(
            forecasts,
            winners,
            horizon=2,
        )


def test_winner_selection_requires_complete_horizon() -> None:
    forecasts = _model_frame(
        final_forecast.SEASONAL_NAIVE_MODEL,
        pd.Timestamp("2025-12-01"),
        pd.date_range(
            "2026-01-01",
            periods=1,
            freq="MS",
        ),
    )

    winners = pd.DataFrame(
        {
            "series_id": ["series_a"],
            "best_model": [final_forecast.SEASONAL_NAIVE_MODEL],
            "best_mae": [10.0],
            "best_rmse": [15.0],
            "best_smape": [2.0],
        }
    )

    with pytest.raises(
        ValueError,
        match=("Each winner series must have exactly 2 forward forecasts"),
    ):
        final_forecast.select_winner_forward_forecasts(
            forecasts,
            winners,
            horizon=2,
        )
