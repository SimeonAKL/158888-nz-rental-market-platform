"""Pooled recursive XGBoost forecasting."""

from __future__ import annotations

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from rmp.forecasting.features import build_forecasting_features

BASE_FEATURE_COLUMNS = [
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_6",
    "lag_12",
    "rolling_mean_3",
    "rolling_mean_6",
    "rolling_mean_12",
    "month",
    "quarter",
    "year",
]


def build_xgboost_model() -> XGBRegressor:
    """Create the fixed pooled XGBoost forecasting model."""

    return XGBRegressor(
        objective="reg:squarederror",
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=2,
        tree_method="hist",
    )


def _location_feature_names(
    location_keys: list[str],
) -> list[str]:
    """Return deterministic one-hot geography-location feature names."""

    return [
        f"location_{location_key}"
        for location_key in location_keys
    ]


def _add_location_features(
    frame: pd.DataFrame,
    location_keys: list[str],
) -> pd.DataFrame:
    """Add one-hot indicators for unique geography-location identities."""

    result = frame.copy()

    geography_location = (
        result["geography_level"].astype(str)
        + "_"
        + pd.to_numeric(
            result["location_id"],
            errors="raise",
        )
        .astype(int)
        .astype(str)
    )

    for location_key in location_keys:
        result[
            f"location_{location_key}"
        ] = (
            geography_location
            == location_key
        ).astype(float)

    return result


def prepare_training_data(
    history: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.Series,
    list[str],
    list[str],
]:
    """Build leakage-safe pooled training data."""

    required = {
        "period_date",
        "series_id",
        "geography_level",
        "location_id",
        "metric",
        "value",
    }

    missing = required.difference(
        history.columns
    )

    if missing:
        raise ValueError(
            "Missing required history columns: "
            f"{sorted(missing)}"
        )

    if history.empty:
        raise ValueError(
            "History cannot be empty."
        )

    if history["metric"].nunique() != 1:
        raise ValueError(
            "Pooled XGBoost must be trained "
            "on one target metric at a time."
        )

    data = history.copy()

    data["period_date"] = pd.to_datetime(
        data["period_date"]
    )

    data["value"] = pd.to_numeric(
        data["value"],
        errors="raise",
    )

    location_keys = sorted(
        (
            data["geography_level"].astype(str)
            + "_"
            + pd.to_numeric(
                data["location_id"],
                errors="raise",
            )
            .astype(int)
            .astype(str)
        )
        .unique()
        .tolist()
    )

    featured = build_forecasting_features(
        data
    )

    featured = _add_location_features(
        featured,
        location_keys,
    )

    location_columns = (
        _location_feature_names(
            location_keys
        )
    )

    feature_columns = (
        BASE_FEATURE_COLUMNS
        + location_columns
    )

    training = featured.dropna(
        subset=(
            feature_columns
            + ["value"]
        )
    ).copy()

    if training.empty:
        raise ValueError(
            "No complete feature rows are "
            "available for XGBoost training."
        )

    x_train = training[
        feature_columns
    ].astype(float)

    y_train = training[
        "value"
    ].astype(float)

    if not np.isfinite(
        x_train.to_numpy()
    ).all():
        raise ValueError(
            "Training features contain "
            "non-finite values."
        )

    if not np.isfinite(
        y_train.to_numpy()
    ).all():
        raise ValueError(
            "Training targets contain "
            "non-finite values."
        )

    return (
        x_train,
        y_train,
        location_keys,
        feature_columns,
    )


