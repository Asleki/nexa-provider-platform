BEGIN;

-- P006.UI.10.2 / migration identity M006.10.2
-- Governed NexiLabs account and credential persistence authority.
--
-- This migration creates authority structure only. It intentionally seeds no
-- Guest accounts, NexaDevs Developer accounts, password verifiers, Developer
-- Setup material, or Enigma catalogue/profile data. Private development
-- fixtures remain development/test material and are not Production authority.

CREATE SCHEMA IF NOT EXISTS nexilabs_auth;
REVOKE ALL ON SCHEMA nexilabs_auth FROM PUBLIC;

CREATE TABLE nexilabs_auth.principal_account (
    principal_id text PRIMARY KEY,
    username text NOT NULL,
    username_key text NOT NULL,
    identity_type text NOT NULL CHECK (
        identity_type IN ('guest', 'nexadevs_developer')
    ),
    account_state text NOT NULL DEFAULT 'PENDING' CHECK (
        account_state IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'DISABLED', 'CLOSED')
    ),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at timestamptz NULL,
    CHECK (length(btrim(principal_id)) BETWEEN 1 AND 255),
    CHECK (length(btrim(username)) BETWEEN 1 AND 128),
    CHECK (length(username_key) BETWEEN 1 AND 256),
    CHECK (username_key = btrim(username_key)),
    CHECK (updated_at >= created_at),
    CHECK (account_state <> 'CLOSED' OR closed_at IS NOT NULL)
);
CREATE UNIQUE INDEX ux_nexilabs_auth_principal_username_key
    ON nexilabs_auth.principal_account (username_key);
CREATE INDEX ix_nexilabs_auth_principal_identity_state
    ON nexilabs_auth.principal_account (identity_type, account_state);

CREATE TABLE nexilabs_auth.principal_profile (
    principal_id text PRIMARY KEY
        REFERENCES nexilabs_auth.principal_account(principal_id),
    first_name text NOT NULL,
    last_name text NOT NULL,
    date_of_birth date NULL,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (length(btrim(first_name)) BETWEEN 1 AND 160),
    CHECK (length(btrim(last_name)) BETWEEN 1 AND 160),
    CHECK (updated_at >= created_at)
);

CREATE TABLE nexilabs_auth.principal_permission (
    permission_assignment_id text PRIMARY KEY,
    principal_id text NOT NULL
        REFERENCES nexilabs_auth.principal_account(principal_id),
    permission_code text NOT NULL,
    permission_state text NOT NULL DEFAULT 'ACTIVE' CHECK (
        permission_state IN ('ACTIVE', 'REVOKED')
    ),
    granted_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at timestamptz NULL,
    CHECK (length(btrim(permission_assignment_id)) BETWEEN 1 AND 255),
    CHECK (length(btrim(permission_code)) BETWEEN 1 AND 255),
    CHECK ((permission_state = 'ACTIVE') = (revoked_at IS NULL))
);
CREATE UNIQUE INDEX ux_nexilabs_auth_active_permission
    ON nexilabs_auth.principal_permission (principal_id, permission_code)
    WHERE permission_state = 'ACTIVE';
CREATE INDEX ix_nexilabs_auth_permission_principal
    ON nexilabs_auth.principal_permission (principal_id, permission_state);

CREATE TABLE nexilabs_auth.account_email (
    email_id text PRIMARY KEY,
    principal_id text NOT NULL
        REFERENCES nexilabs_auth.principal_account(principal_id),
    email_address text NOT NULL,
    email_key text NOT NULL,
    verification_state text NOT NULL DEFAULT 'UNVERIFIED' CHECK (
        verification_state IN ('UNVERIFIED', 'PENDING', 'VERIFIED', 'REVOKED')
    ),
    is_primary boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verification_requested_at timestamptz NULL,
    verification_reference text NULL,
    verified_at timestamptz NULL,
    revoked_at timestamptz NULL,
    CHECK (length(btrim(email_id)) BETWEEN 1 AND 255),
    CHECK (position('@' IN email_address) > 1),
    CHECK (email_address !~ '[[:space:]]'),
    CHECK (length(email_key) BETWEEN 3 AND 320),
    CHECK (email_key = btrim(email_key)),
    CHECK (verification_state <> 'VERIFIED' OR verified_at IS NOT NULL),
    CHECK (verification_state <> 'REVOKED' OR revoked_at IS NOT NULL)
);
CREATE UNIQUE INDEX ux_nexilabs_auth_email_key
    ON nexilabs_auth.account_email (email_key);
