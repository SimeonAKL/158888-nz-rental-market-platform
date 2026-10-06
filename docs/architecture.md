# System Architecture

## Purpose

This document describes the implemented architecture of the New Zealand
Regional Rental Market Analytics and Forecasting Platform.

The system is designed as a reproducible analytical pipeline built around
official New Zealand rental-market data. It separates source acquisition,
transformation, analytical preparation, forecasting, anomaly detection, and
presentation so that each stage can be tested and reproduced independently.

## 1. Architectural Overview

The platform follows a layered data-processing architecture:

    Official data sources
            |
            v
    Acquisition and snapshots
            |
            v
    Raw data
            |
            v
    Transformation and validation
            |
            v
    Staging / cleaned data
            |
            v
    Analytics-ready monthly panel
            |
            +-------------------+
            |                   |
            v                   v
       Forecasting        Anomaly detection
            |                   |
            v                   v
    Forecast outputs      Alert outputs
            |                   |
            +---------+---------+
                      |
                      v
              Streamlit dashboard

The architecture deliberately separates research evaluation outputs from
production forecast outputs.

## 2. Source Layer

The project uses official Tenancy Services / MBIE rental-market data.

The core analytical sources are:

- Rental Bond data;
- Market Rent statistics.

Source files and API responses are acquired through project scripts and stored
as dated snapshots where applicable.

Recent observations affected by the 2025-2026 Bond Hub migration are retained
with explicit provisional-source provenance rather than silently treated as
final observations.

## 3. Acquisition Layer

Acquisition code is located primarily under:

- `src/rmp/acquisition/`
- `scripts/acquire_market_rent.py`
- `scripts/acquire_rental_bond.py`

Responsibilities include:

- obtaining official source data;
- retaining source metadata;
- recording snapshot provenance;
- preserving source-level provisional status;
- avoiding private or unofficial scraping.

Raw source material is stored under:

    data/raw/

Raw files are treated as source evidence and are not modified in place by later
analytical stages.

## 4. Transformation and Validation Layer

Transformation logic is located under:

- `src/rmp/transform/`
- `src/rmp/validation/`

Associated scripts include:

- `scripts/transform_market_rent.py`
- `scripts/transform_rental_bond.py`
- `scripts/validate_cross_source.py`

This layer standardises:

- dates;
- geographic identifiers;
- geographic names;
- metric names;
- numeric values;
- source provenance.

It also performs source-specific and cross-source validation before analytical
datasets are built.

## 5. Storage Layer

The repository contains database schema and migration support under:

    db/migrations/

Database loading utilities are available under:

    src/rmp/db/

The architecture supports PostgreSQL-compatible storage, including Supabase,
but the analytical workflow does not depend exclusively on a live database.

Processed CSV-based outputs are retained as the principal reproducible
interface between later analytical stages.

This design keeps the project operationally simple while retaining a database
implementation for structured persistence and demonstration.

## 6. Analytics Layer

Analytics preparation is implemented under:

    src/rmp/analytics/

The main processed analytical dataset is the monthly panel.

Its core dimensions are:

- `series_id`;
- `period_date`;
- `geography_level`;
- `location_id`;
- `location_name`;
- `metric`.

The two principal metrics are:

- `median_rent`;
- `bonds_lodged`.

The consolidated panel currently contains Region and Territorial Authority
series.

A separate series catalog records completeness and forecasting eligibility.

The analytical panel retains source provenance using
`source_snapshot_provisional` and related snapshot metadata.

## 7. Forecasting Architecture

Forecasting code is located under:

    src/rmp/forecasting/

The research comparison layer evaluates three candidate approaches:

- Seasonal Naive;
- ETS additive damped;
- pooled recursive XGBoost.

Rolling-origin evaluation is used with:

- MAE;
- RMSE;
- sMAPE.

The research layer retains model-comparison and per-series winner evidence.

The production layer is intentionally separate.

Following temporally separated policy validation, the production forecasting
policy is:

    fixed_ets_v1

with:

    ets_additive_damped

used for all production forecast series.

