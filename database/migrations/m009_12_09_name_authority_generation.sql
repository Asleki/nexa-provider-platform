BEGIN;
CREATE TABLE IF NOT EXISTS reference.name_generation_source_snapshot (
 snapshot_id varchar(256) PRIMARY KEY, runtime_mode varchar(32) NOT NULL CHECK (runtime_mode='simulation'), checksum char(64) NOT NULL,
 member_count integer NOT NULL CHECK (member_count>=0), created_at timestamptz NOT NULL, metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS reference.name_generation_source_member (
 snapshot_id varchar(256) NOT NULL REFERENCES reference.name_generation_source_snapshot(snapshot_id) ON DELETE RESTRICT,
 name_id varchar(256) NOT NULL REFERENCES reference.canonical_name(name_id) ON DELETE RESTRICT, ordinal integer NOT NULL CHECK (ordinal>=0),
 name_kind varchar(32) NOT NULL CHECK (name_kind IN ('first_name','middle_name','surname')), profile jsonb NOT NULL DEFAULT '{}'::jsonb,
 PRIMARY KEY(snapshot_id,name_id), UNIQUE(snapshot_id,ordinal)
);
CREATE TABLE IF NOT EXISTS reference.name_generation_batch (
 generation_batch_id varchar(256) PRIMARY KEY, runtime_mode varchar(32) NOT NULL CHECK (runtime_mode='simulation'),
 source_snapshot_id varchar(256) NOT NULL REFERENCES reference.name_generation_source_snapshot(snapshot_id), source_snapshot_checksum char(64) NOT NULL,
 requested_count integer NOT NULL CHECK (requested_count>=0), batch_size integer NOT NULL CHECK (batch_size BETWEEN 1 AND 10000),
 random_seed text NOT NULL, generator_algorithm varchar(128) NOT NULL, generator_version integer NOT NULL CHECK (generator_version>=1),
 rules_version integer NOT NULL CHECK (rules_version>=1), status varchar(32) NOT NULL CHECK (status IN ('draft','validated','ready','running','paused','completed','failed','cancelled','exhausted')),
 next_sequence integer NOT NULL DEFAULT 0 CHECK (next_sequence>=0), attempted_count integer NOT NULL DEFAULT 0, inserted_count integer NOT NULL DEFAULT 0,
 existing_count integer NOT NULL DEFAULT 0, skipped_count integer NOT NULL DEFAULT 0, failed_count integer NOT NULL DEFAULT 0,
 checkpoint_sequence integer NOT NULL DEFAULT 0, row_version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL, completed_at timestamptz,
 result_checksum char(64), lease_owner varchar(256), lease_expires_at timestamptz, configuration jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS reference.name_generation_checkpoint (
 checkpoint_id varchar(256) PRIMARY KEY, generation_batch_id varchar(256) NOT NULL REFERENCES reference.name_generation_batch(generation_batch_id) ON DELETE RESTRICT,
 checkpoint_sequence integer NOT NULL, first_generation_sequence integer NOT NULL, last_generation_sequence integer NOT NULL, next_generation_sequence integer NOT NULL,
 attempted_count integer NOT NULL, inserted_count integer NOT NULL, existing_count integer NOT NULL, skipped_count integer NOT NULL, failed_count integer NOT NULL,
 batch_checksum char(64) NOT NULL, source_snapshot_checksum char(64) NOT NULL, committed_at timestamptz NOT NULL,
 UNIQUE(generation_batch_id,checkpoint_sequence)
);
CREATE TABLE IF NOT EXISTS reference.name_generation_result (
 generation_batch_id varchar(256) NOT NULL REFERENCES reference.name_generation_batch(generation_batch_id) ON DELETE RESTRICT,
 generation_sequence integer NOT NULL CHECK (generation_sequence>=0), generation_family varchar(64) NOT NULL,
 authority_name_id varchar(256) NOT NULL REFERENCES reference.name_authority_record(authority_name_id) ON DELETE RESTRICT,
 composition_key char(64) NOT NULL, outcome varchar(32) NOT NULL CHECK (outcome IN ('inserted','existing','skipped','failed')),
 committed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY(generation_batch_id,generation_sequence)
);
CREATE INDEX IF NOT EXISTS ix_name_generation_result_authority ON reference.name_generation_result(authority_name_id);
CREATE TABLE IF NOT EXISTS reference.name_authority_read_model (
 authority_name_id varchar(256) PRIMARY KEY REFERENCES reference.name_authority_record(authority_name_id) ON DELETE RESTRICT,
 runtime_mode varchar(32) NOT NULL CHECK (runtime_mode IN ('simulation','production')), composition_type varchar(64) NOT NULL,
 display_name varchar(600) NOT NULL, search_name varchar(600) NOT NULL, ordered_component_ids jsonb NOT NULL,
 ordered_component_values jsonb NOT NULL, source_strategy varchar(128) NOT NULL, status varchar(32) NOT NULL,
 generation_family varchar(64), generation_batch_id varchar(256), schema_version integer NOT NULL, read_model_version integer NOT NULL,
 projected_at timestamptz NOT NULL, metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS ix_name_authority_read_cursor ON reference.name_authority_read_model(runtime_mode,search_name,authority_name_id);
CREATE INDEX IF NOT EXISTS ix_name_authority_read_generation ON reference.name_authority_read_model(runtime_mode,generation_family,generation_batch_id);
CREATE TABLE IF NOT EXISTS reference.name_authority_projection_checkpoint (
 projection_name varchar(128) NOT NULL, runtime_mode varchar(32) NOT NULL, last_authority_name_id varchar(256), projected_count integer NOT NULL,
 read_model_version integer NOT NULL, checksum char(64) NOT NULL, updated_at timestamptz NOT NULL, PRIMARY KEY(projection_name,runtime_mode)
);
COMMIT;