CREATE UNIQUE INDEX ux_nexilabs_auth_primary_email
    ON nexilabs_auth.account_email (principal_id)
    WHERE is_primary AND verification_state <> 'REVOKED';
CREATE INDEX ix_nexilabs_auth_email_principal_state
    ON nexilabs_auth.account_email (principal_id, verification_state);

CREATE TABLE nexilabs_auth.credential_verifier (
    credential_id text PRIMARY KEY,
    principal_id text NOT NULL
        REFERENCES nexilabs_auth.principal_account(principal_id),
    credential_kind text NOT NULL,
    verifier_scheme text NOT NULL,
    verifier_version integer NOT NULL DEFAULT 1 CHECK (verifier_version > 0),
    verifier_payload text NOT NULL,
    credential_state text NOT NULL DEFAULT 'ACTIVE' CHECK (
        credential_state IN ('ACTIVE', 'RETIRED', 'REVOKED')
    ),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at timestamptz NULL,
    CHECK (length(btrim(credential_id)) BETWEEN 1 AND 255),
    CHECK (length(btrim(credential_kind)) BETWEEN 1 AND 80),
    CHECK (length(btrim(verifier_scheme)) BETWEEN 1 AND 80),
    CHECK (length(verifier_payload) BETWEEN 20 AND 4096),
    CHECK ((credential_state = 'ACTIVE') = (ended_at IS NULL))
);
CREATE UNIQUE INDEX ux_nexilabs_auth_active_password
    ON nexilabs_auth.credential_verifier (principal_id)
    WHERE credential_kind = 'password' AND credential_state = 'ACTIVE';
CREATE INDEX ix_nexilabs_auth_credential_principal_state
    ON nexilabs_auth.credential_verifier (principal_id, credential_state);

COMMENT ON COLUMN nexilabs_auth.credential_verifier.verifier_payload IS
    'Opaque credential verifier only; never a plaintext or reversible password.';

CREATE TABLE nexilabs_auth.developer_access_request (
    request_id text PRIMARY KEY,
    first_name text NOT NULL,
    last_name text NOT NULL,
    email_address text NOT NULL,
    email_key text NOT NULL,
    request_state text NOT NULL DEFAULT 'SUBMITTED' CHECK (
        request_state IN (
            'SUBMITTED', 'UNDER_REVIEW', 'APPROVED',
            'REJECTED', 'WITHDRAWN', 'EXPIRED'
        )
    ),
    requested_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decided_at timestamptz NULL,
    decision_reference text NULL,
    CHECK (length(btrim(request_id)) BETWEEN 1 AND 255),
    CHECK (length(btrim(first_name)) BETWEEN 1 AND 160),
    CHECK (length(btrim(last_name)) BETWEEN 1 AND 160),
    CHECK (position('@' IN email_address) > 1),
    CHECK (email_address !~ '[[:space:]]'),
    CHECK (length(email_key) BETWEEN 3 AND 320),
    CHECK (email_key = btrim(email_key)),
    CHECK (
        request_state NOT IN ('APPROVED', 'REJECTED')
        OR (
            decided_at IS NOT NULL
            AND decision_reference IS NOT NULL
            AND length(btrim(decision_reference)) BETWEEN 1 AND 1024
        )
    )
);
CREATE UNIQUE INDEX ux_nexilabs_auth_open_developer_request_email
    ON nexilabs_auth.developer_access_request (email_key)
    WHERE request_state IN ('SUBMITTED', 'UNDER_REVIEW', 'APPROVED');
CREATE INDEX ix_nexilabs_auth_developer_request_state
    ON nexilabs_auth.developer_access_request (request_state, requested_at);

