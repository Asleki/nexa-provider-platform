BEGIN;
CREATE SCHEMA IF NOT EXISTS geography;
CREATE TABLE geography.nngla_geometry_authority_record (
 geometry_id text PRIMARY KEY CHECK(geometry_id ~ '^NG-GEO-[0-9]{6}$'), subject_type text NOT NULL, subject_id text NOT NULL,
 geometry_role_code text NOT NULL, source_geometry_id text NOT NULL, source_dataset_id text NOT NULL, source_version text NOT NULL,
 geometry_type_code text NOT NULL, crs_code text NOT NULL, authoritative_level text NOT NULL, vertex_count integer, part_count integer,
 valid_from date NOT NULL, valid_to date, supersedes_geometry_id text, superseded_by_geometry_id text,
 qualification_status text NOT NULL, publication_status text NOT NULL, checksum_sha256 text NOT NULL CHECK(checksum_sha256 ~ '^[0-9a-f]{64}$'),
 source_path_reference text NOT NULL, runtime_effect_scope text NOT NULL,
 CHECK(valid_to IS NULL OR valid_to>=valid_from), CHECK(supersedes_geometry_id IS NULL OR supersedes_geometry_id<>geometry_id),
 CHECK(superseded_by_geometry_id IS NULL OR superseded_by_geometry_id<>geometry_id)
);
CREATE TABLE geography.nngla_survey_record (
 survey_id text PRIMARY KEY CHECK(survey_id ~ '^NG-SRV-[0-9]{6}$'), accuracy_class_code text NOT NULL, source_reference text NOT NULL,
 instrument_record_reference text, surveyor_approval_reference text, status text NOT NULL
);
CREATE TABLE geography.nngla_survey_control_point (
 survey_control_candidate_id text PRIMARY KEY, source_point_id text NOT NULL UNIQUE, candidate_role text NOT NULL,
 longitude double precision NOT NULL CHECK(longitude BETWEEN -180 AND 180), latitude double precision NOT NULL CHECK(latitude BETWEEN -90 AND 90),
 crs_code text NOT NULL, accuracy_class_code text NOT NULL, qualification_status text NOT NULL, source_basis text NOT NULL
);
CREATE TABLE geography.nngla_road_reference_candidate (
 road_candidate_id text PRIMARY KEY CHECK(road_candidate_id ~ '^NG-RD-CAND-[0-9]{6}$'), road_name_id text NOT NULL,
 canonical_name text NOT NULL, road_class_code text NOT NULL, planning_status text NOT NULL, geometry_status text NOT NULL,
 geometry_reference text, addressing_eligible boolean NOT NULL, region_code text, source_basis text NOT NULL, runtime_effect_scope text NOT NULL
);
CREATE TABLE geography.nngla_road (
 road_id text PRIMARY KEY CHECK(road_id ~ '^NG-RD-[0-9]{6}$'), source_candidate_id text NOT NULL UNIQUE REFERENCES geography.nngla_road_reference_candidate(road_candidate_id),
 road_name_id text NOT NULL, road_class_code text NOT NULL, geometry_id text, lifecycle_status text NOT NULL, runtime_effect_scope text NOT NULL
);
CREATE TABLE geography.nngla_addressable_site (
 site_id text PRIMARY KEY, place_id text, administrative_area_id text, road_id text, parcel_id text, geometry_reference text,
 site_status text NOT NULL, runtime_effect_scope text NOT NULL
);
CREATE TABLE geography.nngla_address (
 address_id text PRIMARY KEY CHECK(address_id ~ '^NG-ADR-[0-9]{6}$'), site_id text NOT NULL REFERENCES geography.nngla_addressable_site(site_id),
 road_id text, display_address_number text NOT NULL, unit_designator text, lifecycle_status text NOT NULL, parcel_id text, runtime_effect_scope text NOT NULL
);
COMMIT;
