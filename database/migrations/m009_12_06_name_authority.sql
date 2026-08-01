BEGIN;
CREATE SCHEMA IF NOT EXISTS reference;
CREATE TABLE IF NOT EXISTS reference.manual_name_candidate (
 candidate_id varchar(256) PRIMARY KEY, request_id varchar(256) NOT NULL UNIQUE, operation_id varchar(256) NOT NULL,
 runtime_mode varchar(32) NOT NULL CHECK (runtime_mode='production'), raw_name_value varchar(200) NOT NULL,
 requested_name_kind varchar(32) NOT NULL CHECK (requested_name_kind IN ('first_name','middle_name','surname')),
 sex_usage varchar(32) NOT NULL CHECK (sex_usage IN ('male','female','unisex','unspecified')),
 origin_declaration jsonb NOT NULL DEFAULT '{}'::jsonb, language_declaration jsonb NOT NULL DEFAULT '{}'::jsonb,
 community_declaration jsonb NOT NULL DEFAULT '{}'::jsonb, script_code varchar(32),
 status varchar(32) NOT NULL CHECK (status IN ('draft','submitted','validated','quarantined','approved','rejected','cancelled')),
 schema_version integer NOT NULL CHECK (schema_version>=1), submitted_by_actor_id varchar(256) NOT NULL,
 submitted_by_actor_type varchar(128) NOT NULL, submitted_at timestamptz NOT NULL, notes text,
 canonical_name_id varchar(256) REFERENCES reference.canonical_name(name_id), reviewed_by_actor_id varchar(256),
 reviewed_at timestamptz, decision_reason text
);
CREATE INDEX IF NOT EXISTS ix_manual_name_candidate_status ON reference.manual_name_candidate(runtime_mode,status,submitted_at);
CREATE TABLE IF NOT EXISTS reference.name_authority_record (
 authority_name_id varchar(256) PRIMARY KEY, runtime_mode varchar(32) NOT NULL CHECK (runtime_mode IN ('simulation','production')),
 composition_type varchar(64) NOT NULL CHECK (composition_type IN ('single_name','first_surname','first_middle','first_middle_surname','international_pair','compound_surname')),
 composition_key char(64) NOT NULL, display_name varchar(600) NOT NULL, search_name varchar(600) NOT NULL,
 source_strategy varchar(128) NOT NULL, status varchar(32) NOT NULL CHECK (status IN ('active','suspended','retired','superseded')),
 schema_version integer NOT NULL CHECK (schema_version>=1), created_at timestamptz NOT NULL, created_by_actor_id varchar(256) NOT NULL,
 approved_at timestamptz, approved_by_actor_id varchar(256), supersedes_authority_name_id varchar(256) REFERENCES reference.name_authority_record(authority_name_id),
 metadata jsonb NOT NULL DEFAULT '{}'::jsonb, UNIQUE(runtime_mode,composition_key)
);
CREATE INDEX IF NOT EXISTS ix_name_authority_search ON reference.name_authority_record(runtime_mode,search_name,authority_name_id);
CREATE TABLE IF NOT EXISTS reference.name_authority_component (
 authority_name_id varchar(256) NOT NULL REFERENCES reference.name_authority_record(authority_name_id) ON DELETE RESTRICT,
 position integer NOT NULL CHECK (position>=1), name_id varchar(256) NOT NULL REFERENCES reference.canonical_name(name_id) ON DELETE RESTRICT,
 component_role varchar(64) NOT NULL CHECK (component_role IN ('single_name','first_name','middle_name','surname')),
 name_kind_snapshot varchar(32) NOT NULL CHECK (name_kind_snapshot IN ('first_name','middle_name','surname')),
 separator_after varchar(16) NOT NULL DEFAULT ' ', metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
 PRIMARY KEY(authority_name_id,position)
);
CREATE INDEX IF NOT EXISTS ix_name_authority_component_name ON reference.name_authority_component(name_id,authority_name_id);
COMMIT;
