"""Database loading logic for Market Rent staging data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Connection, Engine

from rmp.acquisition.market_rent_snapshot import (
    DEFAULT_RAW_ROOT,
    calculate_sha256,
)
from rmp.config import get_database_config
from rmp.transform.market_rent import (
    DEFAULT_STAGING_ROOT,
    OUTPUT_COLUMNS,
    load_snapshot_metadata,
)

SOURCE_NAME = "market_rent_api"


INTEGER_COLUMNS = {
    "bonds_lodged",
    "bonds_closed",
    "active_bonds",
}


NUMERIC_COLUMNS = {
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
}


class MarketRentLoadError(ValueError):
    """Raised when Market Rent data cannot be loaded."""


@dataclass(frozen=True)
class MarketRentLoadResult:
    """Summary of one Market Rent database load."""

    snapshot_id: int
    rows_processed: int
    raw_snapshot: Path
    staging_file: Path


def build_database_engine() -> Engine:
    """Create the configured PostgreSQL SQLAlchemy engine."""
    config = get_database_config()

    database_url = URL.create(
        drivername="postgresql+psycopg2",
        username=str(config["user"]),
        password=str(config["password"]),
        host=str(config["host"]),
        port=int(config["port"]),
        database=str(config["database"]),
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
    )


def infer_raw_snapshot_path(
    staging_path: Path,
    *,
    staging_root: Path = DEFAULT_STAGING_ROOT,
    raw_root: Path = DEFAULT_RAW_ROOT,
) -> Path:
    """Infer the raw JSON path associated with a staging CSV.

    The staging and raw directories use the same YYYY/MM/DD
    structure and the same filename stem.

    Parameters
    ----------
    staging_path:
        Path to the staging CSV.
    staging_root:
        Root directory for Market Rent staging data.
    raw_root:
        Root directory for Market Rent raw snapshots.

    Returns
    -------
    Path
        Expected raw JSON snapshot path.

    Raises
    ------
    MarketRentLoadError
        If the staging path does not belong to the expected
        staging directory.
    """
    try:
        relative_path = staging_path.resolve().relative_to(staging_root.resolve())

    except ValueError as exc:
        raise MarketRentLoadError(
            "Staging file is outside the configured Market Rent staging directory."
        ) from exc

    return (raw_root.resolve() / relative_path).with_suffix(".json")


def read_market_rent_staging(
    staging_path: Path,
) -> pd.DataFrame:
    """Read and validate a Market Rent staging CSV."""
    if not staging_path.exists():
        raise MarketRentLoadError(f"Staging file does not exist: {staging_path}")

    if staging_path.suffix.lower() != ".csv":
        raise MarketRentLoadError("Market Rent staging file must be CSV.")

    dataframe = pd.read_csv(
        staging_path,
        keep_default_na=False,
        na_values=[""],
    )

    if dataframe.empty:
        raise MarketRentLoadError("Market Rent staging CSV is empty.")

    missing_columns = [column for column in OUTPUT_COLUMNS if column not in dataframe.columns]

    if missing_columns:
        missing = ", ".join(missing_columns)

        raise MarketRentLoadError(f"Market Rent staging CSV is missing columns: {missing}")

    return dataframe


def _parse_retrieved_at(
    value: str,
) -> datetime:
    """Parse and validate a timezone-aware retrieval timestamp."""
    try:
        retrieved_at = datetime.fromisoformat(value)

    except ValueError as exc:
        raise MarketRentLoadError("Invalid retrieved_at_utc timestamp.") from exc

    if retrieved_at.tzinfo is None:
        raise MarketRentLoadError("retrieved_at_utc must be timezone-aware.")

    return retrieved_at


def _optional_integer(
    value: Any,
    *,
    column: str,
) -> int | None:
    """Convert an optional staging value to a Python integer."""
    if pd.isna(value):
        return None

    try:
        numeric_value = float(value)

    except (TypeError, ValueError) as exc:
        raise MarketRentLoadError(f"Column '{column}' contains a non-numeric value.") from exc

    if not numeric_value.is_integer():
        raise MarketRentLoadError(f"Column '{column}' must contain whole-number values.")

    return int(numeric_value)


def _optional_decimal(
    value: Any,
    *,
    column: str,
) -> Decimal | None:
    """Convert an optional staging value to Decimal."""
    if pd.isna(value):
        return None

    try:
        return Decimal(str(value))

    except Exception as exc:
        raise MarketRentLoadError(f"Column '{column}' contains a non-numeric value.") from exc


def validate_snapshot_lineage(
    dataframe: pd.DataFrame,
    *,
    raw_path: Path,
    metadata: dict[str, Any],
) -> datetime:
    """Validate staging-to-raw snapshot lineage.

    Returns
    -------
    datetime
        Parsed retrieval timestamp from metadata.
    """
    metadata_raw_file = metadata.get("raw_file")

    if metadata_raw_file != raw_path.name:
        raise MarketRentLoadError("Metadata raw_file does not match the raw snapshot filename.")

    metadata_checksum = metadata.get("sha256")

    if not isinstance(
        metadata_checksum,
        str,
    ):
        raise MarketRentLoadError("Snapshot metadata is missing sha256.")

    actual_checksum = calculate_sha256(raw_path.read_bytes())

    if actual_checksum != metadata_checksum:
        raise MarketRentLoadError("Raw snapshot checksum does not match snapshot metadata.")

    source_snapshots = set(dataframe["source_snapshot"].dropna())

    if source_snapshots != {raw_path.name}:
        raise MarketRentLoadError("Staging source_snapshot does not match the raw snapshot.")

    metadata_retrieved_at = _parse_retrieved_at(
        str(
            metadata.get(
                "retrieved_at_utc",
                "",
            )
        )
    )

    staging_timestamps = {
        _parse_retrieved_at(str(value)) for value in dataframe["retrieved_at_utc"].dropna()
    }

    if staging_timestamps != {metadata_retrieved_at}:
        raise MarketRentLoadError("Staging retrieved_at_utc does not match snapshot metadata.")

    return metadata_retrieved_at


def prepare_market_rent_records(
    dataframe: pd.DataFrame,
    *,
    retrieved_at: datetime,
) -> list[dict[str, Any]]:
    """Convert staging rows into database-ready records."""
    records: list[dict[str, Any]] = []

    for index, row in dataframe.iterrows():
        try:
            period_start = date.fromisoformat(str(row["period_start"]))

            period_end = date.fromisoformat(str(row["period_end"]))

        except ValueError as exc:
            raise MarketRentLoadError(f"Row {index} contains an invalid period date.") from exc

        record: dict[str, Any] = {
            "period_start": period_start,
            "period_end": period_end,
            "area_definition": str(row["area_definition"]),
            "area_name": str(row["area"]),
            "dwelling_type": str(row["dwelling_type"]),
            "bedrooms": str(row["bedrooms"]),
            "retrieved_at": retrieved_at,
        }

        for column in INTEGER_COLUMNS:
            record[column] = _optional_integer(
                row[column],
                column=column,
            )

        for column in NUMERIC_COLUMNS:
            record[column] = _optional_decimal(
                row[column],
                column=column,
            )

        records.append(record)

    return records


def register_snapshot(
    connection: Connection,
    *,
    raw_path: Path,
    metadata: dict[str, Any],
    row_count: int,
) -> int:
    """Register a raw snapshot or return its existing snapshot ID."""
    request_parameters = metadata.get(
        "request_parameters",
        {},
    )

    if not isinstance(
        request_parameters,
        dict,
    ):
        raise MarketRentLoadError("Snapshot request_parameters must be a JSON object.")

    retrieved_at = _parse_retrieved_at(
        str(
            metadata.get(
                "retrieved_at_utc",
                "",
            )
        )
    )

    metadata_path = raw_path.with_name(f"{raw_path.stem}.metadata.json")

    insert_result = connection.execute(
        text(
            """
            INSERT INTO raw.snapshots (
                source_name,
                source_url,
                file_name,
                retrieved_at,
                checksum_sha256,
                row_count,
                status,
                notes,
                environment,
                request_parameters,
                metadata_file_name
            )
            VALUES (
                :source_name,
                :source_url,
                :file_name,
                :retrieved_at,
                :checksum_sha256,
                :row_count,
                :status,
                :notes,
                :environment,
                CAST(:request_parameters AS JSONB),
                :metadata_file_name
            )
            ON CONFLICT (
                source_name,
                checksum_sha256
            )
            DO NOTHING
            RETURNING snapshot_id
            """
        ),
        {
            "source_name": SOURCE_NAME,
            "source_url": metadata.get("endpoint"),
            "file_name": raw_path.name,
            "retrieved_at": retrieved_at,
            "checksum_sha256": metadata["sha256"],
            "row_count": row_count,
            "status": "validated",
            "notes": ("Market Rent API snapshot registered by ETL loader."),
            "environment": metadata.get("environment"),
            "request_parameters": (json.dumps(request_parameters)),
            "metadata_file_name": (metadata_path.name),
        },
    )

    snapshot_id = insert_result.scalar_one_or_none()

    if snapshot_id is not None:
        return int(snapshot_id)

    existing_result = connection.execute(
        text(
            """
            SELECT snapshot_id
            FROM raw.snapshots
            WHERE source_name = :source_name
              AND checksum_sha256 = :checksum_sha256
            """
        ),
        {
            "source_name": SOURCE_NAME,
            "checksum_sha256": metadata["sha256"],
        },
    )

    existing_snapshot_id = existing_result.scalar_one_or_none()

    if existing_snapshot_id is None:
        raise MarketRentLoadError("Unable to register or locate the raw snapshot.")

    return int(existing_snapshot_id)


def upsert_market_rent_records(
    connection: Connection,
    *,
    records: list[dict[str, Any]],
    snapshot_id: int,
) -> None:
    """UPSERT Market Rent records into clean.market_rent."""
    if not records:
        raise MarketRentLoadError("No Market Rent records were provided for loading.")

    database_records = []

    for record in records:
        database_record = dict(record)

        database_record["source_snapshot_id"] = snapshot_id

        database_records.append(database_record)

    connection.execute(
        text(
            """
            INSERT INTO clean.market_rent (
                period_start,
                period_end,
                area_definition,
                area_name,
                dwelling_type,
                bedrooms,
                bonds_lodged,
                bonds_closed,
                active_bonds,
                mean_rent,
                lower_quartile_rent,
                median_rent,
                upper_quartile_rent,
                rent_std_dev,
                bond_rent_ratio,
                log_mean,
                log_std_dev,
                synthetic_lower_quartile,
                synthetic_upper_quartile,
                source_snapshot_id,
                retrieved_at
            )
            VALUES (
                :period_start,
                :period_end,
                :area_definition,
                :area_name,
                :dwelling_type,
                :bedrooms,
                :bonds_lodged,
                :bonds_closed,
                :active_bonds,
                :mean_rent,
                :lower_quartile_rent,
                :median_rent,
                :upper_quartile_rent,
                :rent_std_dev,
                :bond_rent_ratio,
                :log_mean,
                :log_std_dev,
                :synthetic_lower_quartile,
                :synthetic_upper_quartile,
                :source_snapshot_id,
                :retrieved_at
            )
            ON CONFLICT ON CONSTRAINT
                uq_clean_market_rent_observation
            DO UPDATE SET
                bonds_lodged =
                    EXCLUDED.bonds_lodged,
                bonds_closed =
                    EXCLUDED.bonds_closed,
                active_bonds =
                    EXCLUDED.active_bonds,
                mean_rent =
                    EXCLUDED.mean_rent,
                lower_quartile_rent =
                    EXCLUDED.lower_quartile_rent,
                median_rent =
                    EXCLUDED.median_rent,
                upper_quartile_rent =
                    EXCLUDED.upper_quartile_rent,
                rent_std_dev =
                    EXCLUDED.rent_std_dev,
                bond_rent_ratio =
                    EXCLUDED.bond_rent_ratio,
                log_mean =
                    EXCLUDED.log_mean,
                log_std_dev =
                    EXCLUDED.log_std_dev,
                synthetic_lower_quartile =
                    EXCLUDED.synthetic_lower_quartile,
                synthetic_upper_quartile =
                    EXCLUDED.synthetic_upper_quartile,
                source_snapshot_id =
                    EXCLUDED.source_snapshot_id,
                retrieved_at =
                    EXCLUDED.retrieved_at,
                updated_at = NOW()
            """
        ),
        database_records,
    )


def mark_snapshot_loaded(
    connection: Connection,
    *,
    snapshot_id: int,
    row_count: int,
) -> None:
    """Mark a registered source snapshot as loaded."""
    connection.execute(
        text(
            """
            UPDATE raw.snapshots
            SET status = 'loaded',
                row_count = :row_count
            WHERE snapshot_id = :snapshot_id
            """
        ),
        {
            "snapshot_id": snapshot_id,
            "row_count": row_count,
        },
    )


def load_market_rent_staging(
    staging_path: Path,
    *,
    raw_path: Path | None = None,
    engine: Engine | None = None,
) -> MarketRentLoadResult:
    """Load one Market Rent staging CSV into PostgreSQL.

    Parameters
    ----------
    staging_path:
        Path to a standardised Market Rent staging CSV.
    raw_path:
        Optional corresponding raw JSON snapshot.
        If omitted, the path is inferred.
    engine:
        Optional SQLAlchemy engine.
        Primarily useful for integration testing.

    Returns
    -------
    MarketRentLoadResult
        Summary of the completed load.
    """
    dataframe = read_market_rent_staging(staging_path)

    resolved_raw_path = raw_path if raw_path is not None else infer_raw_snapshot_path(staging_path)

    if not resolved_raw_path.exists():
        raise MarketRentLoadError(f"Corresponding raw snapshot does not exist: {resolved_raw_path}")

    metadata = load_snapshot_metadata(resolved_raw_path)

    retrieved_at = validate_snapshot_lineage(
        dataframe,
        raw_path=resolved_raw_path,
        metadata=metadata,
    )

    records = prepare_market_rent_records(
        dataframe,
        retrieved_at=retrieved_at,
    )

    owns_engine = engine is None

    database_engine = engine if engine is not None else build_database_engine()

    try:
        with database_engine.begin() as connection:
            snapshot_id = register_snapshot(
                connection,
                raw_path=resolved_raw_path,
                metadata=metadata,
                row_count=len(records),
            )

            upsert_market_rent_records(
                connection,
                records=records,
                snapshot_id=snapshot_id,
            )

            mark_snapshot_loaded(
                connection,
                snapshot_id=snapshot_id,
                row_count=len(records),
            )

    finally:
        if owns_engine:
            database_engine.dispose()

    return MarketRentLoadResult(
        snapshot_id=snapshot_id,
        rows_processed=len(records),
        raw_snapshot=resolved_raw_path,
        staging_file=staging_path,
    )
