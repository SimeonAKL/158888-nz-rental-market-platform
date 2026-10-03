"""Build analytics-ready monthly rental market panels."""

from __future__ import annotations

import pandas as pd

CORE_METRICS = (
    "median_rent",
    "bonds_lodged",
)

EXCLUDED_LOCATION_IDS = {
    -99,  # ALL
    -1,   # NA / unknown
}

AUCKLAND_TA_LOCATION_ID = 76


def select_core_geographies(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Select the core project geography scope.

    Core scope:
    - all valid New Zealand Regions
    - Auckland Territorial Authority only

    Aggregate and unknown geography rows are excluded.
    """

    required_columns = {
        "geography_level",
        "location_id",
    }

    missing = required_columns.difference(df.columns)

    if missing:
        raise ValueError(
            "Missing required geography columns: "
            f"{sorted(missing)}"
        )

    valid_regions = (
        (df["geography_level"] == "region")
        & ~df["location_id"].isin(
            EXCLUDED_LOCATION_IDS
        )
    )

    auckland_ta = (
        (
            df["geography_level"]
            == "territorial_authority"
        )
        & (
            df["location_id"]
            == AUCKLAND_TA_LOCATION_ID
        )
    )

    result = df.loc[
        valid_regions | auckland_ta
    ].copy()

    return result


def reshape_metrics(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Convert the clean wide table to long modelling format."""

    required_columns = {
        "period_date",
        "geography_level",
        "location_id",
        "location_name",
        "median_rent",
        "bonds_lodged",
        "is_provisional",
        "source_snapshot_id",
    }

    missing = required_columns.difference(df.columns)

    if missing:
        raise ValueError(
            "Missing required analytics columns: "
            f"{sorted(missing)}"
        )

    panel = df.melt(
        id_vars=[
            "period_date",
            "geography_level",
            "location_id",
            "location_name",
            "is_provisional",
            "source_snapshot_id",
        ],
        value_vars=list(CORE_METRICS),
        var_name="metric",
        value_name="value",
    )

    panel["period_date"] = pd.to_datetime(
        panel["period_date"]
    )

    panel["value"] = pd.to_numeric(
        panel["value"],
        errors="coerce",
    )

    panel["series_id"] = (
        panel["geography_level"].astype(str)
        + "_"
        + panel["location_id"].astype(str)
        + "_"
        + panel["metric"].astype(str)
    )

    return panel


def validate_monthly_panel(
    panel: pd.DataFrame,
) -> None:
    """Run structural validation on the analytics panel."""

    required_columns = {
        "period_date",
        "series_id",
        "geography_level",
        "location_id",
        "location_name",
        "metric",
        "value",
        "is_provisional",
        "source_snapshot_id",
    }

    missing = required_columns.difference(
        panel.columns
    )

    if missing:
        raise ValueError(
            "Monthly panel is missing columns: "
            f"{sorted(missing)}"
        )

    invalid_metrics = set(
        panel["metric"].dropna().unique()
    ).difference(CORE_METRICS)

    if invalid_metrics:
        raise ValueError(
            "Unexpected metrics found: "
            f"{sorted(invalid_metrics)}"
        )

    duplicates = panel.duplicated(
        subset=[
            "period_date",
            "series_id",
        ],
        keep=False,
    )

    if duplicates.any():
        duplicate_count = int(
            duplicates.sum()
        )

        raise ValueError(
            "Duplicate monthly observations found: "
            f"{duplicate_count}"
        )

    if panel["period_date"].isna().any():
        raise ValueError(
            "Monthly panel contains null period_date."
        )

    valid_days = panel[
        "period_date"
    ].dt.day.eq(1)

    if not valid_days.all():
        raise ValueError(
            "All period_date values must be "
            "the first day of the month."
        )


def build_monthly_panel(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Build the Phase 3 analytics-ready monthly panel."""

    core = select_core_geographies(df)

    panel = reshape_metrics(core)

    panel = panel[
        [
            "period_date",
            "series_id",
            "geography_level",
            "location_id",
            "location_name",
            "metric",
            "value",
            "is_provisional",
            "source_snapshot_id",
        ]
    ]

    panel = panel.sort_values(
        [
            "metric",
            "geography_level",
            "location_id",
            "period_date",
        ]
    ).reset_index(drop=True)

    validate_monthly_panel(panel)

    return panel
