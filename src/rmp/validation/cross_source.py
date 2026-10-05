"""Cross-source validation between Market Rent and Rental Bond data."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine

from rmp.config import get_database_config

DEFAULT_MEDIAN_RENT_TOLERANCE = Decimal(20)
DEFAULT_BONDS_LODGED_PCT_TOLERANCE = Decimal(20)


class CrossSourceValidationError(ValueError):
    """Raised when cross-source validation cannot be completed."""


@dataclass(frozen=True)
class RegionComparison:
    """Comparison result for one named region."""

    region: str

    market_median_rent: Decimal
    rental_median_rent: Decimal
    median_rent_difference: Decimal
    median_rent_status: str

    market_bonds_lodged: int
    rental_bonds_lodged: int
    bonds_lodged_difference: int
    bonds_lodged_difference_pct: Decimal | None
    bonds_lodged_status: str


@dataclass(frozen=True)
class CrossSourceValidationResult:
    """Summary of one cross-source validation run."""

    period_date: str

    market_region_count: int
    rental_region_count: int
    matched_region_count: int

    missing_in_market: tuple[str, ...]
    missing_in_rental: tuple[str, ...]

    comparisons: tuple[RegionComparison, ...]

    median_pass_count: int
    median_warn_count: int

    bonds_pass_count: int
    bonds_warn_count: int

    overall_status: str


def build_database_engine() -> Engine:
    """Create configured PostgreSQL engine."""
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


def _as_decimal(
    value: Any,
) -> Decimal:
    """Convert database numeric value to Decimal."""
    return Decimal(str(value))


def _percentage_difference(
    *,
    observed: int,
    reference: int,
) -> Decimal | None:
    """Return signed percentage difference from reference."""
    if reference == 0:
        return None

    difference = observed - reference

    return Decimal(difference) / Decimal(reference) * Decimal(100)


def _status_from_absolute_difference(
    *,
    difference: Decimal,
    tolerance: Decimal,
) -> str:
    """Return PASS or WARN for absolute numeric tolerance."""
    if abs(difference) <= tolerance:
        return "PASS"

    return "WARN"


def _status_from_percentage_difference(
    *,
    difference_pct: Decimal | None,
    tolerance_pct: Decimal,
) -> str:
    """Return PASS or WARN for percentage tolerance."""
    if difference_pct is None:
        return "WARN"

    if abs(difference_pct) <= tolerance_pct:
        return "PASS"

    return "WARN"


def get_latest_common_period(
    engine: Engine,
) -> str:
    """Return latest period available in both aggregate datasets."""
    query = text(
        """
        WITH market_periods AS (
            SELECT DISTINCT period_start AS period_date
            FROM clean.market_rent
            WHERE area_definition = 'REGC2019'
              AND dwelling_type = 'ALL'
              AND bedrooms = 'ALL'
              AND area_name NOT IN ('ALL', 'NA')
        ),
        rental_periods AS (
            SELECT DISTINCT period_date
            FROM clean.rental_bond
            WHERE geography_level = 'region'
              AND location_id NOT IN (-99, -1)
        )
        SELECT MAX(m.period_date)
        FROM market_periods AS m
        INNER JOIN rental_periods AS r
            ON m.period_date = r.period_date
        """
    )

    with engine.connect() as connection:
        period = connection.execute(query).scalar_one_or_none()

    if period is None:
        raise CrossSourceValidationError("No common Market Rent and Rental Bond period was found.")

    return period.isoformat()


def load_market_rent_aggregate_rows(
    engine: Engine,
    *,
    period_date: str,
) -> dict[
    str,
    dict[str, Any],
]:
    """Load named Region-level Market Rent aggregate rows."""
    query = text(
        """
        SELECT
            area_name,
            median_rent,
            bonds_lodged
        FROM clean.market_rent
        WHERE period_start = CAST(
            :period_date AS DATE
        )
          AND area_definition = 'REGC2019'
          AND dwelling_type = 'ALL'
          AND bedrooms = 'ALL'
          AND area_name NOT IN (
              'ALL',
              'NA'
          )
        ORDER BY area_name
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {
                "period_date": period_date,
            },
        ).all()

    return {
        row.area_name: {
            "median_rent": row.median_rent,
            "bonds_lodged": row.bonds_lodged,
        }
        for row in rows
    }


