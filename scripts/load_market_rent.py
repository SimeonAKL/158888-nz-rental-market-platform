"""Load Market Rent staging data into PostgreSQL."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from rmp.db.market_rent_loader import (
    MarketRentLoadError,
    load_market_rent_staging,
)
from rmp.transform.market_rent import (
    DEFAULT_STAGING_ROOT,
)


def find_latest_staging_file() -> Path:
    """Return the latest Market Rent staging CSV."""
    files = list(
        DEFAULT_STAGING_ROOT.rglob(
            "*.csv"
        )
    )

    if not files:
        raise FileNotFoundError(
            "No Market Rent staging CSV files "
            "were found."
        )

    return max(files)


def build_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Load a Market Rent staging CSV "
            "into PostgreSQL."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        help=(
            "Path to a Market Rent staging CSV. "
            "If omitted, the latest staging "
            "file is used."
        ),
    )

    return parser


def main() -> int:
    """Run the Market Rent database load."""
    parser = build_parser()

    args = parser.parse_args()

    try:
        staging_path = (
            args.input
            if args.input is not None
            else find_latest_staging_file()
        )

        print("=" * 60)
        print("Market Rent database load")
        print("=" * 60)

        print(
            f"Staging file: {staging_path}"
        )
        print()
        print(
            "Validating lineage and loading data..."
        )

        result = load_market_rent_staging(
            staging_path
        )

    except (
        FileNotFoundError,
        MarketRentLoadError,
        SQLAlchemyError,
        OSError,
    ) as exc:
        print()
        print("Database load FAILED")
        print(f"Error: {exc}")

        return 1

    print()
    print("Database load successful.")
    print(
        f"Snapshot ID   : "
        f"{result.snapshot_id}"
    )
    print(
        f"Rows processed: "
        f"{result.rows_processed}"
    )
    print(
        f"Raw snapshot  : "
        f"{result.raw_snapshot}"
    )

    print()
    print("=" * 60)
    print("Market Rent database load PASSED")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())