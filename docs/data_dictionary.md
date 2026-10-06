# Data Dictionary

## Purpose

This document describes the main processed datasets used by the analytics, forecasting, anomaly-detection, and dashboard layers.

## 1. Analytical monthly panel

**File:** `data/processed/analytics/monthly_panel.csv`

**Current size:** 64,956 rows, 164 series.

| Field | Meaning |
|---|---|
| `period_date` | Monthly observation date. |
| `series_id` | Unique geography-metric time-series identifier. |
| `geography_level` | Geographic level, such as Region or Territorial Authority. |
| `location_id` | Geographic identifier. |
| `location_name` | Human-readable location name. |
| `metric` | Analytical metric: `median_rent` or `bonds_lodged`. |
| `value` | Observed monthly value. |
| `source_snapshot_provisional` | Whether the source snapshot is provisional. |
| `source_snapshot_id` | Source snapshot identifier. |

`monthly_panel.csv` is the main historical dataset used by forecasting, anomaly detection, and the dashboard.

`source_snapshot_provisional` is a provenance field, not an anomaly flag.

## 2. Series catalogue

**File:** `data/processed/analytics/series_catalog.csv`

**Current size:** 164 rows.

| Field | Meaning |
|---|---|
| `series_id` | Analytical series identifier. |
| `geography_level` | Geographic level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `metric` | Series metric. |
| `start_period` | Earliest observation. |
| `end_period` | Latest observation. |
| `n_observations` | Number of observations. |
| `expected_observations` | Expected monthly observations across the date range. |
| `missing_months` | Missing monthly periods. |
| `null_values` | Null analytical values. |
| `completeness_rate` | Share of expected observations available. |
| `continuous_start` | Start of continuous usable history. |
| `continuous_months` | Consecutive usable months. |
| `eligible_for_forecasting` | Whether the series passes forecasting-readiness checks. |

The catalogue contains 164 historical series. Of these, 132 are initially forecast-eligible before duplicate Auckland series are removed from the modelling scope.

## 3. Monthly seasonality

**File:** `data/processed/analytics/monthly_seasonality.csv`

This dataset summarises month-of-year behaviour for each analytical series.

| Field | Meaning |
|---|---|
| `series_id` | Analytical series identifier. |
| `metric` | Series metric. |
| `geography_level` | Geographic level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `month` | Calendar month number. |
| `median_value` | Median historical value for the month. |
| `mean_value` | Mean historical value for the month. |
| `minimum_value` | Minimum historical value for the month. |
| `maximum_value` | Maximum historical value for the month. |
| `n_observations` | Number of observations used. |

## 4. Combined rolling-origin predictions

**File:** `data/processed/forecasting/combined_predictions.csv`

**Current size:** 28,080 rows.

This is a research evaluation dataset combining predictions from all candidate models.

| Field | Meaning |
|---|---|
| `model` | Candidate model. |
| `series_id` | Forecasted series. |
| `metric` | Forecasted metric. |
| `geography_level` | Geographic level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `origin` | Rolling forecast origin. |
| `forecast_period` | Predicted target month. |
| `reference_period` | Reference period associated with the record. |
| `horizon_step` | Months ahead. |
| `actual` | Observed target. |
| `predicted` | Forecast value. |
| `error` | Forecast error. |
| `absolute_error` | Absolute error. |
| `squared_error` | Squared error. |

This file supports model comparison and does not represent the production forward forecast.

## 5. Forecast evaluation summaries

### 5.1 Model comparison

**File:** `data/processed/forecasting/model_comparison.csv`

**Current size:** 6 rows.

| Field | Meaning |
|---|---|
| `model` | Candidate model. |
| `metric` | Evaluated metric. |
| `n_series` | Series represented. |
| `n_forecasts` | Forecast observations used. |
| `mae` | Mean Absolute Error. |
| `rmse` | Root Mean Squared Error. |
| `smape` | Symmetric Mean Absolute Percentage Error. |
| `rank_mae` | MAE rank. |
| `rank_rmse` | RMSE rank. |
| `rank_smape` | sMAPE rank. |
| `mae_improvement_vs_baseline_pct` | MAE improvement over Seasonal Naive. |
| `rmse_improvement_vs_baseline_pct` | RMSE improvement over Seasonal Naive. |
| `smape_improvement_vs_baseline_pct` | sMAPE improvement over Seasonal Naive. |

These are research comparison metrics, not independent post-selection production estimates.

### 5.2 Metrics by origin

**File:** `data/processed/forecasting/metrics_by_origin.csv`

Stores model error summaries for each rolling forecast origin.

### 5.3 Metrics by series

**File:** `data/processed/forecasting/metrics_by_series.csv`

Stores model error summaries for each series.

### 5.4 Metrics by horizon

**File:** `data/processed/forecasting/metrics_by_horizon.csv`

Stores error summaries by forecast horizon.

## 6. Series-level research winners

**File:** `data/processed/forecasting/series_model_winners.csv`

**Current size:** 130 rows.

