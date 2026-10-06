# NZ Regional Rental Market Analytics and Forecasting Platform

**Massey University — 158888 Information Technology Professional Project**

A reproducible analytics, forecasting, anomaly-detection, and visualisation platform for exploring regional rental-market conditions in New Zealand using official Tenancy Services / Ministry of Business, Innovation and Employment (MBIE) data.

---

## 1. Project Overview

This individual project develops an end-to-end rental-market analytics platform for New Zealand.

The system integrates official rental bond and market rent data into a reproducible workflow covering:

- data acquisition and source snapshotting
- data validation and transformation
- geographic harmonisation
- monthly rental-market analytics
- time-series forecasting
- forecasting model comparison
- interpretable anomaly detection
- interactive Streamlit visualisation
- data-quality and provenance reporting

The platform is designed to support regional rental-market exploration and comparison while maintaining clear distinctions between historical observations, model-generated forecasts, and analytical anomaly alerts.

---

## 2. Project Objectives

The project aims to:

1. Build a reproducible pipeline for acquiring and processing official New Zealand rental-market data.
2. Harmonise rental information across Regions and valid Territorial Authorities.
3. Provide historical analysis of rental-market trends and variation.
4. Compare statistical and machine-learning forecasting approaches using time-aware validation.
5. Generate short-term forward forecasts for eligible rental-market series.
6. Identify unusual historical and forecast-residual behaviour using interpretable anomaly-detection methods.
7. Present the resulting evidence through an interactive dashboard.
8. Maintain transparent data-quality, provenance, modelling, and interpretation controls.

---

## 3. Analytical Scope

The platform analyses rental-market information at:

- New Zealand Region level
- valid Territorial Authority level where the available data satisfies analytical requirements

The two principal analytical measures are:

- **Median rent** — monthly median weekly rent in New Zealand dollars
- **Bond lodgements** — monthly counts of new rental bond lodgements

Not every historical series is necessarily eligible for forecasting. Forecast eligibility is determined using explicit data-quality and modelling-readiness rules.

---

## 4. Key Features

### Data engineering

- official source acquisition
- immutable raw-data snapshots
- source metadata and provenance tracking
- staging and processed datasets
- validation checks
- geographic harmonisation
- cross-source validation
- modelling-readiness assessment

### Historical analytics

- monthly rental-market time series
- geographic comparison
- long-term trend exploration
- rent and bond activity analysis
- data-quality context

### Forecasting

The project evaluates three forecasting approaches:

- **Seasonal Naive** — baseline model
- **ETS** — statistical exponential-smoothing model
- **XGBoost** — pooled machine-learning forecasting model

Models are evaluated using rolling-origin time-series validation and the following metrics:

- Mean Absolute Error (**MAE**)
- Root Mean Squared Error (**RMSE**)
- Symmetric Mean Absolute Percentage Error (**sMAPE**)

A documented production-model policy is then used to generate the final six-month forward forecasts for forecast-eligible series.

### Anomaly detection

The platform combines two complementary anomaly-detection paths:

- historical anomaly detection
- forecast-residual anomaly detection

Anomaly outputs are presented as **analytical alerts**. They identify unusual statistical behaviour but do not establish the cause of a market event.

### Interactive dashboard

The Streamlit dashboard contains five analytical modules:

1. **Overview**
2. **Historical Analytics**
3. **Forecasting**
4. **Model Performance**
5. **Anomaly Detection**

---

## 5. Data Sources

The project uses official New Zealand rental-market data published through Tenancy Services and MBIE.

Primary sources include:

### Rental Bond Data

Rental bond information is used to construct monthly measures of rental-market activity and median rent.

### Market Rent API

The MBIE / Tenancy Services Market Rent API is used as an additional official rental-market source and for cross-source validation where applicable.

API credentials are supplied through environment variables and are never committed to the repository.

---

## 6. System Architecture

The project follows a staged analytical pipeline:

