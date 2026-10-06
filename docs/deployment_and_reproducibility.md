# Deployment and Reproducibility

## Purpose

This document records the current runtime, configuration, analytical
reproduction, and deployment requirements of the New Zealand Regional Rental
Market Analytics and Forecasting Platform.

It distinguishes between:

- source-code reproducibility;
- analytical-output reproducibility;
- local dashboard execution;
- final deployment packaging.

The final clean-clone and deployment-packaging validation is intentionally
deferred until the deployment stage.

---

## 1. Python Environment

The project package currently requires:

    Python >= 3.12

The main development and validation environment used during the later project
stages is:

    Python 3.14.2

Project dependencies and package metadata are defined in:

    pyproject.toml

The validated development environment is also recorded in:

    requirements-tested.txt

A final Python 3.12 compatibility run remains part of the deployment/final
packaging validation.

---

## 2. Installation

After cloning the repository, the project can be installed in editable mode:

    pip install -e .

Development dependencies should be installed according to the configuration in
`pyproject.toml`.

The authoritative setup instructions are maintained in the repository README.

---

## 3. Environment Variables and Secrets

Environment-specific configuration is supplied through environment variables.

A local `.env` file may be used during development.

The `.env` file is intentionally excluded from Git and must not be committed,
because it can contain credentials or environment-specific configuration.

Examples include:

- database connection settings;
- API credentials;
- deployment-specific secrets.

For deployment, equivalent values must be configured using the deployment
platform's environment-variable or secret-management mechanism.

No production credential should be embedded directly in source code or
committed configuration.

---

## 4. Generated Data Policy

The project treats raw, staging, and processed datasets as generated build
artifacts.

The principal directories are:

    data/raw/
    data/staging/
    data/processed/

These generated files are normally excluded from Git tracking, apart from
placeholder files where required.

This avoids committing large analytical datasets and source snapshots into the
main Git history.

The consequence is important:

> A fresh clone currently contains the source code required to rebuild the
> system, but it does not automatically contain all processed datasets required
> for immediate dashboard execution.

This limitation will be resolved as part of the final deployment and packaging
stage.

---

## 5. Reproducibility Model

The project distinguishes three forms of reproducibility.

### 5.1 Source-code reproducibility

The repository contains the Python source code, tests, scripts, configuration,
database migrations, and technical documentation required to understand and
rebuild the system.

### 5.2 Analytical reproducibility

Generated analytical outputs can be rebuilt by running the documented pipeline
in the correct dependency order.

### 5.3 Immediate runtime reproducibility

Immediate dashboard execution requires the expected processed datasets to
already exist.

Because those datasets are currently excluded from normal Git tracking, this is
not yet guaranteed from a clean clone.

Final runtime packaging is therefore a deployment-stage task rather than a
completed repository property.

---

## 6. Core Data Pipeline

The high-level processing sequence is:

    official source acquisition
              |
              v
    source transformation
              |
              v
    validation
              |
              v
    analytics-ready monthly panel
              |
              v
    forecasting and model comparison
              |
              v
    production forecasts
              |
              v
    anomaly detection and evaluation
              |
              v
    dashboard-ready outputs

The complete command sequence is maintained in `README.md`.

Later stages depend on outputs produced by earlier stages, so the documented
execution order should be preserved.

---

## 7. Forecasting Reproduction

The three candidate forecasting models are generated with:

    python scripts/run_seasonal_naive.py
    python scripts/run_ets.py
    python scripts/run_xgboost.py

Their unified research comparison is built with:

    python scripts/build_model_comparison.py

The temporally separated production-policy validation is then run with:

    python scripts/validate_selection_policy.py

Final forward forecasts are generated with:

    python scripts/build_final_forecasts.py

The current production policy is:

    fixed_ets_v1

using:

    ets_additive_damped

for all production forecast series.

The production-policy rationale and held-out evaluation evidence are documented
in:

    docs/forecast_policy_decision.md

---

## 8. Anomaly Reproduction

