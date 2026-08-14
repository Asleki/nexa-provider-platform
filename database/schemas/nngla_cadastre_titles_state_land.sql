-- P006.7.7/P006.7.8 additive NNGLA cadastre/title/state-land schema contract.
-- Contract only. Reuses locked NNGLA/PostGIS foundations and does not register
-- or execute an AWS PostgreSQL migration.
CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.nngla_parcel (
    parcel_id text PRIMARY KEY CHECK (parcel_id ~ '^NV-[0-9]{2}-[0-9]{3}-[0-9]{4,}$'),
    parent_parcel_id text,
    cadastral_series text NOT NULL,
    parcel_sequence text NOT NULL,
    parcel_status text NOT NULL,
    geometry_reference text,
    land_use_code text,
    survey_status text NOT NULL,
    created_effective_at date NOT NULL,
    retired_effective_at date,
    source_reference text NOT NULL,
    runtime_effect_scope text NOT NULL,
    CHECK (parent_parcel_id IS NULL OR parent_parcel_id ~ '^NV-[0-9]{2}-[0-9]{3}-[0-9]{4,}$'),
    CHECK (parent_parcel_id IS NULL OR parent_parcel_id <> parcel_id),
    CHECK (geometry_reference IS NULL OR geometry_reference ~ '^NG-GEO-[0-9]{6}$'),
    CHECK (retired_effective_at IS NULL OR retired_effective_at >= created_effective_at)
);

CREATE TABLE geography.nngla_parcel_lineage (
    lineage_id text PRIMARY KEY,
    action text NOT NULL,
    effective_on date NOT NULL,
    source_reference text NOT NULL,
    human_decision_reference text,
    simulation_assessment_reference text
);

CREATE TABLE geography.nngla_parcel_lineage_member (
    lineage_id text NOT NULL REFERENCES geography.nngla_parcel_lineage(lineage_id),
    parcel_id text NOT NULL CHECK (parcel_id ~ '^NV-[0-9]{2}-[0-9]{3}-[0-9]{4,}$'),
    lineage_role text NOT NULL CHECK (lineage_role IN ('PREDECESSOR','SUCCESSOR')),
    PRIMARY KEY (lineage_id, parcel_id, lineage_role)
);

CREATE TABLE geography.nngla_cadastral_geometry_assignment (
    parcel_id text NOT NULL CHECK (parcel_id ~ '^NV-[0-9]{2}-[0-9]{3}-[0-9]{4,}$'),
    geometry_id text NOT NULL CHECK (geometry_id ~ '^NG-GEO-[0-9]{6}$'),
    survey_id text CHECK (survey_id IS NULL OR survey_id ~ '^NG-SRV-[0-9]{6}$'),
    geometry_role_code text NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    source_reference text NOT NULL,
    PRIMARY KEY (parcel_id, geometry_id),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE geography.nngla_title (
    title_id text PRIMARY KEY CHECK (title_id ~ '^NG-TTL-[0-9]{6}$'),
    parcel_id text NOT NULL CHECK (parcel_id ~ '^NV-[0-9]{2}-[0-9]{3}-[0-9]{4,}$'),
    title_type_code text NOT NULL,
    tenure_type_code text NOT NULL,
    holder_reference text NOT NULL,
    title_status text NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    source_reference text NOT NULL,
    runtime_effect_scope text NOT NULL,
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE geography.nngla_state_land (
    state_land_record_id text PRIMARY KEY,
    parcel_id text NOT NULL CHECK (parcel_id ~ '^NV-[0-9]{2}-[0-9]{3}-[0-9]{4,}$'),
    state_land_category_code text NOT NULL,
    administrative_area_id text,
    status text NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    source_reference text NOT NULL,
    runtime_effect_scope text NOT NULL,
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);
