"""Run pooled recursive XGBoost rolling-origin evaluation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from rmp.forecasting.metrics import (
    calculate_forecast_metrics,
)
from rmp.forecasting.selection import select_forecasting_series
from rmp.forecasting.splits import (
    DEFAULT_FORECAST_HORIZON,
    DEFAULT_MIN_HISTORY_MONTHS,
    DEFAULT_N_ORIGINS,
    generate_rolling_origins,
)
from rmp.forecasting.xgboost_pooled import (
    pooled_recursive_forecast,
)

INPUT_PATH = Path(
    "data/processed/analytics/monthly_panel.csv"
)

CATALOG_PATH = Path(
    "data/processed/analytics/series_catalog.csv"
)

OUTPUT_DIR = Path(
    "data/processed/forecasting"
)

MODEL_NAME = "xgboost_pooled_recursive"


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
    """Load the validated monthly modelling panel."""

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

    return panel.sort_values(
        [
            "metric",
            "series_id",
            "period_date",
        ]
    ).reset_index(drop=True)



def load_series_catalog() -> pd.DataFrame:
    """Load Phase 3 forecasting-eligibility metadata."""

    if not CATALOG_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {CATALOG_PATH}"
        )

    catalog = pd.read_csv(
        CATALOG_PATH,
        parse_dates=["continuous_start"],
    )

    required = {
        "series_id",
        "continuous_start",
        "continuous_months",
        "eligible_for_forecasting",
    }

    missing = required.difference(
        catalog.columns
    )

    if missing:
        raise ValueError(
            "Series catalog is missing required columns: "
            f"{sorted(missing)}"
        )

    if catalog.empty:
        raise ValueError(
            "Series catalog is empty."
        )

    return catalog


def run_forecasts(
    panel: pd.DataFrame,
) -> pd.DataFrame:
    """Run target-specific pooled recursive forecasts."""

    prediction_frames: list[
        pd.DataFrame
    ] = []

    for metric_name, metric_data in panel.groupby(
        "metric",
        sort=True,
    ):
        metric_data = metric_data.copy()

        first_series_id = (
            metric_data["series_id"]
            .sort_values()
            .iloc[0]
        )

        periods = metric_data.loc[
            metric_data["series_id"]
            == first_series_id,
            "period_date",
        ].sort_values()

        splits = generate_rolling_origins(
            periods,
            forecast_horizon=(
                DEFAULT_FORECAST_HORIZON
            ),
            n_origins=DEFAULT_N_ORIGINS,
            min_history_months=(
                DEFAULT_MIN_HISTORY_MONTHS
            ),
        )

        for split in splits:
            history = metric_data.loc[
                metric_data["period_date"]
                <= split.origin
            ].copy()

            future_dates = pd.date_range(
                start=split.test_start,
                end=split.test_end,
                freq="MS",
            )

            forecast = (
                pooled_recursive_forecast(
                    history,
                    future_dates,
                )
            )

            actuals = metric_data.loc[
                (
                    metric_data["period_date"]
                    >= split.test_start
                )
                & (
                    metric_data["period_date"]
                    <= split.test_end
                ),
                [
                    "series_id",
                    "period_date",
                    "value",
                ],
            ].copy()

            actuals = actuals.rename(
                columns={
                    "period_date": "forecast_period",
                    "value": "actual",
                }
            )

            result = forecast.merge(
                actuals,
                on=[
                    "series_id",
                    "forecast_period",
                ],
                how="left",
                validate="one_to_one",
            )

            if result["actual"].isna().any():
                raise ValueError(
                    "Missing actual values for "
                    f"{metric_name} at origin "
                    f"{split.origin.date()}."
                )

            result["origin"] = (
                split.origin
            )

            result["model"] = (
                MODEL_NAME
            )

            result["error"] = (
                result["actual"]
                - result["predicted"]
            )

            result["absolute_error"] = (
                result["error"].abs()
            )

            result["squared_error"] = (
                result["error"] ** 2
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
    """Calculate project forecasting metrics."""

    return calculate_forecast_metrics(
        group["actual"],
        group["predicted"],
    )


def build_metrics_by_origin(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate per-series, per-origin metrics."""

    group_columns = [
        "model",
        "series_id",
        "metric",
        "geography_level",
        "location_id",
        "location_name",
        "origin",
    ]

    rows = []

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
    """Calculate metrics across origins for each series."""

    group_columns = [
        "model",
        "series_id",
        "metric",
        "geography_level",
        "location_id",
        "location_name",
    ]

    rows = []

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
    """Build overall and target-specific XGBoost summaries."""

    rows = []

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
            **calculate_group_metrics(
                predictions
            ),
        }
    )

    for metric_name, group in predictions.groupby(
        "metric",
        sort=True,
    ):
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
                **calculate_group_metrics(
                    group
                ),
            }
        )

    return pd.DataFrame(rows)


def validate_predictions(
    panel: pd.DataFrame,
    predictions: pd.DataFrame,
) -> None:
    """Validate Phase 4.3 output completeness."""

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

    origins = predictions.groupby(
        "series_id"
    )["origin"].nunique()

    if not (
        origins
        == DEFAULT_N_ORIGINS
    ).all():
        raise ValueError(
            "Each series must have exactly "
            f"{DEFAULT_N_ORIGINS} origins."
        )

    numeric_columns = [
        "actual",
        "predicted",
        "error",
        "absolute_error",
        "squared_error",
    ]

    if not np.isfinite(
        predictions[
            numeric_columns
        ].to_numpy(
            dtype=float
        )
    ).all():
        raise ValueError(
            "XGBoost results contain "
            "non-finite values."
        )


def main() -> None:
    """Run pooled recursive XGBoost evaluation."""

    panel = load_monthly_panel()
    catalog = load_series_catalog()

    panel = select_forecasting_series(
        panel,
        catalog,
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
        / "xgboost_predictions.csv",
        index=False,
    )

    metrics_by_origin.to_csv(
        OUTPUT_DIR
        / "xgboost_metrics_by_origin.csv",
        index=False,
    )

    metrics_by_series.to_csv(
        OUTPUT_DIR
        / "xgboost_metrics_by_series.csv",
        index=False,
    )

    summary.to_csv(
        OUTPUT_DIR
        / "xgboost_summary.csv",
        index=False,
    )

    print(
        "Pooled recursive XGBoost evaluation complete."
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
