BEGIN;
DROP TABLE IF EXISTS reference.name_authority_projection_checkpoint;
DROP TABLE IF EXISTS reference.name_authority_read_model;
DROP TABLE IF EXISTS reference.name_generation_result;
DROP TABLE IF EXISTS reference.name_generation_checkpoint;
DROP TABLE IF EXISTS reference.name_generation_batch;
DROP TABLE IF EXISTS reference.name_generation_source_member;
DROP TABLE IF EXISTS reference.name_generation_source_snapshot;
COMMIT;
