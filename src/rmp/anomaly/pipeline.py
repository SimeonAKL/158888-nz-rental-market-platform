"""Pipeline helpers for anomaly detection outputs."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from rmp.anomaly.consolidate import (
    consolidate_anomaly_outputs,
)
from rmp.anomaly.forecast import (
    detect_forecast_residual_anomalies,
)
from rmp.anomaly.forecast_practical import (
    add_forecast_practical_significance,
)
from rmp.anomaly.historical import (
    detect_historical_anomalies,
)
from rmp.anomaly.practical import (
    add_practical_significance,
)
from rmp.anomaly.validation import (
    build_anomaly_metadata,
    validate_anomaly_summary,
)

DEFAULT_HISTORICAL_INPUT_PATH = Path("data/processed/analytics/monthly_panel.csv")

DEFAULT_PREDICTIONS_PATH = Path("data/processed/forecasting/combined_predictions.csv")

DEFAULT_WINNERS_PATH = Path("data/processed/forecasting/series_model_winners.csv")

DEFAULT_OUTPUT_DIR = Path("data/processed/anomaly")


def build_historical_anomaly_output(
    input_path: Path = DEFAULT_HISTORICAL_INPUT_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> pd.DataFrame:
    """Build and save historical anomaly output."""
    if not input_path.exists():
        raise FileNotFoundError(f"Analytics panel not found: {input_path}")

    panel = pd.read_csv(input_path)

    anomalies = detect_historical_anomalies(panel)

    anomalies = add_practical_significance(anomalies)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = output_dir / "historical_anomalies.csv"

    anomalies.to_csv(
        output_path,
        index=False,
    )

    return anomalies


def build_forecast_anomaly_output(
    predictions_path: Path = DEFAULT_PREDICTIONS_PATH,
    winners_path: Path = DEFAULT_WINNERS_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> pd.DataFrame:
    """Build and save forecast-residual anomaly output."""
    if not predictions_path.exists():
        raise FileNotFoundError(f"Combined prediction file not found: {predictions_path}")

    if not winners_path.exists():
        raise FileNotFoundError(f"Series winner file not found: {winners_path}")

    predictions = pd.read_csv(predictions_path)

    winners = pd.read_csv(winners_path)

    anomalies = detect_forecast_residual_anomalies(
        predictions,
        winners,
    )

    anomalies = add_forecast_practical_significance(anomalies)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = output_dir / "forecast_anomalies.csv"

    anomalies.to_csv(
        output_path,
        index=False,
    )

    return anomalies


def build_anomaly_summary_output(
    historical_path: Path = (DEFAULT_OUTPUT_DIR / "historical_anomalies.csv"),
    forecast_path: Path = (DEFAULT_OUTPUT_DIR / "forecast_anomalies.csv"),
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> pd.DataFrame:
    """Build consolidated dashboard-ready anomaly output."""
    if not historical_path.exists():
        raise FileNotFoundError(f"Historical anomaly file not found: {historical_path}")

    if not forecast_path.exists():
        raise FileNotFoundError(f"Forecast anomaly file not found: {forecast_path}")

    historical = pd.read_csv(historical_path)

    forecast = pd.read_csv(forecast_path)

    summary = consolidate_anomaly_outputs(
        historical,
        forecast,
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = output_dir / "anomaly_summary.csv"

    summary.to_csv(
        output_path,
        index=False,
    )

    return summary


def build_anomaly_validation_outputs(
    summary_path: Path = (DEFAULT_OUTPUT_DIR / "anomaly_summary.csv"),
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate final anomaly output and save metadata summaries."""
    if not summary_path.exists():
        raise FileNotFoundError(f"Anomaly summary file not found: {summary_path}")

    summary = pd.read_csv(summary_path)

    validation = validate_anomaly_summary(summary)

    metadata = build_anomaly_metadata(summary)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    validation.to_csv(
        output_dir / "anomaly_validation_summary.csv",
        index=False,
    )

    metadata.to_csv(
        output_dir / "anomaly_metadata_summary.csv",
        index=False,
    )

    return validation, metadata
