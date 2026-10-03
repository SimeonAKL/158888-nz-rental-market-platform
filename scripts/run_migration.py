"""Run a SQL migration against the configured PostgreSQL database."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import URL, create_engine
from sqlalchemy.exc import SQLAlchemyError

from rmp.config import get_database_config


def build_database_url() -> URL:
    """Build the PostgreSQL connection URL."""
    config = get_database_config()

    return URL.create(
        drivername="postgresql+psycopg2",
        username=str(config["user"]),
        password=str(config["password"]),
        host=str(config["host"]),
        port=int(config["port"]),
        database=str(config["database"]),
    )


def run_migration(
    migration_path: Path,
) -> None:
    """Execute one SQL migration file inside a transaction."""
    if not migration_path.exists():
        raise FileNotFoundError(
            f"Migration file does not exist: {migration_path}"
        )

    if migration_path.suffix.lower() != ".sql":
        raise ValueError(
            "Migration file must have a .sql extension."
        )

    sql = migration_path.read_text(
        encoding="utf-8"
    ).strip()

    if not sql:
        raise ValueError(
            f"Migration file is empty: {migration_path}"
        )

    engine = create_engine(
        build_database_url(),
        pool_pre_ping=True,
    )

    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                sql
            )

    finally:
        engine.dispose()


def build_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Run a SQL migration against "
            "the configured PostgreSQL database."
        )
    )

    parser.add_argument(
        "migration",
        type=Path,
        help="Path to the SQL migration file.",
    )

    return parser


def main() -> int:
    """Run the requested migration."""
    parser = build_parser()
    args = parser.parse_args()

    print("=" * 60)
    print("Database migration")
    print("=" * 60)

    print(f"Migration: {args.migration}")
    print()
    print("Executing migration...")

    try:
        run_migration(
            args.migration
        )

    except (
        FileNotFoundError,
        ValueError,
        SQLAlchemyError,
    ) as exc:
        print()
        print("Migration FAILED")
        print(f"Error: {exc}")

        return 1

    print()
    print("Migration successful.")

    print()
    print("=" * 60)
    print("Database migration PASSED")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())