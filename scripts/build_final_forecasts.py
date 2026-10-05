"""Build final six-month winner-model forward forecasts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from rmp.forecasting.final_forecast import (
    DEFAULT_FORWARD_HORIZON,
    build_all_model_forward_forecasts,
    select_winner_forward_forecasts,
)
from rmp.forecasting.selection import (
    select_forecasting_series,
)

PANEL_PATH = Path("data/processed/analytics/monthly_panel.csv")

CATALOG_PATH = Path("data/processed/analytics/series_catalog.csv")

WINNERS_PATH = Path("data/processed/forecasting/series_model_winners.csv")

OUTPUT_PATH = Path("data/processed/forecasting/final_forward_forecasts.csv")


def main() -> None:
    """Build and save final forward forecasts."""
    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=["period_date"],
    )

    catalog = pd.read_csv(
        CATALOG_PATH,
        parse_dates=["continuous_start"],
    )

    winners = pd.read_csv(WINNERS_PATH)

    history = select_forecasting_series(
        panel,
        catalog,
    )

    all_forecasts = build_all_model_forward_forecasts(
        history,
        horizon=DEFAULT_FORWARD_HORIZON,
    )

    final = select_winner_forward_forecasts(
        all_forecasts,
        winners,
        horizon=DEFAULT_FORWARD_HORIZON,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("Final forward forecasting complete.")
    print()
    print(f"Forecast origin: {final['forecast_origin'].iloc[0]}")
    print(f"Forecast period: {final['forecast_period'].min()} to {final['forecast_period'].max()}")
    print(f"Series: {final['series_id'].nunique()}")
    print(f"Rows: {len(final)}")
    print(f"Horizon: {final['horizon_step'].nunique()} months")

    print()
    print("=== WINNER MODELS ===")
    print(
        final[
            [
                "series_id",
                "model",
            ]
        ]
        .drop_duplicates()["model"]
        .value_counts()
    )

    print()
    print(f"Output written to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
