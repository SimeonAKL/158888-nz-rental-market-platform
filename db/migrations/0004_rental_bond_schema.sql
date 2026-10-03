-- ============================================================
-- Migration 0004
-- Create cleaned Rental Bond observation table
-- ============================================================


CREATE TABLE IF NOT EXISTS clean.rental_bond (
    rental_bond_id BIGSERIAL PRIMARY KEY,

    period_date DATE NOT NULL,

    geography_level TEXT NOT NULL,
    location_id INTEGER NOT NULL,
    location_name TEXT NOT NULL,

    bonds_lodged INTEGER,
    active_bonds INTEGER,
    bonds_closed INTEGER,

    median_rent NUMERIC,
    geometric_mean_rent NUMERIC,
    upper_quartile_rent NUMERIC,
    lower_quartile_rent NUMERIC,
    log_std_dev_weekly_rent NUMERIC,

    is_provisional BOOLEAN NOT NULL DEFAULT FALSE,

    source_snapshot_id BIGINT NOT NULL
        REFERENCES raw.snapshots(snapshot_id),

    retrieved_at TIMESTAMPTZ NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_clean_rental_bond_observation
    UNIQUE (
        period_date,
        geography_level,
        location_id
    ),

    CONSTRAINT chk_clean_rental_bond_geography_level
    CHECK (
        geography_level IN (
            'region',
            'territorial_authority'
        )
    )
);


CREATE INDEX IF NOT EXISTS idx_clean_rental_bond_period
ON clean.rental_bond (
    period_date
);


CREATE INDEX IF NOT EXISTS idx_clean_rental_bond_geography
ON clean.rental_bond (
    geography_level,
    location_id
);


CREATE INDEX IF NOT EXISTS idx_clean_rental_bond_series
ON clean.rental_bond (
    geography_level,
    location_id,
    period_date
);


CREATE INDEX IF NOT EXISTS idx_clean_rental_bond_location_name
ON clean.rental_bond (
    geography_level,
    location_name
);