CREATE TABLE nexilabs_auth.developer_setup (
    developer_setup_id text PRIMARY KEY,
    request_id text NOT NULL
        REFERENCES nexilabs_auth.developer_access_request(request_id),
    setup_lookup_key text NOT NULL,
    setup_secret_verifier_scheme text NOT NULL,
    setup_secret_verifier_version integer NOT NULL DEFAULT 1 CHECK (
        setup_secret_verifier_version > 0
    ),
    setup_secret_verifier_payload text NOT NULL,
    setup_state text NOT NULL DEFAULT 'ISSUED' CHECK (
        setup_state IN ('ISSUED', 'CONSUMED', 'REVOKED', 'EXPIRED')
    ),
    issued_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz NULL,
    revoked_at timestamptz NULL,
    resulting_principal_id text NULL
        REFERENCES nexilabs_auth.principal_account(principal_id),
    issuance_reference text NULL,
    CHECK (length(btrim(developer_setup_id)) BETWEEN 1 AND 255),
    CHECK (length(btrim(setup_lookup_key)) BETWEEN 20 AND 512),
    CHECK (setup_lookup_key = btrim(setup_lookup_key)),
    CHECK (length(btrim(setup_secret_verifier_scheme)) BETWEEN 1 AND 80),
    CHECK (length(setup_secret_verifier_payload) BETWEEN 20 AND 4096),
    CHECK (expires_at > issued_at),
    CHECK (
        setup_state <> 'CONSUMED'
        OR (consumed_at IS NOT NULL AND resulting_principal_id IS NOT NULL)
    ),
    CHECK (setup_state <> 'REVOKED' OR revoked_at IS NOT NULL)
);
CREATE UNIQUE INDEX ux_nexilabs_auth_developer_setup_lookup_key
    ON nexilabs_auth.developer_setup (setup_lookup_key);
CREATE UNIQUE INDEX ux_nexilabs_auth_active_developer_setup_request
    ON nexilabs_auth.developer_setup (request_id)
    WHERE setup_state = 'ISSUED';
CREATE UNIQUE INDEX ux_nexilabs_auth_developer_setup_result_principal
    ON nexilabs_auth.developer_setup (resulting_principal_id)
    WHERE resulting_principal_id IS NOT NULL;
CREATE INDEX ix_nexilabs_auth_developer_setup_state_expiry
    ON nexilabs_auth.developer_setup (setup_state, expires_at);

COMMENT ON COLUMN nexilabs_auth.developer_setup.developer_setup_id IS
    'Internal durable authority identity; never the user-presented Developer Setup secret.';
COMMENT ON COLUMN nexilabs_auth.developer_setup.setup_lookup_key IS
    'Server-derived non-secret lookup key for a user-presented Developer Setup value; derivation secret remains outside the database.';
COMMENT ON COLUMN nexilabs_auth.developer_setup.setup_secret_verifier_payload IS
    'Opaque verifier for the secret component of Developer Setup; never the reusable raw secret.';

CREATE TABLE nexilabs_auth.enigma_catalogue (
    catalogue_id text PRIMARY KEY,
    word_length integer NOT NULL CHECK (word_length IN (3, 4, 5)),
    catalogue_version integer NOT NULL CHECK (catalogue_version > 0),
    catalogue_state text NOT NULL DEFAULT 'DRAFT' CHECK (
        catalogue_state IN ('DRAFT', 'QUALIFIED', 'ACTIVE', 'RETIRED')
    ),
    source_reference text NOT NULL,
    source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    qualified_at timestamptz NULL,
    retired_at timestamptz NULL,
    UNIQUE (catalogue_id, word_length),
    CHECK (length(btrim(catalogue_id)) BETWEEN 1 AND 255),
    CHECK (length(btrim(source_reference)) BETWEEN 1 AND 1024),
    CHECK (catalogue_state NOT IN ('QUALIFIED', 'ACTIVE') OR qualified_at IS NOT NULL),
    CHECK (catalogue_state <> 'RETIRED' OR retired_at IS NOT NULL)
);
CREATE UNIQUE INDEX ux_nexilabs_auth_enigma_catalogue_version
    ON nexilabs_auth.enigma_catalogue (word_length, catalogue_version);
CREATE UNIQUE INDEX ux_nexilabs_auth_active_enigma_catalogue
    ON nexilabs_auth.enigma_catalogue (word_length)
    WHERE catalogue_state = 'ACTIVE';

