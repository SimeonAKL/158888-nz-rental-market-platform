"""Transform Rental Bond raw snapshots into staging CSV files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rmp.acquisition.rental_bond_snapshot import (
    DEFAULT_RAW_ROOT,
)
from rmp.transform.rental_bond import (
    RentalBondTransformError,
    write_rental_bond_staging_csv,
)

SUPPORTED_DATASETS = [
    "region",
    "territorial_authority",
]


def find_latest_raw_snapshot(
    dataset: str,
) -> Path:
    """Return the latest raw snapshot for a Rental Bond dataset."""
    files = [
        path
        for path in DEFAULT_RAW_ROOT.rglob(f"rental_bond_{dataset}_*.csv")
        if not path.name.endswith(".metadata.csv")
    ]

    if not files:
        raise FileNotFoundError(f"No Rental Bond raw snapshots found for dataset: {dataset}")

    return max(files)


def build_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=("Transform an official Rental Bond raw CSV into staging format.")
    )

    parser.add_argument(
        "dataset",
        choices=SUPPORTED_DATASETS,
        help=("Rental Bond dataset to transform."),
    )

    parser.add_argument(
        "--input",
        type=Path,
        help=("Optional raw CSV path. If omitted, the latest matching snapshot is used."),
    )

    return parser


def main() -> int:
    """Run Rental Bond staging transformation."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        raw_path = args.input if args.input is not None else find_latest_raw_snapshot(args.dataset)

        print("=" * 60)
        print("Rental Bond staging transformation")
        print("=" * 60)

        print(f"Dataset     : {args.dataset}")

        print(f"Raw snapshot: {raw_path}")

        print()
        print("Validating and transforming data...")

        staging_path = write_rental_bond_staging_csv(raw_path)

    except (
        FileNotFoundError,
        FileExistsError,
        RentalBondTransformError,
        OSError,
    ) as exc:
        print()
        print("Transformation FAILED")
        print(f"Error: {exc}")

        return 1

    print()
    print("Transformation successful.")

    print(f"Staging CSV : {staging_path}")

    print()
    print("=" * 60)
    print("Rental Bond transformation PASSED")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
