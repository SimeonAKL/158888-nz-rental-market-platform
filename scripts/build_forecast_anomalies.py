"""Build forecast-residual anomaly detection output."""

from __future__ import annotations

from rmp.anomaly.pipeline import (
    build_forecast_anomaly_output,
)


def main() -> None:
    """Run forecast residual anomaly detection."""
    anomalies = build_forecast_anomaly_output()

    available = anomalies[anomalies["forecast_score_available"]]

    detected = anomalies[anomalies["forecast_is_anomaly"]]

    moderate = detected[detected["forecast_severity"] == "moderate"]

    high = detected[detected["forecast_severity"] == "high"]

    print("Forecast residual anomaly detection complete.")
    print()

    print(f"Rows: {len(anomalies)}")

    print(f"Series: {anomalies['series_id'].nunique()}")

    print(f"Models used: {anomalies['model'].nunique()}")

    print(f"Score-available rows: {len(available)}")

    print(f"Detected anomalies: {len(detected)}")

    print(f"Moderate anomalies: {len(moderate)}")

    print(f"High anomalies: {len(high)}")

    print()
    print("=== WINNER MODELS USED ===")

    print(anomalies["model"].value_counts())

    print()
    print("=== SCALE METHODS ===")

    print(anomalies["forecast_scale_method"].value_counts(dropna=False))

    if not detected.empty:
        print()
        print("=== MOST EXTREME FORECAST RESIDUAL ANOMALIES ===")

        extreme = (
            detected.assign(absolute_score=detected["forecast_anomaly_score"].abs())
            .sort_values(
                "absolute_score",
                ascending=False,
            )
            .head(20)
        )

        columns = [
            column
            for column in [
                "forecast_period",
                "series_id",
                "location_name",
                "metric",
                "model",
                "actual",
                "predicted",
                "forecast_residual",
                "forecast_residual_pct",
                "residual_median",
                "forecast_anomaly_score",
                "forecast_direction",
                "forecast_severity",
            ]
            if column in extreme.columns
        ]

        print(extreme[columns].to_string(index=False))


if __name__ == "__main__":
    main()
