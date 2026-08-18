BEGIN;
DROP FUNCTION IF EXISTS geography.nngla_reserve_geometry_id(text,text,text,text);
DROP TABLE IF EXISTS geography.nngla_physical_state_change_candidate;
DROP TABLE IF EXISTS geography.nngla_survey_observation_candidate;
DROP TABLE IF EXISTS geography.nngla_geometry_supersession_link;
DROP TABLE IF EXISTS geography.nngla_geometry_change_candidate;
DROP TABLE IF EXISTS geography.nngla_geometry_id_reservation;
DROP TABLE IF EXISTS geography.nngla_geometry_id_allocator;
COMMIT;
