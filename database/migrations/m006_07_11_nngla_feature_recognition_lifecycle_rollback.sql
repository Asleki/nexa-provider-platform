BEGIN;
DROP FUNCTION IF EXISTS geography.nngla_reserve_feature_id(text,text,text);
DROP TABLE IF EXISTS geography.nngla_feature_lifecycle_event;
DROP TABLE IF EXISTS geography.nngla_feature_recognition_result;
DROP TABLE IF EXISTS geography.nngla_feature_candidate_observation;
DROP TABLE IF EXISTS geography.nngla_feature_runtime_candidate;
DROP TABLE IF EXISTS geography.nngla_feature_id_reservation;
DROP TABLE IF EXISTS geography.nngla_feature_id_allocator;
COMMIT;
