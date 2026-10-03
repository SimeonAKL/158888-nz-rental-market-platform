"""Tests for the Phase 3 monthly analytics panel."""

from decimal import Decimal

import pandas as pd
import pytest

from rmp.analytics.monthly_panel import (
    build_monthly_panel,
    select_core_geographies,
    validate_monthly_panel,
)


@pytest.fixture
def sample_clean_data() -> pd.DataFrame:
    """Create representative clean rental bond data."""

    return pd.DataFrame(
        [
            {
                "period_date": "2026-06-01",
                "geography_level": "region",
                "location_id": 2,
                "location_name": "Auckland Region",
                "median_rent": Decimal(650),
                "bonds_lodged": 1000,
                "is_provisional": True,
                "source_snapshot_id": 4,
            },
            {
                "period_date": "2026-07-01",
                "geography_level": "region",
                "location_id": 2,
                "location_name": "Auckland Region",
                "median_rent": Decimal(660),
                "bonds_lodged": 1100,
                "is_provisional": True,
                "source_snapshot_id": 4,
            },
            {
                "period_date": "2026-06-01",
                "geography_level": (
                    "territorial_authority"
                ),
                "location_id": 76,
                "location_name": "Auckland",
                "median_rent": Decimal(670),
                "bonds_lodged": 900,
                "is_provisional": True,
                "source_snapshot_id": 5,
            },
            {
                "period_date": "2026-07-01",
                "geography_level": (
                    "territorial_authority"
                ),
                "location_id": 76,
                "location_name": "Auckland",
                "median_rent": Decimal(680),
                "bonds_lodged": 950,
                "is_provisional": True,
                "source_snapshot_id": 5,
            },
            {
                "period_date": "2026-07-01",
                "geography_level": "region",
                "location_id": -99,
                "location_name": "ALL",
                "median_rent": Decimal(590),
                "bonds_lodged": 15000,
                "is_provisional": True,
                "source_snapshot_id": 4,
            },
            {
                "period_date": "2026-07-01",
                "geography_level": "region",
                "location_id": -1,
                "location_name": "NA",
                "median_rent": Decimal(590),
                "bonds_lodged": 1400,
                "is_provisional": True,
                "source_snapshot_id": 4,
            },
            {
                "period_date": "2026-07-01",
                "geography_level": (
                    "territorial_authority"
                ),
                "location_id": 60,
                "location_name": "Hamilton City",
                "median_rent": Decimal(550),
                "bonds_lodged": 400,
                "is_provisional": True,
                "source_snapshot_id": 5,
            },
        ]
    )


def test_select_core_geographies(
    sample_clean_data: pd.DataFrame,
) -> None:
    """Only valid Regions and Auckland TA should remain."""

    result = select_core_geographies(
        sample_clean_data
    )

    assert set(
        result["location_id"]
    ) == {2, 76}

    assert -99 not in set(
        result["location_id"]
    )

    assert -1 not in set(
        result["location_id"]
    )

    assert 60 not in set(
        result["location_id"]
    )


def test_build_monthly_panel(
    sample_clean_data: pd.DataFrame,
) -> None:
    """Two metrics should be produced per source row."""

    panel = build_monthly_panel(
        sample_clean_data
    )

    assert len(panel) == 8

    assert set(
        panel["metric"]
    ) == {
        "median_rent",
        "bonds_lodged",
    }

    assert panel[
        "series_id"
    ].nunique() == 4

    assert pd.api.types.is_datetime64_any_dtype(
        panel["period_date"]
    )


def test_panel_has_no_duplicate_periods(
    sample_clean_data: pd.DataFrame,
) -> None:
    """Each series-month combination must be unique."""

    panel = build_monthly_panel(
        sample_clean_data
    )

    duplicate_count = panel.duplicated(
        subset=[
            "series_id",
            "period_date",
        ]
    ).sum()

    assert duplicate_count == 0


def test_validate_rejects_duplicates(
    sample_clean_data: pd.DataFrame,
) -> None:
    """Duplicate observations should fail validation."""

    panel = build_monthly_panel(
        sample_clean_data
    )

    duplicated = pd.concat(
        [
            panel,
            panel.iloc[[0]],
        ],
        ignore_index=True,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate monthly observations",
    ):
        validate_monthly_panel(
            duplicated
        )
