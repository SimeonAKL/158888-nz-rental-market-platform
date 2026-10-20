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


def test_excludes_all_reviewed_duplicate_ta_series() -> None:
    """Reviewed Region-equivalent TA series must not enter modelling."""

    dates = pd.date_range(
        "2020-01-01",
        periods=3,
        freq="MS",
    )

    excluded_series = [
        "territorial_authority_28_bonds_lodged",
        "territorial_authority_28_median_rent",
        "territorial_authority_51_bonds_lodged",
        "territorial_authority_51_median_rent",
        "territorial_authority_52_bonds_lodged",
        "territorial_authority_52_median_rent",
        "territorial_authority_53_bonds_lodged",
        "territorial_authority_53_median_rent",
        "territorial_authority_76_bonds_lodged",
        "territorial_authority_76_median_rent",
    ]

    retained_series = "territorial_authority_3_bonds_lodged"
    all_series = excluded_series + [retained_series]

    rows = []

    for series_id in all_series:
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
            "series_id": all_series,
            "continuous_start": ["2020-01-01"] * len(all_series),
            "continuous_months": [120] * len(all_series),
            "eligible_for_forecasting": [True] * len(all_series),
        }
    )

    result = select_forecasting_series(
        panel,
        catalog,
    )

    assert set(result["series_id"]) == {retained_series}

    assert set(result["series_id"]).isdisjoint(excluded_series)


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
        match="No modelled series remain after forecasting selection",
    ):
        select_forecasting_series(
            panel,
            catalog,
        )
