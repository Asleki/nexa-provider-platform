BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.coordinate_reference (
    coordinate_reference_id text NOT NULL,
    version integer NOT NULL CHECK (version > 0),
    authority_name text NOT NULL,
    authority_code text NOT NULL,
    application_axis_order text[] NOT NULL,
    unit text NOT NULL,
    lifecycle_status text NOT NULL CHECK (lifecycle_status IN ('candidate','qualified','approved','active','superseded','quarantined','rejected')),
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (coordinate_reference_id, version),
    CHECK (coordinate_reference_id LIKE 'crs:%'),
    CHECK (application_axis_order = ARRAY['longitude','latitude']::text[])
);

CREATE TABLE geography.world_boundary (
    boundary_id text PRIMARY KEY,
    dataset_id text NOT NULL,
    semantic_name text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (boundary_id LIKE 'boundary:%'),
    CHECK (dataset_id LIKE 'dataset:%')
);

CREATE TABLE geography.source_package (
    source_package_id text PRIMARY KEY,
    dataset_id text NOT NULL,
    dataset_version integer NOT NULL CHECK (dataset_version > 0),
    source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
    media_type text NOT NULL,
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('production','simulation','shared_reference')),
    visibility text NOT NULL CHECK (visibility IN ('public','internal','restricted','confidential')),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (source_package_id LIKE 'source-package:%')
);

CREATE TABLE geography.world_boundary_version (
    boundary_id text NOT NULL REFERENCES geography.world_boundary(boundary_id),
    boundary_version integer NOT NULL CHECK (boundary_version > 0),
    coordinate_reference_id text NOT NULL,
    coordinate_reference_version integer NOT NULL,
    source_package_id text NOT NULL REFERENCES geography.source_package(source_package_id),
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('production','simulation','shared_reference')),
    visibility text NOT NULL CHECK (visibility IN ('public','internal','restricted','confidential')),
    lifecycle_status text NOT NULL CHECK (lifecycle_status IN ('candidate','qualified','approved','active','superseded','quarantined','rejected')),
    geometry geometry(MultiPolygon, 4326) NOT NULL,
    extent geometry(Polygon, 4326) GENERATED ALWAYS AS (ST_Envelope(geometry)) STORED,
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    supersedes_version integer NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (boundary_id, boundary_version),
    FOREIGN KEY (coordinate_reference_id, coordinate_reference_version)
        REFERENCES geography.coordinate_reference(coordinate_reference_id, version),
    CHECK (NOT ST_IsEmpty(geometry)),
    CHECK (ST_IsValid(geometry)),
    CHECK (ST_SRID(geometry) = 4326),
    CHECK (GeometryType(geometry) = 'MULTIPOLYGON'),
    CHECK (supersedes_version IS NULL OR supersedes_version <> boundary_version)
);

CREATE UNIQUE INDEX ux_world_boundary_active_runtime
    ON geography.world_boundary_version (boundary_id, runtime_mode)
    WHERE lifecycle_status = 'active';

CREATE INDEX ix_world_boundary_geometry_gist
    ON geography.world_boundary_version USING gist (geometry);

CREATE TABLE geography.boundary_qualification (
    qualification_id text PRIMARY KEY,
    boundary_id text NOT NULL,
    boundary_version integer NOT NULL,
    validation_receipt_id text NOT NULL,
    submitter_actor_id text NOT NULL,
    approver_actor_id text NOT NULL,
    decision text NOT NULL CHECK (decision IN ('qualified','rejected','quarantined')),
    receipt_sha256 text NOT NULL CHECK (receipt_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (boundary_id, boundary_version)
        REFERENCES geography.world_boundary_version(boundary_id, boundary_version),
    CHECK (qualification_id LIKE 'qualification:%'),
    CHECK (submitter_actor_id <> approver_actor_id)
);

CREATE TABLE geography.boundary_publication (
    publication_id text PRIMARY KEY,
    boundary_id text NOT NULL,
    boundary_version integer NOT NULL,
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('production','simulation','shared_reference')),
    visibility text NOT NULL CHECK (visibility = 'public'),
    lifecycle_status text NOT NULL CHECK (lifecycle_status IN ('approved','active')),
    content_sha256 text NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    published_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (boundary_id, boundary_version)
        REFERENCES geography.world_boundary_version(boundary_id, boundary_version),
    CHECK (publication_id LIKE 'publication:%')
);

COMMIT;
