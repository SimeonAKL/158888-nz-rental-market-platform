"""Acquire official Tenancy Services Rental Bond CSV snapshots."""

from __future__ import annotations

import argparse
import sys

from rmp.acquisition.rental_bond_snapshot import (
    RentalBondAcquisitionError,
    acquire_rental_bond_snapshot,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        description=("Download an official Tenancy Services Rental Bond CSV snapshot.")
    )

    parser.add_argument(
        "dataset",
        choices=[
            "region",
            "territorial_authority",
        ],
        help=("Rental Bond dataset to download."),
    )

    return parser


def main() -> int:
    """Acquire one Rental Bond dataset."""
    parser = build_parser()
    args = parser.parse_args()

    print("=" * 60)
    print("Rental Bond data acquisition")
    print("=" * 60)

    print(f"Dataset: {args.dataset}")

    print()
    print("Downloading official Tenancy Services CSV...")

    try:
        snapshot = acquire_rental_bond_snapshot(args.dataset)

    except (
        RentalBondAcquisitionError,
        ValueError,
        OSError,
    ) as exc:
        print()
        print("Acquisition FAILED")
        print(f"Error: {exc}")

        return 1

    print()
    print("Acquisition successful.")

    print(f"Raw CSV      : {snapshot.raw_path}")

    print(f"Metadata     : {snapshot.metadata_path}")

    print(f"SHA-256      : {snapshot.sha256}")

    print(f"File size    : {snapshot.file_size_bytes} bytes")

    print()
    print("=" * 60)
    print("Rental Bond acquisition PASSED")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