| Field | Meaning |
|---|---|
| `series_id` | Modelled series. |
| `metric` | Forecasted metric. |
| `geography_level` | Geographic level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `best_model` | Research-layer winner. |
| `best_mae` | Winner MAE. |
| `best_rmse` | Winner RMSE. |
| `best_smape` | Winner sMAPE. |

The research winner is selected primarily by lowest sMAPE, with MAE and RMSE as tie-breakers.

`best_model` does not determine the production model.

## 7. Final forward forecasts

**File:** `data/processed/forecasting/final_forward_forecasts.csv`

**Current size:** 780 rows, 130 series, six horizons per series.

| Field | Meaning |
|---|---|
| `series_id` | Forecasted series. |
| `metric` | Forecasted metric. |
| `geography_level` | Geographic level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `model` | Production model. |
| `forecast_origin` | Final observed period used as origin. |
| `forecast_period` | Future month forecast. |
| `horizon_step` | Months ahead. |
| `predicted` | Forecast value. |
| `backtest_mae` | Historical MAE for the production model. |
| `backtest_rmse` | Historical RMSE for the production model. |
| `backtest_smape` | Historical sMAPE for the production model. |
| `forecast_policy` | Production policy identifier. |

Current production settings:

```text
model = ets_additive_damped
forecast_policy = fixed_ets_v1
```

The production scope contains 65 `median_rent` and 65 `bonds_lodged` series.

## 8. Historical anomaly output

**File:** `data/processed/anomaly/historical_anomalies.csv`

**Current size:** 64,956 rows, 164 series.

### Identity and provenance

| Field | Meaning |
|---|---|
| `period_date` | Monthly observation date. |
| `series_id` | Series identifier. |
| `geography_level` | Geographic level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `metric` | Metric. |
| `value` | Observed value. |
| `source_snapshot_provisional` | Provisional-source flag. |
| `source_snapshot_id` | Source snapshot identifier. |

### Historical detector fields

| Field | Meaning |
|---|---|
| `seasonal_reference` | Value at the configured seasonal lag. |
| `seasonal_change` | Difference from the seasonal reference. |
| `historical_change_expected` | Expected seasonal change from the rolling baseline. |
| `historical_mad` | Rolling Median Absolute Deviation. |
| `historical_iqr` | Rolling IQR fallback scale. |
| `historical_expected` | Expected observation. |
| `historical_deviation` | Observed minus expected value. |
| `historical_deviation_pct` | Deviation as a percentage. |
| `historical_scale_method` | Scale method: `mad`, `iqr`, or `unavailable`. |
| `historical_scale` | Scale used for scoring. |
| `historical_score` | Robust anomaly score. |
| `historical_score_available` | Whether a score is available. |
| `historical_severity` | `normal`, `moderate`, `high`, or `unavailable`. |
| `historical_direction` | `high`, `low`, `normal`, or `unavailable`. |
| `historical_is_anomaly` | Statistical anomaly flag. |
| `seasonal_lag` | Seasonal lag. |
| `baseline_window` | Rolling baseline size. |
| `minimum_baseline_observations` | Minimum observations required. |

### Practical-significance fields

| Field | Meaning |
|---|---|
| `practical_abs_threshold` | Minimum absolute deviation threshold. |
| `practical_pct_threshold` | Minimum percentage deviation threshold. |
| `practical_significance_available` | Whether practical-significance scoring is available. |
| `practical_significance` | Whether practical criteria are met. |
| `statistical_anomaly` | Retained statistical anomaly flag. |
| `dashboard_alert` | Whether statistical and practical criteria both trigger. |
| `alert_status` | Historical alert classification. |

A statistical anomaly is not automatically a dashboard alert. Neither classification establishes causation.

## 9. Forecast-residual anomaly output

**File:** `data/processed/anomaly/forecast_anomalies.csv`

**Current size:** 1,560 rows.

This dataset evaluates one-step-ahead residual behaviour using the research-layer winner for each series.

### Forecast and error fields

| Field | Meaning |
|---|---|
| `model` | Model for the prediction record. |
| `series_id` | Series identifier. |
| `metric` | Forecasted metric. |
| `geography_level` | Geographic level. |
| `location_id` | Geographic identifier. |
| `location_name` | Geographic name. |
| `origin` | Rolling forecast origin. |
| `forecast_period` | Predicted target month. |
| `reference_period` | Reference period. |
| `horizon_step` | Forecast horizon. |
| `actual` | Observed value. |
| `predicted` | Forecast value. |
| `error` | Forecast error. |
| `absolute_error` | Absolute error. |
| `squared_error` | Squared error. |
| `best_model` | Research-layer winner for the series. |

### Residual anomaly fields

| Field | Meaning |
|---|---|
| `forecast_residual` | Actual minus predicted. |
| `forecast_residual_pct` | Residual relative to forecast. |
| `forecast_error_direction` | Whether actual was above or below forecast. |
| `residual_median` | Median of earlier out-of-sample residuals. |
| `residual_mad` | MAD of earlier residuals. |
| `residual_iqr` | IQR fallback scale. |
| `forecast_scale_method` | Scale estimator used. |
| `forecast_residual_scale` | Residual scale. |
| `forecast_anomaly_score` | Robust residual score. |
| `forecast_score_available` | Whether a score is available. |
| `forecast_severity` | Residual anomaly severity. |
| `forecast_direction` | Residual anomaly direction. |
| `forecast_is_anomaly` | Statistical residual anomaly flag. |
| `forecast_anomaly_horizon` | Horizon used by the detector. |
| `minimum_prior_residuals` | Minimum prior residual history required. |

