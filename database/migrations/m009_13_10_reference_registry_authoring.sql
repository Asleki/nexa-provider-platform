BEGIN;
CREATE SEQUENCE IF NOT EXISTS reference.tribe_code_seq START WITH 1;
CREATE SEQUENCE IF NOT EXISTS reference.language_code_seq START WITH 1;
CREATE SEQUENCE IF NOT EXISTS reference.origin_code_seq START WITH 1;
CREATE TABLE IF NOT EXISTS reference.reference_authority_record (
 reference_id text PRIMARY KEY,
 reference_code text NOT NULL UNIQUE CHECK (reference_code ~ '^[a-z]{3}_[0-9]{3,12}$'),
 reference_type text NOT NULL CHECK (reference_type IN ('tribe','language','origin')),
 canonical_label text NOT NULL CHECK (length(btrim(canonical_label)) BETWEEN 1 AND 200),
 search_label text NOT NULL CHECK (length(search_label)>0),
 runtime_mode text NOT NULL CHECK (runtime_mode IN ('production','simulation')),
 status text NOT NULL CHECK (status IN ('active','suspended','retired')),
 source_reference text NOT NULL,
 origin_type text NULL CHECK (origin_type IS NULL OR origin_type IN ('country','nationality_label','regional_culture','historic_region','linguistic_culture','source_declared_origin')),
 native_label text NULL,
 attributes jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(attributes)='object'),
 created_at timestamptz NOT NULL,
 created_by_actor_id text NOT NULL,
 approved_by_actor_id text NOT NULL,
 CHECK (created_by_actor_id<>approved_by_actor_id),
 UNIQUE(runtime_mode,reference_type,search_label)
);
CREATE INDEX IF NOT EXISTS ix_reference_authority_type_status ON reference.reference_authority_record(runtime_mode,reference_type,status);
CREATE TABLE IF NOT EXISTS reference.name_orthography_profile (
 profile_id text PRIMARY KEY,
 name_id text NOT NULL UNIQUE REFERENCES reference.canonical_name(name_id) ON DELETE RESTRICT,
 runtime_mode text NOT NULL CHECK (runtime_mode IN ('production','simulation')),
 structure_type text NOT NULL CHECK (structure_type IN ('simple','compound_space_separated','hyphenated','apostrophized','prefixed_compound','joined_prefix','multi_surname','mixed_form')),
 canonical_value_snapshot text NOT NULL,
 accented boolean NOT NULL,
 accent_stripping_authorized boolean NOT NULL DEFAULT false CHECK (accent_stripping_authorized=false),
 tokens jsonb NOT NULL CHECK (jsonb_typeof(tokens)='array'),
 separators jsonb NOT NULL CHECK (jsonb_typeof(separators)='array'),
 source_reference text NOT NULL,
 attributes jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(attributes)='object'),
 created_at timestamptz NOT NULL,
 created_by_actor_id text NOT NULL,
 approved_by_actor_id text NOT NULL,
 CHECK (created_by_actor_id<>approved_by_actor_id)
);
CREATE INDEX IF NOT EXISTS ix_name_orthography_structure ON reference.name_orthography_profile(runtime_mode,structure_type,accented);
CREATE TABLE IF NOT EXISTS reference.name_context_relationship (
 relationship_id text PRIMARY KEY,
 name_id text NOT NULL REFERENCES reference.canonical_name(name_id) ON DELETE RESTRICT,
 runtime_mode text NOT NULL CHECK (runtime_mode IN ('production','simulation')),
 relationship_role text NOT NULL CHECK (relationship_role IN ('native_surname_tribe','surname_origin','surname_language','first_name_language','middle_name_language','not_applicable_tribe','not_applicable_origin')),
 relationship_state text NOT NULL CHECK (relationship_state IN ('resolved','not_applicable','source_not_provided','quarantined','conflict')),
 target_reference_id text NULL REFERENCES reference.reference_authority_record(reference_id) ON DELETE RESTRICT,
 source_reference text NOT NULL,
 attributes jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(attributes)='object'),
 created_at timestamptz NOT NULL,
 created_by_actor_id text NOT NULL,
 approved_by_actor_id text NOT NULL,
 CHECK (created_by_actor_id<>approved_by_actor_id),
 CHECK ((relationship_state='resolved' AND target_reference_id IS NOT NULL) OR (relationship_state<>'resolved')),
 CHECK ((relationship_state='not_applicable' AND target_reference_id IS NULL) OR relationship_state<>'not_applicable'),
 UNIQUE(name_id,relationship_role,target_reference_id,relationship_state)
);
CREATE INDEX IF NOT EXISTS ix_name_context_target ON reference.name_context_relationship(runtime_mode,relationship_role,target_reference_id);
COMMIT;
