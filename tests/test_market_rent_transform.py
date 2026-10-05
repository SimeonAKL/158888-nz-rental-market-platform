"""Tests for Market Rent staging transformation."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from rmp.transform.market_rent import (
    MarketRentTransformError,
    parse_period_covered,
    transform_market_rent_payload,
    write_market_rent_staging_csv,
)


def make_valid_payload() -> dict:
    """Return a representative Market Rent payload."""
    return {
        "areaDefinition": "REGC2019",
        "periodCovered": "2026-7-1/2026-7-31",
        "items": [
            {
                "area": "Auckland Region",
                "dwell": "Apartment",
                "nBedrms": "1",
                "nLodged": 609,
                "nClosed": 342,
                "nCurr": 9693,
                "mean": 502,
                "lq": 450,
                "med": 490,
                "uq": 539,
                "sd": 209,
                "brr": 3.84,
                "lmean": 6.1854,
                "lsd": 0.2386,
                "slq": 413,
                "suq": 570,
            }
        ],
    }


def test_parse_period_covered() -> None:
    """API periodCovered should become ISO dates."""
    start, end = parse_period_covered("2026-7-1/2026-7-31")

    assert start == "2026-07-01"
    assert end == "2026-07-31"


def test_invalid_period_covered_fails() -> None:
    """Invalid periodCovered values should be rejected."""
    with pytest.raises(
        MarketRentTransformError,
        match="invalid date",
    ):
        parse_period_covered("invalid/2026-7-31")


def test_transform_payload_maps_columns() -> None:
    """API fields should map to staging column names."""
    dataframe = transform_market_rent_payload(
        make_valid_payload(),
        source_snapshot="example.json",
        retrieved_at_utc=("2026-10-02T22:38:15+00:00"),
    )

    assert len(dataframe) == 1

    row = dataframe.iloc[0]

    assert row["area_definition"] == "REGC2019"

    assert row["period_start"] == "2026-07-01"

    assert row["period_end"] == "2026-07-31"

    assert row["dwelling_type"] == "Apartment"

    assert row["bedrooms"] == "1"

    assert row["bonds_lodged"] == 609

    assert row["median_rent"] == 490

    assert row["source_snapshot"] == "example.json"


def test_transform_preserves_numeric_values() -> None:
    """Numeric statistics should remain numeric."""
    dataframe = transform_market_rent_payload(
        make_valid_payload(),
        source_snapshot="example.json",
        retrieved_at_utc=("2026-10-02T22:38:15+00:00"),
    )

    assert pd.api.types.is_numeric_dtype(dataframe["median_rent"])

    assert pd.api.types.is_numeric_dtype(dataframe["bonds_lodged"])


def test_write_staging_csv(
    tmp_path: Path,
) -> None:
    """A raw snapshot should produce a staging CSV."""
    raw_root = tmp_path / "raw" / "market_rent" / "2026" / "10" / "02"

    raw_root.mkdir(parents=True)

    raw_path = raw_root / ("statistics_regional-council-2019_2026-07_test.json")

    raw_path.write_text(
        json.dumps(make_valid_payload()),
        encoding="utf-8",
    )

    metadata_path = raw_path.with_name(f"{raw_path.stem}.metadata.json")

    metadata_path.write_text(
        json.dumps({"retrieved_at_utc": ("2026-10-02T22:38:15+00:00")}),
        encoding="utf-8",
    )

    staging_root = tmp_path / "staging" / "market_rent"

    output_path = write_market_rent_staging_csv(
        raw_path,
        staging_root=staging_root,
    )

    assert output_path.exists()

    dataframe = pd.read_csv(output_path)

    assert len(dataframe) == 1

    assert dataframe.loc[0, "area"] == "Auckland Region"

    assert dataframe.loc[0, "median_rent"] == 490

    assert dataframe.loc[0, "bonds_lodged"] == 609
