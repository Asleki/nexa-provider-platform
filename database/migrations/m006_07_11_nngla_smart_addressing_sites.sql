BEGIN;
-- P006.7.11.7.11-.12 additive smart-addressing/site contract.
-- Host/domain agnostic. This schema contains no deployment-host binding.
-- It extends locked road/address/site tables through new relations; it does not rewrite them.
CREATE SCHEMA IF NOT EXISTS geography;


CREATE SEQUENCE geography.nngla_address_id_sequence START WITH 1 INCREMENT BY 1 NO CYCLE;

CREATE TABLE geography.nngla_road_segment (
    road_segment_id text PRIMARY KEY CHECK (road_segment_id LIKE 'roadseg:nngla:%'),
    road_id text NOT NULL CHECK (road_id ~ '^NG-RD-[0-9]{6}$'),
    source_road_candidate_id text NOT NULL CHECK (source_road_candidate_id ~ '^NG-RD-CAND-[0-9]{6}$'),
    segment_sequence integer NOT NULL CHECK (segment_sequence > 0),
    segment_role text NOT NULL,
    geometry_id text CHECK (geometry_id IS NULL OR geometry_id ~ '^NG-GEO-[0-9]{6}$'),
    geometry_status text NOT NULL,
    addressing_scope_eligible boolean NOT NULL,
    runtime_effect_scope text NOT NULL,
    UNIQUE (road_id, segment_sequence)
);

CREATE TABLE geography.nngla_road_frontage (
    frontage_id text PRIMARY KEY CHECK (frontage_id LIKE 'frontage:nngla:%'),
    site_id text NOT NULL,
    road_id text NOT NULL CHECK (road_id ~ '^NG-RD-[0-9]{6}$'),
    road_segment_id text NOT NULL REFERENCES geography.nngla_road_segment(road_segment_id),
    frontage_role text NOT NULL,
    access_status text NOT NULL,
    qualification_status text NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE geography.nngla_address_series (
    series_id text PRIMARY KEY CHECK (series_id LIKE 'addrseries:nngla:%'),
    road_id text NOT NULL CHECK (road_id ~ '^NG-RD-[0-9]{6}$'),
    road_segment_id text REFERENCES geography.nngla_road_segment(road_segment_id),
    policy_code text NOT NULL,
    scope_type text NOT NULL,
    scope_reference text NOT NULL,
    start_number bigint NOT NULL CHECK (start_number >= 0),
    sequence_step bigint NOT NULL CHECK (sequence_step > 0),
    next_sequence bigint NOT NULL CHECK (next_sequence >= 0),
    number_format_rule_code text NOT NULL,
    side_rule text NOT NULL,
    allow_suffix boolean NOT NULL,
    status text NOT NULL,
    UNIQUE (road_id, scope_type, scope_reference, side_rule)
);

CREATE TABLE geography.nngla_address_number_reservation (
    reservation_id text PRIMARY KEY CHECK (reservation_id LIKE 'addrres:nngla:%'),
    series_id text NOT NULL REFERENCES geography.nngla_address_series(series_id),
    site_id text NOT NULL,
    reserved_address_id text NOT NULL CHECK (reserved_address_id ~ '^NG-ADR-[0-9]{6}$'),
    display_address_number text NOT NULL,
    normalized_number_key text NOT NULL,
    idempotency_key text NOT NULL,
    reservation_status text NOT NULL,
    canonical_address_created boolean NOT NULL DEFAULT false,
    authority_runtime_mode text NOT NULL CHECK (authority_runtime_mode='production'),
    reserved_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (series_id, normalized_number_key),
    UNIQUE (reserved_address_id),
    UNIQUE (series_id, idempotency_key)
);

CREATE TABLE geography.nngla_structure_site_reference (
    structure_site_reference_id text PRIMARY KEY CHECK (structure_site_reference_id LIKE 'structsite:nngla:%'),
    site_id text NOT NULL,
    structure_reference_type_code text NOT NULL,
    external_registry_code text NOT NULL,
    external_structure_reference text NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    reference_status text NOT NULL,
    UNIQUE (site_id, external_registry_code, external_structure_reference, effective_from),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

CREATE TABLE geography.nngla_site_address_assignment (
    assignment_id text PRIMARY KEY CHECK (assignment_id LIKE 'siteaddr:nngla:%'),
    site_id text NOT NULL,
    reservation_id text NOT NULL REFERENCES geography.nngla_address_number_reservation(reservation_id),
    address_id text NOT NULL CHECK (address_id ~ '^NG-ADR-[0-9]{6}$'),
    assignment_status text NOT NULL,
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    effective_from date NOT NULL,
    effective_to date,
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- Contract function: row-level locking serializes allocation within one series while
-- independent series can allocate concurrently. The unique key is scoped by series,
-- so the same visible number may exist in different legitimate scopes.
CREATE OR REPLACE FUNCTION geography.nngla_reserve_address_number(
    p_series_id text,
    p_site_id text,
    p_reservation_id text,
    p_idempotency_key text
) RETURNS TABLE(reservation_id text, display_address_number text)
LANGUAGE plpgsql AS $$
DECLARE
    v_series geography.nngla_address_series%ROWTYPE;
    v_number bigint;
    v_address_sequence bigint;
    v_reserved_address_id text;
BEGIN
    SELECT * INTO v_series
      FROM geography.nngla_address_series
     WHERE series_id = p_series_id AND status = 'ACTIVE'
     FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'unknown/inactive address series %', p_series_id; END IF;

    SELECT r.reservation_id, r.display_address_number
      INTO reservation_id, display_address_number
      FROM geography.nngla_address_number_reservation r
     WHERE r.series_id = p_series_id AND r.idempotency_key = p_idempotency_key;
    IF FOUND THEN RETURN NEXT; RETURN; END IF;

    v_number := v_series.next_sequence;
    UPDATE geography.nngla_address_series
       SET next_sequence = next_sequence + sequence_step
     WHERE series_id = p_series_id;

    v_address_sequence := nextval('geography.nngla_address_id_sequence');
    IF v_address_sequence > 999999 THEN RAISE EXCEPTION 'NG-ADR six-digit namespace exhausted'; END IF;
    v_reserved_address_id := 'NG-ADR-' || lpad(v_address_sequence::text, 6, '0');

    INSERT INTO geography.nngla_address_number_reservation(
        reservation_id, series_id, site_id, reserved_address_id,
        display_address_number, normalized_number_key, idempotency_key,
        reservation_status, canonical_address_created, authority_runtime_mode
    ) VALUES (
        p_reservation_id, p_series_id, p_site_id, v_reserved_address_id,
        v_number::text, upper(v_number::text), p_idempotency_key,
        'RESERVED', false, 'production'
    );
    reservation_id := p_reservation_id;
    display_address_number := v_number::text;
    RETURN NEXT;
END;
$$;
COMMIT;
