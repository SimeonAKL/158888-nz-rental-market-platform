-- ============================================================
-- Migration 0003
-- Add Market Rent snapshot metadata and clean observation table
-- ============================================================


-- ------------------------------------------------------------
-- 1. Extend raw snapshot metadata
-- ------------------------------------------------------------

ALTER TABLE raw.snapshots
ADD COLUMN IF NOT EXISTS environment TEXT;

ALTER TABLE raw.snapshots
ADD COLUMN IF NOT EXISTS request_parameters JSONB;

ALTER TABLE raw.snapshots
ADD COLUMN IF NOT EXISTS metadata_file_name TEXT;


-- ------------------------------------------------------------
-- 2. Create cleaned Market Rent table
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS clean.market_rent (
    market_rent_id BIGSERIAL PRIMARY KEY,

    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    area_definition TEXT NOT NULL,
    area_name TEXT NOT NULL,

    dwelling_type TEXT NOT NULL,
    bedrooms TEXT NOT NULL,

    bonds_lodged INTEGER,
    bonds_closed INTEGER,
    active_bonds INTEGER,

    mean_rent NUMERIC,
    lower_quartile_rent NUMERIC,
    median_rent NUMERIC,
    upper_quartile_rent NUMERIC,
    rent_std_dev NUMERIC,

    bond_rent_ratio NUMERIC,
    log_mean NUMERIC,
    log_std_dev NUMERIC,
    synthetic_lower_quartile NUMERIC,
    synthetic_upper_quartile NUMERIC,

    source_snapshot_id BIGINT NOT NULL
        REFERENCES raw.snapshots(snapshot_id),

    retrieved_at TIMESTAMPTZ NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_clean_market_rent_observation
    UNIQUE (
        period_start,
        period_end,
        area_definition,
        area_name,
        dwelling_type,
        bedrooms
    )
);


-- ------------------------------------------------------------
-- 3. Indexes for dashboard, analysis and forecasting
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_clean_market_rent_period
ON clean.market_rent (
    period_end
);


CREATE INDEX IF NOT EXISTS idx_clean_market_rent_area
ON clean.market_rent (
    area_definition,
    area_name
);


CREATE INDEX IF NOT EXISTS idx_clean_market_rent_series
ON clean.market_rent (
    area_name,
    dwelling_type,
    bedrooms,
    period_end
);