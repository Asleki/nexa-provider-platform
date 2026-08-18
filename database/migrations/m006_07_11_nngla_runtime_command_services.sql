BEGIN;
-- P006.7.11.7.18 additive NNGLA runtime command durability contract.
-- Does not alter locked canonical domain tables. CSV remains bootstrap/config only.
CREATE SCHEMA IF NOT EXISTS geography;

CREATE TABLE geography.nngla_runtime_command_receipt (
    receipt_id text PRIMARY KEY CHECK (receipt_id LIKE 'runtime-command:nngla:%'),
    command_code text NOT NULL,
    command_version integer NOT NULL CHECK (command_version > 0),
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    effect_scope text NOT NULL,
    principal_id text NOT NULL,
    idempotency_key text NOT NULL,
    request_fingerprint text NOT NULL CHECK (request_fingerprint ~ '^[0-9a-f]{64}$'),
    status text NOT NULL CHECK (status IN ('CLAIMED','COMPLETED','REJECTED')),
    reference_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    event_id text,
    audit_id text,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    UNIQUE (runtime_mode, command_code, idempotency_key)
);

CREATE TABLE geography.nngla_runtime_bulk_operation_receipt (
    bulk_operation_id text PRIMARY KEY CHECK (bulk_operation_id LIKE 'bulk:nngla:%'),
    bulk_policy_code text NOT NULL,
    runtime_mode text NOT NULL CHECK (runtime_mode IN ('simulation','production')),
    principal_id text NOT NULL,
    requested_count integer NOT NULL CHECK (requested_count >= 0),
    completed_count integer NOT NULL DEFAULT 0 CHECK (completed_count >= 0),
    failure_count integer NOT NULL DEFAULT 0 CHECK (failure_count >= 0),
    status text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz
);

CREATE OR REPLACE FUNCTION geography.nngla_claim_runtime_command(
    p_receipt_id text,
    p_command_code text,
    p_command_version integer,
    p_runtime_mode text,
    p_effect_scope text,
    p_principal_id text,
    p_idempotency_key text,
    p_request_fingerprint text
) RETURNS geography.nngla_runtime_command_receipt
LANGUAGE plpgsql
AS $$
DECLARE
    r geography.nngla_runtime_command_receipt;
BEGIN
    INSERT INTO geography.nngla_runtime_command_receipt(
        receipt_id,command_code,command_version,runtime_mode,effect_scope,
        principal_id,idempotency_key,request_fingerprint,status
    ) VALUES (
        p_receipt_id,p_command_code,p_command_version,p_runtime_mode,p_effect_scope,
        p_principal_id,p_idempotency_key,p_request_fingerprint,'CLAIMED'
    )
    ON CONFLICT (runtime_mode,command_code,idempotency_key) DO NOTHING;

    SELECT * INTO r
      FROM geography.nngla_runtime_command_receipt
     WHERE runtime_mode=p_runtime_mode AND command_code=p_command_code AND idempotency_key=p_idempotency_key
     FOR UPDATE;

    IF r.request_fingerprint <> p_request_fingerprint THEN
        RAISE EXCEPTION 'NNGLA runtime command idempotency conflict';
    END IF;
    RETURN r;
END;
$$;
COMMIT;
