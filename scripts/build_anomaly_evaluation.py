"""Build reproducible anomaly-detector evaluation evidence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from rmp.anomaly.evaluation import (
    evaluate_historical_threshold_sensitivity,
    evaluate_synthetic_historical_injection,
    evaluate_transition_period,
    validate_anomaly_evaluation_summary,
)

HISTORICAL_ANOMALY_PATH = Path(
    "data/processed/anomaly/historical_anomalies.csv"
)

OUTPUT_PATH = Path(
    "data/processed/anomaly/anomaly_evaluation_summary.csv"
)


def main() -> None:
    """Run anomaly evaluation and save a unified summary."""
    if not HISTORICAL_ANOMALY_PATH.exists():
        raise FileNotFoundError(
            f"Historical anomaly file not found: {HISTORICAL_ANOMALY_PATH}"
        )

    historical = pd.read_csv(HISTORICAL_ANOMALY_PATH)

    synthetic = evaluate_synthetic_historical_injection()
    sensitivity = evaluate_historical_threshold_sensitivity()
    transition = evaluate_transition_period(historical)

    synthetic_output = synthetic.copy()
    synthetic_output["evaluation_group"] = "synthetic_injection"

    sensitivity_output = sensitivity.copy()
    sensitivity_output["evaluation_group"] = "threshold_sensitivity"

    transition_output = transition.copy()
    transition_output["evaluation_group"] = "transition_period"

    summary = pd.concat(
        [
            synthetic_output,
            sensitivity_output,
            transition_output,
        ],
        ignore_index=True,
        sort=False,
    )

    summary = validate_anomaly_evaluation_summary(summary)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("Anomaly detector evaluation complete.")
    print()
    print(f"Output: {OUTPUT_PATH}")
    print(f"Rows: {len(summary)}")
    print()
    print(
        summary[
            [
                "evaluation_group",
                "evaluation",
            ]
        ]
        .value_counts()
        .to_string()
    )


if __name__ == "__main__":
    main()
