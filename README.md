# NZ Regional Rental Market Analytics and Forecasting Platform

**Massey University — 158888 Information Technology Professional Project**

## Project Overview

This project develops a regional rental market analytics and forecasting
platform for New Zealand using official Tenancy Services / MBIE rental data.

The platform is intended to support:

- reproducible rental data acquisition and processing
- regional rental market analysis
- time-series forecasting
- forecasting model comparison
- interpretable anomaly detection
- interactive Streamlit visualisation
- data-quality and provenance reporting

## Core Technology Stack

- Python
- pandas
- PostgreSQL / Supabase
- statsmodels
- XGBoost
- scikit-learn
- Streamlit
- pytest
- Git / GitHub
- GitHub Codespaces

## Project Structure

```text
data/
    raw/          Immutable source snapshots
    staging/      Validated intermediate data
    processed/    Cleaned and harmonised outputs
    reference/    Geographic reference data

db/
    migrations/   PostgreSQL schema definitions

src/rmp/
    Core Python package

scripts/
    Development and operational utilities

tests/
    Automated tests

docs/
    Project documentation
```

## Development Environment

The project is developed primarily using GitHub Codespaces.

Install the core and development dependencies with:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run static checks:

```bash
ruff check .
```

## Database

The project uses Supabase-hosted PostgreSQL.

Database credentials must be supplied using environment variables.
Real credentials must never be committed to Git.

See `.env.example` for the required configuration variables.

## Current Development Stage

Phase 1 — Foundations and Data Infrastructure.
