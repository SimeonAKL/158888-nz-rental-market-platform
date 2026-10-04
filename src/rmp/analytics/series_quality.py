"""Time-series quality summaries for analytics-ready data."""

from __future__ import annotations

import pandas as pd

MIN_HISTORY_MONTHS = 60
FORECAST_HORIZON = 6
N_ROLLING_ORIGINS = 12

REQUIRED_CONTINUOUS_MONTHS = (
    MIN_HISTORY_MONTHS
    + FORECAST_HORIZON
    + N_ROLLING_ORIGINS
    - 1
)


def build_series_catalog(
    panel: pd.DataFrame,
) -> pd.DataFrame:
    """Build one metadata row per forecasting series."""

    required_columns = {
        "series_id",
        "period_date",
        "geography_level",
        "location_id",
        "location_name",
        "metric",
        "value",
    }

    missing = required_columns.difference(panel.columns)

    if missing:
        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing)}"
        )

    data = panel.copy()

    data["period_date"] = pd.to_datetime(
        data["period_date"]
    )

    rows: list[dict[str, object]] = []

    for series_id, group in data.groupby(
        "series_id",
        sort=True,
    ):
        group = group.sort_values(
            "period_date"
        )

        start_period = group[
            "period_date"
        ].min()

        end_period = group[
            "period_date"
        ].max()

        expected_periods = pd.date_range(
            start=start_period,
            end=end_period,
            freq="MS",
        )

        observed_periods = pd.DatetimeIndex(
            group["period_date"].dropna().unique()
        )

        missing_periods = expected_periods.difference(
            observed_periods
        )

        observed_set = set(observed_periods)

        continuous_start = end_period

        for period in reversed(expected_periods):
            if period in observed_set:
                continuous_start = period
            else:
                break

        continuous_months = (
            (end_period.year - continuous_start.year) * 12
            + end_period.month
            - continuous_start.month
            + 1
        )

        n_observations = len(group)

        expected_observations = len(
            expected_periods
        )

        completeness_rate = (
            n_observations
            / expected_observations
            if expected_observations
            else 0.0
        )

        first = group.iloc[0]

        rows.append(
            {
                "series_id": series_id,
                "geography_level": (
                    first["geography_level"]
                ),
                "location_id": (
                    int(first["location_id"])
                ),
                "location_name": (
                    first["location_name"]
                ),
                "metric": first["metric"],
                "start_period": start_period,
                "end_period": end_period,
                "n_observations": (
                    n_observations
                ),
                "expected_observations": (
                    expected_observations
                ),
                "missing_months": (
                    len(missing_periods)
                ),
                "null_values": (
                    int(
                        group[
                            "value"
                        ].isna().sum()
                    )
                ),
                "completeness_rate": (
                    completeness_rate
                ),
                "continuous_start": (
                    continuous_start
                ),
                "continuous_months": (
                    continuous_months
                ),
                "eligible_for_forecasting": (
                    continuous_months
                    >= REQUIRED_CONTINUOUS_MONTHS
                    and group.loc[
                        group["period_date"]
                        >= continuous_start,
                        "value",
                    ].notna().all()
                ),
            }
        )

    catalog = pd.DataFrame(rows)

    return catalog.sort_values(
        [
            "metric",
            "geography_level",
            "location_id",
        ]
    ).reset_index(drop=True)


def build_quality_summary(
    panel: pd.DataFrame,
) -> pd.DataFrame:
    """Build structural and value quality checks per series."""

    required_columns = {
        "series_id",
        "period_date",
        "metric",
        "value",
        "is_provisional",
    }

    missing = required_columns.difference(panel.columns)

    if missing:
        raise ValueError(
            "Missing required columns: "
            f"{sorted(missing)}"
        )

    data = panel.copy()

    data["period_date"] = pd.to_datetime(
        data["period_date"]
    )

    rows: list[dict[str, object]] = []

    for series_id, group in data.groupby(
        "series_id",
        sort=True,
    ):
        duplicate_periods = int(
            group.duplicated(
                subset=["period_date"]
            ).sum()
        )

        null_values = int(
            group["value"].isna().sum()
        )

        negative_values = int(
            (group["value"] < 0).sum()
        )

        zero_values = int(
            (group["value"] == 0).sum()
        )

        provisional_observations = int(
            group[
                "is_provisional"
            ].fillna(False).sum()
        )

        if (
            duplicate_periods == 0
            and null_values == 0
            and negative_values == 0
        ):
            status = "PASS"
        else:
            status = "FAIL"

        rows.append(
            {
                "series_id": series_id,
                "metric": (
                    group["metric"].iloc[0]
                ),
                "duplicate_periods": (
                    duplicate_periods
                ),
                "null_values": (
                    null_values
                ),
                "negative_values": (
                    negative_values
                ),
                "zero_values": (
                    zero_values
                ),
                "provisional_observations": (
                    provisional_observations
                ),
                "status": status,
            }
        )

    return pd.DataFrame(rows).sort_values(
        [
            "metric",
            "series_id",
        ]
    ).reset_index(drop=True)
