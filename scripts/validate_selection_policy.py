"""Run strict held-out validation of forecast production policies."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from rmp.forecasting.policy_validation import (
    AUDITED_CUTOFF,
    evaluate_policies,
    select_series_winners,
    split_by_target_cutoff,
)

PREDICTIONS_PATH = Path(
    "data/processed/forecasting/combined_predictions.csv"
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate per-series selection against fixed-model "
            "forecast policies."
        )
    )

    parser.add_argument(
        "--cutoff",
        default=None,
        help=(
            "Optional cutoff date in YYYY-MM-DD format. "
            "If omitted, the audited Pass 2 cutoff "
            "2025-08-01 is used."
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Run held-out forecast-policy validation."""
    args = parse_args()

    if not PREDICTIONS_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {PREDICTIONS_PATH}"
        )

    predictions = pd.read_csv(
        PREDICTIONS_PATH,
        parse_dates=[
            "origin",
            "forecast_period",
        ],
    )

    cutoff = (
        pd.Timestamp(args.cutoff)
        if args.cutoff is not None
        else AUDITED_CUTOFF
    )

    selection, evaluation = split_by_target_cutoff(
        predictions,
        cutoff,
    )

    winners = select_series_winners(
        selection
    )

    results = evaluate_policies(
        evaluation,
        winners,
    )

    overlap = set(
        selection["forecast_period"]
    ).intersection(
        evaluation["forecast_period"]
    )

    print("===== VALIDATION WINDOW =====")
    print("Cutoff:", cutoff.date())

    print(
        "Selection targets:",
        selection["forecast_period"].min().date(),
        "to",
        selection["forecast_period"].max().date(),
    )

    print(
        "Evaluation targets:",
        evaluation["forecast_period"].min().date(),
        "to",
        evaluation["forecast_period"].max().date(),
    )

    print(
        "Target overlap:",
        len(overlap),
    )

    print()
    print("===== SELECTION WINNER COUNTS =====")

    print(
        winners["model"]
        .value_counts()
        .to_string()
    )

    print()
    print("===== POLICY RESULTS =====")

    print(
        results.to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
