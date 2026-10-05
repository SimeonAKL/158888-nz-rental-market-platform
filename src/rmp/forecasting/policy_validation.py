"""Strict held-out validation for forecast production policies."""

from __future__ import annotations

import pandas as pd

from rmp.forecasting.metrics import smape

AUDITED_CUTOFF = pd.Timestamp("2025-08-01")

SELECTED_POLICY = "per_series_selection"

FIXED_POLICY_PREFIX = "fixed_"

REQUIRED_COLUMNS = {
    "model",
    "series_id",
    "metric",
    "origin",
    "forecast_period",
    "actual",
    "predicted",
}


def validate_predictions(
    predictions: pd.DataFrame,
) -> pd.DataFrame:
    """Validate and normalize unified rolling-origin predictions."""
    missing = REQUIRED_COLUMNS.difference(predictions.columns)

    if missing:
        raise ValueError(f"Predictions are missing required columns: {sorted(missing)}")

    if predictions.empty:
        raise ValueError("Predictions cannot be empty.")

    data = predictions.copy()

    data["origin"] = pd.to_datetime(
        data["origin"],
        errors="raise",
    )

    data["forecast_period"] = pd.to_datetime(
        data["forecast_period"],
        errors="raise",
    )

    return data


def default_cutoff(
    predictions: pd.DataFrame,
) -> pd.Timestamp:
    """Return the fixed audited Pass 2 cutoff."""
    data = validate_predictions(predictions)

    origins = pd.DatetimeIndex(data["origin"].dropna().unique())

    if AUDITED_CUTOFF not in origins:
        raise ValueError("Audited cutoff 2025-08-01 is not present in prediction origins.")

    return AUDITED_CUTOFF


def split_by_target_cutoff(
    predictions: pd.DataFrame,
    cutoff: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create strict target-non-overlapping selection/evaluation sets."""
    data = validate_predictions(predictions)

    cutoff = pd.Timestamp(cutoff)

    selection = data.loc[data["forecast_period"] <= cutoff].copy()

    evaluation = data.loc[(data["origin"] >= cutoff) & (data["forecast_period"] > cutoff)].copy()

    if selection.empty:
        raise ValueError("Selection period contains no forecasts.")

    if evaluation.empty:
        raise ValueError("Evaluation period contains no forecasts.")

    overlap = set(selection["forecast_period"]).intersection(evaluation["forecast_period"])

    if overlap:
        raise ValueError("Selection and evaluation target months overlap.")

    return selection, evaluation


def select_series_winners(
    selection: pd.DataFrame,
) -> pd.DataFrame:
    """Select the lowest-sMAPE model per series from selection data."""
    data = validate_predictions(selection)

    rows: list[dict[str, object]] = []

    for (series_id, model), group in data.groupby(
        [
            "series_id",
            "model",
        ],
        sort=True,
    ):
        rows.append(
            {
                "series_id": series_id,
                "model": model,
                "selection_smape": smape(
                    group["actual"],
                    group["predicted"],
                ),
            }
        )

    scores = pd.DataFrame(rows)

    winners = (
        scores.sort_values(
            [
                "series_id",
                "selection_smape",
                "model",
            ]
        )
        .groupby(
            "series_id",
            as_index=False,
        )
        .first()
        .reset_index(drop=True)
    )

    if winners["series_id"].duplicated().any():
        raise ValueError("Selection produced duplicate series winners.")

    return winners


def evaluate_policies(
    evaluation: pd.DataFrame,
    winners: pd.DataFrame,
) -> pd.DataFrame:
    """Compare per-series selection against fixed-model policies."""
    data = validate_predictions(evaluation)

    if winners.empty:
        raise ValueError("Winner mapping cannot be empty.")

    if winners["series_id"].duplicated().any():
        raise ValueError("Winner mapping contains duplicate series.")

    if set(data["series_id"]) != set(winners["series_id"]):
        raise ValueError("Every evaluated series must have exactly one selection-period winner.")

    selected = data.merge(
        winners[
            [
                "series_id",
                "model",
            ]
        ],
        on=[
            "series_id",
            "model",
        ],
        how="inner",
        validate="many_to_one",
    )

    if set(selected["series_id"]) != set(data["series_id"]):
        raise ValueError("Selected policy does not cover every evaluation series.")

    rows: list[dict[str, object]] = []

    def add_scope(
        scope: str,
        scope_evaluation: pd.DataFrame,
        scope_selected: pd.DataFrame,
    ) -> None:
        rows.append(
            {
                "scope": scope,
                "policy": SELECTED_POLICY,
                "n_series": int(scope_selected["series_id"].nunique()),
                "n_forecasts": len(scope_selected),
                "smape": smape(
                    scope_selected["actual"],
                    scope_selected["predicted"],
                ),
            }
        )

        for model, group in scope_evaluation.groupby(
            "model",
            sort=True,
        ):
            rows.append(
                {
                    "scope": scope,
                    "policy": (f"{FIXED_POLICY_PREFIX}{model}"),
                    "n_series": int(group["series_id"].nunique()),
                    "n_forecasts": len(group),
                    "smape": smape(
                        group["actual"],
                        group["predicted"],
                    ),
                }
            )

    add_scope(
        "all",
        data,
        selected,
    )

    for metric in sorted(data["metric"].unique()):
        add_scope(
            str(metric),
            data.loc[data["metric"] == metric],
            selected.loc[selected["metric"] == metric],
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "scope",
                "policy",
            ]
        )
        .reset_index(drop=True)
    )
