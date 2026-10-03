"""Historical descriptive summaries for modelling readiness."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _validate_panel_columns(
    panel: pd.DataFrame,
) -> None:
    """Validate required columns for historical summaries."""

    required_columns = {
        "period_date",
        "series_id",
        "geography_level",
        "location_id",
        "location_name",
        "metric",
        "value",
    }

    missing = required_columns.difference(
        panel.columns
    )

    if missing:
        raise ValueError(
            "Missing required historical summary columns: "
            f"{sorted(missing)}"
        )


def build_historical_summary(
    panel: pd.DataFrame,
) -> pd.DataFrame:
    """Build one descriptive summary row per forecasting series.

    The summary contains:
    - date coverage
    - observation count
    - descriptive statistics
    - latest value
    - one-month change
    - twelve-month change
    - twelve-month percentage change
    - average and standard deviation of monthly changes
    """

    _validate_panel_columns(panel)

    data = panel.copy()

    data["period_date"] = pd.to_datetime(
        data["period_date"]
    )

    data["value"] = pd.to_numeric(
        data["value"],
        errors="coerce",
    )

    rows: list[dict[str, object]] = []

    for series_id, group in data.groupby(
        "series_id",
        sort=True,
    ):
        group = group.sort_values(
            "period_date"
        ).reset_index(drop=True)

        values = group["value"]

        first = group.iloc[0]
        latest = group.iloc[-1]

        latest_value = float(
            latest["value"]
        )

        change_1m = np.nan

        if len(group) >= 2:
            change_1m = float(
                latest_value
                - group.iloc[-2]["value"]
            )

        change_12m = np.nan
        pct_change_12m = np.nan

        if len(group) >= 13:
            value_12m_ago = float(
                group.iloc[-13]["value"]
            )

            change_12m = float(
                latest_value
                - value_12m_ago
            )

            if value_12m_ago != 0:
                pct_change_12m = float(
                    (
                        latest_value
                        - value_12m_ago
                    )
                    / value_12m_ago
                    * 100.0
                )

        monthly_change = values.diff()

        rows.append(
            {
                "series_id": series_id,
                "metric": first["metric"],
                "geography_level": (
                    first["geography_level"]
                ),
                "location_id": int(
                    first["location_id"]
                ),
                "location_name": (
                    first["location_name"]
                ),
                "start_period": (
                    group["period_date"].min()
                ),
                "end_period": (
                    group["period_date"].max()
                ),
                "n_observations": len(group),
                "mean": float(
                    values.mean()
                ),
                "median": float(
                    values.median()
                ),
                "std": float(
                    values.std()
                ),
                "minimum": float(
                    values.min()
                ),
                "maximum": float(
                    values.max()
                ),
                "latest_value": latest_value,
                "change_1m": change_1m,
                "change_12m": change_12m,
                "pct_change_12m": (
                    pct_change_12m
                ),
                "mean_monthly_change": float(
                    monthly_change.mean()
                ),
                "std_monthly_change": float(
                    monthly_change.std()
                ),
            }
        )

    summary = pd.DataFrame(rows)

    return summary.sort_values(
        [
            "metric",
            "geography_level",
            "location_id",
        ]
    ).reset_index(drop=True)


def build_monthly_seasonality_summary(
    panel: pd.DataFrame,
) -> pd.DataFrame:
    """Summarise historical values by calendar month.

    This provides an interpretable month-of-year profile for
    assessing whether recurring seasonal patterns may exist.
    """

    _validate_panel_columns(panel)

    data = panel.copy()

    data["period_date"] = pd.to_datetime(
        data["period_date"]
    )

    data["value"] = pd.to_numeric(
        data["value"],
        errors="coerce",
    )

    data["month"] = (
        data["period_date"].dt.month
    )

    summary = (
        data.groupby(
            [
                "series_id",
                "metric",
                "geography_level",
                "location_id",
                "location_name",
                "month",
            ],
            as_index=False,
            sort=True,
        )
        .agg(
            mean_value=(
                "value",
                "mean",
            ),
            median_value=(
                "value",
                "median",
            ),
            std_value=(
                "value",
                "std",
            ),
            minimum_value=(
                "value",
                "min",
            ),
            maximum_value=(
                "value",
                "max",
            ),
            n_observations=(
                "value",
                "count",
            ),
        )
    )

    return summary.sort_values(
        [
            "metric",
            "geography_level",
            "location_id",
            "month",
        ]
    ).reset_index(drop=True)


def build_recent_history_summary(
    panel: pd.DataFrame,
    recent_months: int = 24,
) -> pd.DataFrame:
    """Build descriptive statistics for the most recent history.

    This summary is useful for comparing recent behaviour with
    the full historical record without introducing modelling
    assumptions.
    """

    if recent_months < 1:
        raise ValueError(
            "recent_months must be at least 1."
        )

    _validate_panel_columns(panel)

    data = panel.copy()

    data["period_date"] = pd.to_datetime(
        data["period_date"]
    )

    data["value"] = pd.to_numeric(
        data["value"],
        errors="coerce",
    )

    rows: list[dict[str, object]] = []

    for series_id, group in data.groupby(
        "series_id",
        sort=True,
    ):
        group = group.sort_values(
            "period_date"
        ).reset_index(drop=True)

        recent = group.tail(
            recent_months
        )

        first = group.iloc[0]

        rows.append(
            {
                "series_id": series_id,
                "metric": first["metric"],
                "geography_level": (
                    first["geography_level"]
                ),
                "location_id": int(
                    first["location_id"]
                ),
                "location_name": (
                    first["location_name"]
                ),
                "recent_start_period": (
                    recent["period_date"].min()
                ),
                "recent_end_period": (
                    recent["period_date"].max()
                ),
                "recent_observations": (
                    len(recent)
                ),
                "recent_mean": float(
                    recent["value"].mean()
                ),
                "recent_median": float(
                    recent["value"].median()
                ),
                "recent_std": float(
                    recent["value"].std()
                ),
                "recent_minimum": float(
                    recent["value"].min()
                ),
                "recent_maximum": float(
                    recent["value"].max()
                ),
            }
        )

    return pd.DataFrame(rows).sort_values(
        [
            "metric",
            "geography_level",
            "location_id",
        ]
    ).reset_index(drop=True)
