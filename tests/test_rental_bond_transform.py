"""Tests for Rental Bond staging transformation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from rmp.transform.rental_bond import (
    OUTPUT_COLUMNS,
    RentalBondTransformError,
    get_staging_path,
    parse_timeframe,
    transform_rental_bond_dataframe,
    write_rental_bond_staging_csv,
)


def make_raw_dataframe() -> pd.DataFrame:
    """Return representative Rental Bond raw data."""
    return pd.DataFrame(
        [
            {
                "TimeFrame": "1/07/2026",
                "location_id": 2,
                "location": "Auckland Region",
                "LodgedBonds": 5592,
                "ActiveBonds": 170511,
                "ClosedBonds": 4254,
                "MedianRent": 640,
                "GeometricMeanRent": 620,
                "UpperQuartileRent": 750,
                "LowerQuartileRent": 520,
                "LogStdDevWeeklyRent": 0.3667,
            },
            {
                "TimeFrame": "1/07/2026",
                "location_id": -1,
                "location": "NA",
                "LodgedBonds": 1776,
                "ActiveBonds": 86619,
                "ClosedBonds": 1869,
                "MedianRent": 575,
                "GeometricMeanRent": 540,
                "UpperQuartileRent": 700,
                "LowerQuartileRent": 449,
                "LogStdDevWeeklyRent": 0.4271,
            },
        ]
    )


def test_parse_timeframe() -> None:
    """Rental Bond monthly date should convert to ISO format."""
    assert parse_timeframe("1/07/2026") == "2026-07-01"


def test_invalid_timeframe_fails() -> None:
    """Invalid Rental Bond monthly dates should fail."""
    with pytest.raises(
        RentalBondTransformError,
        match="Invalid Rental Bond TimeFrame",
    ):
        parse_timeframe("2026-07-01")


def test_transform_region_dataframe() -> None:
    """Region data should transform to standard staging schema."""
    dataframe = make_raw_dataframe()

    result = transform_rental_bond_dataframe(
        dataframe,
        dataset="region",
        source_snapshot="example.csv",
        retrieved_at_utc=("2026-10-03T06:37:38+00:00"),
        is_provisional=True,
    )

    assert result.columns.tolist() == OUTPUT_COLUMNS

    assert len(result) == 2

    assert (
        result.loc[
            0,
            "period_date",
        ]
        == "2026-07-01"
    )

    assert (
        result.loc[
            0,
            "geography_level",
        ]
        == "region"
    )

    assert (
        result.loc[
            0,
            "location_name",
        ]
        == "Auckland Region"
    )

    assert (
        result.loc[
            0,
            "median_rent",
        ]
        == 640
    )

    assert (
        result.loc[
            0,
            "bonds_lodged",
        ]
        == 5592
    )


def test_transform_preserves_na_location() -> None:
    """Official 'NA' geography value must remain a string."""
    dataframe = make_raw_dataframe()

    result = transform_rental_bond_dataframe(
        dataframe,
        dataset="region",
        source_snapshot="example.csv",
        retrieved_at_utc=("2026-10-03T06:37:38+00:00"),
        is_provisional=True,
    )

    assert (
        result.loc[
            1,
            "location_id",
        ]
        == -1
    )

    assert (
        result.loc[
            1,
            "location_name",
        ]
        == "NA"
    )


def test_transform_territorial_authority() -> None:
    """TA data should preserve its geography level."""
    dataframe = make_raw_dataframe()

    result = transform_rental_bond_dataframe(
        dataframe,
        dataset="territorial_authority",
        source_snapshot="example.csv",
        retrieved_at_utc=("2026-10-03T06:37:38+00:00"),
        is_provisional=True,
    )

    assert (
        result.loc[
            0,
            "geography_level",
        ]
        == "territorial_authority"
    )


def test_get_staging_path(
    tmp_path: Path,
) -> None:
    """Raw directory structure should map to staging."""
    raw_root = tmp_path / "raw" / "rental_bond"

    staging_root = tmp_path / "staging" / "rental_bond"

    raw_path = raw_root / "2026" / "10" / "03" / "rental_bond_region_example.csv"

    expected = (staging_root / "2026" / "10" / "03" / "rental_bond_region_example.csv").resolve()

    result = get_staging_path(
        raw_path,
        raw_root=raw_root,
        staging_root=staging_root,
    )

    assert result == expected


def test_write_staging_csv(
    tmp_path: Path,
) -> None:
    """Validated raw data should write a standard staging CSV."""
    raw_root = tmp_path / "raw" / "rental_bond"

    staging_root = tmp_path / "staging" / "rental_bond"

    raw_path = raw_root / "2026" / "10" / "03" / "rental_bond_region_example.csv"

    raw_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = make_raw_dataframe()

    dataframe.to_csv(
        raw_path,
        index=False,
    )

    metadata_path = raw_path.with_name(f"{raw_path.stem}.metadata.json")

    metadata = {
        "metadata_schema_version": 1,
        "source": ("MBIE / Tenancy Services Rental Bond Data"),
        "publisher": ("Ministry of Business, Innovation and Employment"),
        "dataset": "region",
        "source_url": "https://example.com/example.csv",
        "retrieved_at_utc": ("2026-10-03T06:37:38+00:00"),
        "raw_file": raw_path.name,
        "file_size_bytes": raw_path.stat().st_size,
        "sha256": "example-checksum",
        "provisional": True,
        "notes": "Test metadata.",
    }

    metadata_path.write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )

    staging_path = write_rental_bond_staging_csv(
        raw_path,
        raw_root=raw_root,
        staging_root=staging_root,
    )

    assert staging_path.exists()

    result = pd.read_csv(
        staging_path,
        keep_default_na=False,
    )

    assert result.shape == (
        2,
        len(OUTPUT_COLUMNS),
    )

    assert result.columns.tolist() == OUTPUT_COLUMNS

    assert (
        result.loc[
            1,
            "location_name",
        ]
        == "NA"
    )

    assert (
        result.loc[
            0,
            "source_snapshot",
        ]
        == raw_path.name
    )

    assert bool(
        result.loc[
            0,
            "is_provisional",
        ]
    )
