BEGIN;
CREATE SCHEMA IF NOT EXISTS reference;
CREATE TABLE IF NOT EXISTS reference.canonical_name (
 name_id TEXT PRIMARY KEY CHECK (name_id ~ '^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$'),
 canonical_value TEXT NOT NULL CHECK (length(btrim(canonical_value)) BETWEEN 1 AND 200),
 search_value TEXT NOT NULL CHECK (length(search_value)>0),
 name_kind TEXT NOT NULL CHECK (name_kind IN ('first_name','middle_name','surname')),
 status TEXT NOT NULL CHECK (status IN ('active','inactive','deprecated')),
 runtime_mode TEXT NOT NULL CHECK (runtime_mode ~ '^[a-z][a-z0-9_-]{0,63}$'),
 schema_version INTEGER NOT NULL CHECK (schema_version>=1),
 created_at TIMESTAMPTZ NOT NULL,
 source_reference TEXT NULL CHECK (source_reference IS NULL OR source_reference ~ '^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$'),
 language_refs JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(language_refs)='array'),
 country_refs JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(country_refs)='array'),
 region_refs JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(region_refs)='array'),
 culture_refs JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(culture_refs)='array'),
 script_code TEXT NULL CHECK (script_code IS NULL OR length(script_code) BETWEEN 1 AND 32),
 attributes JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(attributes)='object'),
 CONSTRAINT uq_canonical_name_identity UNIQUE(runtime_mode,name_kind,search_value)
);
CREATE INDEX IF NOT EXISTS ix_canonical_name_runtime_kind_search ON reference.canonical_name(runtime_mode,name_kind,search_value);
CREATE INDEX IF NOT EXISTS ix_canonical_name_status ON reference.canonical_name(status);
COMMIT;
