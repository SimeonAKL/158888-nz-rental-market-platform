"""Series selection rules for forecasting evaluation."""

from __future__ import annotations

import pandas as pd

EXCLUDED_FORECAST_SERIES = {
    "territorial_authority_76_bonds_lodged",
    "territorial_authority_76_median_rent",
}


def select_forecasting_series(
    panel: pd.DataFrame,
) -> pd.DataFrame:
    """Return the non-duplicated series used for forecasting.

    Auckland Territorial Authority is geographically equivalent to
    Auckland Region in the current project dataset. The two Auckland TA
    series are therefore excluded from forecasting to avoid duplicate
    weighting while retaining the regional Auckland series.
    """

    if "series_id" not in panel.columns:
        raise ValueError(
            "Missing required column: series_id"
        )

    selected = panel.loc[
        ~panel["series_id"].isin(
            EXCLUDED_FORECAST_SERIES
        )
    ].copy()

    if selected.empty:
        raise ValueError(
            "No forecasting series remain after selection."
        )

    return selected.reset_index(drop=True)
