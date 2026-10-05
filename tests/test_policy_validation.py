"""Tests for strict held-out forecast-policy validation."""

from __future__ import annotations

import pandas as pd

from rmp.forecasting.policy_validation import (
    AUDITED_CUTOFF,
    SELECTED_POLICY,
    default_cutoff,
    evaluate_policies,
    select_series_winners,
    split_by_target_cutoff,
)

MODELS = (
    "ets_additive_damped",
    "xgboost_pooled_recursive",
)


def make_predictions() -> pd.DataFrame:
    """Create deterministic rolling-origin predictions."""
    rows: list[dict[str, object]] = []

    origins = pd.date_range(
        "2025-02-01",
        periods=12,
        freq="MS",
    )

    series_config = {
        "series_1": {
            "metric": "bonds_lodged",
            "best_model": "ets_additive_damped",
        },
        "series_2": {
            "metric": "median_rent",
            "best_model": "xgboost_pooled_recursive",
        },
    }

    for series_id, config in series_config.items():
        for origin in origins:
            for step in range(1, 7):
                forecast_period = origin + pd.DateOffset(months=step)

                for model in MODELS:
                    if model == config["best_model"]:
                        error = 1.0
                    else:
                        error = 5.0

                    rows.append(
                        {
                            "model": model,
                            "series_id": series_id,
                            "metric": config["metric"],
                            "origin": origin,
                            "forecast_period": forecast_period,
                            "horizon_step": step,
                            "actual": 100.0,
                            "predicted": 100.0 + error,
                        }
                    )

    return pd.DataFrame(rows)


def test_default_cutoff_is_fixed_audited_date() -> None:
    """Default validation cutoff should reproduce Pass 2 audit."""
    predictions = make_predictions()

    assert default_cutoff(predictions) == AUDITED_CUTOFF

    assert AUDITED_CUTOFF == pd.Timestamp("2025-08-01")


def test_split_has_zero_target_overlap() -> None:
    """Selection and evaluation must not share target months."""
    predictions = make_predictions()

    selection, evaluation = split_by_target_cutoff(
        predictions,
        AUDITED_CUTOFF,
    )

    assert selection["forecast_period"].max() <= AUDITED_CUTOFF

    assert evaluation["forecast_period"].min() > AUDITED_CUTOFF

    assert (evaluation["origin"] >= AUDITED_CUTOFF).all()

    overlap = set(selection["forecast_period"]).intersection(evaluation["forecast_period"])

    assert not overlap


def test_selection_period_winners_are_series_specific() -> None:
    """Lowest-sMAPE model should be selected per series."""
    predictions = make_predictions()

    selection, _ = split_by_target_cutoff(
        predictions,
        AUDITED_CUTOFF,
    )

    winners = select_series_winners(selection)

    winner_map = dict(
        zip(
            winners["series_id"],
            winners["model"],
            strict=True,
        )
    )

    assert winner_map == {
        "series_1": "ets_additive_damped",
        "series_2": "xgboost_pooled_recursive",
    }


def test_evaluate_policies_reports_selected_and_fixed_models() -> None:
    """Evaluation should contain selected and fixed-model policies."""
    predictions = make_predictions()

    selection, evaluation = split_by_target_cutoff(
        predictions,
        AUDITED_CUTOFF,
    )

    winners = select_series_winners(selection)

    results = evaluate_policies(
        evaluation,
        winners,
    )

    assert set(results["scope"]) == {
        "all",
        "bonds_lodged",
        "median_rent",
    }

    policies = set(results["policy"])

    assert SELECTED_POLICY in policies

    assert "fixed_ets_additive_damped" in policies

    assert "fixed_xgboost_pooled_recursive" in policies

    overall = results.loc[results["scope"] == "all"]

    assert not overall.empty

    assert overall["n_series"].min() > 0

    assert overall["n_forecasts"].min() > 0
