# Data Dictionary

## Purpose

This document describes the principal processed datasets produced by the
New Zealand Regional Rental Market Analytics and Forecasting Platform.

It focuses on the analytical, forecasting, anomaly-detection, validation, and
dashboard-facing outputs used by the implemented system.

The documented schemas reflect the current project outputs.

---

## 1. Analytical Monthly Panel

**File**

    data/processed/analytics/monthly_panel.csv

**Current size**

- 64,956 rows
- 164 series

This is the principal consolidated monthly analytical dataset.

| Field | Meaning |
| --- | --- |
| `period_date` | Monthly observation date. |
| `series_id` | Unique identifier for a geography-metric time series. |
| `geography_level` | Geographic aggregation level, such as Region or Territorial Authority. |
| `location_id` | Source or project identifier for the geographic unit. |
| `location_name` | Human-readable geographic name. |
| `metric` | Analytical measure. Core values are `median_rent` and `bonds_lodged`. |
| `value` | Observed monthly value for the series. |
| `source_snapshot_provisional` | Boolean provenance indicator showing whether the source snapshot is treated as provisional. |
| `source_snapshot_id` | Identifier linking the analytical observation to its source snapshot. |

### Interpretation

`monthly_panel.csv` is the main historical analytical interface used by later
forecasting, anomaly-detection, and dashboard stages.

`source_snapshot_provisional` describes source-data status. It does not mean
that an observation is statistically anomalous or invalid.

---

## 2. Series Catalog

**File**

    data/processed/analytics/series_catalog.csv

**Current size**

- 164 rows

There is one row per analytical series.

| Field | Meaning |
| --- | --- |
| `series_id` | Unique analytical series identifier. |
| `geography_level` | Geographic aggregation level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `metric` | Series metric. |
| `start_period` | Earliest available observation in the series. |
| `end_period` | Latest available observation in the series. |
| `n_observations` | Number of available observations. |
| `expected_observations` | Number of monthly observations expected across the series date range. |
| `missing_months` | Number of missing monthly periods. |
| `null_values` | Number of null analytical values. |
| `completeness_rate` | Proportion of expected observations that are available. |
| `continuous_start` | Start of the continuous usable history considered for modelling readiness. |
| `continuous_months` | Number of consecutive usable months. |
| `eligible_for_forecasting` | Boolean indicating whether the series passes forecasting-readiness requirements. |

### Interpretation

Forecast eligibility is narrower than historical analytical availability.

A series can therefore appear in the analytical panel while not being used in
forecast modelling.

The current catalog contains 164 historical series, of which 132 are marked
eligible for forecasting before explicit duplicate-series exclusion in the
forecast selection layer.

---

## 3. Combined Rolling-Origin Predictions

**File**

    data/processed/forecasting/combined_predictions.csv

**Current size**

- 28,080 rows

This dataset combines rolling-origin research predictions from the candidate
forecasting models.

| Field | Meaning |
| --- | --- |
| `model` | Candidate forecasting model that generated the prediction. |
| `series_id` | Forecasted series identifier. |
| `metric` | Forecasted metric. |
| `geography_level` | Geographic aggregation level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `origin` | Forecast origin used for the rolling-origin evaluation. |
| `forecast_period` | Target month being predicted. |
| `reference_period` | Reference period associated with the evaluation record. |
| `horizon_step` | Forecast horizon measured in months ahead. |
| `actual` | Observed target value. |
| `predicted` | Model prediction. |
| `error` | Forecast error. |
| `absolute_error` | Absolute forecast error. |
| `squared_error` | Squared forecast error. |

### Interpretation

This is a **research evaluation dataset**.

It is used for comparative model assessment and does not itself represent the
production forward forecast.

---

## 4. Model Comparison

**File**

    data/processed/forecasting/model_comparison.csv

**Current size**

- 6 rows

This dataset summarises aggregate rolling-origin forecasting performance by
model and metric.

