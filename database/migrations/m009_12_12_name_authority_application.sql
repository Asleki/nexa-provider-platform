BEGIN;
CREATE TABLE IF NOT EXISTS reference.name_authority_command_receipt (
 idempotency_key text PRIMARY KEY,
 operation text NOT NULL,
 actor_id text NOT NULL,
 runtime_mode text NOT NULL CHECK (runtime_mode IN ('production','simulation')),
 request_hash text NOT NULL,
 response_payload jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS reference.name_authority_change_journal (
 change_sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 authority_name_id text NOT NULL,
 runtime_mode text NOT NULL CHECK (runtime_mode IN ('production','simulation')),
 change_type text NOT NULL,
 read_model_version integer NOT NULL,
 occurred_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(runtime_mode, authority_name_id, read_model_version, change_type)
);
CREATE INDEX IF NOT EXISTS ix_name_authority_change_journal_runtime_sequence ON reference.name_authority_change_journal(runtime_mode,change_sequence);
CREATE TABLE IF NOT EXISTS reference.name_authority_sync_receipt (
 receipt_id text PRIMARY KEY,
 request_id text NOT NULL,
 device_id text NOT NULL,
 actor_id text NOT NULL,
 runtime_mode text NOT NULL CHECK (runtime_mode IN ('production','simulation')),
 snapshot_id text NOT NULL,
 applied_count integer NOT NULL CHECK (applied_count>=0),
 failed_count integer NOT NULL CHECK (failed_count>=0),
 conflict_count integer NOT NULL CHECK (conflict_count>=0),
 checksum text NOT NULL,
 completed_at timestamptz NOT NULL
);
COMMIT;
