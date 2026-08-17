
-- P006.7.11.7.16 additive generic physical-feature recognition/lifecycle contract.
-- Extends around locked geography.nngla_spatial_feature; does not rewrite existing canonical feature identities.
CREATE SCHEMA IF NOT EXISTS geography;
CREATE TABLE geography.nngla_feature_id_allocator (
  allocator_key text PRIMARY KEY CHECK (allocator_key='NG-FEAT'),
  next_sequence bigint NOT NULL CHECK (next_sequence>0)
);
CREATE TABLE geography.nngla_feature_id_reservation (
  reservation_id text PRIMARY KEY CHECK (reservation_id LIKE 'featres:nngla:%'),
  candidate_id text NOT NULL CHECK (candidate_id LIKE 'featcand:nngla:%'),
  feature_id text NOT NULL UNIQUE CHECK (feature_id ~ '^NG-FEAT-[0-9]{6}$'),
  idempotency_key text NOT NULL UNIQUE,
  authority_runtime_mode text NOT NULL CHECK (authority_runtime_mode='production'),
  reserved_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(candidate_id)
);
CREATE TABLE geography.nngla_feature_runtime_candidate (
  candidate_id text PRIMARY KEY CHECK(candidate_id LIKE 'featcand:nngla:%'),
  source_feature_id text NOT NULL,
  feature_type_code text NOT NULL,
  source_dataset_id text NOT NULL,
  source_record_reference text NOT NULL,
  physical_origin_class text NOT NULL CHECK(physical_origin_class='NATURAL'),
  geometry_reference text,
  geometry_status text NOT NULL,
  qualification_status text NOT NULL,
  existing_canonical_feature_id text CHECK(existing_canonical_feature_id IS NULL OR existing_canonical_feature_id ~ '^NG-FEAT-[0-9]{6}$'),
  runtime_mode text NOT NULL CHECK(runtime_mode IN('simulation','production')),
  runtime_effect_scope text NOT NULL,
  candidate_status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(source_dataset_id,source_feature_id,feature_type_code,runtime_mode)
);
CREATE TABLE geography.nngla_feature_candidate_observation (
  link_id text PRIMARY KEY CHECK(link_id LIKE 'featobs:nngla:%'),
  candidate_id text NOT NULL REFERENCES geography.nngla_feature_runtime_candidate(candidate_id),
  observation_type text NOT NULL,
  source_dataset_id text NOT NULL,
  source_record_id text NOT NULL,
  source_path_reference text,
  source_sha256 text CHECK(source_sha256 IS NULL OR source_sha256 ~ '^[0-9a-f]{64}$'),
  evidence_status text NOT NULL,
  UNIQUE(candidate_id,source_dataset_id,source_record_id,observation_type)
);
CREATE TABLE geography.nngla_feature_recognition_result (
  result_id text PRIMARY KEY CHECK(result_id LIKE 'featresult:nngla:%'),
  candidate_id text NOT NULL REFERENCES geography.nngla_feature_runtime_candidate(candidate_id),
  feature_type_code text NOT NULL,
  disposition text NOT NULL CHECK(disposition IN('REUSE_CANONICAL','RECOGNIZE_NEW','DEFER','REJECT')),
  canonical_feature_id text CHECK(canonical_feature_id IS NULL OR canonical_feature_id ~ '^NG-FEAT-[0-9]{6}$'),
  qualified boolean NOT NULL,
  production_authority_required boolean NOT NULL,
  geometry_ready boolean NOT NULL,
  history_preserved boolean NOT NULL CHECK(history_preserved=true),
  result_status text NOT NULL,
  findings text NOT NULL,
  decided_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE geography.nngla_feature_lifecycle_event (
  lifecycle_event_id text PRIMARY KEY CHECK(lifecycle_event_id LIKE 'featlifecycle:nngla:%'),
  feature_id text NOT NULL CHECK(feature_id ~ '^NG-FEAT-[0-9]{6}$'),
  from_status text NOT NULL,
  to_status text NOT NULL,
  effective_on date NOT NULL,
  authority_runtime_mode text NOT NULL CHECK(authority_runtime_mode='production'),
  reason_reference text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK(from_status<>to_status)
);
CREATE OR REPLACE FUNCTION geography.nngla_reserve_feature_id(p_reservation_id text,p_candidate_id text,p_idempotency_key text) RETURNS text
LANGUAGE plpgsql AS $$
DECLARE v_next bigint; v_existing text; v_id text;
BEGIN
 SELECT feature_id INTO v_existing FROM geography.nngla_feature_id_reservation WHERE idempotency_key=p_idempotency_key; IF FOUND THEN RETURN v_existing; END IF;
 INSERT INTO geography.nngla_feature_id_allocator(allocator_key,next_sequence)
 SELECT 'NG-FEAT',COALESCE(MAX(n),0)+1 FROM (
   SELECT substring(feature_id from '[0-9]{6}$')::bigint n FROM geography.nngla_spatial_feature WHERE feature_id ~ '^NG-FEAT-[0-9]{6}$'
   UNION ALL SELECT substring(canonical_id from '[0-9]{6}$')::bigint FROM geography.nngla_canonical_crosswalk WHERE canonical_id ~ '^NG-FEAT-[0-9]{6}$'
   UNION ALL SELECT substring(feature_id from '[0-9]{6}$')::bigint FROM geography.nngla_feature_id_reservation
 ) q ON CONFLICT (allocator_key) DO NOTHING;
 SELECT next_sequence INTO v_next FROM geography.nngla_feature_id_allocator WHERE allocator_key='NG-FEAT' FOR UPDATE;
 IF v_next>999999 THEN RAISE EXCEPTION 'NG-FEAT six-digit namespace exhausted'; END IF;
 v_id:='NG-FEAT-'||lpad(v_next::text,6,'0');
 INSERT INTO geography.nngla_feature_id_reservation(reservation_id,candidate_id,feature_id,idempotency_key,authority_runtime_mode) VALUES(p_reservation_id,p_candidate_id,v_id,p_idempotency_key,'production');
 UPDATE geography.nngla_feature_id_allocator SET next_sequence=next_sequence+1 WHERE allocator_key='NG-FEAT'; RETURN v_id;
END; $$;
