# Technical Decision Log

## Purpose

This log records the main technical and methodological decisions made during the project.

---

## D01 — Use official public rental-market sources only

**Decision:** Use official Tenancy Services / MBIE rental-market data.

**Rationale:** Official sources provide defensible provenance and avoid the licensing and reproducibility problems associated with private scraping.

**Consequences**

- Acquisition uses official files and APIs.
- Snapshot and provisional-status metadata are retained.
- Individual rental listings are not scraped.

---

## D02 — Use a layered database-and-file pipeline

**Decision:** Use PostgreSQL/Supabase for structured persistence and ETL support, then use validated CSV outputs between later analytical stages.

**Rationale:** The database provides lineage, constraints, and structured querying, while file-based analytical interfaces keep modelling and deployment simple.

**Consequences**

- Supabase stores structured source data and lineage.
- The analytical dataset builder reads validated clean database observations.
- Forecasting, anomaly detection, and dashboard runtime do not require a live database connection.
- The deployed dashboard reads frozen CSV artefacts.

---

## D03 — Use a unified monthly analytical panel

**Decision:** Store Region and Territorial Authority observations in one long-format monthly panel.

**Rationale:** A common schema simplifies forecasting, anomaly detection, filtering, and dashboard logic.

**Core fields**

- `period_date`
- `series_id`
- `geography_level`
- `location_id`
- `location_name`
- `metric`
- `value`

Source provenance remains attached to each observation.

---

## D04 — Separate historical availability from forecast eligibility

**Decision:** Keep historically useful series even when they fail forecasting-readiness criteria.

**Rationale:** Historical usefulness and forecasting suitability are not the same.

**Consequences**

- The panel contains 164 analytical series.
- Forecast eligibility is stored separately in `series_catalog.csv`.
- Historical-only series remain available to the dashboard.

---

## D05 — Exclude duplicate Auckland TA forecast series

**Decision:** Exclude:

```text
territorial_authority_76_bonds_lodged
territorial_authority_76_median_rent
```

from the modelling scope.

**Rationale:** Equivalent Auckland coverage already exists elsewhere in the forecasting set, so retaining these series would double-count the same effective geography.

**Consequences**

- 132 series are initially forecast-eligible.
- 130 unique series enter research and production forecasting.
- The final scope contains 65 series per metric.

---

## D06 — Compare three forecasting approaches

**Decision:** Evaluate Seasonal Naive, ETS additive damped, and pooled recursive XGBoost.

**Rationale:** The set provides a transparent baseline, a classical statistical model, and a pooled machine-learning model.

**Consequence:** All candidates are assessed with the same rolling-origin evaluation framework.

---

## D07 — Use rolling-origin forecast validation

**Decision:** Use time-ordered rolling-origin validation rather than random train/test splits.

**Rationale:** Random splitting would violate temporal order and risk future-data leakage.

**Consequences**

- Evaluation uses successive forecast origins.
- MAE, RMSE, and sMAPE are reported.
- Lagged and rolling features use only information available before each origin.

---

## D08 — Select research winners primarily by sMAPE

**Decision:** Rank per-series research winners by lowest sMAPE, with MAE and RMSE as tie-breakers.

**Rationale:** sMAPE is scale-normalised and supports comparison across series of different magnitudes.

**Consequence:** `series_model_winners.csv` is a research output, not a production-selection rule.

---

## D09 — Separate research winners from production policy

**Decision:** Do not use full-window research winners directly as the production forecasting rule.

**Rationale:** Selecting a production policy from the same window used for model comparison would introduce post-selection bias.

**Consequence:** A separate temporally held-out policy validation is used.

---

## D10 — Adopt fixed ETS for production forecasts

**Decision**

```text
forecast_policy = fixed_ets_v1
model = ets_additive_damped
```

for all 130 production series.

**Rationale:** Held-out policy validation showed that fixed ETS gave the strongest overall production performance and avoided unstable per-series switching.

**Consequences**

- Production forecasts use fixed ETS.
- Research winners remain available for comparison.
- The dashboard labels research and production results separately.

See `docs/forecast_policy_decision.md`.

---

## D11 — Preserve provisional-source status

**Decision:** Carry source provisionality through the pipeline as:

```text
source_snapshot_provisional
```

**Rationale:** Recent observations affected by the 2025–2026 Bond Hub migration may be revised or have limited comparability.

**Consequences**

- Provisional status is retained in analytical outputs.
- Dashboard warnings expose this status.
- Provisionality is not treated as an anomaly label.

---

## D12 — Use interpretable robust anomaly detection

**Decision:** Use robust statistical detectors based on seasonal change and forecast residuals.

**Rationale:** The dashboard requires explainable alerts rather than an opaque anomaly classifier.

**Implementation**

Historical detector:

- year-on-year change;
- rolling median;
- MAD;
- IQR fallback.

Forecast detector:

- one-step-ahead residuals;
- earlier out-of-sample residual history;
- robust residual scoring.

---

## D13 — Add practical-significance filtering

**Decision:** Require dashboard alerts to meet both statistical and metric-specific practical-significance criteria.

**Rationale:** A statistically unusual movement may still be too small to be operationally useful.

**Consequence:** Statistical anomaly flags and dashboard alerts are stored separately.

---

## D14 — Keep anomaly interpretation non-causal

**Decision:** Present anomalies as analytical signals rather than explanations of cause.

**Rationale:** The available observational data does not support causal attribution.

**Consequences**

- Dashboard wording avoids causal claims.
- Alerts require contextual interpretation.
- Provisional-source status remains separate from anomaly status.

---

## D15 — Freeze validated outputs for assessment deployment

**Decision:** Deploy the assessment version with a fixed set of validated analytics, forecast, and anomaly CSV outputs.

**Rationale:** Government data may change after submission. A frozen snapshot keeps the live dashboard aligned with the report, screenshots, and evaluated results.

**Consequences**

- Only dashboard-required processed outputs are version controlled.
- Assessment results do not change when upstream data changes.
- Automated refresh remains a future production extension.

---

## D16 — Deploy on Streamlit Community Cloud

**Decision:** Deploy the dashboard from GitHub using Streamlit Community Cloud.

**Rationale:** The application is built in Streamlit and the frozen-runtime design requires no live database or government API connection.

**Consequences**

- `app.py` is the cloud entry point.
- `requirements.txt` defines deployment dependencies.
- Required frozen CSV files are included in the repository.
- No Streamlit secrets are required for the assessment deployment.
- A future live-refresh design would require orchestration and secure secret management.