### Practical-significance fields

| Field | Meaning |
|---|---|
| `forecast_practical_significance_available` | Whether practical scoring is available. |
| `forecast_practical_significance` | Whether practical thresholds are met. |
| `forecast_statistical_anomaly` | Retained statistical anomaly flag. |
| `forecast_dashboard_alert` | Dashboard-facing forecast alert. |
| `forecast_alert_status` | Forecast alert classification. |

This detector belongs to the research anomaly layer and is separate from the fixed-ETS production policy.

## 10. Consolidated anomaly summary

**File:** `data/processed/anomaly/anomaly_summary.csv`

**Current size:** 64,956 rows.

This file combines historical and forecast-residual evidence for dashboard use.

Key consolidation fields:

| Field | Meaning |
|---|---|
| `forecast_model` | Research model used for residual comparison. |
| `origin` | Forecast origin. |
| `horizon_step` | Forecast horizon. |
| `predicted` | Research forecast used in residual comparison. |
| `has_forecast_record` | Whether residual evidence exists. |
| `historical_dashboard_alert` | Historical detector alert. |
| `historical_detector_available` | Whether historical evidence is available. |
| `forecast_detector_available` | Whether forecast evidence is available. |
| `detector_coverage` | Available detector coverage. |
| `overall_status` | Consolidated status. |
| `overall_dashboard_alert` | Consolidated alert flag. |
| `overall_severity` | Consolidated severity. |
| `overall_direction` | Consolidated direction. |

Internal `overall_status` values include:

```text
normal
historical_alert
forecast_alert
confirmed_anomaly
unavailable
```

`confirmed_anomaly` means both detector alert types are present for the same observation. In reports and dashboard interpretation it should be described as **flagged by both detectors**, not as a confirmed real-world event.

## 11. Anomaly validation and metadata

### Structural validation

**File:** `data/processed/anomaly/anomaly_validation_summary.csv`

**Current size:** 16 rows.

| Field | Meaning |
|---|---|
| `check_name` | Validation rule. |
| `passed` | Whether the rule passed. |
| `observed` | Observed result. |
| `expected` | Expected result. |
| `details` | Description of the check. |

These are structural and logical checks, not detector-performance metrics.

### Metadata

**File:** `data/processed/anomaly/anomaly_metadata_summary.csv`

**Current size:** 30 rows.

| Field | Meaning |
|---|---|
| `category` | Metadata category. |
| `item` | Metadata item. |
| `value` | Recorded setting or output value. |

## 12. Anomaly detector evaluation

**File:** `data/processed/anomaly/anomaly_evaluation_summary.csv`

**Current size:** 9 rows.

The file contains three evaluation groups:

1. synthetic anomaly injection;
2. threshold sensitivity;
3. transition-period comparison.

Common fields include:

| Field | Meaning |
|---|---|
| `evaluation` | Evaluation type. |
| `evaluation_group` | Evaluation group. |

Synthetic-injection fields include scenario, shock value, expected and detected anomaly status, direction, severity, score, and pass/fail result.

Threshold-sensitivity fields include threshold, injected recovery, background alert counts, and rates.

Transition-period fields include period, date range, row count, scored observations, anomaly counts, and dashboard alert rates.

The current transition comparison uses equal 19-month windows:

```text
2023-06 to 2024-12
2025-01 to 2026-07
```

The comparison is descriptive and does not establish that the Bond Hub migration caused the observed alerts.

## 13. Semantic boundaries

The following distinctions should be preserved:

- `source_snapshot_provisional` is provenance, not an anomaly flag;
- `eligible_for_forecasting` is a modelling-readiness flag, not a data-validity label;
- `best_model` is a research winner, not the production model;
- `forecast_policy` identifies the production forecasting rule;
- `historical_is_anomaly` and `forecast_is_anomaly` are statistical flags;
- dashboard alerts add practical-significance filtering;
- anomaly alerts are analytical signals, not causal conclusions;
- `confirmed_anomaly` should be described externally as **flagged by both detectors**.

## 14. Data flow

```text
monthly_panel.csv
    ├── series_catalog.csv
    ├── monthly_seasonality.csv
    ├── forecasting research outputs
    │   ├── combined_predictions.csv
    │   ├── model_comparison.csv
    │   ├── series_model_winners.csv
    │   └── final_forward_forecasts.csv
    └── historical_anomalies.csv
        ├── forecast_anomalies.csv
        ├── anomaly_summary.csv
        ├── anomaly_validation_summary.csv
        ├── anomaly_metadata_summary.csv
        └── anomaly_evaluation_summary.csv
```

Reproduction commands are documented in `README.md` and `docs/deployment_and_reproducibility.md`.
