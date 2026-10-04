"""Generate final forward forecasts using series-level winner models."""

from __future__ import annotations

import numpy as np
import pandas as pd

from rmp.forecasting.ets import (
    DEFAULT_SEASONAL_PERIOD,
    ets_forecast,
)
from rmp.forecasting.xgboost_pooled import (
    pooled_recursive_forecast,
)

DEFAULT_FORWARD_HORIZON = 6

SEASONAL_NAIVE_MODEL = "seasonal_naive"
ETS_MODEL = "ets_additive_damped"
XGBOOST_MODEL = "xgboost_pooled_recursive"

SUPPORTED_MODELS = {
    SEASONAL_NAIVE_MODEL,
    ETS_MODEL,
    XGBOOST_MODEL,
}

METADATA_COLUMNS = [
    "series_id",
    "metric",
    "geography_level",
    "location_id",
    "location_name",
]

MODEL_FORECAST_COLUMNS = [
    "model",
    *METADATA_COLUMNS,
    "forecast_origin",
    "forecast_period",
    "horizon_step",
    "predicted",
]

FINAL_FORECAST_COLUMNS = [
    *METADATA_COLUMNS,
    "model",
    "forecast_origin",
    "forecast_period",
    "horizon_step",
    "predicted",
    "backtest_mae",
    "backtest_rmse",
    "backtest_smape",
]


def build_future_periods(
    history: pd.DataFrame,
    horizon: int = DEFAULT_FORWARD_HORIZON,
) -> tuple[pd.Timestamp, pd.DatetimeIndex]:
    """Return the common forecast origin and future monthly periods."""
    if horizon < 1:
        raise ValueError(
            "Forecast horizon must be at least 1."
        )

    if history.empty:
        raise ValueError(
            "Forecasting history cannot be empty."
        )

    if "series_id" not in history.columns:
        raise ValueError(
            "Forecasting history is missing series_id."
        )

    if "period_date" not in history.columns:
        raise ValueError(
            "Forecasting history is missing period_date."
        )

    data = history.copy()

    data["period_date"] = pd.to_datetime(
        data["period_date"]
    )

    end_dates = data.groupby(
        "series_id"
    )["period_date"].max()

    if end_dates.nunique() != 1:
        raise ValueError(
            "All forecast-eligible series must end "
            "at the same forecast origin."
        )

    origin = pd.Timestamp(
        end_dates.iloc[0]
    )

    future_periods = pd.date_range(
        start=origin + pd.offsets.MonthBegin(1),
        periods=horizon,
        freq="MS",
    )

    return origin, future_periods


def seasonal_naive_future_forecast(
    history: pd.DataFrame,
    forecast_periods: pd.DatetimeIndex,
    seasonal_period: int = DEFAULT_SEASONAL_PERIOD,
) -> pd.DataFrame:
    """Generate future seasonal-naive forecasts without future actuals."""
    required = {
        "period_date",
        "value",
    }

    missing = required.difference(
        history.columns
    )

    if missing:
        raise ValueError(
            "Seasonal-naive history is missing columns: "
            f"{sorted(missing)}"
        )

    if history.empty:
        raise ValueError(
            "Seasonal-naive history cannot be empty."
        )

    data = history.copy()

    data["period_date"] = pd.to_datetime(
        data["period_date"]
    )

    data = data.sort_values(
        "period_date"
    ).reset_index(drop=True)

    if data["period_date"].duplicated().any():
        raise ValueError(
            "Seasonal-naive history contains duplicate periods."
        )

    history_values = data.set_index(
        "period_date"
    )["value"]

    rows: list[dict[str, object]] = []

    for horizon_step, forecast_period in enumerate(
        forecast_periods,
        start=1,
    ):
        reference_period = (
            pd.Timestamp(forecast_period)
            - pd.DateOffset(
                months=seasonal_period
            )
        )

        if reference_period not in history_values.index:
            raise ValueError(
                "Seasonal reference period "
                f"{reference_period.date()} is unavailable."
            )

        predicted = float(
            history_values.loc[
                reference_period
            ]
        )

        rows.append(
            {
                "forecast_period": pd.Timestamp(
                    forecast_period
                ),
                "reference_period": reference_period,
                "horizon_step": horizon_step,
                "predicted": predicted,
            }
        )

    return pd.DataFrame(rows)


def _series_metadata(
    series: pd.DataFrame,
) -> dict[str, object]:
    """Return stable metadata for one modelling series."""
    metadata: dict[str, object] = {}

    for column in METADATA_COLUMNS:
        if column not in series.columns:
            raise ValueError(
                f"Forecast history is missing {column}."
            )

        values = series[column].drop_duplicates()

        if len(values) != 1:
            raise ValueError(
                f"Series metadata is not unique for {column}."
            )

        metadata[column] = values.iloc[0]

    return metadata


