# Technical Decision Log

## Purpose

This document records major technical and methodological decisions made during
the development of the New Zealand Regional Rental Market Analytics and
Forecasting Platform.

The purpose is to preserve design rationale, distinguish deliberate choices
from implementation accidents, and provide traceable context for the final
report and repository review.

---

## D01 — Use Official Public Rental-Market Sources Only

**Decision**

Use official Tenancy Services / MBIE rental-market data as the analytical
source base.

**Rationale**

The project requires reproducible and defensible public-sector data provenance.
Private scraping or unofficial sources would make long-term reproducibility,
licensing, and source interpretation less reliable.

**Consequences**

- Acquisition code is designed around official source files and APIs.
- Source snapshot identifiers and provisional-status metadata are retained.
- The platform does not attempt to scrape individual rental listings.

---

## D02 — Keep the Core Pipeline Simple and File-Oriented

**Decision**

Use CSV-based processed outputs as the main interface between analytical stages,
while retaining PostgreSQL-compatible database support as an optional storage
layer.

**Rationale**

The datasets are moderate in size and do not require distributed processing.
A file-oriented pipeline reduces infrastructure complexity and makes each stage
easy to inspect, test, and reproduce.

**Consequences**

- `data/raw`, `data/staging`, and `data/processed` form the primary pipeline
  structure.
- Database migrations and loaders remain available for structured persistence.
- Later modelling and dashboard stages do not require an active database
  connection.

---

## D03 — Use a Unified Monthly Analytical Panel

**Decision**

Represent historical Region and Territorial Authority observations in a single
monthly analytical panel with consistent identifiers and metric names.

**Rationale**

A unified long-format structure simplifies downstream forecasting,
anomaly detection, filtering, and dashboard presentation.

**Consequences**

The main analytical schema uses:

- `period_date`
- `series_id`
- `geography_level`
- `location_id`
- `location_name`
- `metric`
- `value`

Source provenance is retained alongside analytical observations.

---

## D04 — Separate Historical Availability from Forecast Eligibility

**Decision**

Allow historical series to remain available for descriptive analysis even when
they do not pass forecasting-readiness criteria.

**Rationale**

Historical usefulness and forecast suitability are different concepts.
Removing non-forecastable series from the analytical dataset would unnecessarily
reduce descriptive coverage.

**Consequences**

- The monthly panel currently contains 164 series.
- The series catalog separately records `eligible_for_forecasting`.
- Historical-only series remain visible to the analytical system.

---

## D05 — Exclude Duplicate Auckland TA Forecast Series

**Decision**

Explicitly exclude the two duplicate Auckland Territorial Authority forecast
series from the final modelling scope:

    territorial_authority_76_bonds_lodged
    territorial_authority_76_median_rent

**Rationale**

Equivalent Auckland coverage was already represented elsewhere in the
forecasting set. Keeping duplicate analytical series in model evaluation would
double-count the same effective geographic coverage.

**Consequences**

- 132 series are initially marked forecast-eligible.
- 130 unique series form the final research and production forecasting scope.
- The final scope contains 65 series for each metric.

---

## D06 — Compare Three Forecasting Approaches

**Decision**

Evaluate:

- Seasonal Naive;
- ETS additive damped;
- pooled recursive XGBoost.

**Rationale**

The combination provides:

- a transparent seasonal baseline;
- a classical statistical time-series model;
- a machine-learning model capable of learning across geographic series.

This satisfies the project objective of comparing established statistical and
machine-learning forecasting approaches.

**Consequences**

All three candidate approaches are evaluated using rolling-origin validation
and common error metrics.

---

## D07 — Use Rolling-Origin Forecast Validation

**Decision**

Use rolling-origin time-series evaluation instead of random train/test splits.

**Rationale**

Random splitting would violate temporal ordering and could introduce
future-data leakage.

Rolling-origin evaluation more closely represents repeated real-world
forecasting from successive historical origins.

**Consequences**

Model comparison uses temporally ordered forecast origins and evaluates:

- MAE;
- RMSE;
- sMAPE.

Lagged and rolling features are constructed using only information available
before the relevant forecast origin.

---

## D08 — Select Research Winners Primarily by sMAPE

**Decision**

For the research-layer per-series winner output, rank candidate models primarily
by lowest sMAPE, using MAE and RMSE as tie-breakers.

**Rationale**

sMAPE provides a scale-normalised comparison across series with substantially
different magnitudes.

MAE and RMSE remain available as complementary absolute-error measures.

**Consequences**

`series_model_winners.csv` represents research comparison winners rather than
the production deployment policy.

---

## D09 — Separate Research Model Winners from Production Policy

**Decision**

Do not use full-window research winners directly as the production forecasting
policy.

**Rationale**

Using the same evaluation window for model comparison and final policy
selection would make production claims vulnerable to post-selection bias.

A separate temporally held-out policy-validation period was therefore used.

**Consequences**

The repository distinguishes:

- research model-comparison outputs;
- temporally separated policy validation;
- production forward forecasts.

---

## D10 — Adopt Fixed ETS as the Production Forecast Policy

**Decision**

Use:

    forecast_policy = fixed_ets_v1
    model = ets_additive_damped

for all 130 production forecast series.

**Rationale**

Temporally separated held-out policy validation showed ETS to provide the most
stable overall production choice across the two target metrics, while avoiding
additional per-series post-selection complexity.

The decision is based on held-out comparative evidence and operational
simplicity. It is not a claim that ETS is universally superior for every
individual series.

**Consequences**

- Production forecasts use fixed ETS.
- Research winners remain available for descriptive model comparison.
- The dashboard explicitly distinguishes research and production semantics.

Detailed evidence is documented in:

    docs/forecast_policy_decision.md

---

## D11 — Preserve Source Provisionality as Provenance

