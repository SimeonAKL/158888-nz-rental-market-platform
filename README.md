# NZ Regional Rental Market Analytics and Forecasting Platform

**Massey University — 158888 Information Technology Professional Project**

An end-to-end platform for analysing, forecasting, and monitoring regional rental-market conditions in New Zealand using official Tenancy Services / MBIE data.

The project combines reproducible data engineering, time-series forecasting, interpretable anomaly detection, and a Streamlit dashboard.

---

## Project Scope

The platform covers:

- New Zealand Regions;
- valid Territorial Authorities where data quality supports analysis;
- monthly median weekly rent;
- monthly rental bond lodgements.

Historical availability and forecasting eligibility are treated separately. A series can remain available for descriptive analysis even if it does not meet modelling-readiness requirements.

Current analytical scope:

```text
64,956 monthly observations
164 analytical series
132 initially forecast-eligible series
130 final modelling / production forecast series
February 1993 to July 2026
```

The final production scope contains:

```text
65 median_rent series
65 bonds_lodged series
6 forecast months per series
780 forward forecast rows
```

---

## Main Features

### Data engineering

- official source acquisition;
- immutable source snapshots;
- provenance and provisional-status tracking;
- staging and validation;
- PostgreSQL/Supabase persistence;
- cross-source validation;
- modelling-readiness checks.

### Historical analytics

- long-run monthly trends;
- Region and Territorial Authority views;
- seasonality summaries;
- data-quality and provenance context.

### Forecasting

Three candidate models are evaluated:

- Seasonal Naive;
- ETS additive damped;
- pooled recursive XGBoost.

Evaluation uses expanding-window rolling-origin validation with:

- MAE;
- RMSE;
- sMAPE.

Research-model comparison is kept separate from the production policy.

The final production policy is:

```text
forecast_policy = fixed_ets_v1
model = ets_additive_damped
```

### Anomaly detection

Two complementary detector paths are used:

- historical seasonal-change detector;
- forecast-residual detector.

Dashboard alerts also require practical significance. Anomaly results are analytical signals, not causal findings.

### Dashboard

The Streamlit application contains:

1. Overview
2. Historical Analytics
3. Forecasting
4. Model Performance
5. Anomaly Detection

---

## Data Sources

The project uses official New Zealand rental-market data.

### Rental Bond data

Rental Bond data is the primary source for the final monthly analytical panel.

### Market Rent data

The Tenancy Services / MBIE Market Rent API is acquired and stored independently and is used as supporting source evidence, including cross-source validation.

No private rental-listing scraping is used.

Recent observations affected by the 2025–2026 Bond Hub migration retain explicit provisional-source metadata.

---

## Architecture

Development and regeneration flow:

```text
Official Tenancy Services / MBIE data
        ↓
Acquisition and snapshots
        ↓
Raw data
        ↓
Transformation and validation
        ↓
Staging data
        ↓
Supabase PostgreSQL
        ↓
Validated clean observations
        ↓
Monthly analytical panel
        ↓
Forecasting / model comparison
        ↓
Production forecasts
        ↓
Anomaly detection
        ↓
Validated dashboard outputs
```

The deployed assessment version does not query Supabase or government APIs at runtime.

Deployment flow:

```text
GitHub repository
        ↓
frozen validated CSV outputs
        ↓
Streamlit Community Cloud
        ↓
interactive dashboard
```

This frozen deployment keeps the dashboard, report figures, model results, and anomaly outputs consistent during assessment.

See [`docs/architecture.md`](docs/architecture.md) for the full design.

---

## Repository Structure

```text
.
├── app.py
├── pages/
│   ├── 1_Overview.py
│   ├── 2_Historical_Analytics.py
│   ├── 3_Forecasting.py
│   ├── 4_Model_Performance.py
│   └── 5_Anomaly_Detection.py
│
├── src/rmp/
│   ├── acquisition/
│   ├── transform/
│   ├── validation/
│   ├── db/
│   ├── analytics/
│   ├── forecasting/
│   ├── anomaly/
│   └── dashboard/
│
├── scripts/
├── db/migrations/
├── data/
│   ├── raw/
│   ├── staging/
│   ├── processed/
│   └── reference/
├── docs/
├── tests/
├── .streamlit/
├── .env.example
├── pyproject.toml
├── requirements.txt
├── requirements-tested.txt
└── README.md
```