def build_seasonal_naive_forward_forecasts(
    history: pd.DataFrame,
    origin: pd.Timestamp,
    forecast_periods: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Generate future seasonal-naive forecasts for all series."""
    frames: list[pd.DataFrame] = []

    for _, series in history.groupby(
        "series_id",
        sort=True,
    ):
        metadata = _series_metadata(
            series
        )

        forecast = (
            seasonal_naive_future_forecast(
                series,
                forecast_periods,
            )
        )

        result = forecast[
            [
                "forecast_period",
                "horizon_step",
                "predicted",
            ]
        ].copy()

        for column, value in metadata.items():
            result[column] = value

        result["model"] = (
            SEASONAL_NAIVE_MODEL
        )
        result["forecast_origin"] = origin

        frames.append(result)

    return pd.concat(
        frames,
        ignore_index=True,
    )[MODEL_FORECAST_COLUMNS]


def build_ets_forward_forecasts(
    history: pd.DataFrame,
    origin: pd.Timestamp,
    forecast_periods: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Generate future ETS forecasts for all series."""
    frames: list[pd.DataFrame] = []

    for series_id, series in history.groupby(
        "series_id",
        sort=True,
    ):
        metadata = _series_metadata(
            series
        )

        try:
            forecast = ets_forecast(
                series,
                forecast_periods,
            )
        except Exception as exc:
            raise RuntimeError(
                "Final ETS forecasting failed for "
                f"{series_id}."
            ) from exc

        result = forecast.copy()

        result["horizon_step"] = range(
            1,
            len(result) + 1,
        )

        for column, value in metadata.items():
            result[column] = value

        result["model"] = ETS_MODEL
        result["forecast_origin"] = origin

        frames.append(result)

    return pd.concat(
        frames,
        ignore_index=True,
    )[MODEL_FORECAST_COLUMNS]


def build_xgboost_forward_forecasts(
    history: pd.DataFrame,
    origin: pd.Timestamp,
    forecast_periods: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Generate pooled recursive XGBoost forecasts by metric."""
    frames: list[pd.DataFrame] = []

    for metric, metric_data in history.groupby(
        "metric",
        sort=True,
    ):
        try:
            forecast = pooled_recursive_forecast(
                metric_data,
                forecast_periods,
            )
        except Exception as exc:
            raise RuntimeError(
                "Final pooled XGBoost forecasting "
                f"failed for {metric}."
            ) from exc

        result = forecast.copy()

        result["model"] = XGBOOST_MODEL
        result["forecast_origin"] = origin

        frames.append(
            result[
                MODEL_FORECAST_COLUMNS
            ]
        )

    return pd.concat(
        frames,
        ignore_index=True,
    )


def build_all_model_forward_forecasts(
    history: pd.DataFrame,
    horizon: int = DEFAULT_FORWARD_HORIZON,
) -> pd.DataFrame:
    """Generate final-origin forecasts from all candidate models."""
    origin, forecast_periods = (
        build_future_periods(
            history,
            horizon=horizon,
        )
    )

    seasonal = (
        build_seasonal_naive_forward_forecasts(
            history,
            origin,
            forecast_periods,
        )
    )

    ets = build_ets_forward_forecasts(
        history,
        origin,
        forecast_periods,
    )

    xgboost = (
        build_xgboost_forward_forecasts(
            history,
            origin,
            forecast_periods,
        )
    )

    combined = pd.concat(
        [
            seasonal,
            ets,
            xgboost,
        ],
        ignore_index=True,
    )

    duplicate_keys = combined.duplicated(
        subset=[
            "model",
            "series_id",
            "forecast_period",
        ]
    )

    if duplicate_keys.any():
        raise ValueError(
            "Forward forecasts contain duplicate keys."
        )

    numeric_predictions = pd.to_numeric(
        combined["predicted"],
        errors="coerce",
    ).to_numpy(
        dtype=float
    )

    if not np.isfinite(
        numeric_predictions
    ).all():
        raise ValueError(
            "Forward forecasts contain non-finite predictions."
        )

    return combined.sort_values(
        [
            "model",
            "series_id",
            "horizon_step",
        ]
    ).reset_index(drop=True)


def select_winner_forward_forecasts(
    forecasts: pd.DataFrame,
    winners: pd.DataFrame,
    horizon: int = DEFAULT_FORWARD_HORIZON,
) -> pd.DataFrame:
    """Retain each series' Phase 4 winner-model future forecasts."""
    required_winner_columns = {
        "series_id",
        "best_model",
        "best_mae",
        "best_rmse",
        "best_smape",
    }

    missing = required_winner_columns.difference(
        winners.columns
    )

    if missing:
        raise ValueError(
            "Winner metadata is missing columns: "
            f"{sorted(missing)}"
        )

    if winners.empty:
        raise ValueError(
            "Winner metadata cannot be empty."
        )

    if winners["series_id"].duplicated().any():
        raise ValueError(
            "Winner metadata contains duplicate series."
        )

    unknown_models = set(
        winners["best_model"].unique()
    ).difference(
        SUPPORTED_MODELS
    )

    if unknown_models:
        raise ValueError(
            "Unsupported winner models: "
            f"{sorted(unknown_models)}"
        )

    winner_metadata = winners[
        [
            "series_id",
            "best_model",
            "best_mae",
            "best_rmse",
            "best_smape",
        ]
    ].copy()

    merged = forecasts.merge(
        winner_metadata,
        on="series_id",
        how="inner",
        validate="many_to_one",
    )

    selected = merged.loc[
        merged["model"]
        == merged["best_model"]
    ].copy()

    expected_series = set(
        winners["series_id"]
    )

    observed_series = set(
        selected["series_id"]
    )

    if observed_series != expected_series:
        missing_series = sorted(
            expected_series.difference(
                observed_series
            )
        )

        raise ValueError(
            "Final forecasts are missing winner series: "
            f"{missing_series}"
        )

    counts = selected.groupby(
        "series_id"
    )["horizon_step"].count()

    if not counts.eq(horizon).all():
        raise ValueError(
            "Each winner series must have exactly "
            f"{horizon} forward forecasts."
        )

    selected = selected.rename(
        columns={
            "best_mae": "backtest_mae",
            "best_rmse": "backtest_rmse",
            "best_smape": "backtest_smape",
        }
    )

    return selected[
        FINAL_FORECAST_COLUMNS
    ].sort_values(
        [
            "series_id",
            "horizon_step",
        ]
    ).reset_index(drop=True)
