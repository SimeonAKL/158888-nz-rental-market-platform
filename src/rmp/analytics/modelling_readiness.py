"""Modelling-readiness checks for the Phase 3 analytics dataset."""

from __future__ import annotations

import pandas as pd

DEFAULT_FORECAST_HORIZON = 6
DEFAULT_SEASONAL_PERIOD = 12
DEFAULT_N_ORIGINS = 12
DEFAULT_MIN_HISTORY_MONTHS = 60


def build_modelling_readiness(
    panel: pd.DataFrame,
    catalog: pd.DataFrame,
    quality: pd.DataFrame,
) -> pd.DataFrame:
    """Build a one-row modelling-readiness summary.

    The result records whether the analytics dataset satisfies
    the structural requirements for Phase 4 forecasting.
    """

    required_panel_columns = {
        "period_date",
        "series_id",
        "metric",
        "value",
    }

    required_catalog_columns = {
        "series_id",
        "n_observations",
        "missing_months",
        "eligible_for_forecasting",
    }

    required_quality_columns = {
        "series_id",
        "status",
    }

    missing_panel = required_panel_columns.difference(
        panel.columns
    )

    missing_catalog = required_catalog_columns.difference(
        catalog.columns
    )

    missing_quality = required_quality_columns.difference(
        quality.columns
    )

    if missing_panel:
        raise ValueError(
            "Missing required panel columns: "
            f"{sorted(missing_panel)}"
        )

    if missing_catalog:
        raise ValueError(
            "Missing required catalog columns: "
            f"{sorted(missing_catalog)}"
        )

    if missing_quality:
        raise ValueError(
            "Missing required quality columns: "
            f"{sorted(missing_quality)}"
        )

    data = panel.copy()

    data["period_date"] = pd.to_datetime(
        data["period_date"]
    )

    n_series = int(
        data["series_id"].nunique()
    )

    complete_series = int(
        (catalog["missing_months"] == 0).sum()
    )

    eligible_series = int(
        catalog[
            "eligible_for_forecasting"
        ].sum()
    )

    quality_pass_series = int(
        (quality["status"] == "PASS").sum()
    )

    minimum_observations = int(
        catalog["n_observations"].min()
    )

    required_for_evaluation = (
        DEFAULT_MIN_HISTORY_MONTHS
        + DEFAULT_FORECAST_HORIZON
        + DEFAULT_N_ORIGINS
        - 1
    )

    rolling_origin_ready = (
        minimum_observations
        >= required_for_evaluation
    )

    feature_history_ready = (
        minimum_observations
        > DEFAULT_SEASONAL_PERIOD
    )

    all_series_complete = (
        complete_series == n_series
    )

    all_series_eligible = (
        eligible_series == n_series
    )

    all_quality_pass = (
        quality_pass_series == n_series
    )

    dataset_ready = (
        all_series_complete
        and all_series_eligible
        and all_quality_pass
        and rolling_origin_ready
        and feature_history_ready
    )

    return pd.DataFrame(
        [
            {
                "dataset_ready": dataset_ready,
                "n_series": n_series,
                "complete_series": complete_series,
                "forecast_eligible_series": (
                    eligible_series
                ),
                "quality_pass_series": (
                    quality_pass_series
                ),
                "minimum_observations": (
                    minimum_observations
                ),
                "start_period": (
                    data["period_date"].min()
                ),
                "end_period": (
                    data["period_date"].max()
                ),
                "forecast_horizon": (
                    DEFAULT_FORECAST_HORIZON
                ),
                "seasonal_period": (
                    DEFAULT_SEASONAL_PERIOD
                ),
                "rolling_origins": (
                    DEFAULT_N_ORIGINS
                ),
                "minimum_history_months": (
                    DEFAULT_MIN_HISTORY_MONTHS
                ),
                "rolling_origin_ready": (
                    rolling_origin_ready
                ),
                "feature_history_ready": (
                    feature_history_ready
                ),
            }
        ]
    )
