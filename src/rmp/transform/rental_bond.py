"""Transform Rental Bond raw CSV snapshots into staging data."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from rmp.acquisition.rental_bond_snapshot import (
    DEFAULT_RAW_ROOT,
)
from rmp.validation.rental_bond import (
    RentalBondValidationError,
    validate_rental_bond_file,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_STAGING_ROOT = PROJECT_ROOT / "data" / "staging" / "rental_bond"


SUPPORTED_DATASETS = {
    "region",
    "territorial_authority",
}


COLUMN_MAPPING = {
    "location_id": "location_id",
    "location": "location_name",
    "LodgedBonds": "bonds_lodged",
    "ActiveBonds": "active_bonds",
    "ClosedBonds": "bonds_closed",
    "MedianRent": "median_rent",
    "GeometricMeanRent": "geometric_mean_rent",
    "UpperQuartileRent": "upper_quartile_rent",
    "LowerQuartileRent": "lower_quartile_rent",
    "LogStdDevWeeklyRent": "log_std_dev_weekly_rent",
}


OUTPUT_COLUMNS = [
    "period_date",
    "geography_level",
    "location_id",
    "location_name",
    "bonds_lodged",
    "active_bonds",
    "bonds_closed",
    "median_rent",
    "geometric_mean_rent",
    "upper_quartile_rent",
    "lower_quartile_rent",
    "log_std_dev_weekly_rent",
    "source_snapshot",
    "retrieved_at_utc",
    "is_provisional",
]


class RentalBondTransformError(ValueError):
    """Raised when Rental Bond data cannot be transformed."""


def parse_timeframe(
    value: str,
) -> str:
    """Convert DD/MM/YYYY Rental Bond date to ISO date format."""
    try:
        day_text, month_text, year_text = value.split("/")

        parsed = date(
            int(year_text),
            int(month_text),
            int(day_text),
        )

    except (
        AttributeError,
        TypeError,
        ValueError,
    ) as exc:
        raise RentalBondTransformError(f"Invalid Rental Bond TimeFrame: {value}") from exc

    if parsed.day != 1:
        raise RentalBondTransformError(
            "Rental Bond TimeFrame must represent the first day of a month."
        )

    return parsed.isoformat()


def get_metadata_path(
    raw_path: Path,
) -> Path:
    """Return the metadata path paired with a raw snapshot."""
    return raw_path.with_name(f"{raw_path.stem}.metadata.json")


def load_snapshot_metadata(
    raw_path: Path,
) -> dict[str, Any]:
    """Load and validate Rental Bond snapshot metadata."""
    metadata_path = get_metadata_path(raw_path)

    if not metadata_path.exists():
        raise RentalBondTransformError(f"Rental Bond metadata file does not exist: {metadata_path}")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    except (
        OSError,
        json.JSONDecodeError,
    ) as exc:
        raise RentalBondTransformError(
            f"Unable to read Rental Bond metadata: {metadata_path}"
        ) from exc

    raw_file = metadata.get("raw_file")

    if raw_file != raw_path.name:
        raise RentalBondTransformError(
            "Rental Bond metadata raw_file does not match the raw snapshot filename."
        )

    dataset = metadata.get("dataset")

    if dataset not in SUPPORTED_DATASETS:
        raise RentalBondTransformError("Rental Bond metadata contains an unsupported dataset.")

    retrieved_at = metadata.get("retrieved_at_utc")

    if not isinstance(
        retrieved_at,
        str,
    ):
        raise RentalBondTransformError("Rental Bond metadata is missing retrieved_at_utc.")

    try:
        parsed_retrieved_at = datetime.fromisoformat(retrieved_at)

    except ValueError as exc:
        raise RentalBondTransformError(
            "Rental Bond metadata contains an invalid retrieved_at_utc timestamp."
        ) from exc

    if parsed_retrieved_at.tzinfo is None:
        raise RentalBondTransformError("Rental Bond retrieved_at_utc must be timezone-aware.")

    provisional = metadata.get("provisional")

    if not isinstance(
        provisional,
        bool,
    ):
        raise RentalBondTransformError("Rental Bond metadata provisional flag must be boolean.")

    return metadata


def transform_rental_bond_dataframe(
    dataframe: pd.DataFrame,
    *,
    dataset: str,
    source_snapshot: str,
    retrieved_at_utc: str,
    is_provisional: bool,
) -> pd.DataFrame:
    """Transform a validated Rental Bond dataframe."""
    if dataset not in SUPPORTED_DATASETS:
        raise RentalBondTransformError(f"Unsupported Rental Bond dataset: {dataset}")

    transformed = dataframe.copy()

    transformed.insert(
        0,
        "period_date",
        transformed["TimeFrame"].map(parse_timeframe),
    )

    transformed.insert(
        1,
        "geography_level",
        dataset,
    )

    transformed = transformed.rename(columns=COLUMN_MAPPING)

    transformed["source_snapshot"] = source_snapshot

    transformed["retrieved_at_utc"] = retrieved_at_utc

    transformed["is_provisional"] = is_provisional

    missing_columns = [column for column in OUTPUT_COLUMNS if column not in transformed.columns]

    if missing_columns:
        raise RentalBondTransformError(
            f"Rental Bond transformation is missing columns: {', '.join(missing_columns)}"
        )

    return transformed[OUTPUT_COLUMNS].copy()


def transform_rental_bond_file(
    raw_path: Path,
) -> pd.DataFrame:
    """Validate and transform one Rental Bond raw snapshot."""
    try:
        dataframe = validate_rental_bond_file(raw_path)

    except RentalBondValidationError as exc:
        raise RentalBondTransformError("Rental Bond raw snapshot failed validation.") from exc

    metadata = load_snapshot_metadata(raw_path)

    return transform_rental_bond_dataframe(
        dataframe,
        dataset=str(metadata["dataset"]),
        source_snapshot=raw_path.name,
        retrieved_at_utc=str(metadata["retrieved_at_utc"]),
        is_provisional=bool(metadata["provisional"]),
    )


def get_staging_path(
    raw_path: Path,
    *,
    raw_root: Path = DEFAULT_RAW_ROOT,
    staging_root: Path = DEFAULT_STAGING_ROOT,
) -> Path:
    """Return the staging CSV path corresponding to a raw snapshot."""
    try:
        relative_path = raw_path.resolve().relative_to(raw_root.resolve())

    except ValueError as exc:
        raise RentalBondTransformError(
            "Rental Bond raw file is outside the configured raw directory."
        ) from exc

    return (staging_root.resolve() / relative_path).with_suffix(".csv")


def write_rental_bond_staging_csv(
    raw_path: Path,
    *,
    raw_root: Path = DEFAULT_RAW_ROOT,
    staging_root: Path = DEFAULT_STAGING_ROOT,
) -> Path:
    """Transform one Rental Bond raw file and write staging CSV."""
    dataframe = transform_rental_bond_file(raw_path)

    staging_path = get_staging_path(
        raw_path,
        raw_root=raw_root,
        staging_root=staging_root,
    )

    staging_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if staging_path.exists():
        raise FileExistsError(f"Staging file already exists: {staging_path}")

    dataframe.to_csv(
        staging_path,
        index=False,
    )

    return staging_path