| Field | Meaning |
| --- | --- |
| `model` | Candidate forecasting model. |
| `metric` | Evaluated metric. |
| `n_series` | Number of series represented in the comparison. |
| `n_forecasts` | Number of forecast observations contributing to the metrics. |
| `mae` | Mean Absolute Error. |
| `rmse` | Root Mean Squared Error. |
| `smape` | Symmetric Mean Absolute Percentage Error. |
| `rank_mae` | Rank by MAE. |
| `rank_rmse` | Rank by RMSE. |
| `rank_smape` | Rank by sMAPE. |
| `mae_improvement_vs_baseline_pct` | Percentage MAE improvement relative to the Seasonal Naive baseline. |
| `rmse_improvement_vs_baseline_pct` | Percentage RMSE improvement relative to the Seasonal Naive baseline. |
| `smape_improvement_vs_baseline_pct` | Percentage sMAPE improvement relative to the Seasonal Naive baseline. |

### Interpretation

These metrics are comparative research evidence.

They should not be interpreted as independent post-selection production
performance estimates.

---

## 5. Series-Level Research Model Winners

**File**

    data/processed/forecasting/series_model_winners.csv

**Current size**

- 130 rows

This dataset stores the best candidate model for each modelled series under the
research comparison procedure.

| Field | Meaning |
| --- | --- |
| `series_id` | Modelled series identifier. |
| `metric` | Forecasted metric. |
| `geography_level` | Geographic aggregation level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `best_model` | Research-layer selected candidate model. |
| `best_mae` | MAE associated with the selected model. |
| `best_rmse` | RMSE associated with the selected model. |
| `best_smape` | sMAPE associated with the selected model. |

### Selection rule

The research winner is selected primarily by lowest sMAPE, with MAE and RMSE
used as tie-breakers.

### Important distinction

`best_model` is a **research-layer winner**.

It does not determine the final production forecasting model.

---

## 6. Final Forward Forecasts

**File**

    data/processed/forecasting/final_forward_forecasts.csv

**Current size**

- 780 rows
- 130 series
- six forecast horizons per series

This is the production-facing forward forecast output.

| Field | Meaning |
| --- | --- |
| `series_id` | Forecasted series identifier. |
| `metric` | Forecasted metric. |
| `geography_level` | Geographic aggregation level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `model` | Model used to generate the production forecast. |
| `forecast_origin` | Final observed period used as the forecast origin. |
| `forecast_period` | Future month being forecast. |
| `horizon_step` | Number of months ahead from the forecast origin. |
| `predicted` | Forecast value. |
| `backtest_mae` | Historical backtest MAE associated with the production model. |
| `backtest_rmse` | Historical backtest RMSE associated with the production model. |
| `backtest_smape` | Historical backtest sMAPE associated with the production model. |
| `forecast_policy` | Production forecasting policy identifier. |

### Production policy

Current production output uses:

    model = ets_additive_damped
    forecast_policy = fixed_ets_v1

The final production scope contains 130 series:

- 65 `median_rent`
- 65 `bonds_lodged`

Two duplicate Auckland Territorial Authority series are excluded from the
forecasting scope.

---

## 7. Historical Anomaly Output

**File**

    data/processed/anomaly/historical_anomalies.csv

**Current size**

- 64,956 rows
- 164 series

This dataset adds historical anomaly diagnostics to the full analytical panel.

### Identity and provenance fields

| Field | Meaning |
| --- | --- |
| `period_date` | Monthly observation date. |
| `series_id` | Series identifier. |
| `geography_level` | Geographic aggregation level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `metric` | Analytical metric. |
| `value` | Observed value. |
| `source_snapshot_provisional` | Source-level provisional-status indicator. |
| `source_snapshot_id` | Source snapshot identifier. |

### Seasonal and historical baseline fields

