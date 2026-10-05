"""Transformation logic for Market Rent API snapshots."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from rmp.config import PROJECT_ROOT
from rmp.validation.market_rent import (
    MarketRentValidationError,
    validate_market_rent_file,
)

DEFAULT_STAGING_ROOT = PROJECT_ROOT / "data" / "staging" / "market_rent"


COLUMN_MAPPING = {
    "area": "area",
    "dwell": "dwelling_type",
    "nBedrms": "bedrooms",
    "nLodged": "bonds_lodged",
    "nClosed": "bonds_closed",
    "nCurr": "active_bonds",
    "mean": "mean_rent",
    "lq": "lower_quartile_rent",
    "med": "median_rent",
    "uq": "upper_quartile_rent",
    "sd": "rent_std_dev",
    "brr": "bond_rent_ratio",
    "lmean": "log_mean",
    "lsd": "log_std_dev",
    "slq": "synthetic_lower_quartile",
    "suq": "synthetic_upper_quartile",
}


OUTPUT_COLUMNS = [
    "period_start",
    "period_end",
    "area_definition",
    "area",
    "dwelling_type",
    "bedrooms",
    "bonds_lodged",
    "bonds_closed",
    "active_bonds",
    "mean_rent",
    "lower_quartile_rent",
    "median_rent",
    "upper_quartile_rent",
    "rent_std_dev",
    "bond_rent_ratio",
    "log_mean",
    "log_std_dev",
    "synthetic_lower_quartile",
    "synthetic_upper_quartile",
    "source_snapshot",
    "retrieved_at_utc",
]


class MarketRentTransformError(ValueError):
    """Raised when Market Rent data cannot be transformed."""


def _normalise_date_string(
    value: str,
) -> str:
    """Convert an API date into standard ISO YYYY-MM-DD format.

    Examples
    --------
    ``2026-7-1`` becomes ``2026-07-01``.
    """
    parts = value.strip().split("-")

    if len(parts) != 3:
        raise ValueError("Date must contain year, month, and day.")

    try:
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])

    except ValueError as exc:
        raise ValueError("Date components must be numeric.") from exc

    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_period_covered(
    period_covered: str,
) -> tuple[str, str]:
    """Parse the API periodCovered value into ISO dates.

    Parameters
    ----------
    period_covered:
        Market Rent API period string such as
        ``2026-7-1/2026-7-31``.

    Returns
    -------
    tuple[str, str]
        Period start and end dates in YYYY-MM-DD format.

    Raises
    ------
    MarketRentTransformError
        If the period string cannot be parsed.
    """
    if not isinstance(period_covered, str):
        raise MarketRentTransformError("periodCovered must be a string.")

    parts = period_covered.split("/")

    if len(parts) != 2:
        raise MarketRentTransformError(
            "periodCovered must contain a start and end date separated by '/'."
        )

    try:
        start_date = date.fromisoformat(_normalise_date_string(parts[0]))

        end_date = date.fromisoformat(_normalise_date_string(parts[1]))

    except ValueError as exc:
        raise MarketRentTransformError("periodCovered contains an invalid date.") from exc

    if start_date > end_date:
        raise MarketRentTransformError("periodCovered start date must not be after the end date.")

    return (
        start_date.isoformat(),
        end_date.isoformat(),
    )


def get_metadata_path(
    raw_path: Path,
) -> Path:
    """Return the metadata path associated with a raw snapshot."""
    return raw_path.with_name(f"{raw_path.stem}.metadata.json")


def load_snapshot_metadata(
    raw_path: Path,
) -> dict[str, Any]:
    """Load metadata associated with a raw Market Rent snapshot.

    Parameters
    ----------
    raw_path:
        Path to the raw Market Rent JSON snapshot.

    Returns
    -------
    dict[str, Any]
        Parsed snapshot metadata.

    Raises
    ------
    MarketRentTransformError
        If metadata is missing or invalid.
    """
    metadata_path = get_metadata_path(raw_path)

    if not metadata_path.exists():
        raise MarketRentTransformError(f"Market Rent metadata file does not exist: {metadata_path}")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    except json.JSONDecodeError as exc:
        raise MarketRentTransformError(
            f"Market Rent metadata file is not valid JSON: {metadata_path}"
        ) from exc

    if not isinstance(metadata, dict):
        raise MarketRentTransformError("Market Rent metadata must be a JSON object.")

    if "retrieved_at_utc" not in metadata:
        raise MarketRentTransformError("Market Rent metadata is missing 'retrieved_at_utc'.")

    return metadata


def transform_market_rent_payload(
    payload: dict[str, Any],
    *,
    source_snapshot: str,
    retrieved_at_utc: str,
) -> pd.DataFrame:
    """Transform a validated Market Rent payload into staging format.

    Parameters
    ----------
    payload:
        Validated Market Rent API payload.
    source_snapshot:
        Filename of the source raw snapshot.
    retrieved_at_utc:
        UTC timestamp when the source snapshot was retrieved.

    Returns
    -------
    pandas.DataFrame
        Standardised Market Rent staging data.
    """
    period_start, period_end = parse_period_covered(payload["periodCovered"])

    area_definition = str(payload["areaDefinition"])

    items = payload["items"]

    dataframe = pd.DataFrame(items)

    dataframe = dataframe.rename(columns=COLUMN_MAPPING)

    dataframe.insert(
        0,
        "area_definition",
        area_definition,
    )

    dataframe.insert(
        0,
        "period_end",
        period_end,
    )

    dataframe.insert(
        0,
        "period_start",
        period_start,
    )

    dataframe["source_snapshot"] = source_snapshot

    dataframe["retrieved_at_utc"] = retrieved_at_utc

    missing_columns = [column for column in OUTPUT_COLUMNS if column not in dataframe.columns]

    if missing_columns:
        missing = ", ".join(missing_columns)

        raise MarketRentTransformError(
            f"Transformed Market Rent data is missing columns: {missing}"
        )

    dataframe = dataframe[OUTPUT_COLUMNS].copy()

    return dataframe


def transform_market_rent_file(
    raw_path: Path,
) -> pd.DataFrame:
    """Validate and transform one raw Market Rent snapshot.

    Parameters
    ----------
    raw_path:
        Path to raw Market Rent JSON data.

    Returns
    -------
    pandas.DataFrame
        Standardised staging DataFrame.

    Raises
    ------
    MarketRentTransformError
        If validation or transformation fails.
    """
    try:
        payload = validate_market_rent_file(raw_path)

    except MarketRentValidationError as exc:
        raise MarketRentTransformError(
            "Raw Market Rent snapshot failed schema validation."
        ) from exc

    metadata = load_snapshot_metadata(raw_path)

    return transform_market_rent_payload(
        payload,
        source_snapshot=raw_path.name,
        retrieved_at_utc=str(metadata["retrieved_at_utc"]),
    )


def get_staging_path(
    raw_path: Path,
    staging_root: Path | None = None,
) -> Path:
    """Build the staging CSV path for one raw snapshot."""
    root = staging_root if staging_root is not None else DEFAULT_STAGING_ROOT

    try:
        year = raw_path.parents[2].name
        month = raw_path.parents[1].name
        day = raw_path.parents[0].name

        if not (year.isdigit() and month.isdigit() and day.isdigit()):
            raise ValueError

    except (IndexError, ValueError) as exc:
        raise MarketRentTransformError(
            "Raw snapshot path does not contain the expected YYYY/MM/DD structure."
        ) from exc

    output_dir = root / year / month / day

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    return output_dir / (f"{raw_path.stem}.csv")


def write_market_rent_staging_csv(
    raw_path: Path,
    *,
    staging_root: Path | None = None,
) -> Path:
    """Transform a raw snapshot and write an immutable staging CSV.

    Parameters
    ----------
    raw_path:
        Raw Market Rent JSON snapshot.
    staging_root:
        Optional alternative staging directory.

    Returns
    -------
    Path
        Path to the generated staging CSV.

    Raises
    ------
    FileExistsError
        If the staging output already exists.
    """
    dataframe = transform_market_rent_file(raw_path)

    output_path = get_staging_path(
        raw_path,
        staging_root=staging_root,
    )

    if output_path.exists():
        raise FileExistsError(f"Staging file already exists: {output_path}")

    dataframe.to_csv(
        output_path,
        index=False,
    )

    return output_path
