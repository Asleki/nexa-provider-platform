BEGIN;

-- P006.UI.10.2.E / migration identity M006.10.2
-- Credential bundle, private object-reference, optional archive-secret escrow
-- metadata and one-time delivery authority persistence.
--
-- This migration creates persistence structure only. It intentionally seeds no
-- bundle, escrow or delivery rows; stores no ZIP blob, archive password, raw
-- delivery token, public URL or presigned URL; and performs no S3/KMS/mail/API
-- operation. Public credential delivery remains a later operational service.

CREATE TABLE nexilabs_auth.credential_bundle (
    bundle_id text PRIMARY KEY,
    principal_id text NOT NULL,
    enigma_profile_id text NOT NULL,
    bundle_state text NOT NULL DEFAULT 'GENERATED',
    object_provider_code text NOT NULL,
    object_key text NOT NULL,
    content_sha256 text NOT NULL,
    byte_size bigint NOT NULL,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    integrity_verified_at timestamptz NULL,
    object_confirmed_at timestamptz NULL,
    ready_at timestamptz NULL,
    expires_at timestamptz NOT NULL,
    retention_until timestamptz NOT NULL,
    invalidated_at timestamptz NULL,
    retired_at timestamptz NULL,

    CONSTRAINT fk_nexilabs_auth_credential_bundle_principal
        FOREIGN KEY (principal_id)
        REFERENCES nexilabs_auth.principal_account(principal_id),
    CONSTRAINT fk_nexilabs_auth_credential_bundle_enigma_profile
        FOREIGN KEY (enigma_profile_id)
        REFERENCES nexilabs_auth.enigma_profile(profile_id),

    CONSTRAINT ck_nexilabs_auth_credential_bundle_id_nonblank CHECK (
        length(btrim(bundle_id)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_object_provider CHECK (
        object_provider_code ~ '^[A-Z][A-Z0-9_]{2,79}$'
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_object_key CHECK (
        length(btrim(object_key)) BETWEEN 1 AND 2048
        AND object_key = btrim(object_key)
        AND object_key !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_sha256 CHECK (
        content_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_byte_size CHECK (
        byte_size > 0
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_state CHECK (
        bundle_state IN ('GENERATED', 'READY', 'EXPIRED', 'RETIRED', 'INVALIDATED')
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_expiry_retention CHECK (
        expires_at > created_at
        AND retention_until >= expires_at
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_ready_evidence CHECK (
        (integrity_verified_at IS NULL OR integrity_verified_at >= created_at)
        AND (object_confirmed_at IS NULL OR object_confirmed_at >= created_at)
        AND (bundle_state <> 'GENERATED' OR ready_at IS NULL)
        AND (ready_at IS NULL OR (
            integrity_verified_at IS NOT NULL
            AND object_confirmed_at IS NOT NULL
            AND ready_at >= integrity_verified_at
            AND ready_at >= object_confirmed_at
            AND ready_at <= expires_at
        ))
        AND (
            bundle_state <> 'READY'
            OR (
                integrity_verified_at IS NOT NULL
                AND object_confirmed_at IS NOT NULL
                AND ready_at IS NOT NULL
            )
        )
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_invalidation_time CHECK (
        (bundle_state = 'INVALIDATED') = (invalidated_at IS NOT NULL)
        AND (
            invalidated_at IS NULL
            OR invalidated_at >= COALESCE(ready_at, created_at)
        )
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_retired_time CHECK (
        (bundle_state = 'RETIRED') = (retired_at IS NOT NULL)
        AND (
            retired_at IS NULL
            OR (ready_at IS NOT NULL AND retired_at >= ready_at)
        )
    )
);

-- A principal may have only one current generated/ready credential bundle.
-- Historical expired/retired/invalidated rows remain durable.
CREATE UNIQUE INDEX ux_nexilabs_auth_current_credential_bundle
    ON nexilabs_auth.credential_bundle (principal_id)
    WHERE bundle_state IN ('GENERATED', 'READY');
CREATE UNIQUE INDEX ux_nexilabs_auth_credential_bundle_object
    ON nexilabs_auth.credential_bundle (object_provider_code, object_key);
CREATE INDEX ix_nexilabs_auth_credential_bundle_principal
    ON nexilabs_auth.credential_bundle (principal_id, created_at DESC);
CREATE INDEX ix_nexilabs_auth_credential_bundle_state_expiry
    ON nexilabs_auth.credential_bundle (bundle_state, expires_at);

CREATE TABLE nexilabs_auth.credential_bundle_secret (
    bundle_secret_id text PRIMARY KEY,
    bundle_id text NOT NULL,
    escrow_provider_code text NOT NULL,
    encrypted_secret_reference text NOT NULL,
    encryption_context_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    retired_at timestamptz NULL,

    CONSTRAINT fk_nexilabs_auth_credential_bundle_secret_bundle
        FOREIGN KEY (bundle_id)
        REFERENCES nexilabs_auth.credential_bundle(bundle_id),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_secret_id_nonblank CHECK (
        length(btrim(bundle_secret_id)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_secret_provider CHECK (
        escrow_provider_code ~ '^[A-Z][A-Z0-9_]{2,79}$'
        AND lower(escrow_provider_code) NOT IN ('raw', 'plaintext', 'cleartext', 'reversible')
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_secret_reference CHECK (
        length(encrypted_secret_reference) BETWEEN 20 AND 4096
        AND lower(btrim(encrypted_secret_reference)) NOT LIKE 'plaintext:%'
        AND lower(btrim(encrypted_secret_reference)) NOT LIKE 'cleartext:%'
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_secret_context CHECK (
        length(btrim(encryption_context_version)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_credential_bundle_secret_retirement CHECK (
        retired_at IS NULL OR retired_at >= created_at
    )
);
CREATE UNIQUE INDEX ux_nexilabs_auth_active_credential_bundle_secret
    ON nexilabs_auth.credential_bundle_secret (bundle_id)
    WHERE retired_at IS NULL;
CREATE INDEX ix_nexilabs_auth_credential_bundle_secret_bundle
    ON nexilabs_auth.credential_bundle_secret (bundle_id, created_at DESC);

CREATE TABLE nexilabs_auth.credential_delivery (
    delivery_id text PRIMARY KEY,
    bundle_id text NOT NULL,
    token_verifier_scheme text NOT NULL,
    token_verifier_version integer NOT NULL DEFAULT 1,
    token_verifier_payload text NOT NULL,
    delivery_state text NOT NULL DEFAULT 'ISSUED',
    policy_version text NOT NULL,
    logical_delivery_host_code text NOT NULL,
    issued_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz NULL,
    revoked_at timestamptz NULL,
    download_count integer NOT NULL DEFAULT 0,
    first_downloaded_at timestamptz NULL,
    last_downloaded_at timestamptz NULL,

    CONSTRAINT fk_nexilabs_auth_credential_delivery_bundle
        FOREIGN KEY (bundle_id)
        REFERENCES nexilabs_auth.credential_bundle(bundle_id),
    CONSTRAINT ck_nexilabs_auth_credential_delivery_id_nonblank CHECK (
        length(btrim(delivery_id)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_delivery_verifier_scheme CHECK (
        length(btrim(token_verifier_scheme)) BETWEEN 1 AND 80
        AND lower(btrim(token_verifier_scheme)) NOT IN (
            'raw', 'plaintext', 'cleartext', 'reversible'
        )
    ),
    CONSTRAINT ck_nexilabs_auth_delivery_verifier_version CHECK (
        token_verifier_version > 0
    ),
    CONSTRAINT ck_nexilabs_auth_delivery_verifier_payload CHECK (
        length(token_verifier_payload) BETWEEN 20 AND 4096
    ),
    CONSTRAINT ck_nexilabs_auth_credential_delivery_state CHECK (
        delivery_state IN ('ISSUED', 'CONSUMED', 'EXPIRED', 'REVOKED')
    ),
    CONSTRAINT ck_nexilabs_auth_credential_delivery_policy CHECK (
        length(btrim(policy_version)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_credential_delivery_host CHECK (
        logical_delivery_host_code ~ '^[A-Z][A-Z0-9_]{2,79}$'
    ),
    CONSTRAINT ck_nexilabs_auth_credential_delivery_expiry CHECK (
        expires_at > issued_at
    ),
    CONSTRAINT ck_nexilabs_auth_credential_delivery_state_timestamps CHECK (
        (delivery_state = 'CONSUMED') = (consumed_at IS NOT NULL)
        AND (delivery_state = 'REVOKED') = (revoked_at IS NOT NULL)
    ),
    CONSTRAINT ck_nexilabs_auth_credential_delivery_consumed_time CHECK (
        consumed_at IS NULL
        OR (consumed_at >= issued_at AND consumed_at <= expires_at)
    ),
    CONSTRAINT ck_nexilabs_auth_credential_delivery_revoked_time CHECK (
        revoked_at IS NULL OR revoked_at >= issued_at
    ),
    CONSTRAINT ck_nexilabs_auth_credential_delivery_download_accounting CHECK (
        download_count >= 0
        AND (
            (download_count = 0 AND first_downloaded_at IS NULL AND last_downloaded_at IS NULL)
            OR (
                download_count > 0
                AND first_downloaded_at IS NOT NULL
                AND last_downloaded_at IS NOT NULL
                AND first_downloaded_at >= issued_at
                AND first_downloaded_at <= last_downloaded_at
                AND last_downloaded_at <= expires_at
            )
        )
    )
);
CREATE UNIQUE INDEX ux_nexilabs_auth_issued_credential_delivery
    ON nexilabs_auth.credential_delivery (bundle_id)
    WHERE delivery_state = 'ISSUED';
CREATE INDEX ix_nexilabs_auth_credential_delivery_bundle
    ON nexilabs_auth.credential_delivery (bundle_id, issued_at DESC);
CREATE INDEX ix_nexilabs_auth_credential_delivery_state_expiry
    ON nexilabs_auth.credential_delivery (delivery_state, expires_at);

CREATE FUNCTION nexilabs_auth.validate_credential_bundle_owner()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    identity_value text;
    profile_state_value text;
    active_assignment_count integer;
BEGIN
    SELECT identity_type
      INTO identity_value
      FROM nexilabs_auth.principal_account
     WHERE principal_id = NEW.principal_id;

    IF identity_value IS DISTINCT FROM 'nexadevs_developer' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'credential bundle requires a NexaDevs Developer principal';
    END IF;

    SELECT profile_state
      INTO profile_state_value
      FROM nexilabs_auth.enigma_profile
     WHERE profile_id = NEW.enigma_profile_id;

    IF profile_state_value IS DISTINCT FROM 'ACTIVE' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'credential bundle requires an ACTIVE Enigma profile';
    END IF;

    SELECT COUNT(*)
      INTO active_assignment_count
      FROM nexilabs_auth.principal_enigma_profile
     WHERE principal_id = NEW.principal_id
       AND profile_id = NEW.enigma_profile_id
       AND assignment_state = 'ACTIVE';

    IF active_assignment_count <> 1 THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'credential bundle principal/profile ownership is not active and unique';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_credential_bundle_owner
BEFORE INSERT
ON nexilabs_auth.credential_bundle
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_credential_bundle_owner();

CREATE FUNCTION nexilabs_auth.validate_credential_delivery_bundle()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    bundle_state_value text;
BEGIN
    SELECT bundle_state
      INTO bundle_state_value
      FROM nexilabs_auth.credential_bundle
     WHERE bundle_id = NEW.bundle_id;

    IF bundle_state_value IS DISTINCT FROM 'READY' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'credential delivery requires a READY credential bundle';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_credential_delivery_bundle
BEFORE INSERT
ON nexilabs_auth.credential_delivery
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_credential_delivery_bundle();

CREATE FUNCTION nexilabs_auth.validate_credential_bundle_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    issued_delivery_count integer;
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'credential bundles are durable authority and cannot be deleted';
    END IF;

    IF OLD.bundle_state IN ('EXPIRED', 'RETIRED', 'INVALIDATED') THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'terminal credential bundles are immutable';
    END IF;

    IF NEW.bundle_id IS DISTINCT FROM OLD.bundle_id
       OR NEW.principal_id IS DISTINCT FROM OLD.principal_id
       OR NEW.enigma_profile_id IS DISTINCT FROM OLD.enigma_profile_id
       OR NEW.object_provider_code IS DISTINCT FROM OLD.object_provider_code
       OR NEW.object_key IS DISTINCT FROM OLD.object_key
       OR NEW.content_sha256 IS DISTINCT FROM OLD.content_sha256
       OR NEW.byte_size IS DISTINCT FROM OLD.byte_size
       OR NEW.created_at IS DISTINCT FROM OLD.created_at
       OR NEW.expires_at IS DISTINCT FROM OLD.expires_at
       OR NEW.retention_until IS DISTINCT FROM OLD.retention_until THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'credential bundle identity, integrity, object and retention authority are immutable';
    END IF;

    IF OLD.bundle_state = 'GENERATED'
       AND NEW.bundle_state NOT IN ('GENERATED', 'READY', 'EXPIRED', 'INVALIDATED') THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'invalid GENERATED bundle transition';
    END IF;
    IF OLD.bundle_state = 'READY'
       AND NEW.bundle_state NOT IN ('READY', 'EXPIRED', 'RETIRED', 'INVALIDATED') THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'invalid READY bundle transition';
    END IF;

    IF NEW.bundle_state IN ('EXPIRED', 'RETIRED', 'INVALIDATED')
       AND NEW.bundle_state IS DISTINCT FROM OLD.bundle_state THEN
        SELECT COUNT(*)
          INTO issued_delivery_count
          FROM nexilabs_auth.credential_delivery
         WHERE bundle_id = OLD.bundle_id
           AND delivery_state = 'ISSUED';
        IF issued_delivery_count <> 0 THEN
            RAISE EXCEPTION USING
                ERRCODE = '23514',
                MESSAGE = 'credential bundle cannot become terminal while a delivery remains ISSUED';
        END IF;
    END IF;

    IF OLD.integrity_verified_at IS NOT NULL
       AND NEW.integrity_verified_at IS DISTINCT FROM OLD.integrity_verified_at THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'bundle integrity verification time is immutable once set';
    END IF;
    IF OLD.object_confirmed_at IS NOT NULL
       AND NEW.object_confirmed_at IS DISTINCT FROM OLD.object_confirmed_at THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'bundle object confirmation time is immutable once set';
    END IF;
    IF OLD.ready_at IS NOT NULL
       AND NEW.ready_at IS DISTINCT FROM OLD.ready_at THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'bundle ready time is immutable once set';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_credential_bundle_transition
BEFORE UPDATE OR DELETE
ON nexilabs_auth.credential_bundle
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_credential_bundle_transition();

CREATE FUNCTION nexilabs_auth.validate_credential_bundle_secret_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'credential bundle secret metadata is durable authority and cannot be deleted';
    END IF;

    IF OLD.retired_at IS NOT NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'retired credential bundle secret metadata is immutable';
    END IF;

    IF NEW.bundle_secret_id IS DISTINCT FROM OLD.bundle_secret_id
       OR NEW.bundle_id IS DISTINCT FROM OLD.bundle_id
       OR NEW.escrow_provider_code IS DISTINCT FROM OLD.escrow_provider_code
       OR NEW.encrypted_secret_reference IS DISTINCT FROM OLD.encrypted_secret_reference
       OR NEW.encryption_context_version IS DISTINCT FROM OLD.encryption_context_version
       OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'credential bundle secret identity and escrow reference are immutable';
    END IF;

    IF OLD.retired_at IS NULL AND NEW.retired_at IS NULL THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'credential bundle secret update must retire the active escrow metadata';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_credential_bundle_secret_transition
BEFORE UPDATE OR DELETE
ON nexilabs_auth.credential_bundle_secret
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_credential_bundle_secret_transition();

CREATE FUNCTION nexilabs_auth.validate_credential_delivery_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION USING
            ERRCODE = '55000',
            MESSAGE = 'credential deliveries are durable authority and cannot be deleted';
    END IF;

    IF OLD.delivery_state <> 'ISSUED' THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'terminal credential deliveries are immutable';
    END IF;

    IF NEW.delivery_id IS DISTINCT FROM OLD.delivery_id
       OR NEW.bundle_id IS DISTINCT FROM OLD.bundle_id
       OR NEW.token_verifier_scheme IS DISTINCT FROM OLD.token_verifier_scheme
       OR NEW.token_verifier_version IS DISTINCT FROM OLD.token_verifier_version
       OR NEW.token_verifier_payload IS DISTINCT FROM OLD.token_verifier_payload
       OR NEW.policy_version IS DISTINCT FROM OLD.policy_version
       OR NEW.logical_delivery_host_code IS DISTINCT FROM OLD.logical_delivery_host_code
       OR NEW.issued_at IS DISTINCT FROM OLD.issued_at
       OR NEW.expires_at IS DISTINCT FROM OLD.expires_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'credential delivery identity, verifier, host and issuance policy are immutable';
    END IF;

    IF NEW.delivery_state NOT IN ('ISSUED', 'CONSUMED', 'EXPIRED', 'REVOKED') THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'invalid credential delivery transition';
    END IF;

    IF NEW.download_count < OLD.download_count THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'credential delivery download counter cannot decrease';
    END IF;
    IF OLD.first_downloaded_at IS NOT NULL
       AND NEW.first_downloaded_at IS DISTINCT FROM OLD.first_downloaded_at THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'credential delivery first-download time is immutable once set';
    END IF;
    IF OLD.last_downloaded_at IS NOT NULL
       AND (
           NEW.last_downloaded_at IS NULL
           OR NEW.last_downloaded_at < OLD.last_downloaded_at
       ) THEN
        RAISE EXCEPTION USING
            ERRCODE = '23514',
            MESSAGE = 'credential delivery last-download time cannot move backwards';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_credential_delivery_transition
BEFORE UPDATE OR DELETE
ON nexilabs_auth.credential_delivery
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_credential_delivery_transition();

COMMENT ON COLUMN nexilabs_auth.credential_bundle.object_key IS
    'Private object-storage reference only; never a public, presigned or user-facing URL.';
COMMENT ON COLUMN nexilabs_auth.credential_bundle_secret.encrypted_secret_reference IS
    'Optional opaque KMS-encrypted archive-secret ciphertext/reference; never the plaintext archive password.';
COMMENT ON COLUMN nexilabs_auth.credential_delivery.token_verifier_payload IS
    'Opaque delivery-token verifier only; never the raw delivery token or its public URL.';
COMMENT ON COLUMN nexilabs_auth.credential_delivery.logical_delivery_host_code IS
    'Logical host configuration code only; not a hostname, URL or DNS authority.';

REVOKE ALL ON TABLE nexilabs_auth.credential_bundle FROM PUBLIC;
REVOKE ALL ON TABLE nexilabs_auth.credential_bundle_secret FROM PUBLIC;
REVOKE ALL ON TABLE nexilabs_auth.credential_delivery FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_credential_bundle_owner() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_credential_bundle_transition() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_credential_delivery_bundle() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_credential_bundle_secret_transition() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_credential_delivery_transition() FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA nexilabs_auth FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA nexilabs_auth FROM PUBLIC;

COMMIT;
