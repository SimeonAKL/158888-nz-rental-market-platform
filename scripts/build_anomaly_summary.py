"""Build consolidated anomaly summary output."""

from __future__ import annotations

from rmp.anomaly.pipeline import (
    build_anomaly_summary_output,
)


def main() -> None:
    """Build dashboard-ready consolidated anomaly output."""
    summary = build_anomaly_summary_output()

    alerts = summary[
        summary["overall_dashboard_alert"]
    ]

    print(
        "Anomaly consolidation complete."
    )
    print()

    print(
        f"Rows: {len(summary)}"
    )

    print(
        "Series: "
        f"{summary['series_id'].nunique()}"
    )

    print(
        "Periods: "
        f"{summary['period_date'].nunique()}"
    )

    print(
        "Rows with forecast records: "
        f"{summary['has_forecast_record'].sum()}"
    )

    print(
        "Overall dashboard alerts: "
        f"{len(alerts)}"
    )

    print()
    print("=== OVERALL STATUS ===")

    print(
        summary[
            "overall_status"
        ].value_counts(
            dropna=False
        )
    )

    print()
    print("=== OVERALL SEVERITY ===")

    print(
        summary[
            "overall_severity"
        ].value_counts(
            dropna=False
        )
    )

    print()
    print("=== DETECTOR COVERAGE ===")

    print(
        summary[
            "detector_coverage"
        ].value_counts(
            dropna=False
        )
    )

    if not alerts.empty:
        print()
        print(
            "=== CONSOLIDATED ALERTS "
            "WITH FORECAST COVERAGE ==="
        )

        recent = alerts[
            alerts["has_forecast_record"]
        ].copy()

        columns = [
            column
            for column in [
                "period_date",
                "location_name",
                "metric",
                "value",
                "historical_severity",
                "historical_direction",
                "historical_dashboard_alert",
                "forecast_model",
                "predicted",
                "forecast_residual",
                "forecast_error_direction",
                "forecast_severity",
                "forecast_dashboard_alert",
                "overall_status",
                "overall_severity",
                "overall_direction",
            ]
            if column in recent.columns
        ]

        print(
            recent[
                columns
            ].sort_values(
                [
                    "period_date",
                    "location_name",
                    "metric",
                ]
            ).to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()
