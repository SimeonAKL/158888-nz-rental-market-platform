# Anomaly Detector Evaluation

## Purpose

This document records the empirical evaluation of the anomaly-detection
component used by the New Zealand Rental Market Analytics and Forecasting
Platform.

The project proposal specified that at least one interpretable statistical
anomaly-detection method would be evaluated using synthetic anomaly injection,
historical residual behaviour, and documented system-transition periods.

The evaluation described here supplements the existing structural anomaly
validation checks. Structural validation verifies output consistency and
classification logic, whereas this evaluation examines detector behaviour under
controlled and historically relevant conditions.

Anomaly outputs remain analytical alerts only. They do not establish causal
relationships between market movements, data-system changes, or external
events.

## Detector Context

The historical anomaly detector evaluates year-on-year changes rather than raw
monthly levels.

For each series:

- a 12-month seasonal lag is used;
- previous seasonal changes form the historical baseline;
- a rolling median defines the expected change;
- MAD is the primary robust scale estimator;
- IQR is used when MAD is zero;
- the current observation is excluded from its own baseline;
- robust-score thresholds classify observations as normal, moderate, or high.

The default historical detector uses:

- seasonal lag: 12 months;
- baseline window: 36 observations;
- minimum baseline observations: 24;
- moderate threshold: 2.5;
- high threshold: 3.5.

Dashboard alerts additionally require metric-specific practical-significance
criteria.

## 1. Synthetic Anomaly Injection

A deterministic monthly synthetic series was constructed with seasonal,
trend, and non-degenerate irregular variation.

Two controlled shocks were injected separately into the final observation:

- positive shock: +150;
- negative shock: -150.

The detector successfully identified both injected observations.

| Scenario | Shock | Detected | Direction | Severity | Score |
| --- | ---: | --- | --- | --- | ---: |
| Positive shock | +150 | Yes | High | High | 67.45 |
| Negative shock | -150 | Yes | Low | High | -67.45 |

Synthetic injection recovery was therefore 2 out of 2 cases, or 100%, for
these deliberately large test shocks.

This result demonstrates that the detector can recover clearly abnormal
positive and negative movements under the controlled test configuration. It
does not establish sensitivity for every possible anomaly magnitude or market
condition.

## 2. Threshold Sensitivity

The same controlled synthetic environment was evaluated using anomaly-score
thresholds from 2.0 to 4.0.

| Threshold | Injected cases recovered | Recovery rate | Background alerts | Background alert rate |
| ---: | ---: | ---: | ---: | ---: |
| 2.0 | 2 / 2 | 100% | 8 / 60 | 13.33% |
| 2.5 | 2 / 2 | 100% | 8 / 60 | 13.33% |
| 3.0 | 2 / 2 | 100% | 8 / 60 | 13.33% |
| 3.5 | 2 / 2 | 100% | 8 / 60 | 13.33% |
| 4.0 | 2 / 2 | 100% | 0 / 60 | 0.00% |

The injected shocks were sufficiently large to remain detectable at all tested
thresholds.

The background alert rate changed with the threshold, showing that detector
output is sensitive to threshold selection.

The background alert rate is not interpreted as a real-world false-positive
rate because the synthetic background observations do not provide external
ground-truth labels for genuine market anomalies.

## 3. Bond Hub Transition-Period Evaluation

The project proposal identifies the 2025-2026 Bond Hub migration as a known
data-system transition period during which recent observations are provisional
and may not be fully comparable with earlier data.

The available analytical dataset currently ends in July 2026. The transition
evaluation therefore uses:

- Bond Hub transition window: January 2025 to July 2026;
- immediately preceding comparison window: June 2023 to December 2024.

Both windows contain 19 months.

| Period | Scored observations | Statistical anomalies | Statistical anomaly rate | Dashboard alerts | Dashboard alert rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pre-transition comparison | 3,082 | 146 | 4.74% | 124 | 4.02% |
| Bond Hub transition | 3,099 | 249 | 8.03% | 200 | 6.45% |

The detector produced a higher rate of statistical anomaly flags and dashboard
alerts during the documented transition period than during the immediately
preceding equal-length comparison window.

This result is treated as evidence that observations from the transition period
require additional interpretive caution.

It must not be interpreted as evidence that the Bond Hub migration caused the
identified anomalies. The observed difference may reflect data-system effects,
genuine rental-market movements, other external factors, or a combination of
these influences.

## 4. Reproducibility

The evaluation implementation is located in:

- `src/rmp/anomaly/evaluation.py`

The executable evaluation runner is:

- `scripts/build_anomaly_evaluation.py`

Automated tests are located in:

- `tests/test_anomaly_evaluation.py`

Running:

    python scripts/build_anomaly_evaluation.py

produces:

    data/processed/anomaly/anomaly_evaluation_summary.csv

The output contains nine evaluation records:

- two synthetic-injection scenarios;
- five threshold-sensitivity settings;
- two transition-period windows.

## 5. Interpretation and Limitations

This evaluation provides empirical evidence that the implemented anomaly
detector behaves as intended under controlled injected shocks and that its
alert rate responds to threshold choice.

It also documents detector behaviour during a known period of data-system
transition.

However:

- there is no complete external ground-truth dataset of genuine New Zealand
  rental-market anomalies;
- the synthetic experiments use deliberately controlled conditions;
- background alert rates are not equivalent to real-world false-positive
  rates;
- the transition-period comparison is descriptive rather than causal;
- anomaly alerts should be interpreted together with data provenance,
  provisional-data warnings, and contextual market analysis.

Accordingly, the dashboard presents anomaly outputs as analytical alerts rather
than confirmed events or causal findings.
