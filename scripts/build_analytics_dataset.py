"""Build Phase 3 analytics-ready datasets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from rmp.analytics.historical_summary import (
    build_historical_summary,
    build_monthly_seasonality_summary,
    build_recent_history_summary,
)
from rmp.analytics.modelling_readiness import (
    build_modelling_readiness,
)
from rmp.analytics.monthly_panel import (
    build_monthly_panel,
)
from rmp.analytics.series_quality import (
    build_quality_summary,
    build_series_catalog,
)
from rmp.config import (
    PROJECT_ROOT,
    get_database_config,
)


def create_database_engine():
    """Create the project PostgreSQL engine."""

    config = get_database_config()

    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
        database=config["database"],
    )

    return create_engine(database_url)


def load_clean_rental_bond() -> pd.DataFrame:
    """Load required clean rental bond fields."""

    engine = create_database_engine()

    query = text(
        """
        SELECT
            period_date,
            geography_level,
            location_id,
            location_name,
            bonds_lodged,
            median_rent,
            is_provisional,
            source_snapshot_id
        FROM clean.rental_bond
        ORDER BY
            geography_level,
            location_id,
            period_date
        """
    )

    with engine.connect() as conn:
        return pd.read_sql_query(
            query,
            conn,
        )


def save_csv(
    df: pd.DataFrame,
    path: Path,
) -> None:
    """Save a dataframe as CSV."""

    df.to_csv(
        path,
        index=False,
    )

    print(f"Saved: {path}")


def main() -> None:
    """Build all Phase 3 analytics datasets."""

    print("Loading clean rental bond data...")

    source = load_clean_rental_bond()

    print(f"Loaded rows: {len(source):,}")

    panel = build_monthly_panel(source)

    catalog = build_series_catalog(panel)

    quality = build_quality_summary(panel)

    historical_summary = build_historical_summary(panel)

    monthly_seasonality = build_monthly_seasonality_summary(panel)

    recent_history = build_recent_history_summary(
        panel,
        recent_months=24,
    )

    readiness = build_modelling_readiness(
        panel,
        catalog,
        quality,
    )

    output_dir = PROJECT_ROOT / "data" / "processed" / "analytics"

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_csv(
        panel,
        output_dir / "monthly_panel.csv",
    )

    save_csv(
        catalog,
        output_dir / "series_catalog.csv",
    )

    save_csv(
        quality,
        output_dir / "quality_summary.csv",
    )

    save_csv(
        historical_summary,
        output_dir / "historical_summary.csv",
    )

    save_csv(
        monthly_seasonality,
        output_dir / "monthly_seasonality.csv",
    )

    save_csv(
        recent_history,
        output_dir / "recent_history_summary.csv",
    )

    save_csv(
        readiness,
        output_dir / "modelling_readiness.csv",
    )

    print("\n=== Analytics summary ===")

    print(f"Panel rows: {len(panel):,}")

    print(f"Series: {panel['series_id'].nunique()}")

    print(f"Date range: {panel['period_date'].min().date()} to {panel['period_date'].max().date()}")

    print(f"Eligible series: {int(catalog['eligible_for_forecasting'].sum())}/{len(catalog)}")

    print(f"Complete series: {int((catalog['missing_months'] == 0).sum())}/{len(catalog)}")

    print(f"Quality PASS: {int((quality['status'] == 'PASS').sum())}/{len(quality)}")

    print(f"Historical summaries: {len(historical_summary)}")

    print(f"Monthly seasonality rows: {len(monthly_seasonality)}")

    print(f"Recent-history summaries: {len(recent_history)}")

    print(f"Modelling ready: {bool(readiness.iloc[0]['dataset_ready'])}")

    print("\nObservations per series:")

    print(catalog["n_observations"].value_counts().sort_index())

    print("\nCompleteness rates:")

    print(catalog["completeness_rate"].value_counts().sort_index())


if __name__ == "__main__":
    main()