CREATE TABLE nexilabs_auth.enigma_catalogue_entry (
    catalogue_id text NOT NULL,
    word_length integer NOT NULL,
    day_of_month integer NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
    period text NOT NULL CHECK (period IN ('Morning', 'Noon', 'Evening')),
    word_1 text NOT NULL,
    word_2 text NOT NULL,
    word_3 text NOT NULL,
    PRIMARY KEY (catalogue_id, day_of_month, period),
    FOREIGN KEY (catalogue_id, word_length)
        REFERENCES nexilabs_auth.enigma_catalogue(catalogue_id, word_length)
       ,
    CHECK (length(word_1) = word_length AND word_1 ~ '^[A-Z]+$'),
    CHECK (length(word_2) = word_length AND word_2 ~ '^[A-Z]+$'),
    CHECK (length(word_3) = word_length AND word_3 ~ '^[A-Z]+$')
);
CREATE INDEX ix_nexilabs_auth_enigma_catalogue_entry_lookup
    ON nexilabs_auth.enigma_catalogue_entry (
        catalogue_id, word_length, day_of_month, period
    );

-- Secret lookup/response material is intentionally not modeled in catalogue
-- entries. P006.UI.10.2 reserves that credential mechanism for later Enigma
-- provisioning authority instead of persisting development lookup words.

CREATE TABLE nexilabs_auth.enigma_profile (
    profile_id text PRIMARY KEY,
    profile_state text NOT NULL DEFAULT 'PROVISIONING' CHECK (
        profile_state IN ('PROVISIONING', 'ACTIVE', 'RETIRED', 'REVOKED')
    ),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activated_at timestamptz NULL,
    retired_at timestamptz NULL,
    profile_reference text NULL,
    CHECK (length(btrim(profile_id)) BETWEEN 1 AND 255),
    CHECK (profile_state <> 'ACTIVE' OR activated_at IS NOT NULL),
    CHECK (profile_state NOT IN ('RETIRED', 'REVOKED') OR retired_at IS NOT NULL)
);
CREATE INDEX ix_nexilabs_auth_enigma_profile_state
    ON nexilabs_auth.enigma_profile (profile_state, created_at);

CREATE TABLE nexilabs_auth.enigma_profile_catalogue (
    profile_id text NOT NULL
        REFERENCES nexilabs_auth.enigma_profile(profile_id),
    word_length integer NOT NULL CHECK (word_length IN (3, 4, 5)),
    catalogue_id text NOT NULL,
    assigned_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (profile_id, word_length),
    FOREIGN KEY (catalogue_id, word_length)
        REFERENCES nexilabs_auth.enigma_catalogue(catalogue_id, word_length)
);
CREATE INDEX ix_nexilabs_auth_enigma_profile_catalogue
    ON nexilabs_auth.enigma_profile_catalogue (catalogue_id, word_length);

CREATE TABLE nexilabs_auth.principal_enigma_profile (
    assignment_id text PRIMARY KEY,
    principal_id text NOT NULL
        REFERENCES nexilabs_auth.principal_account(principal_id),
    profile_id text NOT NULL
        REFERENCES nexilabs_auth.enigma_profile(profile_id),
    assignment_state text NOT NULL DEFAULT 'ACTIVE' CHECK (
        assignment_state IN ('ACTIVE', 'RETIRED', 'REVOKED')
    ),
    assigned_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at timestamptz NULL,
    CHECK (length(btrim(assignment_id)) BETWEEN 1 AND 255),
    CHECK ((assignment_state = 'ACTIVE') = (ended_at IS NULL))
);
CREATE UNIQUE INDEX ux_nexilabs_auth_active_principal_enigma_profile
    ON nexilabs_auth.principal_enigma_profile (principal_id)
    WHERE assignment_state = 'ACTIVE';
CREATE UNIQUE INDEX ux_nexilabs_auth_active_profile_assignment
    ON nexilabs_auth.principal_enigma_profile (profile_id)
    WHERE assignment_state = 'ACTIVE';

REVOKE ALL ON ALL TABLES IN SCHEMA nexilabs_auth FROM PUBLIC;

COMMIT;
