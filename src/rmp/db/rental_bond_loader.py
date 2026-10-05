"""Database loading logic for Rental Bond staging data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd
from psycopg2.extras import execute_values
from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Connection, Engine

from rmp.acquisition.rental_bond_snapshot import (
    DEFAULT_RAW_ROOT,
    calculate_sha256,
)
from rmp.config import get_database_config
from rmp.transform.rental_bond import (
    DEFAULT_STAGING_ROOT,
    OUTPUT_COLUMNS,
    load_snapshot_metadata,
)

SUPPORTED_DATASETS = {
    "region",
    "territorial_authority",
}

BATCH_SIZE = 1000


INTEGER_COLUMNS = {
    "bonds_lodged",
    "active_bonds",
    "bonds_closed",
}


NUMERIC_COLUMNS = {
    "median_rent",
    "geometric_mean_rent",
    "upper_quartile_rent",
    "lower_quartile_rent",
    "log_std_dev_weekly_rent",
}


class RentalBondLoadError(ValueError):
    """Raised when Rental Bond data cannot be loaded."""


@dataclass(frozen=True)
class RentalBondLoadResult:
    """Summary of one Rental Bond database load."""

    snapshot_id: int
    rows_processed: int
    dataset: str
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
    """Infer the raw CSV path corresponding to a staging CSV."""
    try:
        relative_path = staging_path.resolve().relative_to(staging_root.resolve())

    except ValueError as exc:
        raise RentalBondLoadError(
            "Staging file is outside the configured Rental Bond staging directory."
        ) from exc

    return raw_root.resolve() / relative_path


def read_rental_bond_staging(
    staging_path: Path,
) -> pd.DataFrame:
    """Read and validate a Rental Bond staging CSV."""
    if not staging_path.exists():
        raise RentalBondLoadError(f"Staging file does not exist: {staging_path}")

    if staging_path.suffix.lower() != ".csv":
        raise RentalBondLoadError("Rental Bond staging file must be CSV.")

    dataframe = pd.read_csv(
        staging_path,
        keep_default_na=False,
    )

    if dataframe.empty:
        raise RentalBondLoadError("Rental Bond staging CSV is empty.")

    missing_columns = [column for column in OUTPUT_COLUMNS if column not in dataframe.columns]

    if missing_columns:
        raise RentalBondLoadError(
            f"Rental Bond staging CSV is missing columns: {', '.join(missing_columns)}"
        )

    return dataframe


def _parse_retrieved_at(
    value: str,
) -> datetime:
    """Parse a timezone-aware retrieval timestamp."""
    try:
        retrieved_at = datetime.fromisoformat(value)

    except ValueError as exc:
        raise RentalBondLoadError("Invalid retrieved_at_utc timestamp.") from exc

    if retrieved_at.tzinfo is None:
        raise RentalBondLoadError("retrieved_at_utc must be timezone-aware.")

    return retrieved_at


def _parse_boolean(
    value: Any,
) -> bool:
    """Convert a staging boolean representation to bool."""
    if isinstance(value, bool):
        return value

    normalised = str(value).strip().lower()

    if normalised == "true":
        return True

    if normalised == "false":
        return False

    raise RentalBondLoadError(f"Invalid boolean value: {value}")


def _required_integer(
    value: Any,
    *,
    column: str,
) -> int:
    """Convert a required staging value to integer."""
    try:
        numeric_value = float(value)

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise RentalBondLoadError(f"Column '{column}' contains a non-numeric value.") from exc

    if not numeric_value.is_integer():
        raise RentalBondLoadError(f"Column '{column}' must contain whole-number values.")

    return int(numeric_value)


def _required_decimal(
    value: Any,
    *,
    column: str,
) -> Decimal:
    """Convert a required staging value to Decimal."""
    try:
        return Decimal(str(value))

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise RentalBondLoadError(f"Column '{column}' contains a non-numeric value.") from exc


def validate_snapshot_lineage(
    dataframe: pd.DataFrame,
    *,
    raw_path: Path,
    metadata: dict[str, Any],
) -> tuple[
    str,
    datetime,
    bool,
]:
    """Validate staging-to-raw Rental Bond lineage."""
    metadata_raw_file = metadata.get("raw_file")

    if metadata_raw_file != raw_path.name:
        raise RentalBondLoadError("Metadata raw_file does not match the raw snapshot filename.")

    dataset = metadata.get("dataset")

    if dataset not in SUPPORTED_DATASETS:
        raise RentalBondLoadError("Snapshot metadata contains an unsupported Rental Bond dataset.")

    metadata_checksum = metadata.get("sha256")

    if not isinstance(
        metadata_checksum,
        str,
    ):
        raise RentalBondLoadError("Snapshot metadata is missing sha256.")

    actual_checksum = calculate_sha256(raw_path.read_bytes())

    if actual_checksum != metadata_checksum:
        raise RentalBondLoadError(
            "Raw Rental Bond snapshot checksum does not match snapshot metadata."
        )

    source_snapshots = set(dataframe["source_snapshot"].astype(str))

    if source_snapshots != {raw_path.name}:
        raise RentalBondLoadError(
            "Staging source_snapshot does not match the Rental Bond raw snapshot."
        )

    geography_levels = set(dataframe["geography_level"].astype(str))

    if geography_levels != {dataset}:
        raise RentalBondLoadError(
            "Staging geography_level does not match the Rental Bond dataset metadata."
        )

    metadata_retrieved_at = _parse_retrieved_at(
        str(
            metadata.get(
                "retrieved_at_utc",
                "",
            )
        )
    )

    staging_timestamps = {
        _parse_retrieved_at(str(value)) for value in dataframe["retrieved_at_utc"]
    }

    if staging_timestamps != {metadata_retrieved_at}:
        raise RentalBondLoadError(
            "Staging retrieved_at_utc does not match Rental Bond snapshot metadata."
        )

    metadata_provisional = metadata.get("provisional")

    if not isinstance(
        metadata_provisional,
        bool,
    ):
        raise RentalBondLoadError("Snapshot metadata provisional flag must be boolean.")

    staging_provisional = {_parse_boolean(value) for value in dataframe["is_provisional"]}

    if staging_provisional != {metadata_provisional}:
        raise RentalBondLoadError(
            "Staging is_provisional does not match Rental Bond snapshot metadata."
        )

    return (
        dataset,
        metadata_retrieved_at,
        metadata_provisional,
    )


def prepare_rental_bond_records(
    dataframe: pd.DataFrame,
    *,
    retrieved_at: datetime,
    is_provisional: bool,
) -> list[dict[str, Any]]:
    """Convert staging rows into database-ready records."""
    records: list[dict[str, Any]] = []

    for index, row in dataframe.iterrows():
        try:
            period_date = date.fromisoformat(str(row["period_date"]))

        except ValueError as exc:
            raise RentalBondLoadError(f"Row {index} contains an invalid period_date.") from exc

        geography_level = str(row["geography_level"])

        if geography_level not in SUPPORTED_DATASETS:
            raise RentalBondLoadError(
                f"Row {index} contains an unsupported geography_level: {geography_level}"
            )

        location_name = str(row["location_name"]).strip()

        if not location_name:
            raise RentalBondLoadError(f"Row {index} contains a blank location_name.")

        record: dict[str, Any] = {
            "period_date": period_date,
            "geography_level": geography_level,
            "location_id": _required_integer(
                row["location_id"],
                column="location_id",
            ),
            "location_name": location_name,
            "retrieved_at": retrieved_at,
            "is_provisional": is_provisional,
        }

        for column in INTEGER_COLUMNS:
            record[column] = _required_integer(
                row[column],
                column=column,
            )

        for column in NUMERIC_COLUMNS:
            record[column] = _required_decimal(
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
    dataset: str,
    row_count: int,
) -> int:
    """Register a Rental Bond snapshot or reuse an existing one."""
    source_name = f"rental_bond_{dataset}"

    retrieved_at = _parse_retrieved_at(
        str(
            metadata.get(
                "retrieved_at_utc",
                "",
            )
        )
    )

    metadata_path = raw_path.with_name(f"{raw_path.stem}.metadata.json")

    request_parameters = {
        "dataset": dataset,
    }

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
            "source_name": source_name,
            "source_url": metadata.get("source_url"),
            "file_name": raw_path.name,
            "retrieved_at": retrieved_at,
            "checksum_sha256": metadata["sha256"],
            "row_count": row_count,
            "status": "validated",
            "notes": ("Rental Bond snapshot registered by ETL loader."),
            "environment": None,
            "request_parameters": json.dumps(request_parameters),
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
            "source_name": source_name,
            "checksum_sha256": metadata["sha256"],
        },
    )

    existing_snapshot_id = existing_result.scalar_one_or_none()

    if existing_snapshot_id is None:
        raise RentalBondLoadError("Unable to register or locate the Rental Bond raw snapshot.")

    return int(existing_snapshot_id)


def upsert_rental_bond_records(
    connection: Connection,
    *,
    records: list[dict[str, Any]],
    snapshot_id: int,
    batch_size: int = BATCH_SIZE,
) -> None:
    """Bulk UPSERT Rental Bond records into clean.rental_bond."""
    if not records:
        raise RentalBondLoadError("No Rental Bond records were provided for loading.")

    if batch_size < 1:
        raise RentalBondLoadError("Batch size must be at least 1.")

    sql = """
        INSERT INTO clean.rental_bond (
            period_date,
            geography_level,
            location_id,
            location_name,
            bonds_lodged,
            active_bonds,
            bonds_closed,
            median_rent,
            geometric_mean_rent,
            upper_quartile_rent,
            lower_quartile_rent,
            log_std_dev_weekly_rent,
            is_provisional,
            source_snapshot_id,
            retrieved_at
        )
        VALUES %s
        ON CONFLICT ON CONSTRAINT
            uq_clean_rental_bond_observation
        DO UPDATE SET
            location_name =
                EXCLUDED.location_name,
            bonds_lodged =
                EXCLUDED.bonds_lodged,
            active_bonds =
                EXCLUDED.active_bonds,
            bonds_closed =
                EXCLUDED.bonds_closed,
            median_rent =
                EXCLUDED.median_rent,
            geometric_mean_rent =
                EXCLUDED.geometric_mean_rent,
            upper_quartile_rent =
                EXCLUDED.upper_quartile_rent,
            lower_quartile_rent =
                EXCLUDED.lower_quartile_rent,
            log_std_dev_weekly_rent =
                EXCLUDED.log_std_dev_weekly_rent,
            is_provisional =
                EXCLUDED.is_provisional,
            source_snapshot_id =
                EXCLUDED.source_snapshot_id,
            retrieved_at =
                EXCLUDED.retrieved_at,
            updated_at = NOW()
    """

    values = [
        (
            record["period_date"],
            record["geography_level"],
            record["location_id"],
            record["location_name"],
            record["bonds_lodged"],
            record["active_bonds"],
            record["bonds_closed"],
            record["median_rent"],
            record["geometric_mean_rent"],
            record["upper_quartile_rent"],
            record["lower_quartile_rent"],
            record["log_std_dev_weekly_rent"],
            record["is_provisional"],
            snapshot_id,
            record["retrieved_at"],
        )
        for record in records
    ]

    dbapi_connection = connection.connection.driver_connection

    cursor = dbapi_connection.cursor()

    try:
        execute_values(
            cursor,
            sql,
            values,
            page_size=batch_size,
        )

    finally:
        cursor.close()


def mark_snapshot_loaded(
    connection: Connection,
    *,
    snapshot_id: int,
    row_count: int,
) -> None:
    """Mark a Rental Bond snapshot as loaded."""
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


def load_rental_bond_staging(
    staging_path: Path,
    *,
    raw_path: Path | None = None,
    engine: Engine | None = None,
) -> RentalBondLoadResult:
    """Load one Rental Bond staging CSV into PostgreSQL."""
    dataframe = read_rental_bond_staging(staging_path)

    resolved_raw_path = raw_path if raw_path is not None else infer_raw_snapshot_path(staging_path)

    if not resolved_raw_path.exists():
        raise RentalBondLoadError(
            f"Corresponding Rental Bond raw snapshot does not exist: {resolved_raw_path}"
        )

    metadata = load_snapshot_metadata(resolved_raw_path)

    (
        dataset,
        retrieved_at,
        is_provisional,
    ) = validate_snapshot_lineage(
        dataframe,
        raw_path=resolved_raw_path,
        metadata=metadata,
    )

    records = prepare_rental_bond_records(
        dataframe,
        retrieved_at=retrieved_at,
        is_provisional=is_provisional,
    )

    owns_engine = engine is None

    database_engine = engine if engine is not None else build_database_engine()

    try:
        with database_engine.begin() as connection:
            snapshot_id = register_snapshot(
                connection,
                raw_path=resolved_raw_path,
                metadata=metadata,
                dataset=dataset,
                row_count=len(records),
            )

            upsert_rental_bond_records(
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

    return RentalBondLoadResult(
        snapshot_id=snapshot_id,
        rows_processed=len(records),
        dataset=dataset,
        raw_snapshot=resolved_raw_path,
        staging_file=staging_path,
    )
