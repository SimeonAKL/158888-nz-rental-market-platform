"""Build final six-month forecasts under the production policy."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from rmp.forecasting.final_forecast import (
    DEFAULT_FORWARD_HORIZON,
    build_production_forward_forecasts,
)
from rmp.forecasting.policy import (
    FORECAST_POLICY,
    PRODUCTION_MODEL,
)
from rmp.forecasting.selection import (
    select_forecasting_series,
)

PANEL_PATH = Path("data/processed/analytics/monthly_panel.csv")

CATALOG_PATH = Path("data/processed/analytics/series_catalog.csv")

METRICS_PATH = Path("data/processed/forecasting/metrics_by_series.csv")

OUTPUT_PATH = Path("data/processed/forecasting/final_forward_forecasts.csv")


def main() -> None:
    """Build and save final production forward forecasts."""
    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=["period_date"],
    )

    catalog = pd.read_csv(
        CATALOG_PATH,
        parse_dates=["continuous_start"],
    )

    metrics_by_series = pd.read_csv(METRICS_PATH)

    history = select_forecasting_series(
        panel,
        catalog,
    )

    final = build_production_forward_forecasts(
        history,
        metrics_by_series,
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

    print("Final production forecasting complete.")
    print()
    print(f"Forecast policy: {FORECAST_POLICY}")
    print(f"Production model: {PRODUCTION_MODEL}")
    print(f"Forecast origin: {final['forecast_origin'].iloc[0]}")
    print(f"Forecast period: {final['forecast_period'].min()} to {final['forecast_period'].max()}")
    print(f"Series: {final['series_id'].nunique()}")
    print(f"Rows: {len(final)}")
    print(f"Horizon: {final['horizon_step'].nunique()} months")

    print()
    print("=== PRODUCTION MODELS ===")
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
