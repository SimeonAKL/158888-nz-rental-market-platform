# Deployment and Reproducibility

## Purpose

This document records the final runtime, packaging, and deployment approach for the New Zealand Rental Market Analytics and Forecasting Platform.

The assessment deployment uses a frozen, validated snapshot so that the repository, dashboard, screenshots, model results, and final report remain consistent.

## 1. Environment

The project requires:

```text
Python >= 3.12
```

The later development and analytical validation environment used Python 3.14.2.

Key dependency files:

```text
pyproject.toml
requirements-tested.txt
requirements.txt
```

- `pyproject.toml` defines the package and project dependencies.
- `requirements-tested.txt` records the validated development versions.
- `requirements.txt` defines the Streamlit deployment environment.

## 2. Installation

Deployment-style installation:

```bash
pip install -r requirements.txt
```

Editable development installation:

```bash
pip install -e .
```

The project uses a `src/` package layout.

## 3. Environment variables and secrets

Development and ETL tasks may use:

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

A local `.env` file may be used during development and is excluded from Git. `.env.example` contains placeholders only.

The frozen assessment deployment does not need Supabase credentials or Market Rent API keys because the Streamlit app does not acquire data, rebuild outputs, or refit models at runtime.

## 4. Data packaging

The project uses:

```text
data/raw/
data/staging/
data/processed/
```

Raw and staging data remain generated artefacts and are not committed. Most processed outputs are also ignored by default.

The exception is the set of validated processed CSV files required by the deployed dashboard. These are version controlled as the frozen submission snapshot.

This keeps the runtime reproducible without committing every intermediate file.

## 5. Reproducibility model

### Source-code reproducibility

The repository contains source modules, scripts, migrations, tests, dependency specifications, configuration examples, and documentation.

### ETL reproducibility

Acquisition and transformation stages preserve snapshot metadata, checksums, retrieval timestamps, lineage, and provisional-source status.

### Analytical reproducibility

The implemented pipeline rebuilds:

```text
validated source data
→ monthly analytical panel
→ model evaluation
→ production forecasts
→ anomaly outputs
```

subject to the same source snapshot, software versions, and configuration.

### Submission-runtime reproducibility

The required dashboard CSV files are already included in the repository. A fresh deployment therefore does not need to regenerate analytical outputs before the app can start.

## 6. Processing pipeline

```text
Official Tenancy Services / MBIE sources
        ↓
Acquisition and snapshots
        ↓
Transformation and validation
        ↓
Supabase PostgreSQL
        ↓
Validated clean observations
        ↓
Monthly analytical panel
        ↓
Forecasting and model comparison
        ↓
Production forecasts
        ↓
Anomaly detection
        ↓
Validated dashboard outputs
```

The deployed application starts at the final validated-output boundary.

See `docs/architecture.md` for the full system design.

## 7. Analytics reproduction

Build the analytical datasets with:

```bash
python scripts/build_analytics_dataset.py
```

Current analytical scope:

```text
64,956 monthly observations
164 analytical series
February 1993 to July 2026
```

Primary runtime analytics files:

```text
data/processed/analytics/monthly_panel.csv
data/processed/analytics/series_catalog.csv
data/processed/analytics/monthly_seasonality.csv
```

The monthly panel is built from validated Rental Bond observations stored in PostgreSQL. Market Rent is processed independently and used for supporting cross-source validation.

## 8. Forecasting reproduction

Run the candidate models:

```bash
python scripts/run_seasonal_naive.py
python scripts/run_ets.py
python scripts/run_xgboost.py
```

Build the research comparison:

```bash
python scripts/build_model_comparison.py
```

Validate the production policy:

```bash
python scripts/validate_selection_policy.py
```

Generate final forward forecasts:

```bash
python scripts/build_final_forecasts.py
```

Production policy:

```text
fixed_ets_v1
ets_additive_damped
```

Final production scope:

```text
130 series
65 median_rent
65 bonds_lodged
6 forecast months per series
780 forecast rows
```

