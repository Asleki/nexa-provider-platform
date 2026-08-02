CREATE SCHEMA IF NOT EXISTS platform;
CREATE TABLE IF NOT EXISTS platform.schema_migration (
    migration_id text PRIMARY KEY,
    milestone_id text NOT NULL,
    filename text NOT NULL,
    sequence_number integer NOT NULL UNIQUE CHECK (sequence_number > 0),
    checksum_sha256 char(64) NOT NULL CHECK (checksum_sha256 ~ '^[0-9a-f]{64}$'),
    status text NOT NULL CHECK (status IN ('STARTED','APPLIED','FAILED')),
    execution_id uuid NOT NULL UNIQUE,
    started_at timestamptz NOT NULL,
    completed_at timestamptz,
    execution_duration_ms bigint CHECK (execution_duration_ms IS NULL OR execution_duration_ms >= 0),
    applied_by text NOT NULL,
    database_name text NOT NULL,
    environment_name text NOT NULL,
    runner_version text NOT NULL,
    repository_revision text NOT NULL,
    error_code text,
    error_summary text,
    CHECK ((status='STARTED' AND completed_at IS NULL) OR (status IN ('APPLIED','FAILED') AND completed_at IS NOT NULL)),
    CHECK ((status='FAILED' AND error_code IS NOT NULL) OR (status<>'FAILED' AND error_code IS NULL))
);
