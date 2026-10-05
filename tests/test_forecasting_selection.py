"""Tests for forecasting series selection."""

import pandas as pd
import pytest

from rmp.forecasting.selection import (
    select_forecasting_series,
)


def make_inputs():
    """Create representative forecasting-selection inputs."""

    dates = pd.date_range(
        "2020-01-01",
        periods=12,
        freq="MS",
    )

    rows = []

    for series_id in [
        "region_2_bonds_lodged",
        "territorial_authority_76_bonds_lodged",
        "territorial_authority_3_bonds_lodged",
        "territorial_authority_18_bonds_lodged",
    ]:
        for i, period in enumerate(dates):
            rows.append(
                {
                    "period_date": period,
                    "series_id": series_id,
                    "value": float(i + 1),
                }
            )

    panel = pd.DataFrame(rows)

    catalog = pd.DataFrame(
        {
            "series_id": [
                "region_2_bonds_lodged",
                "territorial_authority_76_bonds_lodged",
                "territorial_authority_3_bonds_lodged",
                "territorial_authority_18_bonds_lodged",
            ],
            "continuous_start": [
                "2020-01-01",
                "2020-01-01",
                "2020-05-01",
                "2020-08-01",
            ],
            "continuous_months": [
                120,
                120,
                100,
                50,
            ],
            "eligible_for_forecasting": [
                True,
                True,
                True,
                False,
            ],
        }
    )

    return panel, catalog


def test_selects_only_eligible_nonduplicate_series() -> None:
    """Only eligible non-duplicate series should remain."""

    panel, catalog = make_inputs()

    result = select_forecasting_series(
        panel,
        catalog,
    )

    assert set(result["series_id"]) == {
        "region_2_bonds_lodged",
        "territorial_authority_3_bonds_lodged",
    }

    assert "territorial_authority_76_bonds_lodged" not in set(result["series_id"])

    assert "territorial_authority_18_bonds_lodged" not in set(result["series_id"])


def test_truncates_to_continuous_start() -> None:
    """Eligible series should begin at their continuous start."""

    panel, catalog = make_inputs()

    result = select_forecasting_series(
        panel,
        catalog,
    )

    kaipara = result.loc[result["series_id"] == "territorial_authority_3_bonds_lodged"]

    assert kaipara["period_date"].min() == pd.Timestamp("2020-05-01")

    assert len(kaipara) == 8


def test_rejects_missing_catalog_columns() -> None:
    """Catalog schema must contain forecast-selection metadata."""

    panel, catalog = make_inputs()

    catalog = catalog.drop(columns=["continuous_start"])

    with pytest.raises(
        ValueError,
        match="Catalog is missing required columns",
    ):
        select_forecasting_series(
            panel,
            catalog,
        )


def test_rejects_when_no_series_are_eligible() -> None:
    """At least one forecast-eligible series must remain."""

    panel, catalog = make_inputs()

    catalog["eligible_for_forecasting"] = False

    with pytest.raises(
        ValueError,
        match="No forecast-eligible series",
    ):
        select_forecasting_series(
            panel,
            catalog,
        )
