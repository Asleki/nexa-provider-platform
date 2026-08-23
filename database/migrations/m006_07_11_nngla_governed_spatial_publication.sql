BEGIN;
-- P006.7.11.14 durable publication ledger. Existing read projection remains authoritative for public reads.
CREATE SCHEMA IF NOT EXISTS geography;
CREATE TABLE geography.nngla_publication_record (
    publication_id text NOT NULL CHECK (publication_id LIKE 'publication:nngla:%'),
    publication_version integer NOT NULL CHECK (publication_version > 0),
    subject_id text NOT NULL,
    record_family text NOT NULL,
    canonical_version integer NOT NULL DEFAULT 1 CHECK (canonical_version > 0),
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    visibility text NOT NULL CHECK (visibility IN ('PUBLIC','INTERNAL','RESTRICTED')),
    geometry_id text CHECK (geometry_id IS NULL OR geometry_id ~ '^NG-GEO-[0-9]{6}$'),
    geometry_version integer CHECK (geometry_version IS NULL OR geometry_version > 0),
    decision text NOT NULL CHECK (decision IN ('PUBLISHED','WITHDRAWN','SUPERSEDED')),
    submitted_by text NOT NULL,
    approved_by text NOT NULL,
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    supersedes_publication_id text,
    published_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(publication_id,publication_version),
    CHECK (submitted_by <> approved_by),
    CHECK (visibility <> 'PUBLIC' OR decision IN ('PUBLISHED','SUPERSEDED'))
);
CREATE UNIQUE INDEX ux_nngla_publication_active_subject_runtime
ON geography.nngla_publication_record(subject_id,runtime_mode,publication_version);
CREATE INDEX ix_nngla_publication_public_read
ON geography.nngla_publication_record(runtime_mode,record_family,visibility,subject_id);
COMMIT;
