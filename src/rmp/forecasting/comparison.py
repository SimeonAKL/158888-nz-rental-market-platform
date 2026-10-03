"""Unified forecasting model evaluation and comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd

from rmp.forecasting.metrics import (
    calculate_forecast_metrics,
)

BASELINE_MODEL = "seasonal_naive"

MODEL_ORDER = [
    "seasonal_naive",
    "ets_additive_damped",
    "xgboost_pooled_recursive",
]

KEY_COLUMNS = [
    "series_id",
    "origin",
    "forecast_period",
    "horizon_step",
]

METADATA_COLUMNS = [
    "metric",
    "geography_level",
    "location_id",
    "location_name",
]

REQUIRED_COLUMNS = [
    "model",
    *KEY_COLUMNS,
    *METADATA_COLUMNS,
    "actual",
    "predicted",
]


def validate_model_predictions(
    predictions: pd.DataFrame,
) -> None:
    """Validate one model's prediction frame."""

    missing = set(
        REQUIRED_COLUMNS
    ).difference(
        predictions.columns
    )

    if missing:
        raise ValueError(
            "Prediction data is missing required columns: "
            f"{sorted(missing)}"
        )

    if predictions.empty:
        raise ValueError(
            "Prediction data cannot be empty."
        )

    if predictions["model"].nunique() != 1:
        raise ValueError(
            "Each prediction frame must contain "
            "exactly one model."
        )

    if predictions[
        KEY_COLUMNS
    ].duplicated().any():
        raise ValueError(
            "Prediction data contains duplicate forecast keys."
        )

    numeric = predictions[
        [
            "actual",
            "predicted",
        ]
    ].to_numpy(
        dtype=float
    )

    if not np.isfinite(
        numeric
    ).all():
        raise ValueError(
            "Prediction values must be finite."
        )


def validate_prediction_alignment(
    model_frames: list[pd.DataFrame],
) -> None:
    """Verify all models were evaluated on identical observations."""

    if len(model_frames) < 2:
        raise ValueError(
            "At least two model prediction frames are required."
        )

    for frame in model_frames:
        validate_model_predictions(
            frame
        )

    reference = (
        model_frames[0][
            KEY_COLUMNS
            + METADATA_COLUMNS
            + ["actual"]
        ]
        .sort_values(
            KEY_COLUMNS
        )
        .reset_index(drop=True)
    )

    reference_keys = reference[
        KEY_COLUMNS
    ]

    for frame in model_frames[1:]:
        candidate = (
            frame[
                KEY_COLUMNS
                + METADATA_COLUMNS
                + ["actual"]
            ]
            .sort_values(
                KEY_COLUMNS
            )
            .reset_index(drop=True)
        )

        if not candidate[
            KEY_COLUMNS
        ].equals(
            reference_keys
        ):
            raise ValueError(
                "Models were not evaluated on "
                "identical forecast observations."
            )

        for column in METADATA_COLUMNS:
            if not candidate[
                column
            ].equals(
                reference[column]
            ):
                raise ValueError(
                    "Model prediction metadata does not align "
                    f"for column: {column}"
                )

        if not np.allclose(
            candidate["actual"].to_numpy(
                dtype=float
            ),
            reference["actual"].to_numpy(
                dtype=float
            ),
            rtol=0.0,
            atol=1e-12,
        ):
            raise ValueError(
                "Actual values differ between model evaluations."
            )


def combine_predictions(
    model_frames: list[pd.DataFrame],
) -> pd.DataFrame:
    """Combine aligned model prediction frames."""

    validate_prediction_alignment(
        model_frames
    )

    combined = pd.concat(
        model_frames,
        ignore_index=True,
    )

    model_rank = {
        model: index
        for index, model in enumerate(
            MODEL_ORDER
        )
    }

    combined["_model_order"] = (
        combined["model"]
        .map(model_rank)
        .fillna(
            len(MODEL_ORDER)
        )
    )

    combined = combined.sort_values(
        [
            "_model_order",
            "series_id",
            "origin",
            "horizon_step",
        ]
    ).drop(
        columns="_model_order"
    )

    return combined.reset_index(
        drop=True
    )


def _metric_row(
    group: pd.DataFrame,
) -> dict[str, float]:
    """Calculate MAE, RMSE and sMAPE for a group."""

    return calculate_forecast_metrics(
        group["actual"],
        group["predicted"],
    )


