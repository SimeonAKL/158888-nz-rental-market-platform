"""Tests for cross-source validation logic."""

from __future__ import annotations

from decimal import Decimal

from rmp.validation.cross_source import (
    compare_sources,
)


def test_matching_regions_pass() -> None:
    """Matching values should pass both checks."""
    market = {
        "Auckland Region": {
            "median_rent": 640,
            "bonds_lodged": 5760,
        },
    }

    rental = {
        "Auckland Region": {
            "median_rent": 640,
            "bonds_lodged": 5592,
        },
    }

    (
        comparisons,
        missing_in_market,
        missing_in_rental,
    ) = compare_sources(
        market_rows=market,
        rental_rows=rental,
    )

    assert (
        missing_in_market
        == ()
    )

    assert (
        missing_in_rental
        == ()
    )

    assert len(
        comparisons
    ) == 1

    comparison = (
        comparisons[0]
    )

    assert (
        comparison.median_rent_status
        == "PASS"
    )

    assert (
        comparison.bonds_lodged_status
        == "PASS"
    )


def test_median_difference_within_tolerance_passes() -> None:
    """Median difference equal to tolerance should pass."""
    market = {
        "Example Region": {
            "median_rent": 620,
            "bonds_lodged": 100,
        },
    }

    rental = {
        "Example Region": {
            "median_rent": 600,
            "bonds_lodged": 100,
        },
    }

    comparisons, _, _ = (
        compare_sources(
            market_rows=market,
            rental_rows=rental,
            median_rent_tolerance=(
                Decimal(20)
            ),
        )
    )

    assert (
        comparisons[0]
        .median_rent_status
        == "PASS"
    )


def test_large_median_difference_warns() -> None:
    """Median difference above tolerance should warn."""
    market = {
        "Example Region": {
            "median_rent": 650,
            "bonds_lodged": 100,
        },
    }

    rental = {
        "Example Region": {
            "median_rent": 600,
            "bonds_lodged": 100,
        },
    }

    comparisons, _, _ = (
        compare_sources(
            market_rows=market,
            rental_rows=rental,
            median_rent_tolerance=(
                Decimal(20)
            ),
        )
    )

    assert (
        comparisons[0]
        .median_rent_status
        == "WARN"
    )


def test_bonds_difference_within_tolerance_passes() -> None:
    """Bonds difference within tolerance should pass."""
    market = {
        "Example Region": {
            "median_rent": 600,
            "bonds_lodged": 110,
        },
    }

    rental = {
        "Example Region": {
            "median_rent": 600,
            "bonds_lodged": 100,
        },
    }

    comparisons, _, _ = (
        compare_sources(
            market_rows=market,
            rental_rows=rental,
            bonds_lodged_pct_tolerance=(
                Decimal(20)
            ),
        )
    )

    assert (
        comparisons[0]
        .bonds_lodged_status
        == "PASS"
    )

    assert (
        comparisons[0]
        .bonds_lodged_difference_pct
        == Decimal(10)
    )


def test_large_bonds_difference_warns() -> None:
    """Large bonds difference should produce warning."""
    market = {
        "Example Region": {
            "median_rent": 600,
            "bonds_lodged": 130,
        },
    }

    rental = {
        "Example Region": {
            "median_rent": 600,
            "bonds_lodged": 100,
        },
    }

    comparisons, _, _ = (
        compare_sources(
            market_rows=market,
            rental_rows=rental,
            bonds_lodged_pct_tolerance=(
                Decimal(20)
            ),
        )
    )

    assert (
        comparisons[0]
        .bonds_lodged_status
        == "WARN"
    )


def test_missing_region_is_reported() -> None:
    """Missing regions should be reported explicitly."""
    market = {
        "Auckland Region": {
            "median_rent": 640,
            "bonds_lodged": 100,
        },
        "Waikato Region": {
            "median_rent": 570,
            "bonds_lodged": 50,
        },
    }

    rental = {
        "Auckland Region": {
            "median_rent": 640,
            "bonds_lodged": 100,
        },
    }

    (
        comparisons,
        missing_in_market,
        missing_in_rental,
    ) = compare_sources(
        market_rows=market,
        rental_rows=rental,
    )

    assert (
        missing_in_market
        == ()
    )

    assert (
        missing_in_rental
        == (
            "Waikato Region",
        )
    )

    assert len(
        comparisons
    ) == 1
