"""Run Market Rent vs Rental Bond cross-source validation."""

from __future__ import annotations

import argparse
import sys
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError

from rmp.validation.cross_source import (
    CrossSourceValidationError,
    validate_cross_source,
)


def build_parser() -> argparse.ArgumentParser:
    """Create command-line parser."""
    parser = argparse.ArgumentParser(
        description=("Validate Market Rent aggregate Region data against Rental Bond Region data.")
    )

    parser.add_argument(
        "--period",
        help=(
            "Optional period date in YYYY-MM-DD format. "
            "If omitted, the latest common period is used."
        ),
    )

    parser.add_argument(
        "--median-tolerance",
        type=Decimal,
        default=Decimal(20),
        help=("Allowed absolute median-rent difference in NZD per week. Default: 20."),
    )

    parser.add_argument(
        "--bonds-pct-tolerance",
        type=Decimal,
        default=Decimal(20),
        help=("Allowed absolute percentage difference for bonds lodged. Default: 20."),
    )

    return parser


def format_decimal(
    value: Decimal,
) -> str:
    """Format decimal for console output."""
    return f"{value:.2f}"


def main() -> int:
    """Run cross-source validation."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = validate_cross_source(
            period_date=args.period,
            median_rent_tolerance=(args.median_tolerance),
            bonds_lodged_pct_tolerance=(args.bonds_pct_tolerance),
        )

    except (
        CrossSourceValidationError,
        SQLAlchemyError,
        OSError,
        ValueError,
    ) as exc:
        print("Cross-source validation FAILED")

        print(f"Error: {exc}")

        return 1

    print("=" * 100)
    print("Market Rent vs Rental Bond Cross-source Validation")
    print("=" * 100)

    print(f"Period              : {result.period_date}")

    print(f"Market Rent regions : {result.market_region_count}")

    print(f"Rental Bond regions : {result.rental_region_count}")

    print(f"Matched regions     : {result.matched_region_count}")

    print()

    if result.missing_in_market:
        print("Missing in Market Rent:")

        for region in result.missing_in_market:
            print(f"  - {region}")

    if result.missing_in_rental:
        print("Missing in Rental Bond:")

        for region in result.missing_in_rental:
            print(f"  - {region}")

    if result.missing_in_market or result.missing_in_rental:
        print()

    print(
        f"{'Region':30}"
        f"{'MR Med':>9}"
        f"{'RB Med':>9}"
        f"{'Med Diff':>10}"
        f"{'Med':>7}"
        f"{'MR Bonds':>10}"
        f"{'RB Bonds':>10}"
        f"{'Diff %':>9}"
        f"{'Bond':>7}"
    )

    print("-" * 101)

    for comparison in result.comparisons:
        pct = (
            "N/A"
            if (comparison.bonds_lodged_difference_pct is None)
            else format_decimal(comparison.bonds_lodged_difference_pct)
        )

        print(
            f"{comparison.region:30}"
            f"{comparison.market_median_rent:>9}"
            f"{comparison.rental_median_rent:>9}"
            f"{comparison.median_rent_difference:>10}"
            f"{comparison.median_rent_status:>7}"
            f"{comparison.market_bonds_lodged:>10}"
            f"{comparison.rental_bonds_lodged:>10}"
            f"{pct:>9}"
            f"{comparison.bonds_lodged_status:>7}"
        )

    print()
    print("-" * 100)

    print("Median rent:")

    print(f"  PASS: {result.median_pass_count}")

    print(f"  WARN: {result.median_warn_count}")

    print()

    print("Bonds lodged:")

    print(f"  PASS: {result.bonds_pass_count}")

    print(f"  WARN: {result.bonds_warn_count}")

    print()

    print(f"Overall result: {result.overall_status}")

    print("=" * 100)

    if result.overall_status == "FAIL":
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
