# Production Forecast Policy Decision

## Context

The forecasting study compares three candidate models:

- Seasonal Naive
- ETS additive damped
- pooled recursive XGBoost

Rolling-origin backtesting is used for model comparison and for descriptive per-series winner analysis. The production policy is evaluated separately so that the final forecasting rule is not chosen from the same results used to describe model performance.

## Held-out policy validation

A temporally separated validation was used to compare production-selection strategies.

- Audited cutoff: `2025-08-01`
- Selection-period targets: `2025-03-01` to `2025-08-01`
- Evaluation-period targets: `2025-09-01` to `2026-07-01`

The selection and evaluation periods do not overlap.

### Selection-period winners

| Model | Series |
|---|---:|
| XGBoost pooled recursive | 67 |
| ETS additive damped | 44 |
| Seasonal Naive | 19 |

This distribution differs from the full-window descriptive winner distribution, indicating that per-series winner selection is not stable across time.

## Held-out results

### Overall

| Policy | sMAPE |
|---|---:|
| Fixed ETS additive damped | 7.9592 |
| Fixed Seasonal Naive | 10.3561 |
| Per-series model selection | 11.3618 |
| Fixed XGBoost pooled recursive | 13.5553 |

### Bonds lodged

| Policy | sMAPE |
|---|---:|
| Fixed ETS additive damped | 13.0104 |
| Fixed Seasonal Naive | 16.9544 |
| Per-series model selection | 19.6499 |
| Fixed XGBoost pooled recursive | 24.1731 |

### Median rent

| Policy | sMAPE |
|---|---:|
| Fixed ETS additive damped | 2.9081 |
| Fixed XGBoost pooled recursive | 2.9376 |
| Per-series model selection | 3.0737 |
| Fixed Seasonal Naive | 3.7577 |

## Production policy

The production policy is:

```text
forecast_policy = fixed_ets_v1
model = ets_additive_damped
```

Fixed ETS is used for all production forecast series.

Per-series winner results remain part of the research comparison layer. They are not used to select the production model for each series.

## Interpretation

The held-out evaluation showed that per-series model selection was less stable and produced higher overall sMAPE than fixed ETS. Fixed ETS was therefore adopted as the production policy.

This does not imply that ETS is the best model for every individual series. The research comparison still retains model-specific and series-level results for analysis.

## Reproduction

Run:

```bash
python scripts/validate_selection_policy.py
```

The default audited cutoff is `2025-08-01`.

A future validation can use:

```bash
python scripts/validate_selection_policy.py --cutoff YYYY-MM-DD
```

A new validation run is a separate experiment and does not automatically replace the audited production policy.
