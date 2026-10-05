"""Build unified Phase 4 forecasting model comparison outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from rmp.forecasting.comparison import (
    MODEL_ORDER,
    build_metrics_by_horizon,
    build_metrics_by_origin,
    build_metrics_by_series,
    build_model_comparison,
    build_series_model_winners,
    combine_predictions,
)

FORECASTING_DIR = Path("data/processed/forecasting")

MODEL_FILES = {
    "seasonal_naive": ("seasonal_naive_predictions.csv"),
    "ets_additive_damped": ("statistical_model_predictions.csv"),
    "xgboost_pooled_recursive": ("xgboost_predictions.csv"),
}


def load_model_predictions() -> list[pd.DataFrame]:
    """Load all Phase 4 model prediction outputs."""

    frames: list[pd.DataFrame] = []

    for model_name in MODEL_ORDER:
        filename = MODEL_FILES[model_name]

        path = FORECASTING_DIR / filename

        if not path.exists():
            raise FileNotFoundError(f"Missing model prediction file: {path}")

        frame = pd.read_csv(
            path,
            parse_dates=[
                "origin",
                "forecast_period",
            ],
        )

        observed_models = set(frame["model"].unique())

        if observed_models != {model_name}:
            raise ValueError(f"{filename} contains unexpected model labels: {observed_models}")

        frames.append(frame)

    return frames


def main() -> None:
    """Build and save all unified Phase 4 comparison outputs."""

    model_frames = load_model_predictions()

    combined = combine_predictions(model_frames)

    metrics_by_origin = build_metrics_by_origin(combined)

    metrics_by_series = build_metrics_by_series(combined)

    metrics_by_horizon = build_metrics_by_horizon(combined)

    model_comparison = build_model_comparison(combined)

    series_winners = build_series_model_winners(metrics_by_series)

    n_models = combined["model"].nunique()
    n_series = combined["series_id"].nunique()
    n_metrics = combined["metric"].nunique()
    n_horizons = combined["horizon_step"].nunique()

    origins_per_series = combined.groupby("series_id")["origin"].nunique()

    if origins_per_series.nunique() != 1:
        raise ValueError("Series do not share a consistent number of rolling origins.")

    n_origins = int(origins_per_series.iloc[0])

    models_per_observation = combined.groupby(
        [
            "series_id",
            "origin",
            "forecast_period",
            "horizon_step",
        ]
    )["model"].nunique()

    if not (models_per_observation == n_models).all():
        raise ValueError("Not every forecast observation contains predictions from every model.")

    expected_predictions = n_models * n_series * n_origins * n_horizons

    if len(combined) != expected_predictions:
        raise ValueError(
            "Unexpected combined prediction count: "
            f"{len(combined)}; "
            f"expected {expected_predictions}."
        )

    expected_origin_rows = n_models * n_series * n_origins

    if len(metrics_by_origin) != expected_origin_rows:
        raise ValueError(
            "Unexpected metrics_by_origin row count: "
            f"{len(metrics_by_origin)}; "
            f"expected {expected_origin_rows}."
        )

    expected_series_rows = n_models * n_series

    if len(metrics_by_series) != expected_series_rows:
        raise ValueError(
            "Unexpected metrics_by_series row count: "
            f"{len(metrics_by_series)}; "
            f"expected {expected_series_rows}."
        )

    expected_horizon_rows = n_models * n_metrics * n_horizons

    if len(metrics_by_horizon) != expected_horizon_rows:
        raise ValueError(
            "Unexpected metrics_by_horizon row count: "
            f"{len(metrics_by_horizon)}; "
            f"expected {expected_horizon_rows}."
        )

    expected_comparison_rows = n_models * n_metrics

    if len(model_comparison) != expected_comparison_rows:
        raise ValueError(
            "Unexpected model_comparison row count: "
            f"{len(model_comparison)}; "
            f"expected {expected_comparison_rows}."
        )

    if len(series_winners) != n_series:
        raise ValueError(
            f"Unexpected series winner row count: {len(series_winners)}; expected {n_series}."
        )

    combined.to_csv(
        FORECASTING_DIR / "combined_predictions.csv",
        index=False,
    )

    metrics_by_origin.to_csv(
        FORECASTING_DIR / "metrics_by_origin.csv",
        index=False,
    )

    metrics_by_series.to_csv(
        FORECASTING_DIR / "metrics_by_series.csv",
        index=False,
    )

    metrics_by_horizon.to_csv(
        FORECASTING_DIR / "metrics_by_horizon.csv",
        index=False,
    )

    model_comparison.to_csv(
        FORECASTING_DIR / "model_comparison.csv",
        index=False,
    )

    series_winners.to_csv(
        FORECASTING_DIR / "series_model_winners.csv",
        index=False,
    )

    print("Unified Phase 4 model comparison complete.")
    print()
    print(f"Combined predictions: {len(combined)}")
    print(f"Metrics by origin: {len(metrics_by_origin)}")
    print(f"Metrics by series: {len(metrics_by_series)}")
    print(f"Metrics by horizon: {len(metrics_by_horizon)}")
    print(f"Model comparison rows: {len(model_comparison)}")
    print(f"Series winners: {len(series_winners)}")

    print()
    print("=== MODEL COMPARISON ===")
    print(model_comparison.to_string(index=False))

    print()
    print("=== SERIES WINNER COUNTS ===")

    winner_counts = (
        series_winners.groupby(
            [
                "metric",
                "best_model",
            ]
        )
        .size()
        .reset_index(name="n_series")
    )

    print(winner_counts.to_string(index=False))

    print()
    print(f"Outputs written to: {FORECASTING_DIR}")


if __name__ == "__main__":
    main()
