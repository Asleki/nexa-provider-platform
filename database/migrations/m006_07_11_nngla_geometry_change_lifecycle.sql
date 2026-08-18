BEGIN;
-- P006.7.11.7.15 additive geometry-change/survey/physical-state lifecycle contract.
-- Historical geometry remains immutable; new geometry versions receive new NG-GEO identities.
CREATE SCHEMA IF NOT EXISTS geography;
CREATE TABLE geography.nngla_geometry_id_allocator (allocator_key text PRIMARY KEY CHECK (allocator_key='NG-GEO'), next_sequence bigint NOT NULL CHECK (next_sequence>0));
CREATE TABLE geography.nngla_geometry_id_reservation (reservation_id text PRIMARY KEY, geometry_id text NOT NULL UNIQUE CHECK (geometry_id ~ '^NG-GEO-[0-9]{6}$'), idempotency_key text NOT NULL UNIQUE, subject_id text NOT NULL, geometry_role_code text NOT NULL, authority_runtime_mode text NOT NULL CHECK(authority_runtime_mode='production'), reserved_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE geography.nngla_geometry_change_candidate (change_candidate_id text PRIMARY KEY, subject_type text NOT NULL, subject_id text NOT NULL, geometry_role_code text NOT NULL, current_geometry_id text NOT NULL CHECK(current_geometry_id ~ '^NG-GEO-[0-9]{6}$'), proposed_geometry_reference text NOT NULL, reserved_geometry_id text CHECK(reserved_geometry_id IS NULL OR reserved_geometry_id ~ '^NG-GEO-[0-9]{6}$'), change_reason_code text NOT NULL, change_nature text NOT NULL, crs_code text NOT NULL, survey_id text, effective_on date, source_reference text NOT NULL, runtime_mode text NOT NULL CHECK(runtime_mode IN('simulation','production')), status text NOT NULL);
CREATE TABLE geography.nngla_geometry_supersession_link (link_id text PRIMARY KEY, subject_id text NOT NULL, geometry_role_code text NOT NULL, predecessor_geometry_id text NOT NULL CHECK(predecessor_geometry_id ~ '^NG-GEO-[0-9]{6}$'), successor_geometry_id text NOT NULL CHECK(successor_geometry_id ~ '^NG-GEO-[0-9]{6}$'), effective_on date NOT NULL, change_reason_code text NOT NULL, survey_id text, authority_runtime_mode text NOT NULL CHECK(authority_runtime_mode='production'), source_reference text NOT NULL, UNIQUE(predecessor_geometry_id,successor_geometry_id), CHECK(predecessor_geometry_id<>successor_geometry_id));
CREATE TABLE geography.nngla_survey_observation_candidate (observation_id text PRIMARY KEY, survey_id text NOT NULL CHECK(survey_id ~ '^NG-SRV-[0-9]{6}$'), subject_id text NOT NULL, observed_at timestamptz NOT NULL, longitude double precision NOT NULL CHECK(longitude BETWEEN -180 AND 180), latitude double precision NOT NULL CHECK(latitude BETWEEN -90 AND 90), elevation_m double precision, crs_code text NOT NULL, accuracy_class_code text NOT NULL, instrument_record_reference text, surveyor_approval_reference text, source_reference text NOT NULL, qualification_status text NOT NULL);
CREATE TABLE geography.nngla_physical_state_change_candidate (state_change_id text PRIMARY KEY, subject_type text NOT NULL, subject_id text NOT NULL, prior_state text NOT NULL, proposed_state text NOT NULL, geometry_change_candidate_id text, effective_on date, source_reference text NOT NULL, runtime_mode text NOT NULL CHECK(runtime_mode IN('simulation','production')), status text NOT NULL, CHECK(prior_state<>proposed_state));
CREATE OR REPLACE FUNCTION geography.nngla_reserve_geometry_id(p_reservation_id text,p_idempotency_key text,p_subject_id text,p_geometry_role_code text) RETURNS text LANGUAGE plpgsql AS $$
DECLARE v_next bigint; v_existing text; v_id text;
BEGIN
 SELECT geometry_id INTO v_existing FROM geography.nngla_geometry_id_reservation WHERE idempotency_key=p_idempotency_key; IF FOUND THEN RETURN v_existing; END IF;
 INSERT INTO geography.nngla_geometry_id_allocator(allocator_key,next_sequence)
 SELECT 'NG-GEO',COALESCE(MAX(n),0)+1 FROM (
   SELECT substring(geometry_id from '[0-9]{6}$')::bigint n FROM geography.nngla_geometry_version
   UNION ALL SELECT substring(geometry_id from '[0-9]{6}$')::bigint FROM geography.nngla_geometry_authority_record
 ) q ON CONFLICT (allocator_key) DO NOTHING;
 SELECT next_sequence INTO v_next FROM geography.nngla_geometry_id_allocator WHERE allocator_key='NG-GEO' FOR UPDATE;
 IF v_next>999999 THEN RAISE EXCEPTION 'NG-GEO six-digit namespace exhausted'; END IF;
 v_id:='NG-GEO-'||lpad(v_next::text,6,'0');
 INSERT INTO geography.nngla_geometry_id_reservation(reservation_id,geometry_id,idempotency_key,subject_id,geometry_role_code,authority_runtime_mode) VALUES(p_reservation_id,v_id,p_idempotency_key,p_subject_id,p_geometry_role_code,'production');
 UPDATE geography.nngla_geometry_id_allocator SET next_sequence=next_sequence+1 WHERE allocator_key='NG-GEO'; RETURN v_id;
END; $$;
COMMIT;