def pooled_recursive_forecast(
    history: pd.DataFrame,
    forecast_periods: pd.Series | pd.DatetimeIndex,
) -> pd.DataFrame:
    """Fit pooled XGBoost and recursively forecast all series.

    A separate pooled model is fitted for one target metric at one
    rolling origin. All regional series for that metric contribute
    training observations.

    Forecasts are produced recursively. After each forecast month,
    predicted values are appended to the working history and become
    available to lag and rolling features for the next forecast step.
    Future observed target values are never supplied to this function.
    """

    if history.empty:
        raise ValueError(
            "History cannot be empty."
        )

    data = history.copy()

    data["period_date"] = pd.to_datetime(
        data["period_date"]
    )

    if data["metric"].nunique() != 1:
        raise ValueError(
            "Recursive forecasting requires "
            "exactly one target metric."
        )

    series_end_dates = data.groupby(
        "series_id"
    )["period_date"].max()

    if series_end_dates.nunique() != 1:
        raise ValueError(
            "All pooled series must end "
            "at the same forecast origin."
        )

    origin = pd.Timestamp(
        series_end_dates.iloc[0]
    )

    future_dates = pd.DatetimeIndex(
        pd.to_datetime(
            forecast_periods
        )
    )

    if len(future_dates) < 1:
        raise ValueError(
            "At least one forecast period is required."
        )

    expected_future = pd.date_range(
        start=(
            origin
            + pd.offsets.MonthBegin(1)
        ),
        periods=len(future_dates),
        freq="MS",
    )

    if not future_dates.equals(
        expected_future
    ):
        raise ValueError(
            "Forecast periods must be consecutive "
            "months immediately after the origin."
        )

    (
        x_train,
        y_train,
        location_keys,
        feature_columns,
    ) = prepare_training_data(
        data
    )

    model = build_xgboost_model()

    model.fit(
        x_train,
        y_train,
    )

    metadata_columns = [
        "series_id",
        "geography_level",
        "location_id",
        "location_name",
        "metric",
    ]

    missing_metadata = set(
        metadata_columns
    ).difference(
        data.columns
    )

    if missing_metadata:
        raise ValueError(
            "Missing recursive forecast metadata: "
            f"{sorted(missing_metadata)}"
        )

    metadata = (
        data.sort_values(
            [
                "series_id",
                "period_date",
            ]
        )
        .groupby(
            "series_id",
            as_index=False,
        )
        .tail(1)[metadata_columns]
        .sort_values(
            "series_id"
        )
        .reset_index(drop=True)
    )

    working_history = data.copy()

    forecast_frames: list[
        pd.DataFrame
    ] = []

    for horizon_step, forecast_date in enumerate(
        future_dates,
        start=1,
    ):
        new_rows = metadata.copy()

        new_rows["period_date"] = (
            forecast_date
        )

        new_rows["value"] = np.nan

        candidate = pd.concat(
            [
                working_history,
                new_rows,
            ],
            ignore_index=True,
            sort=False,
        )

        featured = build_forecasting_features(
            candidate
        )

        current = featured.loc[
            featured["period_date"]
            == forecast_date
        ].copy()

        current = _add_location_features(
            current,
            location_keys,
        )

        current = current.sort_values(
            "series_id"
        ).reset_index(drop=True)

        if current[
            feature_columns
        ].isna().any().any():
            raise ValueError(
                "Recursive forecast features "
                "contain missing values."
            )

        x_future = current[
            feature_columns
        ].astype(float)

        predicted = model.predict(
            x_future
        ).astype(float)

        if not np.isfinite(
            predicted
        ).all():
            raise ValueError(
                "XGBoost produced non-finite forecasts."
            )

        result = current[
            metadata_columns
        ].copy()

        result["forecast_period"] = (
            forecast_date
        )

        result["horizon_step"] = (
            horizon_step
        )

        result["predicted"] = predicted

        forecast_frames.append(
            result
        )

        predicted_rows = metadata.copy()

        predicted_rows["period_date"] = (
            forecast_date
        )

        predicted_rows["value"] = (
            predicted
        )

        working_history = pd.concat(
            [
                working_history,
                predicted_rows,
            ],
            ignore_index=True,
            sort=False,
        )

    return pd.concat(
        forecast_frames,
        ignore_index=True,
    ).sort_values(
        [
            "series_id",
            "forecast_period",
        ]
    ).reset_index(drop=True)
