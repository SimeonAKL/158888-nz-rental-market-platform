# Production Forecast Policy Decision

## Context

The forecasting research layer evaluates three candidate models:

- Seasonal Naive
- ETS additive damped
- pooled recursive XGBoost

Rolling-origin backtesting is retained for comparative model evaluation and
for descriptive per-series winner analysis.

The production forecasting policy is treated separately from the descriptive
winner analysis.

## Held-out policy validation

A strict temporally separated validation was used to test whether selecting a
different model for each series was suitable for production forecasting.

The audited cutoff is:

`2025-08-01`

Selection-period forecast targets:

`2025-03-01` to `2025-08-01`

Evaluation-period forecast targets:

`2025-09-01` to `2026-07-01`

The two periods contain no overlapping forecast target months.

## Selection-period winners

The models selected from the selection period were:

| Model | Series |
|---|---:|
| XGBoost pooled recursive | 67 |
| ETS additive damped | 44 |
| Seasonal Naive | 19 |

This distribution differs substantially from the full-window descriptive
winner distribution, indicating instability in per-series winner selection
across time.

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

## Production policy decision

The production forecasting policy is:

`fixed_ets_v1`

The production model is:

`ets_additive_damped`

Fixed ETS is used for every forecast-eligible series.

The per-series winner results remain part of the research and model-comparison
layer and are not used to choose the production model for each series.

## Interpretation

Winner/backtest metrics are descriptive results from the model-comparison
experiment and are not independent post-selection estimates.

Strict temporally separated validation showed that the per-series selection
policy was unstable and produced poorer held-out sMAPE than fixed ETS.

Therefore ETS was adopted for production forecasts, while candidate-model
comparisons and series-level winner results are retained for comparative
analysis.

## Reproduction

Run:

    python scripts/validate_selection_policy.py

The default audited cutoff is `2025-08-01`.

A future data release may be evaluated with an explicit cutoff:

    python scripts/validate_selection_policy.py --cutoff YYYY-MM-DD

Such a run represents a new validation experiment and does not replace the
audited Pass 2 result automatically.
