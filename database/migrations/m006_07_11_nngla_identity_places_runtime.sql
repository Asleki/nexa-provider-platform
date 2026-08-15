BEGIN;
CREATE SCHEMA IF NOT EXISTS geography;
CREATE TABLE geography.nngla_geographic_name (
    name_id text PRIMARY KEY, canonical_name text NOT NULL, ascii_name text NOT NULL, name_family text NOT NULL,
    naming_status_code text NOT NULL, runtime_effect_scope text NOT NULL CHECK(runtime_effect_scope='SHARED_REFERENCE'),
    source_dataset_id text NOT NULL, source_basis text NOT NULL, record_status text NOT NULL
);
CREATE TABLE geography.nngla_name_assignment (
    assignment_id text PRIMARY KEY, subject_id text NOT NULL, feature_type_code text NOT NULL,
    name_id text NOT NULL REFERENCES geography.nngla_geographic_name(name_id), assignment_status text NOT NULL,
    assignment_role text NOT NULL, gazette_reference text, runtime_effect_scope text NOT NULL,
    effective_from date, effective_to date, CHECK(effective_to IS NULL OR effective_from IS NULL OR effective_to>=effective_from)
);
CREATE TABLE geography.nngla_place_reference (
    place_id text PRIMARY KEY CHECK(place_id ~ '^NG-PLC-[0-9]{6}$'),
    source_place_code text NOT NULL UNIQUE,
    settlement_name_record_id text NOT NULL REFERENCES geography.nngla_geographic_name(name_id),
    place_type_code text NOT NULL, region_code text NOT NULL, parent_source_place_code text,
    spatial_assignment_status text NOT NULL, geometry_reference text,
    runtime_effect_scope text NOT NULL CHECK(runtime_effect_scope='SHARED_REFERENCE'), source_dataset_id text NOT NULL
);
CREATE INDEX ix_nngla_place_source_code ON geography.nngla_place_reference(source_place_code);
CREATE TABLE geography.nngla_administrative_area (
    administrative_area_id text PRIMARY KEY CHECK(administrative_area_id ~ '^NG-ADM-[0-9]{6}$'),
    administrative_candidate_id text NOT NULL UNIQUE, source_record_id text NOT NULL UNIQUE,
    administrative_type_code text NOT NULL, canonical_name text NOT NULL, parent_source_record_id text NOT NULL,
    region_code text NOT NULL, boundary_status text NOT NULL, geometry_reference text,
    lifecycle_status_code text NOT NULL, runtime_effect_scope text NOT NULL, candidate_status text NOT NULL
);
CREATE INDEX ix_nngla_admin_source_record ON geography.nngla_administrative_area(source_record_id);
COMMIT;
