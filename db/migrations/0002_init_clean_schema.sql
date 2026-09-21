-- ============================================================
-- Migration 0002
-- Create cleaned geographic and rental metric tables
-- ============================================================

CREATE SCHEMA IF NOT EXISTS clean;

CREATE TABLE IF NOT EXISTS clean.geo_areas (
    area_code TEXT PRIMARY KEY,
    area_name TEXT NOT NULL,
    area_type TEXT NOT NULL,
    parent_region_code TEXT REFERENCES clean.geo_areas(area_code)
);

CREATE TABLE IF NOT EXISTS clean.rental_metrics (
    id BIGSERIAL PRIMARY KEY,
    area_code TEXT NOT NULL REFERENCES clean.geo_areas(area_code),
    period_date DATE NOT NULL,
    metric TEXT NOT NULL,
    value NUMERIC,
    is_provisional BOOLEAN NOT NULL DEFAULT FALSE,
    source_snapshot_id BIGINT REFERENCES raw.snapshots(snapshot_id),
    UNIQUE (area_code, period_date, metric)
);

CREATE INDEX IF NOT EXISTS idx_clean_rental_metrics_lookup
ON clean.rental_metrics (area_code, metric, period_date);
