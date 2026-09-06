BEGIN;

-- P006.UI.10.2.C / migration identity M006.10.2
-- Layered Admin Operator and immutable Developer review authority persistence.
--
-- This migration extends the existing nexilabs_auth authority only. It creates
-- no principal, Admin Operator, password verifier, Developer decision, session,
-- elevation, OTP, mail, delivery, or Enigma data.

-- Composite ownership target used by admin_operator so the bound Admin email
-- is proven to belong to the same principal rather than merely to exist.
ALTER TABLE nexilabs_auth.account_email
    ADD CONSTRAINT uq_nexilabs_auth_email_id_principal
    UNIQUE (email_id, principal_id);

CREATE TABLE nexilabs_auth.admin_operator (
    admin_operator_id text PRIMARY KEY,
    principal_id text NOT NULL
        REFERENCES nexilabs_auth.principal_account(principal_id),
    admin_developer_id text NOT NULL,
    admin_developer_id_key text NOT NULL,
    bound_admin_email_id text NOT NULL,
    admin_state text NOT NULL DEFAULT 'ACTIVE' CHECK (
        admin_state IN ('ACTIVE', 'DISABLED')
    ),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    disabled_at timestamptz NULL,
    bootstrap_reference text NULL,
    audit_reference text NOT NULL,
    CONSTRAINT uq_nexilabs_auth_admin_operator_id_principal
        UNIQUE (admin_operator_id, principal_id),
    CONSTRAINT fk_nexilabs_auth_admin_operator_email_owner
        FOREIGN KEY (bound_admin_email_id, principal_id)
        REFERENCES nexilabs_auth.account_email(email_id, principal_id),
    CONSTRAINT ck_nexilabs_auth_admin_operator_id_nonblank CHECK (
        length(btrim(admin_operator_id)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_admin_developer_id_nonblank CHECK (
        length(btrim(admin_developer_id)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_admin_developer_id_key_canonical CHECK (
        length(admin_developer_id_key) BETWEEN 1 AND 256
        AND admin_developer_id_key = lower(btrim(admin_developer_id))
    ),
    CONSTRAINT ck_nexilabs_auth_admin_operator_state_time CHECK (
        (admin_state = 'ACTIVE' AND disabled_at IS NULL)
        OR (admin_state = 'DISABLED' AND disabled_at IS NOT NULL)
    ),
    CONSTRAINT ck_nexilabs_auth_admin_bootstrap_reference_nonblank CHECK (
        bootstrap_reference IS NULL
        OR length(btrim(bootstrap_reference)) BETWEEN 1 AND 1024
    ),
    CONSTRAINT ck_nexilabs_auth_admin_audit_reference_nonblank CHECK (
        length(btrim(audit_reference)) BETWEEN 1 AND 1024
    )
);

CREATE UNIQUE INDEX ux_nexilabs_auth_admin_developer_id
    ON nexilabs_auth.admin_operator (admin_developer_id);
CREATE UNIQUE INDEX ux_nexilabs_auth_admin_developer_id_key
    ON nexilabs_auth.admin_operator (admin_developer_id_key);
CREATE UNIQUE INDEX ux_nexilabs_auth_active_admin_operator_principal
    ON nexilabs_auth.admin_operator (principal_id)
    WHERE admin_state = 'ACTIVE';
CREATE INDEX ix_nexilabs_auth_admin_operator_state
    ON nexilabs_auth.admin_operator (admin_state, created_at);
CREATE INDEX ix_nexilabs_auth_admin_operator_email
    ON nexilabs_auth.admin_operator (bound_admin_email_id, admin_state);

CREATE FUNCTION nexilabs_auth.validate_admin_operator_binding()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    principal_identity text;
    principal_state text;
    email_state text;
BEGIN
    -- Disabled rows remain durable historical authority. Revalidation is only
    -- required while a row claims ACTIVE Admin eligibility.
    IF NEW.admin_state <> 'ACTIVE' THEN
        RETURN NEW;
    END IF;

    SELECT identity_type, account_state
      INTO principal_identity, principal_state
      FROM nexilabs_auth.principal_account
     WHERE principal_id = NEW.principal_id;

    IF principal_identity IS DISTINCT FROM 'nexadevs_developer'
       OR principal_state IS DISTINCT FROM 'ACTIVE' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'active Admin Operator requires an ACTIVE nexadevs_developer principal';
    END IF;

    SELECT verification_state
      INTO email_state
      FROM nexilabs_auth.account_email
     WHERE email_id = NEW.bound_admin_email_id
       AND principal_id = NEW.principal_id;

    IF email_state IS DISTINCT FROM 'VERIFIED' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'active Admin Operator requires a VERIFIED bound Admin email owned by the principal';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_admin_operator_binding
BEFORE INSERT OR UPDATE OF principal_id, bound_admin_email_id, admin_state
ON nexilabs_auth.admin_operator
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_admin_operator_binding();

-- The ordinary Developer password remains credential_kind='password'.
-- ADMIN_PASSWORD is a separate verifier record/kind/lifecycle with its own
-- active-record uniqueness boundary.
CREATE UNIQUE INDEX ux_nexilabs_auth_active_admin_password
    ON nexilabs_auth.credential_verifier (principal_id)
    WHERE credential_kind = 'ADMIN_PASSWORD'
      AND credential_state = 'ACTIVE';

ALTER TABLE nexilabs_auth.developer_access_request
    ADD COLUMN terminal_decision_id text NULL,
    ADD CONSTRAINT uq_nexilabs_auth_request_terminal_projection
        UNIQUE (request_id, request_state, decision_reference, decided_at);

CREATE TABLE nexilabs_auth.developer_access_decision (
    decision_id text PRIMARY KEY,
    request_id text NOT NULL,
    reviewer_principal_id text NOT NULL,
    admin_operator_id text NOT NULL,
    decision text NOT NULL CHECK (decision IN ('APPROVED', 'REJECTED')),
    reason_code text NULL,
    safe_explanation text NULL,
    internal_reference text NOT NULL,
    policy_version text NOT NULL,
    receipt_reference text NOT NULL,
    decided_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_nexilabs_auth_developer_decision_request
        UNIQUE (request_id),
    CONSTRAINT uq_nexilabs_auth_developer_decision_projection
        UNIQUE (decision_id, request_id, decision, receipt_reference, decided_at),
    CONSTRAINT fk_nexilabs_auth_developer_decision_request
        FOREIGN KEY (request_id)
        REFERENCES nexilabs_auth.developer_access_request(request_id),
    CONSTRAINT fk_nexilabs_auth_developer_decision_reviewer_operator
        FOREIGN KEY (admin_operator_id, reviewer_principal_id)
        REFERENCES nexilabs_auth.admin_operator(admin_operator_id, principal_id),
    CONSTRAINT fk_nexilabs_auth_decision_request_projection
        FOREIGN KEY (request_id, decision, receipt_reference, decided_at)
        REFERENCES nexilabs_auth.developer_access_request(
            request_id, request_state, decision_reference, decided_at
        )
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT ck_nexilabs_auth_developer_decision_id_nonblank CHECK (
        length(btrim(decision_id)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_developer_decision_reason CHECK (
        (decision = 'APPROVED' AND reason_code IS NULL)
        OR (
            decision = 'REJECTED'
            AND reason_code IN (
                'DUPLICATE_ACTIVE_REQUEST',
                'IDENTITY_NOT_CONFIRMED',
                'ACCESS_ELIGIBILITY_NOT_CONFIRMED',
                'SECURITY_REVIEW_FAILED',
                'PREVIOUS_ACCESS_RESTRICTION',
                'REQUEST_INCOMPLETE',
                'POLICY_REQUIREMENTS_NOT_MET'
            )
        )
    ),
    CONSTRAINT ck_nexilabs_auth_developer_decision_safe_explanation CHECK (
        safe_explanation IS NULL
        OR length(btrim(safe_explanation)) BETWEEN 1 AND 2000
    ),
    CONSTRAINT ck_nexilabs_auth_developer_decision_internal_reference CHECK (
        length(btrim(internal_reference)) BETWEEN 1 AND 1024
    ),
    CONSTRAINT ck_nexilabs_auth_developer_decision_policy_version CHECK (
        length(btrim(policy_version)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_developer_decision_receipt_reference CHECK (
        length(btrim(receipt_reference)) BETWEEN 1 AND 1024
    )
);

CREATE INDEX ix_nexilabs_auth_developer_decision_reviewer
    ON nexilabs_auth.developer_access_decision (reviewer_principal_id, decided_at);
CREATE INDEX ix_nexilabs_auth_developer_decision_admin_operator
    ON nexilabs_auth.developer_access_decision (admin_operator_id, decided_at);
CREATE INDEX ix_nexilabs_auth_developer_decision_decided
    ON nexilabs_auth.developer_access_decision (decided_at, decision);

-- Persistence refuses new review evidence from a disabled Admin Operator.
-- Historical decisions remain readable after an operator is later disabled.
CREATE FUNCTION nexilabs_auth.validate_developer_access_decision_reviewer()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    operator_state text;
BEGIN
    SELECT admin_state
      INTO operator_state
      FROM nexilabs_auth.admin_operator
     WHERE admin_operator_id = NEW.admin_operator_id
       AND principal_id = NEW.reviewer_principal_id;

    IF operator_state IS DISTINCT FROM 'ACTIVE' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'Developer access decision requires an ACTIVE reviewer Admin Operator';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_developer_access_decision_reviewer
BEFORE INSERT
ON nexilabs_auth.developer_access_decision
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_developer_access_decision_reviewer();

-- A terminal request must carry the immutable reviewer-attributed decision row
-- whose decision, receipt and timestamp exactly match the request projection.
ALTER TABLE nexilabs_auth.developer_access_request
    ADD CONSTRAINT ck_nexilabs_auth_request_terminal_decision_presence CHECK (
        (request_state IN ('APPROVED', 'REJECTED'))
        = (terminal_decision_id IS NOT NULL)
    ),
    ADD CONSTRAINT fk_nexilabs_auth_request_terminal_decision
        FOREIGN KEY (
            terminal_decision_id,
            request_id,
            request_state,
            decision_reference,
            decided_at
        )
        REFERENCES nexilabs_auth.developer_access_decision(
            decision_id,
            request_id,
            decision,
            receipt_reference,
            decided_at
        )
        DEFERRABLE INITIALLY DEFERRED;

CREATE FUNCTION nexilabs_auth.reject_developer_access_decision_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '55000',
        MESSAGE = 'Developer access decisions are immutable append-only authority';
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_developer_access_decision_immutable
BEFORE UPDATE OR DELETE
ON nexilabs_auth.developer_access_decision
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.reject_developer_access_decision_mutation();

COMMENT ON TABLE nexilabs_auth.admin_operator IS
    'P006.UI.10.2.C layered Admin eligibility binding over an existing NexaDevs principal; not a third identity type or runtime.';
COMMENT ON COLUMN nexilabs_auth.admin_operator.admin_developer_id IS
    'Governed Admin-designated Developer identifier. Visible prefix/format is intentionally not fixed by this persistence milestone.';
COMMENT ON TABLE nexilabs_auth.developer_access_decision IS
    'Immutable reviewer-attributed terminal Developer access decision evidence.';
COMMENT ON COLUMN nexilabs_auth.developer_access_decision.reason_code IS
    'Administrative/policy rejection reason only; technical enrollment failures are excluded.';

REVOKE ALL ON TABLE nexilabs_auth.admin_operator FROM PUBLIC;
REVOKE ALL ON TABLE nexilabs_auth.developer_access_decision FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_admin_operator_binding() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.reject_developer_access_decision_mutation() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_developer_access_decision_reviewer() FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA nexilabs_auth FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA nexilabs_auth FROM PUBLIC;

COMMIT;
