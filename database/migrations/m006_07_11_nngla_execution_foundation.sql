BEGIN;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.nngla_source_dataset (
    dataset_id text NOT NULL,
    dataset_version text NOT NULL,
    dataset_class text NOT NULL CHECK (dataset_class IN ('REAL_POPULATED_DATASET','REAL_COMPLETE_CONTROLLED_VOCABULARY','REAL_EMPTY_GOVERNED_REGISTER')),
    migration_eligibility text NOT NULL CHECK (migration_eligibility IN ('READY_FOR_MIGRATION_PLANNING','DEFERRED_SPATIAL_OR_LEGAL')),
    data_classification text NOT NULL CHECK (data_classification IN ('PUBLIC','PUBLIC_REFERENCE','INTERNAL','RESTRICTED','LEGAL_RECORD','SECURITY_SENSITIVE')),
    source_authority text NOT NULL,
    recorded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (dataset_id, dataset_version), CHECK (dataset_id LIKE 'dataset:%')
);
CREATE TABLE geography.nngla_source_artifact (
    source_artifact_id text PRIMARY KEY,
    dataset_id text NOT NULL, dataset_version text NOT NULL,
    file_path text NOT NULL, sha256 text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    byte_size bigint NOT NULL CHECK (byte_size >= 0), row_count bigint NULL CHECK (row_count IS NULL OR row_count >= 0),
    recorded_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (dataset_id,dataset_version,file_path),
    FOREIGN KEY (dataset_id,dataset_version) REFERENCES geography.nngla_source_dataset(dataset_id,dataset_version)
);
CREATE TABLE geography.nngla_ingest_batch (
    ingest_batch_id text PRIMARY KEY CHECK (ingest_batch_id LIKE 'ingest:nngla:%'),
    dataset_id text NOT NULL, dataset_version text NOT NULL,
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    effect_scope text NOT NULL CHECK (effect_scope IN ('SHARED_REFERENCE','SIMULATION_ONLY','PRODUCTION_ONLY','RUNTIME_SCOPED','HISTORICAL_REFERENCE')),
    data_classification text NOT NULL CHECK (data_classification IN ('PUBLIC','PUBLIC_REFERENCE','INTERNAL','RESTRICTED','LEGAL_RECORD','SECURITY_SENSITIVE')),
    received_at timestamptz NOT NULL,
    FOREIGN KEY (dataset_id,dataset_version) REFERENCES geography.nngla_source_dataset(dataset_id,dataset_version)
);
CREATE TABLE geography.nngla_staged_record (
    staged_record_id text PRIMARY KEY CHECK (staged_record_id LIKE 'staged:nngla:%'),
    ingest_batch_id text NOT NULL REFERENCES geography.nngla_ingest_batch(ingest_batch_id),
    source_record_id text NOT NULL, source_file text NOT NULL,
    source_row_number bigint NULL CHECK (source_row_number IS NULL OR source_row_number > 0),
    record_family text NOT NULL, candidate_id text NOT NULL,
    pipeline_state text NOT NULL CHECK (pipeline_state IN ('RECEIVED','STAGED','VALIDATED','QUARANTINED','REJECTED','CANONICALIZATION_READY','CANONICALIZED')),
    raw_payload jsonb NOT NULL, staged_at timestamptz NOT NULL,
    UNIQUE (ingest_batch_id,source_record_id)
);
CREATE TABLE geography.nngla_quarantine_record (
    quarantine_id text PRIMARY KEY CHECK (quarantine_id LIKE 'quarantine:nngla:%'),
    staged_record_id text NOT NULL REFERENCES geography.nngla_staged_record(staged_record_id),
    error_code text NOT NULL, error_message text NOT NULL, raw_payload jsonb NOT NULL, quarantined_at timestamptz NOT NULL
);
CREATE TABLE geography.nngla_spatial_feature (
    feature_id text NOT NULL, runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    effect_scope text NOT NULL CHECK (effect_scope IN ('SHARED_REFERENCE','SIMULATION_ONLY','PRODUCTION_ONLY','RUNTIME_SCOPED','HISTORICAL_REFERENCE')),
    authority_id text NOT NULL DEFAULT 'authority:nngla' CHECK (authority_id='authority:nngla'),
    record_family text NOT NULL, lifecycle_status text NOT NULL, effective_from date NOT NULL, effective_to date NULL,
    canonical_version integer NOT NULL CHECK (canonical_version > 0), data_classification text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(feature_id,runtime_mode,canonical_version),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);