---

## Technology Stack

- Python 3.12+
- pandas
- NumPy
- SQLAlchemy
- PostgreSQL / Supabase
- requests
- statsmodels
- XGBoost
- scikit-learn
- Streamlit
- pytest
- Ruff
- Git / GitHub
- GitHub Codespaces

---

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd 158888-nz-rental-market-platform
```

For the deployment-style environment:

```bash
pip install -r requirements.txt
```

For editable development installation:

```bash
pip install -e .
```

The validated development dependency versions are recorded in:

```text
requirements-tested.txt
```

---

## Environment Configuration

Create a local environment file:

```bash
cp .env.example .env
```

Development and ETL tasks may require:

```text
SUPABASE_DB_HOST
SUPABASE_DB_PORT
SUPABASE_DB_NAME
SUPABASE_DB_USER
SUPABASE_DB_PASSWORD

MARKET_RENT_API_ENV
MARKET_RENT_API_SANDBOX_KEY
MARKET_RENT_API_PROD_KEY
```

Sensitive values must not be committed.

The following are excluded from Git:

```text
.env
.env.*
.streamlit/secrets.toml
```

The frozen Streamlit deployment does not require database or API secrets.

---

## Running the Data Pipeline

### 1. Acquire official data

```bash
python scripts/acquire_rental_bond.py
python scripts/acquire_market_rent.py
```

Optional Market Rent connectivity check:

```bash
python scripts/market_rent_smoke_test.py
```

### 2. Transform source data

```bash
python scripts/transform_rental_bond.py
python scripts/transform_market_rent.py
```

### 3. Set up and load PostgreSQL

```bash
python scripts/run_migration.py
python scripts/load_rental_bond.py
python scripts/load_market_rent.py
```

Optional database connectivity check:

```bash
python scripts/db_smoke_test.py
```

### 4. Validate and build analytics

```bash
python scripts/validate_cross_source.py
python scripts/build_analytics_dataset.py
```

---

## Running the Forecasting Pipeline

Run the candidate models:

```bash
python scripts/run_seasonal_naive.py
python scripts/run_ets.py
python scripts/run_xgboost.py
```

Build comparison outputs:

```bash
python scripts/build_model_comparison.py
```

Validate the production policy:

```bash
python scripts/validate_selection_policy.py
```

Generate final six-month forecasts:

```bash
python scripts/build_final_forecasts.py
```

Detailed policy evidence is in:

[`docs/forecast_policy_decision.md`](docs/forecast_policy_decision.md)

---

## Forecasting Results

The full rolling-origin research comparison uses 65 series per metric.

### Bonds lodged

| Model | MAE | RMSE | sMAPE |
|---|---:|---:|---:|
| ETS additive damped | 28.77 | 64.98 | 13.41% |
| XGBoost pooled recursive | 47.50 | 107.01 | 20.51% |
| Seasonal Naive | 50.05 | 125.16 | 22.79% |

### Median rent

| Model | MAE | RMSE | sMAPE |
|---|---:|---:|---:|
| XGBoost pooled recursive | 17.37 | 23.19 | 3.13% |
| ETS additive damped | 17.99 | 23.49 | 3.24% |
| Seasonal Naive | 21.76 | 30.17 | 4.01% |

These are research comparison results. They do not directly determine the production model.

### Production policy validation

A separate temporally held-out policy test selected fixed ETS for production.

Overall held-out sMAPE:

| Policy | sMAPE |
|---|---:|
| Fixed ETS additive damped | 7.9592 |
| Fixed Seasonal Naive | 10.3561 |
| Per-series model selection | 11.3618 |
| Fixed XGBoost pooled recursive | 13.5553 |

The production model is therefore fixed ETS for all 130 forecast series.

---

## Running the Anomaly Pipeline

```bash
python scripts/build_historical_anomalies.py
python scripts/build_forecast_anomalies.py
python scripts/build_anomaly_summary.py
python scripts/build_anomaly_validation.py
python scripts/build_anomaly_evaluation.py
```

The historical detector uses robust seasonal-change baselines based on rolling median, MAD, and IQR fallback.

The forecast-residual detector uses one-step-ahead out-of-sample residuals from the research-layer winner for each series.

Detailed evaluation is in:

[`docs/anomaly_evaluation.md`](docs/anomaly_evaluation.md)

---

## Running the Dashboard

Start locally:

```bash
streamlit run app.py
```

The dashboard reads validated processed CSV outputs and does not run the ETL or modelling pipeline during page rendering.

---

## Deployment

The assessment dashboard is deployed on **Streamlit Community Cloud** from the `main` branch.

Deployment entry point:

```text
app.py
```

Deployment dependencies:

```text
requirements.txt
```

The cloud runtime uses 15 version-controlled processed CSV files:

- 3 analytics files;
- 7 forecasting files;
- 5 anomaly files.

No Streamlit secrets are required because the deployed app does not connect to Supabase or external APIs at runtime.

The frozen snapshot is deliberate: it ensures that the live dashboard remains consistent with the evaluated software artefact and final report.

Deployment details are documented in:

[`docs/deployment_and_reproducibility.md`](docs/deployment_and_reproducibility.md)

---

## Testing and Code Quality

Run the test suite:

```bash
pytest
```

Run static checks:

```bash
ruff check .
```

Repository whitespace check:

```bash
git diff --check
```

The project includes tests for acquisition, transformation, database loading, analytics, forecasting, production-policy logic, anomaly detection, and dashboard data loading.

---

## Data Outputs

Main processed data areas:

```text
data/processed/analytics/
data/processed/forecasting/
data/processed/anomaly/
```

Important runtime files include:

```text
analytics/monthly_panel.csv
analytics/series_catalog.csv
analytics/monthly_seasonality.csv

