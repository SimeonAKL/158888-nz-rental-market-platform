"""Build Phase 3 analytics-ready datasets."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

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

    print(
        f"Saved: {path}"
    )


def main() -> None:
    """Build Phase 3 analytics datasets."""

    print(
        "Loading clean rental bond data..."
    )

    source = load_clean_rental_bond()

    print(
        f"Loaded rows: {len(source):,}"
    )

    panel = build_monthly_panel(
        source
    )

    catalog = build_series_catalog(
        panel
    )

    quality = build_quality_summary(
        panel
    )

    output_dir = (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "analytics"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_csv(
        panel,
        output_dir
        / "monthly_panel.csv",
    )

    save_csv(
        catalog,
        output_dir
        / "series_catalog.csv",
    )

    save_csv(
        quality,
        output_dir
        / "quality_summary.csv",
    )

    print(
        "\n=== Analytics summary ==="
    )

    print(
        f"Panel rows: {len(panel):,}"
    )

    print(
        f"Series: "
        f"{panel['series_id'].nunique()}"
    )

    print(
        "Date range: "
        f"{panel['period_date'].min().date()} "
        "to "
        f"{panel['period_date'].max().date()}"
    )

    print(
        "Eligible series: "
        f"{int(catalog['eligible_for_forecasting'].sum())}"
        f"/{len(catalog)}"
    )

    print(
        "Complete series: "
        f"{int((catalog['missing_months'] == 0).sum())}"
        f"/{len(catalog)}"
    )

    print(
        "Quality PASS: "
        f"{int((quality['status'] == 'PASS').sum())}"
        f"/{len(quality)}"
    )

    print(
        "\nObservations per series:"
    )

    print(
        catalog[
            "n_observations"
        ].value_counts().sort_index()
    )

    print(
        "\nCompleteness rates:"
    )

    print(
        catalog[
            "completeness_rate"
        ].value_counts().sort_index()
    )


if __name__ == "__main__":
    main()
