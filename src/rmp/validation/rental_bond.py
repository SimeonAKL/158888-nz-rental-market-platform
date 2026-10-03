"""Validation for official Tenancy Services Rental Bond CSV files."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

EXPECTED_COLUMNS = [
    "TimeFrame",
    "location_id",
    "location",
    "LodgedBonds",
    "ActiveBonds",
    "ClosedBonds",
    "MedianRent",
    "GeometricMeanRent",
    "UpperQuartileRent",
    "LowerQuartileRent",
    "LogStdDevWeeklyRent",
]


INTEGER_COLUMNS = [
    "location_id",
    "LodgedBonds",
    "ActiveBonds",
    "ClosedBonds",
    "MedianRent",
    "GeometricMeanRent",
    "UpperQuartileRent",
    "LowerQuartileRent",
]


NUMERIC_COLUMNS = [
    "LogStdDevWeeklyRent",
]


class RentalBondValidationError(ValueError):
    """Raised when a Rental Bond CSV fails validation."""


def _validate_timeframe(
    value: object,
    *,
    row_number: int,
) -> None:
    """Validate the Rental Bond monthly date format."""
    if not isinstance(value, str):
        raise RentalBondValidationError(
            f"Row {row_number}: TimeFrame must be a string."
        )

    try:
        day_text, month_text, year_text = value.split("/")

        parsed = date(
            int(year_text),
            int(month_text),
            int(day_text),
        )

    except (ValueError, TypeError) as exc:
        raise RentalBondValidationError(
            f"Row {row_number}: invalid TimeFrame '{value}'."
        ) from exc

    if parsed.day != 1:
        raise RentalBondValidationError(
            f"Row {row_number}: TimeFrame must represent "
            "the first day of a month."
        )


def validate_rental_bond_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Validate an official Rental Bond dataframe."""
    if dataframe.empty:
        raise RentalBondValidationError(
            "Rental Bond dataset is empty."
        )

    actual_columns = dataframe.columns.tolist()

    if actual_columns != EXPECTED_COLUMNS:
        raise RentalBondValidationError(
            "Rental Bond CSV schema does not match "
            "the expected official schema.\n"
            f"Expected: {EXPECTED_COLUMNS}\n"
            f"Actual:   {actual_columns}"
        )

    if dataframe["location"].isna().any():
        raise RentalBondValidationError(
            "Rental Bond dataset contains missing location values."
        )

    if (
        dataframe["location"]
        .astype(str)
        .str.strip()
        .eq("")
        .any()
    ):
        raise RentalBondValidationError(
            "Rental Bond dataset contains blank location values."
        )

    for row_number, value in enumerate(
        dataframe["TimeFrame"],
        start=2,
    ):
        _validate_timeframe(
            value,
            row_number=row_number,
        )

    for column in INTEGER_COLUMNS:
        if dataframe[column].isna().any():
            raise RentalBondValidationError(
                f"Column '{column}' contains missing values."
            )

        converted = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        if converted.isna().any():
            raise RentalBondValidationError(
                f"Column '{column}' contains non-numeric values."
            )

        if not (
            converted % 1 == 0
        ).all():
            raise RentalBondValidationError(
                f"Column '{column}' must contain whole numbers."
            )

    for column in NUMERIC_COLUMNS:
        converted = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

        if converted.isna().any():
            raise RentalBondValidationError(
                f"Column '{column}' contains invalid numeric values."
            )

    return dataframe


def validate_rental_bond_file(
    path: Path,
) -> pd.DataFrame:
    """Read and validate a Rental Bond CSV file."""
    if not path.exists():
        raise RentalBondValidationError(
            f"Rental Bond file does not exist: {path}"
        )

    if path.suffix.lower() != ".csv":
        raise RentalBondValidationError(
            "Rental Bond input file must be CSV."
        )

    try:
        dataframe = pd.read_csv(
            path,
            dtype={
                "TimeFrame": str,
                "location": str,
            },
            keep_default_na=False,
        )

    except (
        OSError,
        pd.errors.ParserError,
    ) as exc:
        raise RentalBondValidationError(
            f"Unable to read Rental Bond CSV: {path}"
        ) from exc

    return validate_rental_bond_dataframe(
        dataframe
    )