This separation prevents descriptive research winners from being mistaken for
the production deployment policy.

The detailed policy decision is documented in:

    docs/forecast_policy_decision.md

## 8. Forecasting Scope

The analytical series catalog contains more series than the final production
forecast output.

Forecast eligibility is determined through modelling-readiness checks.

Two duplicate Auckland Territorial Authority series are explicitly excluded
from forecast selection so that the production/research forecasting scope does
not duplicate equivalent Auckland coverage.

The final production forecasting scope contains 130 series:

- 65 `median_rent` series;
- 65 `bonds_lodged` series.

Each production series has a six-month forecast horizon.

## 9. Anomaly Detection Architecture

Anomaly-detection code is located under:

    src/rmp/anomaly/

Two complementary research detectors are retained.

### Historical detector

The historical detector evaluates unusual year-on-year movements using a
rolling robust baseline.

It uses:

- a 12-month seasonal reference;
- rolling median expected change;
- MAD as the primary robust scale estimate;
- IQR as a fallback where MAD is zero.

### Forecast-residual detector

The forecast detector evaluates one-step-ahead out-of-sample residuals from
the research-layer selected winner model.

The current residual is excluded from its own historical baseline to prevent
future-data leakage.

### Practical significance

Statistical anomaly status is supplemented by metric-specific practical
significance thresholds before dashboard alerts are produced.

### Consolidation

Historical and forecast-residual signals are consolidated into a
dashboard-ready anomaly summary.

Anomaly outputs are analytical alerts only and are not interpreted as causal
events.

Detector-performance evaluation is documented in:

    docs/anomaly_evaluation.md

## 10. Dashboard Layer

The interactive interface is implemented with Streamlit.

The main entry point is:

    app.py

Additional pages are located under:

    pages/

Shared dashboard utilities are located under:

    src/rmp/dashboard/

The dashboard presents:

- project overview and provenance;
- historical trends;
- historical analytics;
- production forecasts;
- research model-performance evidence;
- anomaly alerts and detector context.

The interface distinguishes production forecasts from research-layer model
comparison results.

It also communicates provisional-source status and data-quality limitations.

## 11. Testing and Quality Controls

Automated tests are located under:

    tests/

The repository uses pytest for functional and regression testing.

Quality controls include:

- source-validation tests;
- transformation tests;
- forecasting split and leakage checks;
- model output tests;
- production forecast policy tests;
- anomaly detector tests;
- anomaly evaluation tests;
- dashboard data-loader tests.

Static quality checks use Ruff and Python compilation checks.

`git diff --check` is used to identify whitespace errors before commits.

## 12. Data Flow Boundaries

The principal architectural boundaries are:

### Source boundary

Official source data enters the system through acquisition modules.

### Analytics boundary

Source-specific fields are transformed into consistent analytical semantics.

For example, source-level provisional information is exposed analytically as:

    source_snapshot_provisional

### Research / production boundary

Rolling-origin model comparisons and per-series winner outputs are retained as
research evidence.

They do not directly determine final production forecasts.

### Presentation boundary

The dashboard reads validated processed outputs rather than embedding modelling
logic directly in interface code.

This reduces coupling between modelling and presentation.

## 13. Repository-Level Design Principles

The implemented architecture follows these principles:

- reproducible processing rather than manual spreadsheet transformation;
- official-source provenance;
- explicit handling of provisional observations;
- temporal separation to reduce future-data leakage;
- separation of research evaluation from production policy;
- modular Python components with script-based orchestration;
- interpretable anomaly methods;
- non-causal anomaly communication;
- automated regression testing;
- minimal infrastructure complexity appropriate to the project scale.

## 14. Current Limitations

The architecture does not attempt to provide:

- real-time streaming ingestion;
- individual property valuation;
- causal inference from anomaly alerts;
- complete ground-truth anomaly labels;
- full national SA2-level forecasting;
- a fully database-dependent runtime.

Generated processed datasets are currently treated as reproducible build
artifacts. Deployment and clean-clone data availability are documented
separately in:

    docs/deployment_and_reproducibility.md
