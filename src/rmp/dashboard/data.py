"""Cached data loaders for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ANALYTICS_DIR = Path(
    "data/processed/analytics"
)

FORECASTING_DIR = Path(
    "data/processed/forecasting"
)

ANOMALY_DIR = Path(
    "data/processed/anomaly"
)


def _require_file(
    path: Path,
) -> None:
    """Raise a clear error when a dashboard data file is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Dashboard data file not found: {path}"
        )


@st.cache_data(show_spinner=False)
def load_monthly_panel() -> pd.DataFrame:
    """Load the complete analytical monthly panel."""
    path = (
        ANALYTICS_DIR
        / "monthly_panel.csv"
    )

    _require_file(path)

    data = pd.read_csv(
        path,
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
        data.columns
    )

    if missing:
        raise ValueError(
            "Monthly panel is missing required columns: "
            f"{sorted(missing)}"
        )

    return data.sort_values(
        [
            "series_id",
            "period_date",
        ]
    ).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_series_catalog() -> pd.DataFrame:
    """Load analytical-series quality and forecasting eligibility metadata."""
    path = (
        ANALYTICS_DIR
        / "series_catalog.csv"
    )

    _require_file(path)

    data = pd.read_csv(path)

    if "continuous_start" in data.columns:
        data["continuous_start"] = pd.to_datetime(
            data["continuous_start"],
            errors="coerce",
        )

    return data


@st.cache_data(show_spinner=False)
def load_monthly_seasonality() -> pd.DataFrame:
    """Load monthly seasonality statistics."""
    path = (
        ANALYTICS_DIR
        / "monthly_seasonality.csv"
    )

    _require_file(path)

    data = pd.read_csv(path)

    required = {
        "series_id",
        "metric",
        "geography_level",
        "location_id",
        "location_name",
        "month",
        "median_value",
        "mean_value",
        "minimum_value",
        "maximum_value",
        "n_observations",
    }

    missing = required.difference(
        data.columns
    )

    if missing:
        raise ValueError(
            "Monthly seasonality data is missing required columns: "
            f"{sorted(missing)}"
        )

    return data.sort_values(
        [
            "series_id",
            "month",
        ]
    ).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_combined_predictions() -> pd.DataFrame:
    """Load Phase 4 rolling-origin predictions for all candidate models."""
    path = (
        FORECASTING_DIR
        / "combined_predictions.csv"
    )

    _require_file(path)

    data = pd.read_csv(
        path,
        parse_dates=[
            "origin",
            "forecast_period",
        ],
    )

    return data


@st.cache_data(show_spinner=False)
def load_metrics_by_origin() -> pd.DataFrame:
    """Load unified rolling-origin model metrics."""
    path = (
        FORECASTING_DIR
        / "metrics_by_origin.csv"
    )

    _require_file(path)

    data = pd.read_csv(path)

    if "origin" in data.columns:
        data["origin"] = pd.to_datetime(
            data["origin"],
            errors="coerce",
        )

    return data


@st.cache_data(show_spinner=False)
def load_metrics_by_series() -> pd.DataFrame:
    """Load unified model metrics aggregated by series."""
    path = (
        FORECASTING_DIR
        / "metrics_by_series.csv"
    )

    _require_file(path)

    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_metrics_by_horizon() -> pd.DataFrame:
    """Load model metrics aggregated by forecast horizon."""
    path = (
        FORECASTING_DIR
        / "metrics_by_horizon.csv"
    )

    _require_file(path)

    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_model_comparison() -> pd.DataFrame:
    """Load overall Phase 4 candidate-model comparison."""
    path = (
        FORECASTING_DIR
        / "model_comparison.csv"
    )

    _require_file(path)

    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_series_model_winners() -> pd.DataFrame:
    """Load the selected winner model and backtest metrics for each series."""
    path = (
        FORECASTING_DIR
        / "series_model_winners.csv"
    )

    _require_file(path)

    data = pd.read_csv(path)

    required = {
        "series_id",
        "metric",
        "geography_level",
        "location_id",
        "location_name",
        "best_model",
        "best_mae",
        "best_rmse",
        "best_smape",
    }

    missing = required.difference(
        data.columns
    )

    if missing:
        raise ValueError(
            "Series winner file is missing required columns: "
            f"{sorted(missing)}"
        )

    return data.sort_values(
        "series_id"
    ).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_final_forward_forecasts() -> pd.DataFrame:
    """Load final six-month winner-model forecasts."""
    path = (
        FORECASTING_DIR
        / "final_forward_forecasts.csv"
    )

    _require_file(path)

    data = pd.read_csv(
        path,
        parse_dates=[
            "forecast_origin",
            "forecast_period",
        ],
    )

    required = {
        "series_id",
        "metric",
        "geography_level",
        "location_id",
        "location_name",
        "model",
        "forecast_origin",
        "forecast_period",
        "horizon_step",
        "predicted",
        "backtest_mae",
        "backtest_rmse",
        "backtest_smape",
    }

    missing = required.difference(
        data.columns
    )

    if missing:
        raise ValueError(
            "Final forecast file is missing required columns: "
            f"{sorted(missing)}"
        )

    return data.sort_values(
        [
            "series_id",
            "horizon_step",
        ]
    ).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_anomaly_summary() -> pd.DataFrame:
    """Load consolidated dashboard-ready anomaly results."""
    path = (
        ANOMALY_DIR
        / "anomaly_summary.csv"
    )

    _require_file(path)

    data = pd.read_csv(
        path,
        parse_dates=["period_date"],
    )

    return data


@st.cache_data(show_spinner=False)
def load_historical_anomalies() -> pd.DataFrame:
    """Load historical anomaly detector output."""
    path = (
        ANOMALY_DIR
        / "historical_anomalies.csv"
    )

    _require_file(path)

    data = pd.read_csv(
        path,
        parse_dates=["period_date"],
    )

    return data


@st.cache_data(show_spinner=False)
def load_forecast_anomalies() -> pd.DataFrame:
    """Load forecast-residual anomaly detector output."""
    path = (
        ANOMALY_DIR
        / "forecast_anomalies.csv"
    )

    _require_file(path)

    data = pd.read_csv(
        path,
        parse_dates=[
            "origin",
            "forecast_period",
        ],
    )

    return data


@st.cache_data(show_spinner=False)
def load_anomaly_validation() -> pd.DataFrame:
    """Load Phase 5A anomaly validation results."""
    path = (
        ANOMALY_DIR
        / "anomaly_validation_summary.csv"
    )

    _require_file(path)

    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_anomaly_metadata() -> pd.DataFrame:
    """Load Phase 5A anomaly metadata summary."""
    path = (
        ANOMALY_DIR
        / "anomaly_metadata_summary.csv"
    )

    _require_file(path)

    return pd.read_csv(path)


# ---------------------------------------------------------------------------
# Compatibility aliases
# ---------------------------------------------------------------------------
#
# Keep these lightweight aliases so existing dashboard pages that were built
# during earlier Phase 5B work can continue to use the older loader names.


def load_predictions() -> pd.DataFrame:
    """Compatibility alias for combined rolling-origin predictions."""
    return load_combined_predictions()


def load_winners() -> pd.DataFrame:
    """Compatibility alias for series-level winner metadata."""
    return load_series_model_winners()


def load_forecasts() -> pd.DataFrame:
    """Compatibility alias for final forward forecasts."""
    return load_final_forward_forecasts()
