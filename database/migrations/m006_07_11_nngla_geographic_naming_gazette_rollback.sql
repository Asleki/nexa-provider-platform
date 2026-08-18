BEGIN;
DROP FUNCTION IF EXISTS geography.nngla_reserve_name_id(text,text,text,text,text,text);
DROP TABLE IF EXISTS geography.nngla_name_assignment_result;
DROP TABLE IF EXISTS geography.nngla_gazette_action_candidate;
DROP TABLE IF EXISTS geography.nngla_name_lifecycle_event;
DROP TABLE IF EXISTS geography.nngla_name_id_reservation;
DROP TABLE IF EXISTS geography.nngla_name_family_policy;
COMMIT;
