BEGIN;

-- P006.UI.10.2.D / migration identity M006.10.2
-- Durable approved-email verification challenge authority.
--
-- This migration creates persistence structure only. It intentionally seeds no
-- challenge rows, generates/sends no OTP, performs no verification and stores
-- no raw OTP. Operational issue/verify/resend behavior remains a later service.

CREATE TABLE nexilabs_auth.email_verification_challenge (
    challenge_id text PRIMARY KEY,
    principal_id text NOT NULL,
    email_id text NOT NULL,
    otp_verifier_scheme text NOT NULL,
    otp_verifier_version integer NOT NULL DEFAULT 1,
    otp_verifier_payload text NOT NULL,
    challenge_state text NOT NULL DEFAULT 'ISSUED',
    policy_version text NOT NULL,
    issued_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz NULL,
    invalidated_at timestamptz NULL,
    attempt_count integer NOT NULL DEFAULT 0,
    max_attempts integer NOT NULL,
    resend_count integer NOT NULL DEFAULT 0,
    last_resend_at timestamptz NULL,

    CONSTRAINT fk_nexilabs_auth_email_challenge_principal
        FOREIGN KEY (principal_id)
        REFERENCES nexilabs_auth.principal_account(principal_id),
    CONSTRAINT fk_nexilabs_auth_email_challenge_owner
        FOREIGN KEY (email_id, principal_id)
        REFERENCES nexilabs_auth.account_email(email_id, principal_id),

    CONSTRAINT ck_nexilabs_auth_email_challenge_id_nonblank CHECK (
        length(btrim(challenge_id)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_otp_verifier_scheme CHECK (
        length(btrim(otp_verifier_scheme)) BETWEEN 1 AND 80
        AND lower(btrim(otp_verifier_scheme)) NOT IN (
            'raw', 'plaintext', 'cleartext', 'reversible'
        )
    ),
    CONSTRAINT ck_nexilabs_auth_otp_verifier_version CHECK (
        otp_verifier_version > 0
    ),
    CONSTRAINT ck_nexilabs_auth_otp_verifier_payload CHECK (
        length(otp_verifier_payload) BETWEEN 20 AND 4096
    ),
    CONSTRAINT ck_nexilabs_auth_otp_challenge_state CHECK (
        challenge_state IN ('ISSUED', 'VERIFIED', 'EXPIRED', 'LOCKED', 'INVALIDATED')
    ),
    CONSTRAINT ck_nexilabs_auth_otp_policy_version CHECK (
        length(btrim(policy_version)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_otp_expiry CHECK (
        expires_at > issued_at
    ),
    CONSTRAINT ck_nexilabs_auth_otp_attempts CHECK (
        max_attempts > 0
        AND attempt_count BETWEEN 0 AND max_attempts
        AND (challenge_state <> 'ISSUED' OR attempt_count < max_attempts)
        AND (challenge_state <> 'LOCKED' OR attempt_count = max_attempts)
    ),
    CONSTRAINT ck_nexilabs_auth_otp_state_timestamps CHECK (
        (challenge_state = 'VERIFIED') = (consumed_at IS NOT NULL)
        AND (challenge_state = 'INVALIDATED') = (invalidated_at IS NOT NULL)
    ),
    CONSTRAINT ck_nexilabs_auth_otp_verified_time CHECK (
        consumed_at IS NULL
        OR (consumed_at >= issued_at AND consumed_at <= expires_at)
    ),
    CONSTRAINT ck_nexilabs_auth_otp_invalidated_time CHECK (
        invalidated_at IS NULL OR invalidated_at >= issued_at
    ),
    CONSTRAINT ck_nexilabs_auth_otp_resend_accounting CHECK (
        (
            resend_count = 0
            AND last_resend_at IS NULL
        )
        OR (
            resend_count > 0
            AND last_resend_at IS NOT NULL
            AND last_resend_at >= issued_at
            AND last_resend_at <= expires_at
        )
    )
);

-- Only one currently-issued challenge may govern a principal/email pair. Once
-- the challenge becomes terminal, a later governed issue may create a new row
-- without deleting or overwriting the historical terminal challenge.
CREATE UNIQUE INDEX ux_nexilabs_auth_issued_email_verification_challenge
    ON nexilabs_auth.email_verification_challenge (principal_id, email_id)
    WHERE challenge_state = 'ISSUED';
CREATE INDEX ix_nexilabs_auth_email_verification_challenge_principal
    ON nexilabs_auth.email_verification_challenge (
        principal_id, email_id, issued_at DESC
    );
CREATE INDEX ix_nexilabs_auth_email_verification_challenge_state_expiry
    ON nexilabs_auth.email_verification_challenge (challenge_state, expires_at);

CREATE FUNCTION nexilabs_auth.validate_email_verification_challenge_email()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    email_state text;
BEGIN
    SELECT verification_state
      INTO email_state
      FROM nexilabs_auth.account_email
     WHERE email_id = NEW.email_id
       AND principal_id = NEW.principal_id;

    IF email_state IS NULL OR email_state = 'REVOKED' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'email verification challenge requires a non-revoked email owned by the principal';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_email_verification_challenge_email
BEFORE INSERT
ON nexilabs_auth.email_verification_challenge
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_email_verification_challenge_email();

CREATE FUNCTION nexilabs_auth.validate_email_verification_challenge_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'email verification challenges are durable authority and cannot be deleted';
    END IF;

    -- Terminal rows are immutable historical authority. Operational services
    -- create a later challenge rather than reopening a consumed/expired/locked/
    -- invalidated record.
    IF OLD.challenge_state <> 'ISSUED' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'terminal email verification challenges are immutable';
    END IF;

    IF NEW.challenge_id IS DISTINCT FROM OLD.challenge_id
       OR NEW.principal_id IS DISTINCT FROM OLD.principal_id
       OR NEW.email_id IS DISTINCT FROM OLD.email_id
       OR NEW.issued_at IS DISTINCT FROM OLD.issued_at
       OR NEW.max_attempts IS DISTINCT FROM OLD.max_attempts
       OR NEW.policy_version IS DISTINCT FROM OLD.policy_version THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'email verification challenge identity and issuance policy are immutable';
    END IF;

    IF NEW.expires_at < OLD.expires_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'email verification challenge expiry cannot move backwards';
    END IF;

    IF NEW.attempt_count < OLD.attempt_count
       OR NEW.resend_count < OLD.resend_count THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'email verification attempt/resend counters cannot decrease';
    END IF;

    IF OLD.last_resend_at IS NOT NULL
       AND (
           NEW.last_resend_at IS NULL
           OR NEW.last_resend_at < OLD.last_resend_at
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'email verification last_resend_at cannot move backwards';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_email_verification_challenge_transition
BEFORE UPDATE OR DELETE
ON nexilabs_auth.email_verification_challenge
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_email_verification_challenge_transition();

COMMENT ON COLUMN nexilabs_auth.email_verification_challenge.challenge_id IS
    'Opaque durable challenge identity; never the user-presented OTP.';
COMMENT ON COLUMN nexilabs_auth.email_verification_challenge.otp_verifier_payload IS
    'Opaque non-plaintext verifier material only; raw OTP and verifier key/pepper remain outside PostgreSQL.';
COMMENT ON COLUMN nexilabs_auth.email_verification_challenge.policy_version IS
    'Reference to the server-side OTP policy used when the challenge was issued.';

REVOKE ALL ON TABLE nexilabs_auth.email_verification_challenge FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_email_verification_challenge_email() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_email_verification_challenge_transition() FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA nexilabs_auth FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA nexilabs_auth FROM PUBLIC;

COMMIT;
