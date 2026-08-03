BEGIN;
DROP TABLE IF EXISTS reference.name_context_relationship;
DROP TABLE IF EXISTS reference.name_orthography_profile;
DROP TABLE IF EXISTS reference.reference_authority_record;
DROP SEQUENCE IF EXISTS reference.origin_code_seq;
DROP SEQUENCE IF EXISTS reference.language_code_seq;
DROP SEQUENCE IF EXISTS reference.tribe_code_seq;
COMMIT;