**Decision**

Retain source-level provisional status through the acquisition and processing
pipeline, exposing it at the analytical boundary as:

    source_snapshot_provisional

**Rationale**

Recent source observations are affected by the 2025-2026 Bond Hub migration and
may be revised or have limited comparability with earlier periods.

This is a provenance issue rather than a statistical anomaly classification.

**Consequences**

- Provisional status is retained in analytical outputs.
- Dashboard pages communicate source-status warnings.
- The field is not used as an anomaly label.

---

## D12 — Use Interpretable Robust Anomaly Detection

**Decision**

Use robust statistical anomaly methods based on seasonal changes and
forecast-residual behaviour rather than opaque black-box anomaly classifiers.

**Rationale**

The project requires explainable analytical alerts that can be communicated in
a decision-support dashboard.

Median/MAD-based methods are transparent, robust to extreme observations, and
straightforward to explain.

**Consequences**

The historical detector uses:

- year-on-year changes;
- rolling median;
- MAD;
- IQR fallback.

The forecast detector uses:

- one-step-ahead residuals;
- earlier out-of-sample residual history;
- robust residual scoring.

---

## D13 — Add Practical-Significance Filtering

**Decision**

Require dashboard anomaly alerts to satisfy both statistical anomaly criteria
and metric-specific practical-significance thresholds.

**Rationale**

A statistically unusual change may still be too small to be operationally
meaningful.

Combining statistical and practical criteria reduces low-value alerting.

**Consequences**

The repository retains both:

- raw statistical anomaly status;
- dashboard alert status.

They are deliberately not treated as equivalent concepts.

---

## D14 — Keep Anomaly Interpretation Non-Causal

**Decision**

Present anomaly outputs as analytical alerts rather than explanations of
causes.

**Rationale**

The available observational data does not establish causal relationships
between unusual rental-market observations and external events or system
changes.

**Consequences**

The dashboard and documentation avoid claims such as:

- the Bond Hub migration caused an anomaly;
- a policy change caused a detected movement;
- an alert represents a confirmed market event.

The internal status `confirmed_anomaly` means only that both implemented
detectors flagged the same observation.

Externally it should be described as:

    flagged by both detectors

---

## D15 — Evaluate Anomaly Detection Separately from Structural Validation

**Decision**

Keep detector-performance evaluation separate from structural anomaly-output
validation.

**Rationale**

Structural validation answers whether outputs are internally consistent.
Detector evaluation answers whether the method behaves sensibly under
controlled or historically relevant conditions.

Combining the two would blur distinct validation objectives.

**Consequences**

Structural validation is stored in:

    anomaly_validation_summary.csv

Detector evaluation is stored in:

    anomaly_evaluation_summary.csv

Detector evaluation includes:

- synthetic anomaly injection;
- threshold sensitivity;
- synthetic background alert behaviour;
- Bond Hub transition-period comparison.

Detailed evidence is documented in:

    docs/anomaly_evaluation.md

---

## D16 — Use Equal-Length Adjacent Windows for Transition Evaluation

**Decision**

Compare the available Bond Hub transition period with the immediately preceding
equal-length period.

Current windows are:

    pre-transition: 2023-06 to 2024-12
    transition:     2025-01 to 2026-07

**Rationale**

Using equal adjacent windows provides a more interpretable descriptive
comparison than comparing the transition period with the entire historical
dataset.

**Consequences**

The comparison is treated as descriptive evidence of detector behaviour.

It is explicitly not interpreted as evidence that the system transition caused
the observed increase in alerts.

---

## D17 — Keep Modelling Logic Outside the Dashboard

**Decision**

The Streamlit dashboard consumes validated processed outputs rather than
performing core forecasting or anomaly modelling inside page code.

**Rationale**

Separating presentation from analytical computation improves reproducibility,
testability, and maintainability.

**Consequences**

Dashboard pages primarily:

- load processed datasets;
- filter and summarise results;
- render charts and explanatory text.

Core analytical logic remains under `src/rmp/`.

---

## D18 — Use Automated Tests as the Primary Regression Guard

**Decision**

Maintain pytest-based automated tests across acquisition, transformation,
analytics, forecasting, anomaly detection, and dashboard data interfaces.

**Rationale**

The project contains multiple connected stages where apparently small changes
can alter later outputs.

Automated regression checks provide stronger evidence than manual inspection
alone.

**Consequences**

Repository quality checks include:

    pytest
    ruff check .
    python -m py_compile ...
    git diff --check

Additional clean-environment reproducibility checks are documented separately.

---

## D19 — Treat Generated Analytical Data as Build Artifacts

**Decision**

Keep large raw, staging, and processed datasets out of normal Git tracking.

**Rationale**

Generated analytical outputs can be large and can be reproduced from the
pipeline.

Keeping them outside the main Git history avoids repository bloat.

**Consequences**

A fresh clone does not automatically contain all dashboard datasets.

This creates a deployment/reproducibility packaging requirement that must be
handled explicitly rather than hidden.

The chosen deployment and clean-clone strategy is documented in:

    docs/deployment_and_reproducibility.md

---

## D20 — Prefer Explicit Semantics over Implicit Behaviour

**Decision**

Record important operational distinctions directly in outputs and
documentation.

Examples include:

- `eligible_for_forecasting`;
- `source_snapshot_provisional`;
- `forecast_policy`;
- research winner versus production model;
- statistical anomaly versus dashboard alert.

**Rationale**

The project combines data engineering, modelling, and decision-support
presentation. Ambiguous field meanings could lead to incorrect interpretation
even when the underlying calculations are correct.

**Consequences**

The repository includes dedicated architecture, data dictionary, forecast
policy, anomaly evaluation, and deployment documentation so that key semantic
boundaries are auditable.
