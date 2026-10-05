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
pip install -e ".[dev,forecasting,dashboard]"
```

The repository includes `requirements-tested.txt`, which records the exact
direct dependency versions used for the validated development environment.

For the closest reproduction of the validated environment:

```bash
pip install -r requirements-tested.txt
pip install -e . --no-deps
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

Phase 5 — Analytics, forecasting, anomaly detection and the Streamlit dashboard are implemented. Phase 6 focuses on packaging, documentation, final quality assurance and reporting.
