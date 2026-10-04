"""Series selection rules for forecasting evaluation."""

from __future__ import annotations

import pandas as pd

EXCLUDED_FORECAST_SERIES = {
    "territorial_authority_76_bonds_lodged",
    "territorial_authority_76_median_rent",
}


def select_forecasting_series(
    panel: pd.DataFrame,
    catalog: pd.DataFrame,
) -> pd.DataFrame:
    """Return the quality-gated continuous series used for forecasting.

    Forecasting selection is based on the Phase 3 series catalog:

    - only series marked ``eligible_for_forecasting`` are retained;
    - each retained series is truncated to its latest continuous
      monthly history beginning at ``continuous_start``;
    - Auckland Territorial Authority series are excluded because they
      duplicate Auckland Region in the current source geography.

    Historical analytics can still retain all valid series regardless
    of forecasting eligibility.
    """

    required_panel_columns = {
        "series_id",
        "period_date",
    }

    required_catalog_columns = {
        "series_id",
        "continuous_start",
        "continuous_months",
        "eligible_for_forecasting",
    }

    missing_panel = required_panel_columns.difference(
        panel.columns
    )

    missing_catalog = required_catalog_columns.difference(
        catalog.columns
    )

    if missing_panel:
        raise ValueError(
            "Panel is missing required columns: "
            f"{sorted(missing_panel)}"
        )

    if missing_catalog:
        raise ValueError(
            "Catalog is missing required columns: "
            f"{sorted(missing_catalog)}"
        )

    data = panel.copy()
    metadata = catalog.copy()

    data["period_date"] = pd.to_datetime(
        data["period_date"]
    )

    metadata["continuous_start"] = pd.to_datetime(
        metadata["continuous_start"]
    )

    eligible = metadata.loc[
        metadata["eligible_for_forecasting"]
    ].copy()

    eligible = eligible.loc[
        ~eligible["series_id"].isin(
            EXCLUDED_FORECAST_SERIES
        )
    ].copy()

    if eligible.empty:
        raise ValueError(
            "No forecast-eligible series remain after selection."
        )

    selected = data.merge(
        eligible[
            [
                "series_id",
                "continuous_start",
                "continuous_months",
            ]
        ],
        on="series_id",
        how="inner",
        validate="many_to_one",
    )

    selected = selected.loc[
        selected["period_date"]
        >= selected["continuous_start"]
    ].copy()

    if selected.empty:
        raise ValueError(
            "No forecasting observations remain after "
            "continuous-history filtering."
        )

    # Structural safety check: every selected series must form one
    # complete monthly sequence after truncation.
    for series_id, group in selected.groupby(
        "series_id",
        sort=True,
    ):
        periods = pd.DatetimeIndex(
            group["period_date"]
            .drop_duplicates()
            .sort_values()
        )

        expected = pd.date_range(
            start=periods.min(),
            end=periods.max(),
            freq="MS",
        )

        if not periods.equals(expected):
            raise ValueError(
                f"{series_id} is not continuous after "
                "forecasting selection."
            )

    return (
        selected.drop(
            columns=[
                "continuous_start",
                "continuous_months",
            ]
        )
        .sort_values(
            [
                "series_id",
                "period_date",
            ]
        )
        .reset_index(drop=True)
    )
