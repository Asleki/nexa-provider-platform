BEGIN;
-- P006.7.11.7.14 additive allocation-concurrency/recovery contract.
-- Host/domain agnostic; extends Bundle 17G without altering locked parcel tables.
CREATE SCHEMA IF NOT EXISTS geography;
CREATE TABLE geography.nngla_parcel_reference_series (
  series_id text PRIMARY KEY,
  cadastral_zone text NOT NULL CHECK (cadastral_zone ~ '^[0-9]{2}$'),
  cadastral_series text NOT NULL CHECK (cadastral_series ~ '^[0-9]{3}$'),
  next_sequence bigint NOT NULL CHECK (next_sequence > 0),
  sequence_semantics text NOT NULL CHECK (sequence_semantics='MONOTONIC_NO_REUSE'),
  status text NOT NULL CHECK (status='ACTIVE'),
  UNIQUE(cadastral_zone,cadastral_series)
);
CREATE TABLE geography.nngla_parcel_reference_reservation (
  reservation_id text PRIMARY KEY CHECK (reservation_id LIKE 'parcelres:nngla:%'),
  series_id text NOT NULL REFERENCES geography.nngla_parcel_reference_series(series_id),
  parcel_candidate_id text NOT NULL CHECK (parcel_candidate_id LIKE 'parcelcand:nngla:%'),
  parcel_id text NOT NULL CHECK (parcel_id ~ '^NV-[0-9]{2}-[0-9]{3}-[0-9]{4,}$'),
  idempotency_key text NOT NULL,
  reservation_status text NOT NULL CHECK (reservation_status='RESERVED'),
  legal_effect boolean NOT NULL DEFAULT false CHECK (legal_effect=false),
  canonical_parcel_registered boolean NOT NULL DEFAULT false CHECK (canonical_parcel_registered=false),
  authority_runtime_mode text NOT NULL CHECK (authority_runtime_mode='production'),
  reserved_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (parcel_id),
  UNIQUE (series_id, idempotency_key),
  UNIQUE (parcel_candidate_id)
);
CREATE OR REPLACE FUNCTION geography.nngla_reserve_parcel_reference(p_series_id text,p_reservation_id text,p_parcel_candidate_id text,p_idempotency_key text) RETURNS text
LANGUAGE plpgsql AS $$
DECLARE v_series geography.nngla_parcel_reference_series%ROWTYPE; v_existing text; v_parcel_id text;
BEGIN
 SELECT * INTO v_series FROM geography.nngla_parcel_reference_series WHERE series_id=p_series_id AND status='ACTIVE' FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'unknown/inactive parcel series %',p_series_id; END IF;
 SELECT parcel_id INTO v_existing FROM geography.nngla_parcel_reference_reservation WHERE series_id=p_series_id AND idempotency_key=p_idempotency_key;
 IF FOUND THEN RETURN v_existing; END IF;
 v_parcel_id := 'NV-'||v_series.cadastral_zone||'-'||v_series.cadastral_series||'-'||lpad(v_series.next_sequence::text,4,'0');
 INSERT INTO geography.nngla_parcel_reference_reservation(reservation_id,series_id,parcel_candidate_id,parcel_id,idempotency_key,reservation_status,legal_effect,canonical_parcel_registered,authority_runtime_mode)
 VALUES(p_reservation_id,p_series_id,p_parcel_candidate_id,v_parcel_id,p_idempotency_key,'RESERVED',false,false,'production');
 UPDATE geography.nngla_parcel_reference_series SET next_sequence=next_sequence+1 WHERE series_id=p_series_id;
 RETURN v_parcel_id;
END; $$;
COMMIT;
