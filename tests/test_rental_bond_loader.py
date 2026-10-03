"""Tests for Rental Bond database loading helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from rmp.db.rental_bond_loader import (
    RentalBondLoadError,
    infer_raw_snapshot_path,
    prepare_rental_bond_records,
    read_rental_bond_staging,
)
from rmp.transform.rental_bond import (
    OUTPUT_COLUMNS,
)


def make_staging_dataframe() -> pd.DataFrame:
    """Return representative Rental Bond staging data."""
    return pd.DataFrame(
        [
            {
                "period_date": "2026-07-01",
                "geography_level": "region",
                "location_id": 2,
                "location_name": "Auckland Region",
                "bonds_lodged": 5592,
                "active_bonds": 170511,
                "bonds_closed": 4254,
                "median_rent": 640,
                "geometric_mean_rent": 620,
                "upper_quartile_rent": 750,
                "lower_quartile_rent": 520,
                "log_std_dev_weekly_rent": 0.3667,
                "source_snapshot": (
                    "rental_bond_region_example.csv"
                ),
                "retrieved_at_utc": (
                    "2026-10-03T06:37:38+00:00"
                ),
                "is_provisional": True,
            },
            {
                "period_date": "2026-07-01",
                "geography_level": "region",
                "location_id": -1,
                "location_name": "NA",
                "bonds_lodged": 1776,
                "active_bonds": 86619,
                "bonds_closed": 1869,
                "median_rent": 575,
                "geometric_mean_rent": 540,
                "upper_quartile_rent": 700,
                "lower_quartile_rent": 449,
                "log_std_dev_weekly_rent": 0.4271,
                "source_snapshot": (
                    "rental_bond_region_example.csv"
                ),
                "retrieved_at_utc": (
                    "2026-10-03T06:37:38+00:00"
                ),
                "is_provisional": True,
            },
        ]
    )


def test_infer_raw_snapshot_path(
    tmp_path: Path,
) -> None:
    """Staging path should map to equivalent raw CSV path."""
    staging_root = (
        tmp_path
        / "staging"
        / "rental_bond"
    )

    raw_root = (
        tmp_path
        / "raw"
        / "rental_bond"
    )

    staging_path = (
        staging_root
        / "2026"
        / "10"
        / "03"
        / "rental_bond_region_example.csv"
    )

    expected = (
        raw_root
        / "2026"
        / "10"
        / "03"
        / "rental_bond_region_example.csv"
    ).resolve()

    result = infer_raw_snapshot_path(
        staging_path,
        staging_root=staging_root,
        raw_root=raw_root,
    )

    assert result == expected


def test_read_staging_preserves_na_location(
    tmp_path: Path,
) -> None:
    """Official NA geography must remain a string."""
    dataframe = make_staging_dataframe()

    path = (
        tmp_path
        / "rental_bond.csv"
    )

    dataframe.to_csv(
        path,
        index=False,
    )

    result = read_rental_bond_staging(
        path
    )

    assert (
        result.columns.tolist()
        == OUTPUT_COLUMNS
    )

    assert (
        result.loc[
            1,
            "location_name",
        ]
        == "NA"
    )


def test_prepare_rental_bond_records() -> None:
    """Staging rows should convert to database-ready records."""
    dataframe = (
        make_staging_dataframe()
    )

    retrieved_at = datetime(
        2026,
        10,
        3,
        6,
        37,
        38,
        tzinfo=UTC,
    )

    records = prepare_rental_bond_records(
        dataframe,
        retrieved_at=retrieved_at,
        is_provisional=True,
    )

    assert len(records) == 2

    first = records[0]

    assert (
        first["period_date"].isoformat()
        == "2026-07-01"
    )

    assert (
        first["geography_level"]
        == "region"
    )

    assert (
        first["location_id"]
        == 2
    )

    assert (
        first["location_name"]
        == "Auckland Region"
    )

    assert (
        first["bonds_lodged"]
        == 5592
    )

    assert (
        first["median_rent"]
        == 640
    )

    assert (
        first["is_provisional"]
        is True
    )

    assert (
        first["retrieved_at"]
        == retrieved_at
    )


def test_prepare_preserves_na_location() -> None:
    """Official NA location should survive database preparation."""
    dataframe = (
        make_staging_dataframe()
    )

    retrieved_at = datetime(
        2026,
        10,
        3,
        6,
        37,
        38,
        tzinfo=UTC,
    )

    records = prepare_rental_bond_records(
        dataframe,
        retrieved_at=retrieved_at,
        is_provisional=True,
    )

    second = records[1]

    assert (
        second["location_id"]
        == -1
    )

    assert (
        second["location_name"]
        == "NA"
    )


def test_invalid_period_date_fails() -> None:
    """Invalid staging period dates should fail."""
    dataframe = (
        make_staging_dataframe()
    )

    dataframe.loc[
        0,
        "period_date",
    ] = "invalid-date"

    retrieved_at = datetime(
        2026,
        10,
        3,
        6,
        37,
        38,
        tzinfo=UTC,
    )

    with pytest.raises(
        RentalBondLoadError,
        match="invalid period_date",
    ):
        prepare_rental_bond_records(
            dataframe,
            retrieved_at=retrieved_at,
            is_provisional=True,
        )


def test_invalid_geography_level_fails() -> None:
    """Unsupported geography levels should fail."""
    dataframe = (
        make_staging_dataframe()
    )

    dataframe.loc[
        0,
        "geography_level",
    ] = "unknown"

    retrieved_at = datetime(
        2026,
        10,
        3,
        6,
        37,
        38,
        tzinfo=UTC,
    )

    with pytest.raises(
        RentalBondLoadError,
        match="unsupported geography_level",
    ):
        prepare_rental_bond_records(
            dataframe,
            retrieved_at=retrieved_at,
            is_provisional=True,
        )
