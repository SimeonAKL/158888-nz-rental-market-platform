"""Modelling-readiness checks for the Phase 3 analytics dataset."""

from __future__ import annotations

import pandas as pd

DEFAULT_FORECAST_HORIZON = 6
DEFAULT_SEASONAL_PERIOD = 12
DEFAULT_N_ORIGINS = 12
DEFAULT_MIN_HISTORY_MONTHS = 60

REQUIRED_CONTINUOUS_MONTHS = (
    DEFAULT_MIN_HISTORY_MONTHS + DEFAULT_FORECAST_HORIZON + DEFAULT_N_ORIGINS - 1
)


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
        "continuous_months",
        "eligible_for_forecasting",
    }

    required_quality_columns = {
        "series_id",
        "status",
    }

    missing_panel = required_panel_columns.difference(panel.columns)

    missing_catalog = required_catalog_columns.difference(catalog.columns)

    missing_quality = required_quality_columns.difference(quality.columns)

    if missing_panel:
        raise ValueError(f"Missing required panel columns: {sorted(missing_panel)}")

    if missing_catalog:
        raise ValueError(f"Missing required catalog columns: {sorted(missing_catalog)}")

    if missing_quality:
        raise ValueError(f"Missing required quality columns: {sorted(missing_quality)}")

    data = panel.copy()

    data["period_date"] = pd.to_datetime(data["period_date"])

    n_series = int(data["series_id"].nunique())

    complete_series = int((catalog["missing_months"] == 0).sum())

    eligible_series = int(catalog["eligible_for_forecasting"].sum())

    quality_pass_series = int((quality["status"] == "PASS").sum())

    minimum_observations = int(catalog["n_observations"].min())

    eligible_catalog = catalog.loc[catalog["eligible_for_forecasting"]].copy()

    if eligible_catalog.empty:
        minimum_eligible_continuous_months = 0
    else:
        minimum_eligible_continuous_months = int(eligible_catalog["continuous_months"].min())

    eligible_series_ids = set(eligible_catalog["series_id"])

    quality_pass_series_ids = set(
        quality.loc[
            quality["status"] == "PASS",
            "series_id",
        ]
    )

    eligible_quality_pass_series = len(eligible_series_ids & quality_pass_series_ids)

    rolling_origin_ready = (
        eligible_series > 0 and minimum_eligible_continuous_months >= REQUIRED_CONTINUOUS_MONTHS
    )

    feature_history_ready = (
        eligible_series > 0 and minimum_eligible_continuous_months > DEFAULT_SEASONAL_PERIOD
    )

    eligible_quality_ready = eligible_series > 0 and eligible_quality_pass_series == eligible_series

    dataset_ready = rolling_origin_ready and feature_history_ready and eligible_quality_ready

    return pd.DataFrame(
        [
            {
                "dataset_ready": dataset_ready,
                "n_series": n_series,
                "complete_series": complete_series,
                "forecast_eligible_series": (eligible_series),
                "quality_pass_series": (quality_pass_series),
                "eligible_quality_pass_series": (eligible_quality_pass_series),
                "minimum_observations": (minimum_observations),
                "minimum_eligible_continuous_months": (minimum_eligible_continuous_months),
                "start_period": (data["period_date"].min()),
                "end_period": (data["period_date"].max()),
                "forecast_horizon": (DEFAULT_FORECAST_HORIZON),
                "seasonal_period": (DEFAULT_SEASONAL_PERIOD),
                "rolling_origins": (DEFAULT_N_ORIGINS),
                "minimum_history_months": (DEFAULT_MIN_HISTORY_MONTHS),
                "required_continuous_months": (REQUIRED_CONTINUOUS_MONTHS),
                "rolling_origin_ready": (rolling_origin_ready),
                "feature_history_ready": (feature_history_ready),
            }
        ]
    )
