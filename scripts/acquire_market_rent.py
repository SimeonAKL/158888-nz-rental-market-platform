"""Command-line acquisition script for Market Rent raw snapshots."""

from __future__ import annotations

import argparse
import sys

from rmp.acquisition.market_rent_api import MarketRentAPIError
from rmp.acquisition.market_rent_snapshot import (
    acquire_market_rent_snapshot,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description=("Acquire an immutable raw snapshot from the MBIE Market Rent API.")
    )

    parser.add_argument(
        "--period-ending",
        required=True,
        help=("Period ending in YYYY-MM format, for example 2026-07."),
    )

    parser.add_argument(
        "--num-months",
        type=int,
        default=1,
        help=("Number of months requested. Default: 1."),
    )

    parser.add_argument(
        "--area-definition",
        required=True,
        help=("Market Rent geographic definition, for example regional-council-2019."),
    )

    parser.add_argument(
        "--include-aggregates",
        action="store_true",
        help="Include aggregate records.",
    )

    return parser


def main() -> int:
    """Run the Market Rent raw acquisition."""
    parser = build_parser()

    args = parser.parse_args()

    print("=" * 60)
    print("Market Rent raw acquisition")
    print("=" * 60)

    print(f"Period ending   : {args.period_ending}")
    print(f"Number of months: {args.num_months}")
    print(f"Area definition : {args.area_definition}")
    print(f"Aggregates      : {args.include_aggregates}")

    print()
    print("Requesting Market Rent data...")

    try:
        raw_path, metadata_path = acquire_market_rent_snapshot(
            period_ending=(args.period_ending),
            num_months=args.num_months,
            area_definition=(args.area_definition),
            include_aggregates=(args.include_aggregates),
        )

    except (
        ValueError,
        MarketRentAPIError,
        OSError,
    ) as exc:
        print()
        print("Acquisition FAILED")
        print(f"Error: {exc}")

        return 1

    print()
    print("Acquisition successful.")
    print(f"Raw snapshot : {raw_path}")
    print(f"Metadata     : {metadata_path}")

    print()
    print("=" * 60)
    print("Market Rent acquisition PASSED")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