CREATE TABLE geography.nngla_geometry_version (
    geometry_id text PRIMARY KEY, subject_id text NOT NULL,
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    geometry_role_code text NOT NULL, crs_code text NOT NULL CHECK (crs_code='NG-CRS-EPSG4326'),
    geometry_type_code text NOT NULL CHECK (geometry_type_code IN ('POINT','MULTIPOINT','LINESTRING','MULTILINESTRING','POLYGON','MULTIPOLYGON')),
    geometry geometry(Geometry,4326) NOT NULL, valid_from date NOT NULL, valid_to date NULL,
    supersedes_geometry_id text NULL, source_sha256 text NULL CHECK (source_sha256 IS NULL OR source_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now(), CHECK (NOT ST_IsEmpty(geometry)), CHECK (ST_IsValid(geometry)),
    CHECK (ST_SRID(geometry)=4326), CHECK (valid_to IS NULL OR valid_to >= valid_from),
    CHECK (supersedes_geometry_id IS NULL OR supersedes_geometry_id <> geometry_id)
);
CREATE INDEX ix_nngla_geometry_version_gist ON geography.nngla_geometry_version USING GIST(geometry);
CREATE INDEX ix_nngla_geometry_subject_runtime ON geography.nngla_geometry_version(subject_id,runtime_mode);
CREATE TABLE geography.nngla_canonical_crosswalk (
    crosswalk_id text PRIMARY KEY CHECK (crosswalk_id LIKE 'crosswalk:nngla:%'),
    dataset_id text NOT NULL, dataset_version text NOT NULL, source_record_id text NOT NULL, candidate_id text NOT NULL,
    canonical_id text NOT NULL, canonical_version integer NOT NULL CHECK (canonical_version > 0),
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')), effect_scope text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE(dataset_id,dataset_version,source_record_id,runtime_mode,effect_scope),
    UNIQUE(canonical_id,canonical_version,runtime_mode)
);
CREATE TABLE geography.nngla_canonicalization_receipt (
    receipt_id text PRIMARY KEY CHECK (receipt_id LIKE 'canonicalization:nngla:%'),
    crosswalk_id text NOT NULL REFERENCES geography.nngla_canonical_crosswalk(crosswalk_id),
    staged_record_id text NOT NULL REFERENCES geography.nngla_staged_record(staged_record_id),
    source_payload_sha256 text NOT NULL CHECK (source_payload_sha256 ~ '^[0-9a-f]{64}$'),
    validation_references jsonb NOT NULL DEFAULT '[]'::jsonb, canonicalized_at timestamptz NOT NULL, dry_run boolean NOT NULL DEFAULT false
);
CREATE TABLE geography.nngla_execution_receipt (
    execution_id text PRIMARY KEY CHECK (execution_id LIKE 'nnglarun:%'),
    plan_id text NOT NULL, plan_version integer NOT NULL CHECK(plan_version>0), fingerprint_sha256 text NOT NULL CHECK(fingerprint_sha256 ~ '^[0-9a-f]{64}$'),
    database_name text NOT NULL, environment_name text NOT NULL, runtime_mode text NOT NULL CHECK(runtime_mode IN ('simulation','production')),
    repository_revision text NOT NULL, source_sha256 text NOT NULL CHECK(source_sha256 ~ '^[0-9a-f]{64}$'),
    submitter_actor_id text NOT NULL, approver_actor_id text NOT NULL,
    selected_count integer NOT NULL CHECK(selected_count>=0), inserted_count integer NOT NULL CHECK(inserted_count>=0),
    reused_count integer NOT NULL CHECK(reused_count>=0), quarantined_count integer NOT NULL CHECK(quarantined_count>=0),
    failed_count integer NOT NULL CHECK(failed_count>=0), status text NOT NULL CHECK(status IN ('APPLIED','REUSED','EMPTY','FAILED')),
    started_at timestamptz NOT NULL, completed_at timestamptz NOT NULL,
    CHECK(submitter_actor_id <> approver_actor_id)
);
CREATE UNIQUE INDEX ux_nngla_execution_fingerprint_target ON geography.nngla_execution_receipt(fingerprint_sha256,database_name,environment_name);
CREATE TABLE geography.nngla_execution_item (
    execution_id text NOT NULL REFERENCES geography.nngla_execution_receipt(execution_id),
    source_record_id text NOT NULL, canonical_id text, outcome text NOT NULL,
    crosswalk_id text, canonicalization_receipt_id text, event_id text, audit_id text,
    publication_ready boolean NOT NULL DEFAULT false, detail jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY(execution_id,source_record_id)
);
CREATE INDEX ix_nngla_execution_item_canonical ON geography.nngla_execution_item(canonical_id) WHERE canonical_id IS NOT NULL;
COMMIT;
