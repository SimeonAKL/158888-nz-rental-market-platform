"""Run rolling-origin evaluation for the Holt-Winters ETS model."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from rmp.forecasting.ets import (
    DEFAULT_SEASONAL_PERIOD,
    ets_forecast,
)
from rmp.forecasting.metrics import (
    calculate_forecast_metrics,
)
from rmp.forecasting.selection import select_forecasting_series
from rmp.forecasting.splits import (
    DEFAULT_FORECAST_HORIZON,
    DEFAULT_MIN_HISTORY_MONTHS,
    DEFAULT_N_ORIGINS,
    generate_rolling_origins,
    slice_rolling_origin,
)

INPUT_PATH = Path(
    "data/processed/analytics/monthly_panel.csv"
)

OUTPUT_DIR = Path(
    "data/processed/forecasting"
)

MODEL_NAME = "ets_additive_damped"


PREDICTION_COLUMNS = [
    "model",
    "series_id",
    "metric",
    "geography_level",
    "location_id",
    "location_name",
    "origin",
    "forecast_period",
    "horizon_step",
    "actual",
    "predicted",
    "error",
    "absolute_error",
    "squared_error",
]


def load_monthly_panel() -> pd.DataFrame:
    """Load and validate the monthly modelling panel."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}"
        )

    panel = pd.read_csv(
        INPUT_PATH,
        parse_dates=["period_date"],
    )

    required = {
        "period_date",
        "series_id",
        "metric",
        "geography_level",
        "location_id",
        "location_name",
        "value",
    }

    missing = required.difference(
        panel.columns
    )

    if missing:
        raise ValueError(
            "Monthly panel is missing required columns: "
            f"{sorted(missing)}"
        )

    if panel.empty:
        raise ValueError(
            "Monthly panel is empty."
        )

    if panel[
        [
            "period_date",
            "series_id",
            "value",
        ]
    ].isna().any().any():
        raise ValueError(
            "Monthly panel contains missing modelling values."
        )

    return panel.sort_values(
        [
            "series_id",
            "period_date",
        ]
    ).reset_index(drop=True)


def run_forecasts(
    panel: pd.DataFrame,
) -> pd.DataFrame:
    """Run ETS forecasts over all series and rolling origins."""

    prediction_frames: list[
        pd.DataFrame
    ] = []

    grouped = panel.groupby(
        "series_id",
        sort=True,
    )

    for series_id, series in grouped:
        series = series.sort_values(
            "period_date"
        ).reset_index(drop=True)

        metadata = series.iloc[0]

        splits = generate_rolling_origins(
            series["period_date"],
            forecast_horizon=(
                DEFAULT_FORECAST_HORIZON
            ),
            n_origins=DEFAULT_N_ORIGINS,
            min_history_months=(
                DEFAULT_MIN_HISTORY_MONTHS
            ),
        )

        if len(splits) != DEFAULT_N_ORIGINS:
            raise ValueError(
                f"{series_id} generated "
                f"{len(splits)} origins; "
                f"expected {DEFAULT_N_ORIGINS}."
            )

        for split in splits:
            train, test = slice_rolling_origin(
                series,
                split,
            )

            try:
                forecast = ets_forecast(
                    train,
                    test["period_date"],
                    seasonal_period=(
                        DEFAULT_SEASONAL_PERIOD
                    ),
                )
            except Exception as exc:
                raise RuntimeError(
                    "ETS forecasting failed for "
                    f"{series_id} at origin "
                    f"{split.origin.date()}."
                ) from exc

            actual = test[
                "value"
            ].to_numpy(
                dtype=float
            )

            predicted = forecast[
                "predicted"
            ].to_numpy(
                dtype=float
            )

            error = (
                actual
                - predicted
            )

            result = pd.DataFrame(
                {
                    "model": MODEL_NAME,
                    "series_id": series_id,
                    "metric": metadata[
                        "metric"
                    ],
                    "geography_level": metadata[
                        "geography_level"
                    ],
                    "location_id": metadata[
                        "location_id"
                    ],
                    "location_name": metadata[
                        "location_name"
                    ],
                    "origin": split.origin,
                    "forecast_period": forecast[
                        "forecast_period"
                    ],
                    "horizon_step": range(
                        1,
                        len(test) + 1,
                    ),
                    "actual": actual,
                    "predicted": predicted,
                    "error": error,
                    "absolute_error": np.abs(
                        error
                    ),
                    "squared_error": np.square(
                        error
                    ),
                }
            )

            prediction_frames.append(
                result
            )

    predictions = pd.concat(
        prediction_frames,
        ignore_index=True,
    )

    return predictions[
        PREDICTION_COLUMNS
    ].sort_values(
        [
            "series_id",
            "origin",
            "horizon_step",
        ]
    ).reset_index(drop=True)


def calculate_group_metrics(
    group: pd.DataFrame,
) -> dict[str, float]:
    """Calculate project metrics for one prediction group."""

    return calculate_forecast_metrics(
        group["actual"],
        group["predicted"],
    )