```text
Official rental data
        |
        v
Data acquisition
        |
        v
Raw immutable snapshots
        |
        v
Validation and transformation
        |
        v
Staging / harmonised datasets
        |
        v
Cross-source validation
        |
        v
Processed monthly analytics dataset
        |
        +--------------------------+
        |                          |
        v                          v
Historical analytics        Forecast modelling
                                   |
                                   v
                         Rolling-origin evaluation
                                   |
                                   v
                          Model comparison
                                   |
                                   v
                         Final forward forecasts
        |                          |
        +-------------+------------+
                      |
                      v
              Anomaly detection
                      |
                      v
              Streamlit dashboard
```

The workflow separates source acquisition, transformation, modelling, validation, and presentation so that analytical outputs can be traced back to their underlying source data and processing stages.

---

## 7. Repository Structure

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
│   └── Core Python package for acquisition, processing,
│       forecasting, anomaly detection, configuration,
│       validation, and dashboard support
│
├── scripts/
│   ├── Data acquisition
│   ├── Transformation and loading
│   ├── Validation
│   ├── Analytics dataset construction
│   ├── Forecast model execution
│   ├── Model comparison
│   ├── Final forecast generation
│   └── Anomaly processing
│
├── data/
│   ├── raw/          Immutable source snapshots
│   ├── staging/      Validated intermediate datasets
│   ├── processed/    Analytical and modelling outputs
│   └── reference/    Geographic reference data
│
├── db/
│   └── migrations/   PostgreSQL schema definitions
│
├── docs/
│   └── Project and modelling documentation
│
├── tests/
│   └── Automated test suite
│
├── .streamlit/
│   └── Streamlit configuration
│
├── .env.example
├── pyproject.toml
├── requirements-tested.txt
└── README.md
```

Generated raw, staging, and processed data are excluded from Git except where explicitly required for reference or reproducibility.

---

## 8. Technology Stack

The principal technologies used are:

- **Python 3.12+**
- **pandas** — data transformation and analytics
- **NumPy** — numerical processing
- **SQLAlchemy** — database integration
- **PostgreSQL / Supabase** — structured data storage
- **requests** — API access
- **statsmodels** — ETS forecasting
- **XGBoost** — machine-learning forecasting
- **scikit-learn** — supporting modelling utilities
- **Streamlit** — interactive dashboard
- **pytest** — automated testing
- **Ruff** — static code-quality checking
- **Git / GitHub** — version control
- **GitHub Codespaces** — primary development environment

---

## 9. Requirements

The project requires:

- Python **3.12 or later**
- Git
- Python package installation through `pip`
- MBIE Market Rent API credentials for API-dependent acquisition
- Supabase/PostgreSQL credentials for database-dependent operations

GitHub Codespaces provides the primary validated development environment.

---

## 10. Installation

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd 158888-nz-rental-market-platform
```

Install the project together with development, forecasting, and dashboard dependencies:

```bash
pip install -e ".[dev,forecasting,dashboard]"
```

### Reproducing the validated dependency environment

The repository also contains `requirements-tested.txt`, which records the direct dependency versions used in the validated development environment.

For the closest reproduction of that environment:

```bash
pip install -r requirements-tested.txt
pip install -e . --no-deps
```

---

## 11. Environment Configuration

Create a local `.env` file from the supplied example:

```bash
cp .env.example .env
```

Required configuration includes:

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

For example:

```text
MARKET_RENT_API_ENV=sandbox
```

or, when authorised production access is required:

```text
MARKET_RENT_API_ENV=production
```

Real passwords, API keys, and Streamlit secrets must never be committed to Git.

The following files are intentionally excluded from version control:

```text
.env
.env.*
.streamlit/secrets.toml
```

with `.env.example` retained as the configuration template.

---

## 12. Running the Data Pipeline

The project is organised as a sequence of independently executable scripts.

### 12.1 Acquire official data

Rental bond data:

```bash
python scripts/acquire_rental_bond.py
```

Market Rent API data:

```bash
python scripts/acquire_market_rent.py
```

Optional API connectivity check:

```bash
python scripts/market_rent_smoke_test.py
```

---

### 12.2 Transform source data

Transform rental bond data:

```bash
python scripts/transform_rental_bond.py
```

Transform Market Rent data:

```bash
python scripts/transform_market_rent.py
```

---

