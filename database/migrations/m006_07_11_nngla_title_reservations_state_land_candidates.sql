BEGIN;
-- P006.7.11.7.13 additive title-reference/state-land candidate contract.
-- Host/domain agnostic and additive around locked title/state-land tables.
CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.nngla_title_number_series (
    series_id text PRIMARY KEY CHECK (series_id='titleseries:nngla:sovereign'),
    title_id_pattern text NOT NULL,
    allocation_scope text NOT NULL CHECK (allocation_scope='SOVEREIGN_GLOBAL'),
    prefix text NOT NULL CHECK (prefix='NG-TTL-'),
    sequence_width integer NOT NULL CHECK (sequence_width=6),
    minimum_sequence bigint NOT NULL CHECK (minimum_sequence > 0),
    next_sequence bigint NOT NULL CHECK (next_sequence > 0),
    sequence_semantics text NOT NULL CHECK (sequence_semantics='MONOTONIC_NO_REUSE'),
    issuing_authority_code text NOT NULL CHECK (issuing_authority_code='NNGLA'),
    status text NOT NULL
);

CREATE TABLE geography.nngla_title_reference_reservation (
    reservation_id text PRIMARY KEY CHECK (reservation_id LIKE 'titleres:nngla:%'),
    series_id text NOT NULL REFERENCES geography.nngla_title_number_series(series_id),
    reserved_title_id text NOT NULL CHECK (reserved_title_id ~ '^NG-TTL-[0-9]{6}$'),
    parcel_id text,
    holder_reference text,
    idempotency_key text NOT NULL,
    reservation_status text NOT NULL CHECK (reservation_status='TITLE_NUMBER_RESERVED'),
    legal_title_exists boolean NOT NULL DEFAULT false CHECK (legal_title_exists=false),
    authority_runtime_mode text NOT NULL CHECK (authority_runtime_mode='production'),
    reserved_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (reserved_title_id),
    UNIQUE (series_id, idempotency_key)
);

CREATE TABLE geography.nngla_title_issuance_candidate (
    issuance_candidate_id text PRIMARY KEY CHECK (issuance_candidate_id LIKE 'titleissuecand:nngla:%'),
    reservation_id text NOT NULL REFERENCES geography.nngla_title_reference_reservation(reservation_id),
    title_id text NOT NULL CHECK (title_id ~ '^NG-TTL-[0-9]{6}$'),
    parcel_id text NOT NULL CHECK (parcel_id ~ '^NV-[0-9]{2}-[0-9]{3}-[0-9]{4,}$'),
    title_type_code text NOT NULL,
    tenure_type_code text NOT NULL,
    holder_reference text NOT NULL,
    prior_title_id text CHECK (prior_title_id IS NULL OR prior_title_id ~ '^NG-TTL-[0-9]{6}$'),
    issuance_status text NOT NULL CHECK (issuance_status='ISSUANCE_CANDIDATE'),
    runtime_mode text NOT NULL CHECK (runtime_mode='production'),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (reservation_id),
    UNIQUE (title_id)
);

CREATE TABLE geography.nngla_state_land_candidate_record (
    state_land_candidate_id text PRIMARY KEY CHECK (state_land_candidate_id LIKE 'statelandcand:nngla:%'),
    parcel_id text NOT NULL CHECK (parcel_id ~ '^NV-[0-9]{2}-[0-9]{3}-[0-9]{4,}$'),
    state_land_category_code text NOT NULL,
    administrative_area_id text,
    candidate_status text NOT NULL CHECK (candidate_status='CANDIDATE'),
    legal_state_land_exists boolean NOT NULL DEFAULT false CHECK (legal_state_land_exists=false),
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION geography.nngla_reserve_title_reference(
    p_series_id text,
    p_reservation_id text,
    p_idempotency_key text,
    p_parcel_id text DEFAULT NULL,
    p_holder_reference text DEFAULT NULL
) RETURNS text
LANGUAGE plpgsql AS $$
DECLARE
    v_series geography.nngla_title_number_series%ROWTYPE;
    v_existing text;
    v_reserved_title_id text;
BEGIN
    SELECT * INTO v_series
      FROM geography.nngla_title_number_series
     WHERE series_id=p_series_id AND status='ACTIVE'
     FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'unknown/inactive title series %', p_series_id; END IF;

    SELECT reserved_title_id INTO v_existing
      FROM geography.nngla_title_reference_reservation
     WHERE series_id=p_series_id AND idempotency_key=p_idempotency_key;
    IF FOUND THEN RETURN v_existing; END IF;

    IF v_series.next_sequence > 999999 THEN RAISE EXCEPTION 'NG-TTL six-digit namespace exhausted'; END IF;
    v_reserved_title_id := v_series.prefix || lpad(v_series.next_sequence::text, v_series.sequence_width, '0');
    INSERT INTO geography.nngla_title_reference_reservation(
        reservation_id, series_id, reserved_title_id, parcel_id, holder_reference,
        idempotency_key, reservation_status, legal_title_exists, authority_runtime_mode
    ) VALUES (
        p_reservation_id, p_series_id, v_reserved_title_id, p_parcel_id, p_holder_reference,
        p_idempotency_key, 'TITLE_NUMBER_RESERVED', false, 'production'
    );
    UPDATE geography.nngla_title_number_series
       SET next_sequence = next_sequence + 1
     WHERE series_id=p_series_id;
    RETURN v_reserved_title_id;
END;
$$;
COMMIT;
