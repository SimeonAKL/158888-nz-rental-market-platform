"""Anomaly detection utilities for the rental market platform."""

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

__all__ = [
    "add_forecast_practical_significance",
    "add_practical_significance",
    "build_anomaly_metadata",
    "consolidate_anomaly_outputs",
    "detect_forecast_residual_anomalies",
    "detect_historical_anomalies",
    "validate_anomaly_summary",
]
