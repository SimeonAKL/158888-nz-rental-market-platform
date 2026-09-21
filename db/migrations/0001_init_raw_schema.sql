-- ============================================================
-- Migration 0001
-- Create raw schema and source snapshot metadata table
-- ============================================================

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.snapshots (
    snapshot_id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_url TEXT,
    file_name TEXT NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    checksum_sha256 TEXT NOT NULL,
    row_count INTEGER,
    status TEXT NOT NULL DEFAULT 'downloaded',
    notes TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_snapshots_source_checksum
ON raw.snapshots (source_name, checksum_sha256);
