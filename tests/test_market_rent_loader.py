"""Tests for Market Rent database loading helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from rmp.db.market_rent_loader import (
    MarketRentLoadError,
    infer_raw_snapshot_path,
    prepare_market_rent_records,
    read_market_rent_staging,
)


def make_staging_dataframe() -> pd.DataFrame:
    """Return a representative Market Rent staging dataset."""
    return pd.DataFrame(
        [
            {
                "period_start": "2026-07-01",
                "period_end": "2026-07-31",
                "area_definition": "REGC2019",
                "area": "Auckland Region",
                "dwelling_type": "Apartment",
                "bedrooms": "NA",
                "bonds_lodged": 12,
                "bonds_closed": 45,
                "active_bonds": 669,
                "mean_rent": 570,
                "lower_quartile_rent": 450,
                "median_rent": 560,
                "upper_quartile_rent": 620,
                "rent_std_dev": 178,
                "bond_rent_ratio": 3.93,
                "log_mean": 6.2995,
                "log_std_dev": 0.3201,
                "synthetic_lower_quartile": 439,
                "synthetic_upper_quartile": 675,
                "source_snapshot": "example.json",
                "retrieved_at_utc": (
                    "2026-10-02T22:38:15+00:00"
                ),
            }
        ]
    )


def test_infer_raw_snapshot_path(
    tmp_path: Path,
) -> None:
    """Staging path should map to the equivalent raw JSON path."""
    staging_root = (
        tmp_path
        / "staging"
        / "market_rent"
    )

    raw_root = (
        tmp_path
        / "raw"
        / "market_rent"
    )

    staging_path = (
        staging_root
        / "2026"
        / "10"
        / "02"
        / "example.csv"
    )

    expected = (
        raw_root
        / "2026"
        / "10"
        / "02"
        / "example.json"
    ).resolve()

    result = infer_raw_snapshot_path(
        staging_path,
        staging_root=staging_root,
        raw_root=raw_root,
    )

    assert result == expected


def test_read_staging_preserves_na_bedrooms(
    tmp_path: Path,
) -> None:
    """The bedroom category 'NA' must remain a string."""
    dataframe = make_staging_dataframe()

    path = tmp_path / "market_rent.csv"

    dataframe.to_csv(
        path,
        index=False,
    )

    result = read_market_rent_staging(
        path
    )

    assert (
        result.loc[
            0,
            "bedrooms"
        ]
        == "NA"
    )


def test_prepare_market_rent_records() -> None:
    """Staging columns should map to database-ready records."""
    dataframe = (
        make_staging_dataframe()
    )

    retrieved_at = datetime(
        2026,
        10,
        2,
        22,
        38,
        15,
        tzinfo=UTC,
    )

    records = (
        prepare_market_rent_records(
            dataframe,
            retrieved_at=retrieved_at,
        )
    )

    assert len(records) == 1

    record = records[0]

    assert (
        record["area_name"]
        == "Auckland Region"
    )

    assert (
        record["area_definition"]
        == "REGC2019"
    )

    assert (
        record["dwelling_type"]
        == "Apartment"
    )

    assert record["bedrooms"] == "NA"

    assert record["bonds_lodged"] == 12

    assert record["median_rent"] == 560

    assert (
        record["period_start"].isoformat()
        == "2026-07-01"
    )

    assert (
        record["period_end"].isoformat()
        == "2026-07-31"
    )

    assert (
        record["retrieved_at"]
        == retrieved_at
    )


def test_invalid_period_date_fails() -> None:
    """Invalid staging dates should be rejected."""
    dataframe = (
        make_staging_dataframe()
    )

    dataframe.loc[
        0,
        "period_start",
    ] = "invalid-date"

    retrieved_at = datetime(
        2026,
        10,
        2,
        22,
        38,
        15,
        tzinfo=UTC,
    )

    with pytest.raises(
        MarketRentLoadError,
        match="invalid period date",
    ):
        prepare_market_rent_records(
            dataframe,
            retrieved_at=retrieved_at,
        )