| Field | Meaning |
| --- | --- |
| `seasonal_reference` | Value from the configured seasonal lag. |
| `seasonal_change` | Difference from the seasonal reference. |
| `historical_change_expected` | Expected historical seasonal change derived from the rolling baseline. |
| `historical_mad` | Rolling Median Absolute Deviation. |
| `historical_iqr` | Rolling Interquartile Range used as a scale fallback. |
| `historical_expected` | Expected observation implied by the historical baseline. |
| `historical_deviation` | Observed minus expected value. |
| `historical_deviation_pct` | Historical deviation expressed as a percentage. |
| `historical_scale_method` | Robust scale estimator used, such as `mad`, `iqr`, or `unavailable`. |
| `historical_scale` | Robust scale used for anomaly scoring. |
| `historical_score` | Robust anomaly score. |
| `historical_score_available` | Whether a valid historical anomaly score can be calculated. |

### Classification fields

| Field | Meaning |
| --- | --- |
| `historical_severity` | Statistical classification such as `normal`, `moderate`, `high`, or `unavailable`. |
| `historical_direction` | Direction classification such as `high`, `low`, `normal`, or `unavailable`. |
| `historical_is_anomaly` | Whether the statistical score passes the anomaly threshold. |
| `seasonal_lag` | Seasonal lag used by the detector. |
| `baseline_window` | Historical rolling baseline size. |
| `minimum_baseline_observations` | Minimum history required before scoring. |

### Practical-significance fields

| Field | Meaning |
| --- | --- |
| `practical_abs_threshold` | Metric-specific minimum absolute deviation for practical significance. |
| `practical_pct_threshold` | Metric-specific minimum percentage deviation. |
| `practical_significance_available` | Whether practical-significance assessment is available. |
| `practical_significance` | Whether practical-significance criteria are satisfied. |
| `statistical_anomaly` | Retained statistical anomaly indicator. |
| `dashboard_alert` | Whether statistical and practical criteria jointly trigger a dashboard alert. |
| `alert_status` | Historical alert classification used by the anomaly pipeline. |

### Interpretation

A statistical anomaly is not automatically a dashboard alert.

Dashboard alerting additionally requires practical significance.

Neither classification establishes a causal explanation.

---

## 8. Forecast-Residual Anomaly Output

**File**

    data/processed/anomaly/forecast_anomalies.csv

**Current size**

- 1,560 rows

This dataset evaluates unusual one-step-ahead residual behaviour using the
research-layer selected winner model.

### Forecast identity and error fields

| Field | Meaning |
| --- | --- |
| `model` | Model associated with the rolling-origin prediction record. |
| `series_id` | Series identifier. |
| `metric` | Forecasted metric. |
| `geography_level` | Geographic aggregation level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `origin` | Rolling forecast origin. |
| `forecast_period` | Predicted target month. |
| `reference_period` | Reference period associated with the prediction. |
| `horizon_step` | Forecast horizon. |
| `actual` | Observed value. |
| `predicted` | Predicted value. |
| `error` | Forecast error. |
| `absolute_error` | Absolute error. |
| `squared_error` | Squared error. |
| `best_model` | Research-layer winner model for the series. |

### Residual anomaly fields

| Field | Meaning |
| --- | --- |
| `forecast_residual` | Actual minus predicted value. |
| `forecast_residual_pct` | Residual expressed relative to the forecast. |
| `forecast_error_direction` | Whether actual was above or below forecast. |
| `residual_median` | Median of earlier out-of-sample residuals. |
| `residual_mad` | Median Absolute Deviation of previous residuals. |
| `residual_iqr` | Interquartile Range fallback scale. |
| `forecast_scale_method` | Scale estimator used for forecast anomaly scoring. |
| `forecast_residual_scale` | Robust residual scale. |
| `forecast_anomaly_score` | Robust residual anomaly score. |
| `forecast_score_available` | Whether the forecast anomaly score is available. |
| `forecast_severity` | Forecast-residual anomaly severity. |
| `forecast_direction` | Forecast anomaly direction. |
| `forecast_is_anomaly` | Statistical forecast-residual anomaly indicator. |
| `forecast_anomaly_horizon` | Forecast horizon used by the anomaly detector. |
| `minimum_prior_residuals` | Minimum prior residual history required for scoring. |