def load_rental_bond_region_rows(
    engine: Engine,
    *,
    period_date: str,
) -> dict[
    str,
    dict[str, Any],
]:
    """Load named Region-level Rental Bond rows."""
    query = text(
        """
        SELECT
            location_name,
            median_rent,
            bonds_lodged
        FROM clean.rental_bond
        WHERE period_date = CAST(
            :period_date AS DATE
        )
          AND geography_level = 'region'
          AND location_id NOT IN (
              -99,
              -1
          )
        ORDER BY location_name
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {
                "period_date": period_date,
            },
        ).all()

    return {
        row.location_name: {
            "median_rent": row.median_rent,
            "bonds_lodged": row.bonds_lodged,
        }
        for row in rows
    }


def compare_sources(
    *,
    market_rows: dict[
        str,
        dict[str, Any],
    ],
    rental_rows: dict[
        str,
        dict[str, Any],
    ],
    median_rent_tolerance: Decimal = (DEFAULT_MEDIAN_RENT_TOLERANCE),
    bonds_lodged_pct_tolerance: Decimal = (DEFAULT_BONDS_LODGED_PCT_TOLERANCE),
) -> tuple[
    tuple[RegionComparison, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    """Compare two Region-level aggregate datasets."""
    market_regions = set(market_rows)

    rental_regions = set(rental_rows)

    missing_in_market = tuple(sorted(rental_regions - market_regions))

    missing_in_rental = tuple(sorted(market_regions - rental_regions))

    matched_regions = sorted(market_regions & rental_regions)

    comparisons: list[RegionComparison] = []

    for region in matched_regions:
        market = market_rows[region]

        rental = rental_rows[region]

        market_median = _as_decimal(market["median_rent"])

        rental_median = _as_decimal(rental["median_rent"])

        median_difference = market_median - rental_median

        market_bonds = int(market["bonds_lodged"])

        rental_bonds = int(rental["bonds_lodged"])

        bonds_difference = market_bonds - rental_bonds

        bonds_difference_pct = _percentage_difference(
            observed=market_bonds,
            reference=rental_bonds,
        )

        comparisons.append(
            RegionComparison(
                region=region,
                market_median_rent=(market_median),
                rental_median_rent=(rental_median),
                median_rent_difference=(median_difference),
                median_rent_status=(
                    _status_from_absolute_difference(
                        difference=(median_difference),
                        tolerance=(median_rent_tolerance),
                    )
                ),
                market_bonds_lodged=(market_bonds),
                rental_bonds_lodged=(rental_bonds),
                bonds_lodged_difference=(bonds_difference),
                bonds_lodged_difference_pct=(bonds_difference_pct),
                bonds_lodged_status=(
                    _status_from_percentage_difference(
                        difference_pct=(bonds_difference_pct),
                        tolerance_pct=(bonds_lodged_pct_tolerance),
                    )
                ),
            )
        )

    return (
        tuple(comparisons),
        missing_in_market,
        missing_in_rental,
    )


def validate_cross_source(
    *,
    engine: Engine | None = None,
    period_date: str | None = None,
    median_rent_tolerance: Decimal = (DEFAULT_MEDIAN_RENT_TOLERANCE),
    bonds_lodged_pct_tolerance: Decimal = (DEFAULT_BONDS_LODGED_PCT_TOLERANCE),
) -> CrossSourceValidationResult:
    """Run complete Market Rent vs Rental Bond validation."""
    owns_engine = engine is None

    database_engine = engine if engine is not None else build_database_engine()

    try:
        resolved_period = (
            period_date if period_date is not None else get_latest_common_period(database_engine)
        )

        market_rows = load_market_rent_aggregate_rows(
            database_engine,
            period_date=resolved_period,
        )

        rental_rows = load_rental_bond_region_rows(
            database_engine,
            period_date=resolved_period,
        )

        if not market_rows:
            raise CrossSourceValidationError(
                f"No Market Rent aggregate Region rows found for {resolved_period}."
            )

        if not rental_rows:
            raise CrossSourceValidationError(
                f"No Rental Bond Region rows found for {resolved_period}."
            )

        (
            comparisons,
            missing_in_market,
            missing_in_rental,
        ) = compare_sources(
            market_rows=market_rows,
            rental_rows=rental_rows,
            median_rent_tolerance=(median_rent_tolerance),
            bonds_lodged_pct_tolerance=(bonds_lodged_pct_tolerance),
        )

        median_pass_count = sum(
            comparison.median_rent_status == "PASS" for comparison in comparisons
        )

        median_warn_count = sum(
            comparison.median_rent_status == "WARN" for comparison in comparisons
        )

        bonds_pass_count = sum(
            comparison.bonds_lodged_status == "PASS" for comparison in comparisons
        )

        bonds_warn_count = sum(
            comparison.bonds_lodged_status == "WARN" for comparison in comparisons
        )

        if missing_in_market or missing_in_rental:
            overall_status = "FAIL"

        elif median_warn_count > 0 or bonds_warn_count > 0:
            overall_status = "WARN"

        else:
            overall_status = "PASS"

        return CrossSourceValidationResult(
            period_date=resolved_period,
            market_region_count=len(market_rows),
            rental_region_count=len(rental_rows),
            matched_region_count=len(comparisons),
            missing_in_market=(missing_in_market),
            missing_in_rental=(missing_in_rental),
            comparisons=(comparisons),
            median_pass_count=(median_pass_count),
            median_warn_count=(median_warn_count),
            bonds_pass_count=(bonds_pass_count),
            bonds_warn_count=(bonds_warn_count),
            overall_status=(overall_status),
        )

    finally:
        if owns_engine:
            database_engine.dispose()