forecasting/model_comparison.csv
forecasting/series_model_winners.csv
forecasting/final_forward_forecasts.csv

anomaly/historical_anomalies.csv
anomaly/forecast_anomalies.csv
anomaly/anomaly_summary.csv
```

For full schema definitions, see:

[`docs/data_dictionary.md`](docs/data_dictionary.md)

---

## Interpretation and Limitations

### Source revisions

Official rental-market data can be revised. Recent observations may be more provisional than older observations.

### Forecast coverage

Historical coverage and forecasting coverage are not identical. Series that fail modelling-readiness checks remain available for historical analysis but are excluded from forecasting.

### Forecast uncertainty

Forecasts are statistical estimates, not guaranteed outcomes. Accuracy can vary by geography, metric, horizon, and market conditions.

### Anomaly interpretation

An anomaly indicates unusual statistical behaviour relative to the detector.

It does not establish:

- why the change occurred;
- whether a policy or system change caused it;
- whether intervention is appropriate.

Additional context is required before drawing causal conclusions.

---

## Responsible Use

The platform is intended for:

- rental-market analytics;
- regional comparison;
- forecasting research;
- general market exploration.

It is not designed to provide:

- individual property valuations;
- tenancy or legal advice;
- financial advice;
- investment recommendations;
- guaranteed rental predictions;
- causal explanations for anomaly alerts.

---

## Documentation

Technical documentation is stored in `docs/`:

- [`architecture.md`](docs/architecture.md) — system architecture and data flow
- [`data_dictionary.md`](docs/data_dictionary.md) — processed schemas and field semantics
- [`decision_log.md`](docs/decision_log.md) — technical and methodological decisions
- [`deployment_and_reproducibility.md`](docs/deployment_and_reproducibility.md) — runtime packaging and deployment
- [`forecast_policy_decision.md`](docs/forecast_policy_decision.md) — production forecast policy
- [`anomaly_evaluation.md`](docs/anomaly_evaluation.md) — anomaly detector evaluation

---

## Project Status

Completed:

- acquisition and ETL;
- source validation;
- analytics dataset construction;
- rolling-origin model evaluation;
- production forecast policy;
- final forward forecasting;
- anomaly detection and evaluation;
- Streamlit dashboard;
- deployment packaging;
- Streamlit Community Cloud deployment;
- automated testing and code-quality checks.

Current phase:

> **Phase 6 — Documentation, final report, figures, and submission QA**

---

## Academic Context

This repository was developed as an individual project for:

**158888 — Information Technology Professional Project**

**Master of Information Sciences**

**Massey University, New Zealand**

The repository is part of the technical project artefact and should be read together with the final project report.

---

## Data Attribution

Source rental-market data remains subject to the terms of the relevant New Zealand government data providers.

Users reproducing or redistributing source data should consult the applicable Tenancy Services, MBIE, and New Zealand Government data-use requirements.

Project software and documentation were developed for academic purposes.