The main anomaly outputs are generated with:

    python scripts/build_historical_anomalies.py
    python scripts/build_forecast_anomalies.py
    python scripts/build_anomaly_summary.py
    python scripts/build_anomaly_validation.py

Detector-performance evidence is generated separately with:

    python scripts/build_anomaly_evaluation.py

The resulting evaluation output is:

    data/processed/anomaly/anomaly_evaluation_summary.csv

The detector evaluation methodology is documented in:

    docs/anomaly_evaluation.md

---

## 9. Dashboard Execution

The Streamlit application entry point is:

    app.py

Once the required processed outputs are available, the application can be
started with:

    streamlit run app.py

The dashboard does not perform the core forecasting or anomaly-detection
pipeline during page rendering.

Instead, it consumes validated processed outputs produced by earlier pipeline
stages.

This separation improves testability and keeps modelling logic outside the user
interface.

---

## 10. Required Dashboard Outputs

The dashboard depends on processed analytical outputs including, but not
limited to:

    data/processed/analytics/monthly_panel.csv
    data/processed/analytics/series_catalog.csv

    data/processed/forecasting/combined_predictions.csv
    data/processed/forecasting/model_comparison.csv
    data/processed/forecasting/series_model_winners.csv
    data/processed/forecasting/final_forward_forecasts.csv

    data/processed/anomaly/historical_anomalies.csv
    data/processed/anomaly/forecast_anomalies.csv
    data/processed/anomaly/anomaly_summary.csv
    data/processed/anomaly/anomaly_validation_summary.csv
    data/processed/anomaly/anomaly_metadata_summary.csv

Additional evaluation outputs may be used as reproducibility and reporting
evidence.

The schemas of the principal processed datasets are documented in:

    docs/data_dictionary.md

---

## 11. Testing and Code Quality

The primary automated test command is:

    pytest

Static code checks use:

    ruff check .

Python syntax can be checked with:

    python -m py_compile <file>

Repository whitespace validation uses:

    git diff --check

These checks are used throughout development before commits and major project
milestones.

---

## 12. Current Reproducibility Limitation

The current repository has not yet completed a final clean-clone deployment
test.

Specifically, final evidence is still required for:

- rebuilding or restoring dashboard data from a fresh clone;
- Python 3.12 compatibility;
- deployment secret configuration;
- deployment data packaging;
- successful dashboard startup in the final deployment environment.

These are packaging and deployment concerns rather than unresolved analytical
model defects.

---

## 13. Deferred Deployment Validation

The following work is deliberately deferred until the deployment stage:

1. Select the final mechanism for supplying required processed dashboard data.
2. Configure deployment secrets and environment variables.
3. Test the project in a clean Python 3.12 environment.
4. Perform a clean-clone reproduction test.
5. Verify dashboard startup with the selected deployment data strategy.
6. Update README deployment instructions to match the final implementation.
7. Record final deployment evidence.

Possible data-delivery approaches may include a deployment asset, release
artifact, reproducible bootstrap process, or another repository-appropriate
mechanism.

No approach is documented as final until it has been implemented and tested.

---

## 14. Documentation Responsibilities

The following documents provide complementary reproducibility information:

- `README.md` — installation, pipeline execution, dashboard startup, and project
  overview;
- `docs/architecture.md` — system structure and data-flow boundaries;
- `docs/data_dictionary.md` — processed dataset semantics;
- `docs/forecast_policy_decision.md` — production forecasting policy;
- `docs/anomaly_evaluation.md` — anomaly detector evaluation evidence;
- `docs/decision_log.md` — major design decisions and rationale;
- `docs/deployment_and_reproducibility.md` — runtime and deployment status.

---

## 15. Final Deployment Gate

Deployment should not be considered fully validated until all of the following
have been demonstrated:

    clean clone
        +
    supported Python environment
        +
    dependency installation
        +
    required data availability
        +
    secure environment configuration
        +
    automated tests
        +
    successful Streamlit startup

The final deployment/final-packaging audit will address this gate as M6.