### 12.3 Database setup and loading

Run database migrations:

```bash
python scripts/run_migration.py
```

Optional database connectivity check:

```bash
python scripts/db_smoke_test.py
```

Load rental bond data:

```bash
python scripts/load_rental_bond.py
```

Load Market Rent data:

```bash
python scripts/load_market_rent.py
```

---

### 12.4 Validate and build the analytical dataset

Run cross-source validation:

```bash
python scripts/validate_cross_source.py
```

Build the consolidated analytics dataset:

```bash
python scripts/build_analytics_dataset.py
```

These stages establish the harmonised monthly dataset and determine which time series satisfy the requirements for forecasting.

---

## 13. Running the Forecasting Pipeline

### Seasonal Naive baseline

```bash
python scripts/run_seasonal_naive.py
```

### ETS

```bash
python scripts/run_ets.py
```

### XGBoost

```bash
python scripts/run_xgboost.py
```

### Build model comparison outputs

```bash
python scripts/build_model_comparison.py
```

### Validate the production-model selection policy

```bash
python scripts/validate_selection_policy.py
```

This validation uses the unified rolling-origin prediction output generated by the model-comparison stage and evaluates the documented production-model policy using temporally separated selection and evaluation periods.

### Generate final forward forecasts

```bash
python scripts/build_final_forecasts.py
```

The final forecast generation process follows the documented production-model policy stored in:

```text
docs/forecast_policy_decision.md
```

Model evaluation uses rolling-origin validation rather than random train/test splitting in order to preserve temporal ordering and prevent future-data leakage.

---

## 14. Running the Anomaly Pipeline

Generate historical anomaly outputs:

```bash
python scripts/build_historical_anomalies.py
```

Generate forecast-residual anomaly outputs:

```bash
python scripts/build_forecast_anomalies.py
```

Consolidate anomaly results:

```bash
python scripts/build_anomaly_summary.py
```

Build anomaly validation evidence:

```bash
python scripts/build_anomaly_validation.py
```

Anomaly indicators should be interpreted as statistical alerts requiring further investigation rather than evidence of a confirmed causal event.

---

## 15. Running the Dashboard

Start the Streamlit application from the repository root:

```bash
streamlit run app.py
```

The dashboard provides navigation to:

```text
Overview
Historical Analytics
Forecasting
Model Performance
Anomaly Detection
```

The dashboard distinguishes between:

- observed historical data
- model-generated forward forecasts
- forecasting evaluation results
- anomaly signals
- data-quality and interpretation information

---

## 16. Testing and Code Quality

Run the complete automated test suite:

```bash
pytest
```

Run static code checks:

```bash
ruff check .
```

To run both:

```bash
ruff check .
pytest
```

At the Phase 6 documentation baseline, the repository passes the complete automated test suite and Ruff static checks.

---

## 17. Reproducing the Main Analytical Outputs

A full analytical reproduction generally follows this sequence:

```bash
python scripts/acquire_rental_bond.py
python scripts/acquire_market_rent.py

python scripts/transform_rental_bond.py
python scripts/transform_market_rent.py

python scripts/run_migration.py
python scripts/load_rental_bond.py
python scripts/load_market_rent.py

python scripts/validate_cross_source.py
python scripts/build_analytics_dataset.py

python scripts/run_seasonal_naive.py
python scripts/run_ets.py
python scripts/run_xgboost.py
python scripts/build_model_comparison.py
python scripts/validate_selection_policy.py
python scripts/build_final_forecasts.py

python scripts/build_historical_anomalies.py
python scripts/build_forecast_anomalies.py
python scripts/build_anomaly_summary.py
python scripts/build_anomaly_validation.py

streamlit run app.py
```

Successful reproduction depends on:

- access to required official source data
- valid API credentials where required
- valid database credentials where required
- compatible source-data versions
- successful execution of preceding pipeline stages

---

## 18. Data and Generated Outputs

The repository uses four principal data areas:

```text
data/raw/
data/staging/
data/processed/
data/reference/
```

### `data/raw`

Contains immutable source snapshots and acquisition metadata.

### `data/staging`

Contains validated and transformed intermediate datasets.

