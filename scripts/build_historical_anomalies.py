"""Build historical anomaly detection outputs."""

from __future__ import annotations

from rmp.anomaly.pipeline import build_historical_anomaly_output


def main() -> None:
    """Run the historical anomaly detection pipeline."""
    anomalies = build_historical_anomaly_output()

    available = anomalies[anomalies["historical_score_available"]]

    detected = anomalies[anomalies["historical_is_anomaly"]]

    moderate = detected[detected["historical_severity"] == "moderate"]

    high = detected[detected["historical_severity"] == "high"]

    print("Historical anomaly detection complete.")
    print()
    print(f"Rows: {len(anomalies)}")
    print(f"Series: {anomalies['series_id'].nunique()}")
    print(f"Score-available rows: {len(available)}")
    print(f"Detected anomalies: {len(detected)}")
    print(f"Moderate anomalies: {len(moderate)}")
    print(f"High anomalies: {len(high)}")

    if not detected.empty:
        print()
        print("=== MOST EXTREME HISTORICAL ANOMALIES ===")

        columns = [
            column
            for column in [
                "period_date",
                "series_id",
                "metric",
                "geography",
                "value",
                "historical_expected",
                "historical_score",
                "historical_direction",
                "historical_severity",
            ]
            if column in detected.columns
        ]

        extreme = (
            detected.assign(absolute_score=detected["historical_score"].abs())
            .sort_values(
                "absolute_score",
                ascending=False,
            )
            .head(20)
        )

        print(extreme[columns].to_string(index=False))


if __name__ == "__main__":
    main()
