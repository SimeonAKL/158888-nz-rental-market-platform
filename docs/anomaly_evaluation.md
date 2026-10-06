# Anomaly Detector Evaluation

## Purpose

This document evaluates the historical anomaly detector used in the New Zealand Rental Market Analytics and Forecasting Platform.

The evaluation covers:

- synthetic anomaly injection;
- threshold sensitivity;
- behaviour during the documented 2025–2026 Bond Hub transition period.

These tests supplement structural validation of the anomaly outputs. They assess detector behaviour, not causal relationships between anomalies and external events.

## Detector configuration

The historical detector works on year-on-year changes rather than raw monthly levels.

For each series:

- seasonal lag: 12 months;
- rolling baseline: previous seasonal changes;
- expected change: rolling median;
- primary scale estimator: MAD;
- fallback scale estimator: IQR when MAD is zero;
- current observation excluded from its own baseline.

Default settings:

| Parameter | Value |
|---|---:|
| Seasonal lag | 12 months |
| Baseline window | 36 observations |
| Minimum baseline observations | 24 |
| Moderate threshold | 2.5 |
| High threshold | 3.5 |

Dashboard alerts also require metric-specific practical-significance criteria.

## 1. Synthetic anomaly injection

A deterministic monthly series was created with seasonality, trend, and non-degenerate irregular variation. Two shocks were injected separately into the final observation.

| Scenario | Shock | Detected | Direction | Severity | Score |
|---|---:|---|---|---|---:|
| Positive shock | +150 | Yes | High | High | 67.45 |
| Negative shock | -150 | Yes | Low | High | -67.45 |

Both injected shocks were detected.

This confirms that the detector can recover large positive and negative departures under the controlled test setup. It does not establish sensitivity for smaller shocks or all market conditions.

## 2. Threshold sensitivity

The synthetic environment was evaluated with score thresholds from 2.0 to 4.0.

| Threshold | Injected cases recovered | Recovery rate | Background alerts | Background alert rate |
|---:|---:|---:|---:|---:|
| 2.0 | 2 / 2 | 100% | 8 / 60 | 13.33% |
| 2.5 | 2 / 2 | 100% | 8 / 60 | 13.33% |
| 3.0 | 2 / 2 | 100% | 8 / 60 | 13.33% |
| 3.5 | 2 / 2 | 100% | 8 / 60 | 13.33% |
| 4.0 | 2 / 2 | 100% | 0 / 60 | 0.00% |

The injected shocks were large enough to remain detectable at every tested threshold. Background alerting changed with the threshold, confirming that detector output depends on threshold choice.

`background_alert_rate` is not a real-world false-positive rate because the synthetic background has no external ground-truth anomaly labels.

## 3. Bond Hub transition-period evaluation

The project treats the 2025–2026 Bond Hub migration as a known data-system transition. Recent observations are provisional and may not be fully comparable with earlier data.

The analytical dataset ends in July 2026. Two equal 19-month windows were compared:

- pre-transition comparison: June 2023 to December 2024;
- Bond Hub transition: January 2025 to July 2026.

| Period | Scored observations | Statistical anomalies | Statistical anomaly rate | Dashboard alerts | Dashboard alert rate |
|---|---:|---:|---:|---:|---:|
| Pre-transition comparison | 3,082 | 146 | 4.74% | 124 | 4.02% |
| Bond Hub transition | 3,099 | 249 | 8.03% | 200 | 6.45% |

Both statistical anomaly flags and dashboard alerts were more frequent during the transition window.

This supports additional caution when interpreting observations from that period. It does not show that the Bond Hub migration caused the alerts; market movements, data-system effects, or other factors may contribute.

## 4. Reproduction

Implementation:

```text
src/rmp/anomaly/evaluation.py
```

Runner:

```text
scripts/build_anomaly_evaluation.py
```

Tests:

```text
tests/test_anomaly_evaluation.py
```

Run:

```bash
python scripts/build_anomaly_evaluation.py
```

Output:

```text
data/processed/anomaly/anomaly_evaluation_summary.csv
```

The output contains nine records:

- two synthetic-injection scenarios;
- five threshold-sensitivity settings;
- two transition-period windows.

## 5. Limitations

The evaluation has several limits:

- there is no complete external ground-truth dataset of New Zealand rental-market anomalies;
- synthetic tests use controlled conditions;
- background alert rates are not equivalent to real-world false-positive rates;
- the transition-period comparison is descriptive rather than causal;
- anomaly alerts should be interpreted with source provenance and provisional-data warnings.

The dashboard therefore presents anomaly results as analytical alerts rather than confirmed events.