### `data/processed`

Contains final analytical, forecasting, evaluation, and anomaly outputs used by the dashboard.

### `data/reference`

Contains relatively small reference and geographic concordance information required by the processing pipeline.

Large or generated datasets are not committed to Git unless explicitly required.

---

## 19. Data Quality and Limitations

The platform is subject to several important limitations.

### Source revisions

Official rental-market datasets may be revised after initial publication. Recent observations may therefore be more provisional than older observations.

### Geographic coverage

Historical analytical coverage and forecasting coverage are not identical. A geographic series may be available for historical exploration but excluded from forecasting if it does not satisfy the required completeness or modelling-readiness criteria.

### Forecast uncertainty

Forecasts are statistical estimates based on historical patterns. They are not guaranteed future rental-market outcomes.

Model accuracy can vary:

- by geographic area
- by analytical measure
- by forecast horizon
- over changing market conditions

### Anomaly interpretation

An anomaly indicates unusual statistical behaviour relative to the detector used.

It does **not** demonstrate:

- why the change occurred
- whether a policy caused the change
- whether the observation is economically significant
- whether a market intervention is appropriate

Additional contextual investigation is required before assigning causal explanations.

---

## 20. Responsible Use

The platform is intended for rental-market analytics, comparison, forecasting research, and general market understanding.

It is **not** designed to provide:

- individual property valuations
- tenancy or legal advice
- financial advice
- investment recommendations
- guaranteed rental-price predictions
- causal explanations for detected anomalies

Users should interpret forecasts and anomaly signals together with data-quality information and relevant external context.

---

## 21. Deployment

Deployment forms part of Phase 6 of the project.

The final deployment configuration and public application location will be documented here after deployment validation has been completed.

Current local execution:

```bash
streamlit run app.py
```

Deployment documentation will include:

- hosting platform
- runtime configuration
- dependency installation
- environment/secrets configuration
- application entry point
- deployed application URL
- deployment smoke-test procedure

---

## 22. Project Documentation

Supporting technical documentation is stored in the `docs/` directory.

Current documentation includes:

- `docs/architecture.md` — system architecture, data flow, analytical
  boundaries, and major component responsibilities;
- `docs/data_dictionary.md` — processed dataset schemas, field semantics,
  and research/production distinctions;
- `docs/decision_log.md` — major technical and methodological decisions
  and their rationale;
- `docs/deployment_and_reproducibility.md` — runtime configuration,
  reproducibility model, dashboard dependencies, and deployment-stage
  validation requirements;
- `docs/forecast_policy_decision.md` — temporally separated
  production-model policy evaluation and the fixed ETS production
  decision;
- `docs/anomaly_evaluation.md` — synthetic injection, threshold
  sensitivity, transition-period evaluation, and anomaly interpretation
  limitations.

Final clean-clone and deployment-packaging validation remains part of the
deployment-stage M6 work.

---
## 23. Project Status

The core system has completed:

- data acquisition and ETL development
- source validation
- geographic harmonisation
- analytics dataset construction
- forecasting implementation
- rolling-origin model evaluation
- model comparison
- final forward forecasting
- anomaly detection
- Streamlit dashboard implementation
- automated testing and code-quality review
- final implementation audit and remediation

The project is currently in:

> **Phase 6 — Packaging, Documentation and Final Report**

Phase 6 covers:

1. README and run instructions
2. repository packaging and cleanup
3. deployment
4. architecture and data-flow documentation
5. methods and final-results documentation
6. dashboard screenshots and figures
7. final report preparation
8. final quality assurance and submission checks

---

## 24. Academic Context

This repository was developed as an individual project for:

**158888 — Information Technology Professional Project**

**Master of Information Sciences**

**Massey University, New Zealand**

The repository forms part of the technical project artefact and should be considered together with the associated final project report.

---

## 25. Licence and Data Attribution

Source rental-market data remains subject to the terms and conditions of the relevant New Zealand government data providers.

Users reproducing or redistributing source data should consult the applicable Tenancy Services, MBIE, and New Zealand Government data-use requirements.

This repository contains project-specific software and documentation developed for academic purposes.
