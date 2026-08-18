BEGIN;
DROP FUNCTION IF EXISTS geography.nngla_reserve_title_reference(text,text,text,text,text);
DROP TABLE IF EXISTS geography.nngla_state_land_candidate_record;
DROP TABLE IF EXISTS geography.nngla_title_issuance_candidate;
DROP TABLE IF EXISTS geography.nngla_title_reference_reservation;
DROP TABLE IF EXISTS geography.nngla_title_number_series;
COMMIT;
