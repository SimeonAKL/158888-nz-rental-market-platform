"""Tests for unified forecasting model comparison."""

import pandas as pd
import pytest

from rmp.forecasting.comparison import (
    build_metrics_by_horizon,
    build_model_comparison,
    build_series_model_winners,
    combine_predictions,
    validate_prediction_alignment,
)


def make_predictions(
    model: str,
    error_size: float,
) -> pd.DataFrame:
    """Create deterministic model predictions."""

    rows = []

    actual_values = [
        100.0,
        110.0,
        120.0,
        130.0,
    ]

    dates = pd.date_range(
        "2026-01-01",
        periods=4,
        freq="MS",
    )

    for index, (
        date,
        actual,
    ) in enumerate(
        zip(
            dates,
            actual_values,
            strict=True,
        ),
        start=1,
    ):
        rows.append(
            {
                "model": model,
                "series_id": (
                    "region_1_median_rent"
                ),
                "metric": "median_rent",
                "geography_level": "region",
                "location_id": 1,
                "location_name": "Region 1",
                "origin": pd.Timestamp(
                    "2025-12-01"
                ),
                "forecast_period": date,
                "horizon_step": index,
                "actual": actual,
                "predicted": (
                    actual
                    + error_size
                ),
            }
        )

    return pd.DataFrame(rows)


def test_prediction_alignment_accepts_matching_frames() -> None:
    """Identical evaluation windows should pass validation."""

    first = make_predictions(
        "seasonal_naive",
        10.0,
    )

    second = make_predictions(
        "ets_additive_damped",
        5.0,
    )

    validate_prediction_alignment(
        [
            first,
            second,
        ]
    )


def test_prediction_alignment_rejects_different_actuals() -> None:
    """Models must use identical observed targets."""

    first = make_predictions(
        "seasonal_naive",
        10.0,
    )

    second = make_predictions(
        "ets_additive_damped",
        5.0,
    )

    second.loc[
        second.index[0],
        "actual",
    ] = 999.0

    with pytest.raises(
        ValueError,
        match="Actual values differ",
    ):
        validate_prediction_alignment(
            [
                first,
                second,
            ]
        )


def test_combine_predictions() -> None:
    """Aligned model outputs should combine cleanly."""

    frames = [
        make_predictions(
            "seasonal_naive",
            10.0,
        ),
        make_predictions(
            "ets_additive_damped",
            5.0,
        ),
        make_predictions(
            "xgboost_pooled_recursive",
            2.0,
        ),
    ]

    result = combine_predictions(
        frames
    )

    assert len(result) == 12

    assert result[
        "model"
    ].nunique() == 3


def test_model_comparison_ranks_lower_error_first() -> None:
    """Lower forecast error should produce a better rank."""

    predictions = combine_predictions(
        [
            make_predictions(
                "seasonal_naive",
                10.0,
            ),
            make_predictions(
                "ets_additive_damped",
                5.0,
            ),
            make_predictions(
                "xgboost_pooled_recursive",
                2.0,
            ),
        ]
    )

    result = build_model_comparison(
        predictions
    )

    xgb = result.loc[
        result["model"]
        == "xgboost_pooled_recursive"
    ].iloc[0]

    baseline = result.loc[
        result["model"]
        == "seasonal_naive"
    ].iloc[0]

    assert xgb["rank_mae"] == 1
    assert xgb["rank_rmse"] == 1
    assert xgb["rank_smape"] == 1

    assert (
        xgb[
            "mae_improvement_vs_baseline_pct"
        ]
        > 0
    )

    assert baseline[
        "mae_improvement_vs_baseline_pct"
    ] == pytest.approx(
        0.0
    )


def test_metrics_by_horizon_has_one_row_per_model_step() -> None:
    """Horizon metrics should preserve forecast-step detail."""

    predictions = combine_predictions(
        [
            make_predictions(
                "seasonal_naive",
                10.0,
            ),
            make_predictions(
                "ets_additive_damped",
                5.0,
            ),
            make_predictions(
                "xgboost_pooled_recursive",
                2.0,
            ),
        ]
    )

    result = build_metrics_by_horizon(
        predictions
    )

    assert len(result) == (
        3 * 4
    )

    assert set(
        result["horizon_step"]
    ) == {
        1,
        2,
        3,
        4,
    }


def test_series_winner_uses_lowest_smape() -> None:
    """Series winner should be the model with lowest sMAPE."""

    metrics = pd.DataFrame(
        [
            {
                "model": "seasonal_naive",
                "series_id": "series_1",
                "metric": "median_rent",
                "geography_level": "region",
                "location_id": 1,
                "location_name": "Region 1",
                "mae": 10.0,
                "rmse": 12.0,
                "smape": 5.0,
            },
            {
                "model": "ets_additive_damped",
                "series_id": "series_1",
                "metric": "median_rent",
                "geography_level": "region",
                "location_id": 1,
                "location_name": "Region 1",
                "mae": 6.0,
                "rmse": 7.0,
                "smape": 3.0,
            },
        ]
    )

    result = build_series_model_winners(
        metrics
    )

    assert result.iloc[0][
        "best_model"
    ] == "ets_additive_damped"


def test_alignment_rejects_duplicate_keys() -> None:
    """Duplicate forecast observations should be rejected."""

    first = make_predictions(
        "seasonal_naive",
        10.0,
    )

    first = pd.concat(
        [
            first,
            first.iloc[[0]],
        ],
        ignore_index=True,
    )

    second = make_predictions(
        "ets_additive_damped",
        5.0,
    )

    with pytest.raises(
        ValueError,
        match="duplicate forecast keys",
    ):
        validate_prediction_alignment(
            [
                first,
                second,
            ]
        )