### Practical-significance fields

| Field | Meaning |
| --- | --- |
| `forecast_practical_significance_available` | Whether practical-significance assessment is available. |
| `forecast_practical_significance` | Whether forecast deviation meets practical thresholds. |
| `forecast_statistical_anomaly` | Statistical forecast anomaly indicator retained for downstream use. |
| `forecast_dashboard_alert` | Dashboard-facing forecast anomaly alert. |
| `forecast_alert_status` | Forecast alert classification. |

### Interpretation

The forecast-residual detector is part of the **research anomaly layer**.

It uses research-layer series winners and is separate from the fixed-ETS
production forecasting policy.

---

## 9. Consolidated Anomaly Summary

**File**

    data/processed/anomaly/anomaly_summary.csv

**Current size**

- 64,956 rows

This is the dashboard-ready consolidation of historical and forecast-residual
anomaly evidence.

It includes the historical anomaly fields described above plus forecast
diagnostics where forecast-residual records are available.

### Consolidation-specific fields

| Field | Meaning |
| --- | --- |
| `forecast_model` | Research model associated with the forecast-residual anomaly record. |
| `origin` | Forecast origin associated with the residual record. |
| `horizon_step` | Forecast horizon represented in the anomaly record. |
| `predicted` | Research forecast used for residual comparison. |
| `has_forecast_record` | Whether the observation has corresponding forecast-residual evidence. |
| `historical_dashboard_alert` | Historical detector dashboard-alert status. |
| `historical_detector_available` | Whether historical anomaly evidence is available. |
| `forecast_detector_available` | Whether forecast-residual anomaly evidence is available. |
| `detector_coverage` | Description of which detector evidence is available. |
| `overall_status` | Consolidated anomaly status. |
| `overall_dashboard_alert` | Consolidated dashboard alert indicator. |
| `overall_severity` | Consolidated severity classification. |
| `overall_direction` | Consolidated anomaly direction. |

### `overall_status`

Current internal statuses include:

- `normal`
- `historical_alert`
- `forecast_alert`
- `confirmed_anomaly`
- `unavailable`

The internal value `confirmed_anomaly` means that both detector alert types are
present for the same observation.

For reporting and interpretation it should be described as:

    flagged by both detectors

It should not be interpreted as a confirmed real-world event.

---

## 10. Anomaly Structural Validation Summary

**File**

    data/processed/anomaly/anomaly_validation_summary.csv

**Current size**

- 16 rows

| Field | Meaning |
| --- | --- |
| `check_name` | Name of the structural or logical validation check. |
| `passed` | Whether the check passed. |
| `observed` | Observed validation result. |
| `expected` | Expected result. |
| `details` | Human-readable description of the validation rule. |

### Interpretation

These checks validate output consistency and classification logic.

They are not detector-performance metrics.

Detector-performance evidence is stored separately in
`anomaly_evaluation_summary.csv`.

---

## 11. Anomaly Metadata Summary

**File**

    data/processed/anomaly/anomaly_metadata_summary.csv

**Current size**

- 30 rows

| Field | Meaning |
| --- | --- |
| `category` | Metadata category. |
| `item` | Metadata item name. |
| `value` | Recorded configuration or output value. |

This dataset records reproducibility metadata such as detector thresholds,
configuration values, and output counts.

---

## 12. Anomaly Detector Evaluation Summary

**File**

    data/processed/anomaly/anomaly_evaluation_summary.csv

**Current size**

- 9 rows

This output combines three different detector-evaluation groups in one
audit-oriented dataset.

Because the evaluation groups have different schemas, fields not relevant to a
particular evaluation record are intentionally left null.

### Common fields

| Field | Meaning |
| --- | --- |
| `evaluation` | Evaluation type. |
| `evaluation_group` | High-level evaluation group. |

### Synthetic-injection fields

