"""Load Rental Bond staging data into PostgreSQL."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from rmp.db.rental_bond_loader import (
    RentalBondLoadError,
    load_rental_bond_staging,
)
from rmp.transform.rental_bond import (
    DEFAULT_STAGING_ROOT,
)

SUPPORTED_DATASETS = [
    "region",
    "territorial_authority",
]


def find_latest_staging_file(
    dataset: str,
) -> Path:
    """Return the latest staging CSV for one Rental Bond dataset."""
    files = list(DEFAULT_STAGING_ROOT.rglob(f"rental_bond_{dataset}_*.csv"))

    if not files:
        raise FileNotFoundError(
            f"No Rental Bond staging CSV files were found for dataset: {dataset}"
        )

    return max(files)


def build_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=("Load a Rental Bond staging CSV into PostgreSQL.")
    )

    parser.add_argument(
        "dataset",
        choices=SUPPORTED_DATASETS,
        help=("Rental Bond dataset to load."),
    )

    parser.add_argument(
        "--input",
        type=Path,
        help=(
            "Optional path to a Rental Bond staging CSV. "
            "If omitted, the latest matching file is used."
        ),
    )

    return parser


def main() -> int:
    """Run the Rental Bond database load."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        staging_path = (
            args.input if args.input is not None else find_latest_staging_file(args.dataset)
        )

        print("=" * 60)
        print("Rental Bond database load")
        print("=" * 60)

        print(f"Dataset      : {args.dataset}")

        print(f"Staging file : {staging_path}")

        print()
        print("Validating lineage and loading data...")

        result = load_rental_bond_staging(staging_path)

    except (
        FileNotFoundError,
        RentalBondLoadError,
        SQLAlchemyError,
        OSError,
    ) as exc:
        print()
        print("Database load FAILED")
        print(f"Error: {exc}")

        return 1

    if result.dataset != args.dataset:
        print()
        print("Database load FAILED")
        print("Error: loaded dataset does not match the requested dataset.")

        return 1

    print()
    print("Database load successful.")

    print(f"Dataset       : {result.dataset}")

    print(f"Snapshot ID   : {result.snapshot_id}")

    print(f"Rows processed: {result.rows_processed}")

    print(f"Raw snapshot  : {result.raw_snapshot}")

    print()
    print("=" * 60)
    print("Rental Bond database load PASSED")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
