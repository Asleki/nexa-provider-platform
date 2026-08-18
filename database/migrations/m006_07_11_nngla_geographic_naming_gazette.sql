BEGIN;

-- P006.7.11.7.17 additive data-driven geographic naming/gazette operational contract.
-- Existing geography.nngla_geographic_name and geography.nngla_name_assignment remain canonical and unaltered.
CREATE SCHEMA IF NOT EXISTS geography;
CREATE TABLE geography.nngla_name_family_policy (
  name_family_code text PRIMARY KEY,
  id_prefix text NOT NULL,
  sequence_width integer NOT NULL CHECK(sequence_width=6),
  next_sequence bigint NOT NULL CHECK(next_sequence>0),
  default_scope_type text NOT NULL,
  normalization_policy text NOT NULL,
  allocation_authority_runtime text NOT NULL CHECK(allocation_authority_runtime='production'),
  status text NOT NULL CHECK(status='ACTIVE')
);
CREATE TABLE geography.nngla_name_id_reservation (
  reservation_id text PRIMARY KEY CHECK(reservation_id LIKE 'nameres:nngla:%'),
  name_family_code text NOT NULL REFERENCES geography.nngla_name_family_policy(name_family_code),
  normalized_match_key text NOT NULL,
  scope_type text NOT NULL,
  scope_reference text NOT NULL,
  name_id text NOT NULL UNIQUE CHECK(name_id ~ '^NG-NAM-[A-Z]{3}-[0-9]{6}$'),
  idempotency_key text NOT NULL,
  authority_runtime_mode text NOT NULL CHECK(authority_runtime_mode='production'),
  reservation_status text NOT NULL CHECK(reservation_status='RESERVED'),
  reserved_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(name_family_code,idempotency_key),
  UNIQUE(name_family_code,normalized_match_key,scope_type,scope_reference)
);
CREATE TABLE geography.nngla_name_lifecycle_event (
  lifecycle_event_id text PRIMARY KEY CHECK(lifecycle_event_id LIKE 'namelifecycle:nngla:%'),
  name_id text NOT NULL CHECK(name_id ~ '^NG-NAM-[A-Z]{3}-[0-9]{6}$'),
  from_status text NOT NULL,
  to_status text NOT NULL,
  effective_on date NOT NULL,
  approval_reference text,
  gazette_reference text,
  authority_runtime_mode text NOT NULL CHECK(authority_runtime_mode='production'),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK(from_status<>to_status)
);
CREATE TABLE geography.nngla_gazette_action_candidate (
  candidate_id text PRIMARY KEY CHECK(candidate_id LIKE 'gazettecand:nngla:%'),
  subject_id text NOT NULL,
  name_id text NOT NULL CHECK(name_id ~ '^NG-NAM-[A-Z]{3}-[0-9]{6}$'),
  gazette_action_code text NOT NULL,
  prior_name_id text,
  proposed_effective_on date,
  proposer_reference text,
  decision_reference text,
  runtime_mode text NOT NULL CHECK(runtime_mode IN('simulation','production')),
  candidate_status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE geography.nngla_name_assignment_result (
  result_id text PRIMARY KEY CHECK(result_id LIKE 'nameasnresult:nngla:%'),
  assignment_candidate_id text NOT NULL,
  subject_id text NOT NULL,
  name_id text NOT NULL CHECK(name_id ~ '^NG-NAM-[A-Z]{3}-[0-9]{6}$'),
  assignment_role text NOT NULL CHECK(assignment_role IN('PRIMARY','ALTERNATE','HISTORIC','NICKNAME')),
  source_assignment_status text NOT NULL,
  result_status text NOT NULL,
  official_effect boolean NOT NULL,
  gazette_reference text,
  decided_at timestamptz NOT NULL DEFAULT now(),
  CHECK(NOT official_effect OR gazette_reference IS NOT NULL)
);
CREATE OR REPLACE FUNCTION geography.nngla_reserve_name_id(p_family_code text,p_reservation_id text,p_normalized_match_key text,p_scope_type text,p_scope_reference text,p_idempotency_key text) RETURNS text
LANGUAGE plpgsql AS $$
DECLARE v_family geography.nngla_name_family_policy%ROWTYPE; v_existing text; v_name_id text; v_max bigint;
BEGIN
 SELECT name_id INTO v_existing FROM geography.nngla_name_id_reservation WHERE name_family_code=p_family_code AND idempotency_key=p_idempotency_key; IF FOUND THEN RETURN v_existing; END IF;
 SELECT * INTO v_family FROM geography.nngla_name_family_policy WHERE name_family_code=p_family_code AND status='ACTIVE' FOR UPDATE; IF NOT FOUND THEN RAISE EXCEPTION 'unknown/inactive name family %',p_family_code; END IF;
 SELECT COALESCE(MAX(substring(name_id from '[0-9]{6}$')::bigint),0) INTO v_max FROM geography.nngla_geographic_name WHERE name_id LIKE v_family.id_prefix||'%';
 IF v_family.next_sequence<=v_max THEN UPDATE geography.nngla_name_family_policy SET next_sequence=v_max+1 WHERE name_family_code=p_family_code RETURNING * INTO v_family; END IF;
 IF v_family.next_sequence>999999 THEN RAISE EXCEPTION 'name family namespace exhausted: %',p_family_code; END IF;
 v_name_id:=v_family.id_prefix||lpad(v_family.next_sequence::text,v_family.sequence_width,'0');
 INSERT INTO geography.nngla_name_id_reservation(reservation_id,name_family_code,normalized_match_key,scope_type,scope_reference,name_id,idempotency_key,authority_runtime_mode,reservation_status) VALUES(p_reservation_id,p_family_code,p_normalized_match_key,p_scope_type,p_scope_reference,v_name_id,p_idempotency_key,'production','RESERVED');
 UPDATE geography.nngla_name_family_policy SET next_sequence=next_sequence+1 WHERE name_family_code=p_family_code; RETURN v_name_id;
END; $$;
COMMIT;
