"""Tests for forecasting series selection."""

import pandas as pd

from rmp.forecasting.selection import (
    select_forecasting_series,
)


def test_excludes_duplicate_auckland_ta_series() -> None:
    """Auckland TA duplicates should not enter forecasting."""

    panel = pd.DataFrame(
        {
            "series_id": [
                "region_2_bonds_lodged",
                "territorial_authority_76_bonds_lodged",
                "region_2_median_rent",
                "territorial_authority_76_median_rent",
                "region_3_bonds_lodged",
            ],
            "value": [
                1,
                1,
                2,
                2,
                3,
            ],
        }
    )

    result = select_forecasting_series(
        panel
    )

    assert set(
        result["series_id"]
    ) == {
        "region_2_bonds_lodged",
        "region_2_median_rent",
        "region_3_bonds_lodged",
    }