def build_metrics_by_origin(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate metrics for each series and rolling origin."""

    group_columns = [
        "model",
        "series_id",
        "metric",
        "geography_level",
        "location_id",
        "location_name",
        "origin",
    ]

    rows: list[
        dict[str, object]
    ] = []

    for keys, group in predictions.groupby(
        group_columns,
        sort=True,
        dropna=False,
    ):
        row = dict(
            zip(
                group_columns,
                keys,
                strict=True,
            )
        )

        row["n_forecasts"] = len(
            group
        )

        row.update(
            calculate_group_metrics(
                group
            )
        )

        rows.append(row)

    return pd.DataFrame(
        rows
    ).sort_values(
        [
            "series_id",
            "origin",
        ]
    ).reset_index(drop=True)


def build_metrics_by_series(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate metrics across all origins for each series."""

    group_columns = [
        "model",
        "series_id",
        "metric",
        "geography_level",
        "location_id",
        "location_name",
    ]

    rows: list[
        dict[str, object]
    ] = []

    for keys, group in predictions.groupby(
        group_columns,
        sort=True,
        dropna=False,
    ):
        row = dict(
            zip(
                group_columns,
                keys,
                strict=True,
            )
        )

        row["n_origins"] = group[
            "origin"
        ].nunique()

        row["n_forecasts"] = len(
            group
        )

        row.update(
            calculate_group_metrics(
                group
            )
        )

        rows.append(row)

    return pd.DataFrame(
        rows
    ).sort_values(
        [
            "metric",
            "series_id",
        ]
    ).reset_index(drop=True)


def build_summary(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Build overall and target-level ETS summaries."""

    rows: list[
        dict[str, object]
    ] = []

    overall_metrics = (
        calculate_group_metrics(
            predictions
        )
    )

    rows.append(
        {
            "model": MODEL_NAME,
            "scope": "overall",
            "metric": "all",
            "n_series": predictions[
                "series_id"
            ].nunique(),
            "n_forecasts": len(
                predictions
            ),
            **overall_metrics,
        }
    )

    for metric_name, group in (
        predictions.groupby(
            "metric",
            sort=True,
        )
    ):
        metric_values = (
            calculate_group_metrics(
                group
            )
        )

        rows.append(
            {
                "model": MODEL_NAME,
                "scope": "metric",
                "metric": metric_name,
                "n_series": group[
                    "series_id"
                ].nunique(),
                "n_forecasts": len(
                    group
                ),
                **metric_values,
            }
        )

    return pd.DataFrame(rows)


def validate_predictions(
    panel: pd.DataFrame,
    predictions: pd.DataFrame,
) -> None:
    """Validate expected Phase 4.2 forecast output."""

    n_series = panel[
        "series_id"
    ].nunique()

    expected_rows = (
        n_series
        * DEFAULT_N_ORIGINS
        * DEFAULT_FORECAST_HORIZON
    )

    if len(predictions) != expected_rows:
        raise ValueError(
            "Unexpected prediction count: "
            f"{len(predictions)}; "
            f"expected {expected_rows}."
        )

    if predictions[
        "series_id"
    ].nunique() != n_series:
        raise ValueError(
            "Not all series produced forecasts."
        )

    origins_per_series = (
        predictions.groupby(
            "series_id"
        )["origin"]
        .nunique()
    )

    if not (
        origins_per_series
        == DEFAULT_N_ORIGINS
    ).all():
        raise ValueError(
            "Each series must have exactly "
            f"{DEFAULT_N_ORIGINS} origins."
        )

    expected_horizons = set(
        range(
            1,
            DEFAULT_FORECAST_HORIZON + 1,
        )
    )

    for _, group in predictions.groupby(
        [
            "series_id",
            "origin",
        ]
    ):
        observed_horizons = set(
            group[
                "horizon_step"
            ].tolist()
        )

        if (
            observed_horizons
            != expected_horizons
        ):
            raise ValueError(
                "Invalid forecast horizon steps."
            )

    numeric_columns = [
        "actual",
        "predicted",
        "error",
        "absolute_error",
        "squared_error",
    ]

    values = predictions[
        numeric_columns
    ].to_numpy(
        dtype=float
    )

    if not np.isfinite(
        values
    ).all():
        raise ValueError(
            "ETS forecast results contain "
            "missing or non-finite values."
        )


def main() -> None:
    """Run complete ETS rolling-origin evaluation."""

    panel = select_forecasting_series(
        load_monthly_panel()
    )

    predictions = run_forecasts(
        panel
    )

    validate_predictions(
        panel,
        predictions,
    )

    metrics_by_origin = (
        build_metrics_by_origin(
            predictions
        )
    )

    metrics_by_series = (
        build_metrics_by_series(
            predictions
        )
    )

    summary = build_summary(
        predictions
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    predictions.to_csv(
        OUTPUT_DIR
        / "statistical_model_predictions.csv",
        index=False,
    )

    metrics_by_origin.to_csv(
        OUTPUT_DIR
        / "statistical_model_metrics_by_origin.csv",
        index=False,
    )

    metrics_by_series.to_csv(
        OUTPUT_DIR
        / "statistical_model_metrics_by_series.csv",
        index=False,
    )

    summary.to_csv(
        OUTPUT_DIR
        / "statistical_model_summary.csv",
        index=False,
    )

    print(
        "ETS rolling-origin evaluation complete."
    )
    print(
        f"Series: {panel['series_id'].nunique()}"
    )
    print(
        f"Predictions: {len(predictions)}"
    )
    print(
        f"Origins per series: {DEFAULT_N_ORIGINS}"
    )
    print(
        "Forecast horizon: "
        f"{DEFAULT_FORECAST_HORIZON}"
    )
    print()
    print(
        summary.to_string(
            index=False
        )
    )
    print()
    print(
        f"Outputs written to: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()
