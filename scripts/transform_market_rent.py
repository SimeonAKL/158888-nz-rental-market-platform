"""Transform a raw Market Rent snapshot into staging CSV."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rmp.acquisition.market_rent_snapshot import (
    DEFAULT_RAW_ROOT,
)
from rmp.transform.market_rent import (
    MarketRentTransformError,
    write_market_rent_staging_csv,
)


def find_latest_raw_snapshot() -> Path:
    """Return the most recent Market Rent raw JSON snapshot."""
    files = [
        path
        for path in DEFAULT_RAW_ROOT.rglob(
            "statistics_*.json"
        )
        if not path.name.endswith(
            ".metadata.json"
        )
    ]

    if not files:
        raise FileNotFoundError(
            "No Market Rent raw snapshots were found."
        )

    return max(files)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Transform a validated Market Rent "
            "raw snapshot into staging CSV."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        help=(
            "Path to a Market Rent raw JSON snapshot. "
            "If omitted, the latest snapshot is used."
        ),
    )

    return parser


def main() -> int:
    """Run Market Rent staging transformation."""
    parser = build_parser()

    args = parser.parse_args()

    try:
        raw_path = (
            args.input
            if args.input is not None
            else find_latest_raw_snapshot()
        )

        print("=" * 60)
        print("Market Rent staging transformation")
        print("=" * 60)

        print(f"Raw snapshot: {raw_path}")
        print()
        print("Validating and transforming data...")

        output_path = (
            write_market_rent_staging_csv(
                raw_path
            )
        )

    except (
        FileNotFoundError,
        FileExistsError,
        MarketRentTransformError,
        OSError,
    ) as exc:
        print()
        print("Transformation FAILED")
        print(f"Error: {exc}")

        return 1

    print()
    print("Transformation successful.")
    print(f"Staging CSV: {output_path}")

    print()
    print("=" * 60)
    print("Market Rent transformation PASSED")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())