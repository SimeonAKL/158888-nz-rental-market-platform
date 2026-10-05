"""Tests for Rental Bond CSV validation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from rmp.validation.rental_bond import (
    RentalBondValidationError,
    validate_rental_bond_dataframe,
    validate_rental_bond_file,
)


def make_valid_dataframe() -> pd.DataFrame:
    """Return a small representative Rental Bond dataframe."""
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
            }
        ]
    )


def test_valid_dataframe_passes() -> None:
    """A correctly structured Rental Bond dataset should pass."""
    dataframe = make_valid_dataframe()

    result = validate_rental_bond_dataframe(dataframe)

    assert len(result) == 1
    assert result.loc[0, "location"] == "Auckland Region"


def test_missing_column_fails() -> None:
    """Missing official columns should fail validation."""
    dataframe = make_valid_dataframe().drop(
        columns=[
            "MedianRent",
        ]
    )

    with pytest.raises(
        RentalBondValidationError,
        match="schema",
    ):
        validate_rental_bond_dataframe(dataframe)


def test_invalid_timeframe_fails() -> None:
    """Invalid monthly dates should fail validation."""
    dataframe = make_valid_dataframe()

    dataframe.loc[
        0,
        "TimeFrame",
    ] = "2026-07-01"

    with pytest.raises(
        RentalBondValidationError,
        match="invalid TimeFrame",
    ):
        validate_rental_bond_dataframe(dataframe)


def test_blank_location_fails() -> None:
    """Blank geography names should fail validation."""
    dataframe = make_valid_dataframe()

    dataframe.loc[
        0,
        "location",
    ] = ""

    with pytest.raises(
        RentalBondValidationError,
        match="blank location",
    ):
        validate_rental_bond_dataframe(dataframe)


def test_valid_file_passes(
    tmp_path: Path,
) -> None:
    """A valid CSV file should pass validation."""
    path = tmp_path / "rental_bond.csv"

    dataframe = make_valid_dataframe()

    dataframe.to_csv(
        path,
        index=False,
    )

    result = validate_rental_bond_file(path)

    assert len(result) == 1
