"""Tests for final winner-model forward forecasting."""

from __future__ import annotations

import pandas as pd
import pytest

from rmp.forecasting.final_forecast import (
    build_future_periods,
    seasonal_naive_future_forecast,
    select_winner_forward_forecasts,
)


def test_build_future_periods_uses_common_origin() -> None:
    """Future periods must begin immediately after the shared origin."""
    history = pd.DataFrame(
        {
            "series_id": [
                "series_a",
                "series_a",
                "series_b",
                "series_b",
            ],
            "period_date": pd.to_datetime(
                [
                    "2026-06-01",
                    "2026-07-01",
                    "2026-06-01",
                    "2026-07-01",
                ]
            ),
        }
    )

    origin, future = build_future_periods(
        history,
        horizon=6,
    )

    assert origin == pd.Timestamp(
        "2026-07-01"
    )

    assert future.equals(
        pd.date_range(
            "2026-08-01",
            periods=6,
            freq="MS",
        )
    )


def test_build_future_periods_rejects_mixed_origins() -> None:
    """All final forecast series must share one forecast origin."""
    history = pd.DataFrame(
        {
            "series_id": [
                "series_a",
                "series_a",
                "series_b",
                "series_b",
            ],
            "period_date": pd.to_datetime(
                [
                    "2026-06-01",
                    "2026-07-01",
                    "2026-05-01",
                    "2026-06-01",
                ]
            ),
        }
    )

    with pytest.raises(
        ValueError,
        match="same forecast origin",
    ):
        build_future_periods(
            history,
            horizon=6,
        )


def test_seasonal_naive_future_uses_prior_year() -> None:
    """Future seasonal naive must use t-minus-12 observed values."""
    periods = pd.date_range(
        "2024-01-01",
        periods=24,
        freq="MS",
    )

    history = pd.DataFrame(
        {
            "period_date": periods,
            "value": range(
                100,
                124,
            ),
        }
    )

    future = pd.date_range(
        "2026-01-01",
        periods=2,
        freq="MS",
    )

    forecast = seasonal_naive_future_forecast(
        history,
        future,
    )

    assert forecast[
        "predicted"
    ].tolist() == [
        112.0,
        113.0,
    ]

    assert forecast[
        "horizon_step"
    ].tolist() == [
        1,
        2,
    ]


def test_winner_selection_returns_one_model_per_series() -> None:
    """Only each series' selected winner model should remain."""
    rows = []

    for model in [
        "seasonal_naive",
        "ets_additive_damped",
    ]:
        for series_id, location_id in [
            ("series_a", 1),
            ("series_b", 2),
        ]:
            for horizon_step in [
                1,
                2,
            ]:
                rows.append(
                    {
                        "model": model,
                        "series_id": series_id,
                        "metric": "median_rent",
                        "geography_level": "region",
                        "location_id": location_id,
                        "location_name": (
                            f"Location {location_id}"
                        ),
                        "forecast_origin": pd.Timestamp(
                            "2026-07-01"
                        ),
                        "forecast_period": (
                            pd.Timestamp(
                                "2026-07-01"
                            )
                            + pd.DateOffset(
                                months=horizon_step
                            )
                        ),
                        "horizon_step": horizon_step,
                        "predicted": (
                            500.0
                            + horizon_step
                        ),
                    }
                )

    forecasts = pd.DataFrame(rows)

    winners = pd.DataFrame(
        {
            "series_id": [
                "series_a",
                "series_b",
            ],
            "best_model": [
                "seasonal_naive",
                "ets_additive_damped",
            ],
            "best_mae": [
                10.0,
                12.0,
            ],
            "best_rmse": [
                15.0,
                18.0,
            ],
            "best_smape": [
                2.0,
                3.0,
            ],
        }
    )

    result = select_winner_forward_forecasts(
        forecasts,
        winners,
        horizon=2,
    )

    assert len(result) == 4
    assert result["series_id"].nunique() == 2

    models = (
        result[
            [
                "series_id",
                "model",
            ]
        ]
        .drop_duplicates()
        .set_index("series_id")["model"]
        .to_dict()
    )

    assert models == {
        "series_a": "seasonal_naive",
        "series_b": "ets_additive_damped",
    }