| Field | Meaning |
| --- | --- |
| `scenario` | Synthetic test scenario. |
| `shock_value` | Injected anomaly magnitude. |
| `expected_anomaly` | Whether the injected observation is expected to be anomalous. |
| `detected_anomaly` | Whether the detector identified it. |
| `expected_direction` | Expected anomaly direction. |
| `observed_direction` | Detector-classified direction. |
| `severity` | Detector severity classification. |
| `score` | Robust anomaly score. |
| `passed` | Whether detection and direction matched expectations. |

### Threshold-sensitivity fields

| Field | Meaning |
| --- | --- |
| `threshold` | Evaluated anomaly-score threshold. |
| `injected_cases` | Number of injected synthetic cases. |
| `injected_recovered` | Number successfully identified at the threshold. |
| `injection_recovery_rate` | Proportion of injected cases recovered. |
| `background_scored_observations` | Number of scored synthetic background observations. |
| `background_alerts` | Number of background observations crossing the tested threshold. |
| `background_alert_rate` | Proportion of scored background observations crossing the threshold. |

`background_alert_rate` is not a real-world false-positive rate because no
external ground-truth anomaly labels exist for the synthetic background.

### Transition-period fields

| Field | Meaning |
| --- | --- |
| `period` | Comparison-period label. |
| `start_date` | Start of evaluation window. |
| `end_date` | End of evaluation window. |
| `months` | Number of months in the window. |
| `rows` | Total analytical rows within the window. |
| `scored_observations` | Number of observations with valid detector scores. |
| `statistical_anomalies` | Number of statistical anomaly flags. |
| `statistical_anomaly_rate` | Statistical anomalies divided by scored observations. |
| `dashboard_alerts` | Number of dashboard alerts. |
| `dashboard_alert_rate` | Dashboard alerts divided by scored observations. |

The current transition evaluation compares:

    2023-06 to 2024-12
    versus
    2025-01 to 2026-07

using equal 19-month windows.

This comparison is descriptive and must not be interpreted as evidence that
the Bond Hub migration caused the observed alerts.

---

## 13. Research and Production Semantics

Several outputs have deliberately different purposes.

### Research outputs

The following are primarily research/comparison evidence:

    combined_predictions.csv
    model_comparison.csv
    series_model_winners.csv
    forecast_anomalies.csv

They support model comparison, rolling-origin analysis, and research-layer
anomaly detection.

### Production-facing output

The production forecast output is:

    final_forward_forecasts.csv

It follows the documented fixed ETS production policy.

### Dashboard-facing analytical outputs

The main dashboard-facing historical and anomaly datasets are:

    monthly_panel.csv
    anomaly_summary.csv

The dashboard also reads forecasting and evaluation outputs for dedicated
forecasting and model-performance views.

---

## 14. Important Semantic Boundaries

The following distinctions must be preserved in analysis and reporting:

- `source_snapshot_provisional` is a provenance field, not an anomaly flag;
- `eligible_for_forecasting` is a modelling-readiness flag, not a data-validity label;
- `best_model` describes a research comparison winner, not the production model;
- `forecast_policy` identifies the production forecasting policy;
- `historical_is_anomaly` and `forecast_is_anomaly` are statistical flags;
- `dashboard_alert` adds practical-significance filtering;
- anomaly alerts are analytical signals, not causal conclusions;
- `confirmed_anomaly` is an internal consolidation label and should be described externally as an observation flagged by both detectors.

---

## 15. Data Lifecycle

The principal processed-data flow is:

    monthly_panel.csv
          |
          +--> series_catalog.csv
          |
          +--> forecasting research outputs
          |        |
          |        +--> combined_predictions.csv
          |        +--> model_comparison.csv
          |        +--> series_model_winners.csv
          |        +--> final_forward_forecasts.csv
          |
          +--> historical_anomalies.csv
                   |
                   +--> forecast_anomalies.csv
                   |
                   +--> anomaly_summary.csv
                   +--> anomaly_validation_summary.csv
                   +--> anomaly_metadata_summary.csv
                   +--> anomaly_evaluation_summary.csv

The exact reproduction commands are documented in the repository README and
in `docs/deployment_and_reproducibility.md`.