See `docs/forecast_policy_decision.md`.

## 9. Anomaly reproduction

Run:

```bash
python scripts/build_historical_anomalies.py
python scripts/build_forecast_anomalies.py
python scripts/build_anomaly_summary.py
python scripts/build_anomaly_validation.py
python scripts/build_anomaly_evaluation.py
```

Evaluation details are in `docs/anomaly_evaluation.md`.

## 10. Dashboard runtime

Start locally with:

```bash
streamlit run app.py
```

The dashboard reads processed CSV files through:

```text
src/rmp/dashboard/data.py
```

It does not run acquisition, database loading, forecasting, or anomaly generation during page rendering.

## 11. Deployment runtime assets

The deployed dashboard uses 15 processed CSV files.

### Analytics

```text
data/processed/analytics/monthly_panel.csv
data/processed/analytics/series_catalog.csv
data/processed/analytics/monthly_seasonality.csv
```

### Forecasting

```text
data/processed/forecasting/combined_predictions.csv
data/processed/forecasting/metrics_by_origin.csv
data/processed/forecasting/metrics_by_series.csv
data/processed/forecasting/metrics_by_horizon.csv
data/processed/forecasting/model_comparison.csv
data/processed/forecasting/series_model_winners.csv
data/processed/forecasting/final_forward_forecasts.csv
```

### Anomaly detection

```text
data/processed/anomaly/anomaly_summary.csv
data/processed/anomaly/historical_anomalies.csv
data/processed/anomaly/forecast_anomalies.csv
data/processed/anomaly/anomaly_validation_summary.csv
data/processed/anomaly/anomaly_metadata_summary.csv
```

## 12. Frozen submission snapshot

The frozen snapshot keeps the following aligned during assessment:

- repository outputs;
- dashboard values;
- forecast and anomaly results;
- screenshots;
- report tables and figures.

Upstream government data may change after submission, so automatic refresh could otherwise make the live dashboard differ from the submitted report.

The pipeline can still be rerun in future; automated refresh is outside the assessment deployment.

## 13. Streamlit Community Cloud deployment

Deployment source:

```text
Repository: SimeonAKL/158888-nz-rental-market-platform
Branch: main
Entry point: app.py
```

Deployment dependencies are installed from `requirements.txt`.

No Streamlit secrets are required for the frozen assessment runtime.

Runtime path:

```text
GitHub repository
→ frozen validated CSV assets
→ Streamlit Community Cloud
→ dashboard
```

The app does not query live Supabase or government APIs at runtime.

## 14. Deployment validation

The final deployment checks included:

- 15 required runtime files present, 0 missing;
- total runtime asset size approximately 53 MB;
- clean dependency and import validation;
- successful loading of primary dashboard datasets;
- successful local Streamlit startup;
- successful Streamlit Community Cloud deployment;
- manual checks of Home, Overview, Historical Analytics, Forecasting, Model Performance, and Anomaly Detection.

## 15. Testing and security

Primary checks:

```bash
pytest
ruff check .
git diff --check
```

Sensitive local files remain excluded from Git:

```text
.env
.env.*
.streamlit/secrets.toml
```

The assessment deployment needs no database or API credentials.

## 16. Future refresh

A future production workflow could automate:

```text
scheduled trigger
→ source acquisition
→ ETL and validation
→ Supabase update
→ analytics regeneration
→ fixed ETS refit
→ forecast regeneration
→ anomaly regeneration
→ publication
```

Routine refresh should refit the approved production model using new validated history. Changing the production model should require a separate policy review.

## 17. Related documentation

- `README.md` — setup, pipeline commands, and project overview
- `docs/architecture.md` — system architecture and data flow
- `docs/data_dictionary.md` — dataset schemas and semantics
- `docs/forecast_policy_decision.md` — production forecast policy
- `docs/anomaly_evaluation.md` — anomaly evaluation
- `docs/decision_log.md` — technical decisions