def build_metrics_by_origin(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Build unified per-series, per-origin metrics."""

    columns = [
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
        columns,
        sort=True,
        dropna=False,
    ):
        row = dict(
            zip(
                columns,
                keys,
                strict=True,
            )
        )

        row["n_forecasts"] = len(
            group
        )

        row.update(
            _metric_row(
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
            "origin",
            "model",
        ]
    ).reset_index(drop=True)


def build_metrics_by_series(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Build unified per-series metrics."""

    columns = [
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
        columns,
        sort=True,
        dropna=False,
    ):
        row = dict(
            zip(
                columns,
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
            _metric_row(
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
            "model",
        ]
    ).reset_index(drop=True)


def build_metrics_by_horizon(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Build target-level metrics for each forecast horizon."""

    columns = [
        "model",
        "metric",
        "horizon_step",
    ]

    rows: list[
        dict[str, object]
    ] = []

    for keys, group in predictions.groupby(
        columns,
        sort=True,
    ):
        row = dict(
            zip(
                columns,
                keys,
                strict=True,
            )
        )

        row["n_series"] = group[
            "series_id"
        ].nunique()

        row["n_forecasts"] = len(
            group
        )

        row.update(
            _metric_row(
                group
            )
        )

        rows.append(row)

    return pd.DataFrame(
        rows
    ).sort_values(
        [
            "metric",
            "horizon_step",
            "model",
        ]
    ).reset_index(drop=True)


def build_model_comparison(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Build target-level model rankings and baseline improvements."""

    rows: list[
        dict[str, object]
    ] = []

    for (
        model_name,
        metric_name,
    ), group in predictions.groupby(
        [
            "model",
            "metric",
        ],
        sort=True,
    ):
        row = {
            "model": model_name,
            "metric": metric_name,
            "n_series": group[
                "series_id"
            ].nunique(),
            "n_forecasts": len(
                group
            ),
        }

        row.update(
            _metric_row(
                group
            )
        )

        rows.append(row)

    comparison = pd.DataFrame(
        rows
    )

    for metric_name in [
        "mae",
        "rmse",
        "smape",
    ]:
        comparison[
            f"rank_{metric_name}"
        ] = (
            comparison.groupby(
                "metric"
            )[metric_name]
            .rank(
                method="min",
                ascending=True,
            )
            .astype(int)
        )

    baseline = comparison.loc[
        comparison["model"]
        == BASELINE_MODEL,
        [
            "metric",
            "mae",
            "rmse",
            "smape",
        ],
    ].copy()

    if baseline["metric"].duplicated().any():
        raise ValueError(
            "Baseline model has duplicate metric rows."
        )

    baseline = baseline.rename(
        columns={
            "mae": "baseline_mae",
            "rmse": "baseline_rmse",
            "smape": "baseline_smape",
        }
    )

    comparison = comparison.merge(
        baseline,
        on="metric",
        how="left",
        validate="many_to_one",
    )

    if comparison[
        [
            "baseline_mae",
            "baseline_rmse",
            "baseline_smape",
        ]
    ].isna().any().any():
        raise ValueError(
            "Seasonal Naive baseline is missing "
            "for one or more target metrics."
        )

    for metric_name in [
        "mae",
        "rmse",
        "smape",
    ]:
        baseline_column = (
            f"baseline_{metric_name}"
        )

        improvement_column = (
            f"{metric_name}_improvement_vs_baseline_pct"
        )

        comparison[
            improvement_column
        ] = (
            (
                comparison[baseline_column]
                - comparison[metric_name]
            )
            / comparison[baseline_column]
            * 100.0
        )

    comparison = comparison.drop(
        columns=[
            "baseline_mae",
            "baseline_rmse",
            "baseline_smape",
        ]
    )

    return comparison.sort_values(
        [
            "metric",
            "rank_smape",
            "model",
        ]
    ).reset_index(drop=True)


def build_series_model_winners(
    metrics_by_series: pd.DataFrame,
) -> pd.DataFrame:
    """Identify the best model for every individual series."""

    required = {
        "model",
        "series_id",
        "metric",
        "geography_level",
        "location_id",
        "location_name",
        "mae",
        "rmse",
        "smape",
    }

    missing = required.difference(
        metrics_by_series.columns
    )

    if missing:
        raise ValueError(
            "Series metrics are missing columns: "
            f"{sorted(missing)}"
        )

    rows: list[
        dict[str, object]
    ] = []

    for series_id, group in metrics_by_series.groupby(
        "series_id",
        sort=True,
    ):
        best = group.sort_values(
            [
                "smape",
                "mae",
                "rmse",
                "model",
            ]
        ).iloc[0]

        rows.append(
            {
                "series_id": series_id,
                "metric": best[
                    "metric"
                ],
                "geography_level": best[
                    "geography_level"
                ],
                "location_id": best[
                    "location_id"
                ],
                "location_name": best[
                    "location_name"
                ],
                "best_model": best[
                    "model"
                ],
                "best_mae": best[
                    "mae"
                ],
                "best_rmse": best[
                    "rmse"
                ],
                "best_smape": best[
                    "smape"
                ],
            }
        )

    return pd.DataFrame(
        rows
    ).sort_values(
        [
            "metric",
            "location_name",
        ]
    ).reset_index(drop=True)
