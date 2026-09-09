BEGIN;

-- P006.UI.10.2.F / migration identity M006.10.2
-- Immutable Developer-enrollment lifecycle evidence, provider-neutral notification
-- delivery evidence, and governed Admin audit-export artifact metadata.
--
-- This migration creates persistence structure only. It intentionally seeds no
-- enrollment events, notifications or audit exports; sends no mail; stores no
-- rendered email body, password, OTP, Developer Setup secret, archive password,
-- Enigma response, raw download token, provider credential, public URL or report
-- bytes; and performs no object-storage, report-generation or account-activation
-- operation. Operational enrollment/mail/audit services remain later work.

CREATE TABLE nexilabs_auth.enrollment_event (
    event_id text PRIMARY KEY,
    request_id text NOT NULL,
    event_type text NOT NULL,
    authority_type text NOT NULL,
    authority_id text NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_reference text NOT NULL,
    correlation_id text NULL,
    causation_event_id text NULL,

    CONSTRAINT fk_nexilabs_auth_enrollment_event_request
        FOREIGN KEY (request_id)
        REFERENCES nexilabs_auth.developer_access_request(request_id),
    CONSTRAINT fk_nexilabs_auth_enrollment_event_causation
        FOREIGN KEY (causation_event_id)
        REFERENCES nexilabs_auth.enrollment_event(event_id),
    CONSTRAINT ck_nexilabs_auth_enrollment_event_id_nonblank CHECK (
        length(btrim(event_id)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_enrollment_event_type CHECK (
        event_type IN (
            'REQUEST_RECEIVED', 'UNDER_REVIEW', 'APPROVED', 'REJECTED',
            'SETUP_ISSUED', 'SETUP_VERIFIED', 'OTP_ISSUED', 'EMAIL_VERIFIED',
            'ENIGMA_PROVISIONED', 'BUNDLE_READY', 'DELIVERY_ISSUED',
            'ACCOUNT_ACTIVATED'
        )
    ),
    CONSTRAINT ck_nexilabs_auth_enrollment_event_authority_type CHECK (
        authority_type IN (
            'DEVELOPER_ACCESS_REQUEST', 'DEVELOPER_ACCESS_DECISION',
            'DEVELOPER_SETUP', 'EMAIL_VERIFICATION_CHALLENGE',
            'PRINCIPAL_ENIGMA_PROFILE', 'CREDENTIAL_BUNDLE',
            'CREDENTIAL_DELIVERY', 'PRINCIPAL_ACCOUNT'
        )
    ),
    CONSTRAINT ck_nexilabs_auth_enrollment_event_authority_id CHECK (
        length(btrim(authority_id)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_enrollment_event_source_reference CHECK (
        length(btrim(source_reference)) BETWEEN 1 AND 1024
        AND source_reference = btrim(source_reference)
        AND source_reference !~ '@'
        AND source_reference !~ '[[:space:]]'
        AND source_reference !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'
    ),
    CONSTRAINT ck_nexilabs_auth_enrollment_event_correlation CHECK (
        correlation_id IS NULL
        OR (
            length(btrim(correlation_id)) BETWEEN 1 AND 1024
            AND correlation_id = btrim(correlation_id)
            AND correlation_id !~ '@'
            AND correlation_id !~ '[[:space:]]'
            AND correlation_id !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'
        )
    ),
    CONSTRAINT ck_nexilabs_auth_enrollment_event_causation_not_self CHECK (
        causation_event_id IS NULL OR causation_event_id <> event_id
    )
);

CREATE UNIQUE INDEX ux_nexilabs_auth_enrollment_event_authority
    ON nexilabs_auth.enrollment_event (
        request_id, event_type, authority_type, authority_id
    );
CREATE INDEX ix_nexilabs_auth_enrollment_event_request
    ON nexilabs_auth.enrollment_event (request_id, occurred_at, event_id);
CREATE INDEX ix_nexilabs_auth_enrollment_event_authority
    ON nexilabs_auth.enrollment_event (authority_type, authority_id);
CREATE INDEX ix_nexilabs_auth_enrollment_event_correlation
    ON nexilabs_auth.enrollment_event (correlation_id, occurred_at)
    WHERE correlation_id IS NOT NULL;

CREATE FUNCTION nexilabs_auth.validate_enrollment_event_authority()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    request_state_value text;
    decision_request_id text;
    decision_value text;
    setup_request_id text;
    setup_state_value text;
    setup_principal_id text;
    challenge_principal_id text;
    challenge_state_value text;
    assignment_principal_id text;
    assignment_state_value text;
    profile_state_value text;
    bundle_principal_id text;
    bundle_state_value text;
    delivery_principal_id text;
    delivery_state_value text;
    principal_identity_value text;
    principal_state_value text;
    causation_request_id text;
    causation_occurred_at timestamptz;
BEGIN
    IF NEW.event_type IN ('REQUEST_RECEIVED', 'UNDER_REVIEW') THEN
        IF NEW.authority_type <> 'DEVELOPER_ACCESS_REQUEST'
           OR NEW.authority_id <> NEW.request_id THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'request lifecycle event must reference its Developer access request';
        END IF;
        SELECT request_state INTO request_state_value
          FROM nexilabs_auth.developer_access_request
         WHERE request_id = NEW.request_id;
        IF NEW.event_type = 'REQUEST_RECEIVED'
           AND request_state_value IS DISTINCT FROM 'SUBMITTED' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'REQUEST_RECEIVED requires a SUBMITTED Developer access request';
        END IF;
        IF NEW.event_type = 'UNDER_REVIEW'
           AND request_state_value IS DISTINCT FROM 'UNDER_REVIEW' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'UNDER_REVIEW requires an UNDER_REVIEW Developer access request';
        END IF;

    ELSIF NEW.event_type IN ('APPROVED', 'REJECTED') THEN
        IF NEW.authority_type <> 'DEVELOPER_ACCESS_DECISION' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'terminal review event must reference immutable Developer decision authority';
        END IF;
        SELECT request_id, decision
          INTO decision_request_id, decision_value
          FROM nexilabs_auth.developer_access_decision
         WHERE decision_id = NEW.authority_id;
        IF decision_request_id IS DISTINCT FROM NEW.request_id
           OR decision_value IS DISTINCT FROM NEW.event_type THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'terminal review event does not match Developer decision authority';
        END IF;

    ELSIF NEW.event_type IN ('SETUP_ISSUED', 'SETUP_VERIFIED') THEN
        IF NEW.authority_type <> 'DEVELOPER_SETUP' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'Setup lifecycle event must reference Developer Setup authority';
        END IF;
        SELECT request_id, setup_state, resulting_principal_id
          INTO setup_request_id, setup_state_value, setup_principal_id
          FROM nexilabs_auth.developer_setup
         WHERE developer_setup_id = NEW.authority_id;
        IF setup_request_id IS DISTINCT FROM NEW.request_id THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'Setup lifecycle event does not belong to enrollment request';
        END IF;
        IF NEW.event_type = 'SETUP_ISSUED'
           AND setup_state_value IS DISTINCT FROM 'ISSUED' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'SETUP_ISSUED requires ISSUED Developer Setup authority';
        END IF;
        IF NEW.event_type = 'SETUP_VERIFIED'
           AND (setup_state_value IS DISTINCT FROM 'CONSUMED' OR setup_principal_id IS NULL) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'SETUP_VERIFIED requires consumed Setup with resulting principal';
        END IF;

    ELSIF NEW.event_type IN ('OTP_ISSUED', 'EMAIL_VERIFIED') THEN
        IF NEW.authority_type <> 'EMAIL_VERIFICATION_CHALLENGE' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'email lifecycle event must reference email verification challenge authority';
        END IF;
        SELECT principal_id, challenge_state
          INTO challenge_principal_id, challenge_state_value
          FROM nexilabs_auth.email_verification_challenge
         WHERE challenge_id = NEW.authority_id;
        IF NOT EXISTS (
            SELECT 1 FROM nexilabs_auth.developer_setup
             WHERE request_id = NEW.request_id
               AND resulting_principal_id = challenge_principal_id
        ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'email verification challenge principal does not belong to enrollment request';
        END IF;
        IF NEW.event_type = 'OTP_ISSUED'
           AND challenge_state_value IS DISTINCT FROM 'ISSUED' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'OTP_ISSUED requires ISSUED challenge authority';
        END IF;
        IF NEW.event_type = 'EMAIL_VERIFIED'
           AND challenge_state_value IS DISTINCT FROM 'VERIFIED' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'EMAIL_VERIFIED requires VERIFIED challenge authority';
        END IF;

    ELSIF NEW.event_type = 'ENIGMA_PROVISIONED' THEN
        IF NEW.authority_type <> 'PRINCIPAL_ENIGMA_PROFILE' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'ENIGMA_PROVISIONED must reference principal Enigma assignment authority';
        END IF;
        SELECT pep.principal_id, pep.assignment_state, ep.profile_state
          INTO assignment_principal_id, assignment_state_value, profile_state_value
          FROM nexilabs_auth.principal_enigma_profile AS pep
          JOIN nexilabs_auth.enigma_profile AS ep ON ep.profile_id = pep.profile_id
         WHERE pep.assignment_id = NEW.authority_id;
        IF assignment_state_value IS DISTINCT FROM 'ACTIVE'
           OR profile_state_value IS DISTINCT FROM 'ACTIVE'
           OR NOT EXISTS (
                SELECT 1 FROM nexilabs_auth.developer_setup
                 WHERE request_id = NEW.request_id
                   AND resulting_principal_id = assignment_principal_id
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'ENIGMA_PROVISIONED requires active same-enrollment Enigma authority';
        END IF;

    ELSIF NEW.event_type = 'BUNDLE_READY' THEN
        IF NEW.authority_type <> 'CREDENTIAL_BUNDLE' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'BUNDLE_READY must reference credential bundle authority';
        END IF;
        SELECT principal_id, bundle_state
          INTO bundle_principal_id, bundle_state_value
          FROM nexilabs_auth.credential_bundle
         WHERE bundle_id = NEW.authority_id;
        IF bundle_state_value IS DISTINCT FROM 'READY'
           OR NOT EXISTS (
                SELECT 1 FROM nexilabs_auth.developer_setup
                 WHERE request_id = NEW.request_id
                   AND resulting_principal_id = bundle_principal_id
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'BUNDLE_READY requires READY same-enrollment bundle authority';
        END IF;

    ELSIF NEW.event_type = 'DELIVERY_ISSUED' THEN
        IF NEW.authority_type <> 'CREDENTIAL_DELIVERY' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'DELIVERY_ISSUED must reference credential delivery authority';
        END IF;
        SELECT b.principal_id, d.delivery_state
          INTO delivery_principal_id, delivery_state_value
          FROM nexilabs_auth.credential_delivery AS d
          JOIN nexilabs_auth.credential_bundle AS b ON b.bundle_id = d.bundle_id
         WHERE d.delivery_id = NEW.authority_id;
        IF delivery_state_value IS DISTINCT FROM 'ISSUED'
           OR NOT EXISTS (
                SELECT 1 FROM nexilabs_auth.developer_setup
                 WHERE request_id = NEW.request_id
                   AND resulting_principal_id = delivery_principal_id
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'DELIVERY_ISSUED requires ISSUED same-enrollment delivery authority';
        END IF;

    ELSIF NEW.event_type = 'ACCOUNT_ACTIVATED' THEN
        IF NEW.authority_type <> 'PRINCIPAL_ACCOUNT' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'ACCOUNT_ACTIVATED must reference principal account authority';
        END IF;
        SELECT identity_type, account_state
          INTO principal_identity_value, principal_state_value
          FROM nexilabs_auth.principal_account
         WHERE principal_id = NEW.authority_id;
        IF principal_identity_value IS DISTINCT FROM 'nexadevs_developer'
           OR principal_state_value IS DISTINCT FROM 'ACTIVE'
           OR NOT EXISTS (
                SELECT 1 FROM nexilabs_auth.developer_setup
                 WHERE request_id = NEW.request_id
                   AND resulting_principal_id = NEW.authority_id
           ) THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'ACCOUNT_ACTIVATED requires ACTIVE same-enrollment Developer principal';
        END IF;
    END IF;

    IF NEW.causation_event_id IS NOT NULL THEN
        SELECT request_id, occurred_at
          INTO causation_request_id, causation_occurred_at
          FROM nexilabs_auth.enrollment_event
         WHERE event_id = NEW.causation_event_id;
        IF causation_request_id IS DISTINCT FROM NEW.request_id
           OR causation_occurred_at > NEW.occurred_at THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'causation event must belong to the same request and not occur later';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_enrollment_event_authority
BEFORE INSERT
ON nexilabs_auth.enrollment_event
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_enrollment_event_authority();

CREATE FUNCTION nexilabs_auth.reject_enrollment_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION USING
        ERRCODE = '55000',
        MESSAGE = 'enrollment events are immutable append-only authority';
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_enrollment_event_immutable
BEFORE UPDATE OR DELETE
ON nexilabs_auth.enrollment_event
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.reject_enrollment_event_mutation();


CREATE TABLE nexilabs_auth.notification_delivery (
    notification_id text PRIMARY KEY,
    event_id text NOT NULL,
    template_code text NOT NULL,
    template_version integer NOT NULL DEFAULT 1,
    recipient_reference text NOT NULL,
    provider_message_reference text NULL,
    delivery_state text NOT NULL DEFAULT 'QUEUED',
    queued_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at timestamptz NULL,
    failed_at timestamptz NULL,
    failure_code text NULL,

    CONSTRAINT fk_nexilabs_auth_notification_delivery_event
        FOREIGN KEY (event_id)
        REFERENCES nexilabs_auth.enrollment_event(event_id),
    CONSTRAINT ck_nexilabs_auth_notification_id_nonblank CHECK (
        length(btrim(notification_id)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_notification_template CHECK (
        template_code IN (
            'DEVELOPER_REQUEST_RECEIVED', 'ADMIN_DEVELOPER_REQUEST_ALERT',
            'DEVELOPER_REQUEST_APPROVED', 'DEVELOPER_REQUEST_REJECTED',
            'DEVELOPER_SETUP_ISSUED', 'EMAIL_VERIFICATION_OTP',
            'CREDENTIAL_BUNDLE_READY', 'DEVELOPER_WELCOME', 'SECURITY_ALERT'
        )
    ),
    CONSTRAINT ck_nexilabs_auth_notification_template_version CHECK (
        template_version > 0
    ),
    CONSTRAINT ck_nexilabs_auth_notification_recipient_reference CHECK (
        length(btrim(recipient_reference)) BETWEEN 1 AND 1024
        AND recipient_reference = btrim(recipient_reference)
        AND recipient_reference !~ '@'
        AND recipient_reference !~ '[[:space:]]'
        AND recipient_reference !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'
    ),
    CONSTRAINT ck_nexilabs_auth_notification_provider_reference CHECK (
        provider_message_reference IS NULL
        OR (
            length(btrim(provider_message_reference)) BETWEEN 1 AND 1024
            AND provider_message_reference = btrim(provider_message_reference)
            AND provider_message_reference !~ '@'
            AND provider_message_reference !~ '[[:space:]]'
            AND provider_message_reference !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'
        )
    ),
    CONSTRAINT ck_nexilabs_auth_notification_delivery_state CHECK (
        delivery_state IN ('QUEUED', 'SENT', 'FAILED')
    ),
    CONSTRAINT ck_nexilabs_auth_notification_terminal_evidence CHECK (
        (
            delivery_state = 'QUEUED'
            AND sent_at IS NULL AND failed_at IS NULL AND failure_code IS NULL
        )
        OR (
            delivery_state = 'SENT'
            AND sent_at IS NOT NULL AND sent_at >= queued_at
            AND failed_at IS NULL AND failure_code IS NULL
        )
        OR (
            delivery_state = 'FAILED'
            AND failed_at IS NOT NULL AND failed_at >= queued_at
            AND sent_at IS NULL
            AND failure_code ~ '^[A-Z][A-Z0-9_]{2,79}$'
        )
    )
);

CREATE INDEX ix_nexilabs_auth_notification_delivery_event
    ON nexilabs_auth.notification_delivery (event_id, queued_at, notification_id);
CREATE INDEX ix_nexilabs_auth_notification_delivery_state
    ON nexilabs_auth.notification_delivery (delivery_state, queued_at);
CREATE INDEX ix_nexilabs_auth_notification_delivery_template
    ON nexilabs_auth.notification_delivery (template_code, queued_at);

CREATE FUNCTION nexilabs_auth.validate_notification_event_template()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    event_type_value text;
BEGIN
    SELECT event_type INTO event_type_value
      FROM nexilabs_auth.enrollment_event
     WHERE event_id = NEW.event_id;

    IF NEW.template_code = 'DEVELOPER_REQUEST_RECEIVED'
       AND event_type_value IS DISTINCT FROM 'REQUEST_RECEIVED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'request-received template requires REQUEST_RECEIVED event';
    ELSIF NEW.template_code = 'ADMIN_DEVELOPER_REQUEST_ALERT'
       AND event_type_value IS DISTINCT FROM 'REQUEST_RECEIVED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'Admin request alert requires REQUEST_RECEIVED event';
    ELSIF NEW.template_code = 'DEVELOPER_REQUEST_APPROVED'
       AND event_type_value IS DISTINCT FROM 'APPROVED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'approval template requires APPROVED event';
    ELSIF NEW.template_code = 'DEVELOPER_REQUEST_REJECTED'
       AND event_type_value IS DISTINCT FROM 'REJECTED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'rejection template requires REJECTED event';
    ELSIF NEW.template_code = 'DEVELOPER_SETUP_ISSUED'
       AND event_type_value IS DISTINCT FROM 'SETUP_ISSUED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'Setup template requires SETUP_ISSUED event';
    ELSIF NEW.template_code = 'EMAIL_VERIFICATION_OTP'
       AND event_type_value IS DISTINCT FROM 'OTP_ISSUED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'OTP template requires OTP_ISSUED event';
    ELSIF NEW.template_code = 'CREDENTIAL_BUNDLE_READY'
       AND event_type_value IS DISTINCT FROM 'BUNDLE_READY' THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'bundle-ready template requires BUNDLE_READY event';
    ELSIF NEW.template_code = 'DEVELOPER_WELCOME'
       AND event_type_value IS DISTINCT FROM 'ACCOUNT_ACTIVATED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'welcome template requires ACCOUNT_ACTIVATED event';
    END IF;

    IF NEW.template_code IN ('ADMIN_DEVELOPER_REQUEST_ALERT', 'SECURITY_ALERT') THEN
        IF NEW.recipient_reference <> 'NEXILABS_ADMIN_OPERATIONS' THEN
            RAISE EXCEPTION USING ERRCODE = '23514',
                MESSAGE = 'operations notification must use logical operations recipient reference';
        END IF;
    ELSIF NEW.recipient_reference = 'NEXILABS_ADMIN_OPERATIONS' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'applicant notification cannot use operations recipient reference';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_notification_event_template
BEFORE INSERT
ON nexilabs_auth.notification_delivery
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_notification_event_template();

CREATE FUNCTION nexilabs_auth.validate_notification_delivery_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'notification delivery evidence is durable authority and cannot be deleted';
    END IF;

    IF OLD.delivery_state <> 'QUEUED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'terminal notification delivery evidence is immutable';
    END IF;

    IF NEW.notification_id IS DISTINCT FROM OLD.notification_id
       OR NEW.event_id IS DISTINCT FROM OLD.event_id
       OR NEW.template_code IS DISTINCT FROM OLD.template_code
       OR NEW.template_version IS DISTINCT FROM OLD.template_version
       OR NEW.recipient_reference IS DISTINCT FROM OLD.recipient_reference
       OR NEW.queued_at IS DISTINCT FROM OLD.queued_at THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'notification identity, event, template, recipient and queue time are immutable';
    END IF;

    IF OLD.provider_message_reference IS NOT NULL
       AND NEW.provider_message_reference IS DISTINCT FROM OLD.provider_message_reference THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'provider message reference is immutable once recorded';
    END IF;

    IF NEW.delivery_state NOT IN ('QUEUED', 'SENT', 'FAILED') THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'invalid notification delivery transition';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_notification_delivery_transition
BEFORE UPDATE OR DELETE
ON nexilabs_auth.notification_delivery
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_notification_delivery_transition();


CREATE TABLE nexilabs_auth.audit_export (
    export_id text PRIMARY KEY,
    requested_by_admin_operator_id text NOT NULL,
    report_type text NOT NULL,
    filter_reference text NOT NULL,
    object_provider_code text NOT NULL,
    object_key text NOT NULL,
    content_sha256 text NOT NULL,
    byte_size bigint NOT NULL,
    export_state text NOT NULL DEFAULT 'AVAILABLE',
    generated_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamptz NOT NULL,
    retention_until timestamptz NOT NULL,
    expired_at timestamptz NULL,
    retired_at timestamptz NULL,

    CONSTRAINT fk_nexilabs_auth_audit_export_admin_operator
        FOREIGN KEY (requested_by_admin_operator_id)
        REFERENCES nexilabs_auth.admin_operator(admin_operator_id),
    CONSTRAINT ck_nexilabs_auth_audit_export_id_nonblank CHECK (
        length(btrim(export_id)) BETWEEN 1 AND 255
    ),
    CONSTRAINT ck_nexilabs_auth_audit_export_report_type CHECK (
        report_type ~ '^[A-Z][A-Z0-9_]{2,79}$'
    ),
    CONSTRAINT ck_nexilabs_auth_audit_export_filter_reference CHECK (
        length(btrim(filter_reference)) BETWEEN 1 AND 2048
        AND filter_reference = btrim(filter_reference)
        AND filter_reference ~ '^[A-Z][A-Z0-9_]{2,79}:[A-Za-z0-9][A-Za-z0-9._:/=-]{0,1966}$'
        AND filter_reference !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'
    ),
    CONSTRAINT ck_nexilabs_auth_audit_export_object_provider CHECK (
        object_provider_code ~ '^[A-Z][A-Z0-9_]{2,79}$'
    ),
    CONSTRAINT ck_nexilabs_auth_audit_export_object_key CHECK (
        length(btrim(object_key)) BETWEEN 1 AND 2048
        AND object_key = btrim(object_key)
        AND object_key !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'
    ),
    CONSTRAINT ck_nexilabs_auth_audit_export_sha256 CHECK (
        content_sha256 ~ '^[0-9a-f]{64}$'
    ),
    CONSTRAINT ck_nexilabs_auth_audit_export_byte_size CHECK (
        byte_size > 0
    ),
    CONSTRAINT ck_nexilabs_auth_audit_export_state CHECK (
        export_state IN ('AVAILABLE', 'EXPIRED', 'RETIRED')
    ),
    CONSTRAINT ck_nexilabs_auth_audit_export_retention CHECK (
        expires_at > generated_at
        AND retention_until >= expires_at
    ),
    CONSTRAINT ck_nexilabs_auth_audit_export_state_timestamps CHECK (
        (
            export_state = 'AVAILABLE'
            AND expired_at IS NULL AND retired_at IS NULL
        )
        OR (
            export_state = 'EXPIRED'
            AND expired_at IS NOT NULL AND retired_at IS NULL
        )
        OR (
            export_state = 'RETIRED'
            AND retired_at IS NOT NULL
        )
    ),
    CONSTRAINT ck_nexilabs_auth_audit_export_expired_time CHECK (
        expired_at IS NULL OR expired_at >= expires_at
    ),
    CONSTRAINT ck_nexilabs_auth_audit_export_retired_time CHECK (
        retired_at IS NULL OR retired_at >= retention_until
    )
);

CREATE UNIQUE INDEX ux_nexilabs_auth_audit_export_object
    ON nexilabs_auth.audit_export (object_provider_code, object_key);
CREATE INDEX ix_nexilabs_auth_audit_export_admin
    ON nexilabs_auth.audit_export (requested_by_admin_operator_id, generated_at DESC);
CREATE INDEX ix_nexilabs_auth_audit_export_state_expiry
    ON nexilabs_auth.audit_export (export_state, expires_at);

CREATE FUNCTION nexilabs_auth.validate_audit_export_requester()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    operator_state_value text;
BEGIN
    SELECT admin_state INTO operator_state_value
      FROM nexilabs_auth.admin_operator
     WHERE admin_operator_id = NEW.requested_by_admin_operator_id;

    IF operator_state_value IS DISTINCT FROM 'ACTIVE' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'audit export requires an ACTIVE Admin Operator requester';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_audit_export_requester
BEFORE INSERT
ON nexilabs_auth.audit_export
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_audit_export_requester();

CREATE FUNCTION nexilabs_auth.validate_audit_export_transition()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION USING ERRCODE = '55000',
            MESSAGE = 'audit export metadata is durable authority and cannot be deleted';
    END IF;

    IF OLD.export_state = 'RETIRED' THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'retired audit export metadata is immutable';
    END IF;

    IF NEW.export_id IS DISTINCT FROM OLD.export_id
       OR NEW.requested_by_admin_operator_id IS DISTINCT FROM OLD.requested_by_admin_operator_id
       OR NEW.report_type IS DISTINCT FROM OLD.report_type
       OR NEW.filter_reference IS DISTINCT FROM OLD.filter_reference
       OR NEW.object_provider_code IS DISTINCT FROM OLD.object_provider_code
       OR NEW.object_key IS DISTINCT FROM OLD.object_key
       OR NEW.content_sha256 IS DISTINCT FROM OLD.content_sha256
       OR NEW.byte_size IS DISTINCT FROM OLD.byte_size
       OR NEW.generated_at IS DISTINCT FROM OLD.generated_at
       OR NEW.expires_at IS DISTINCT FROM OLD.expires_at
       OR NEW.retention_until IS DISTINCT FROM OLD.retention_until THEN
        RAISE EXCEPTION USING ERRCODE = '23514',
            MESSAGE = 'audit export identity, query reference, artifact integrity and retention are immutable';
    END IF;

    IF OLD.export_state = 'AVAILABLE'
       AND NEW.export_state NOT IN ('AVAILABLE', 'EXPIRED', 'RETIRED') THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'invalid AVAILABLE audit export transition';
    END IF;
    IF OLD.export_state = 'EXPIRED'
       AND NEW.export_state NOT IN ('EXPIRED', 'RETIRED') THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'expired audit export cannot become available again';
    END IF;

    IF OLD.expired_at IS NOT NULL
       AND NEW.expired_at IS DISTINCT FROM OLD.expired_at THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'audit export expired_at is immutable once set';
    END IF;
    IF OLD.retired_at IS NOT NULL
       AND NEW.retired_at IS DISTINCT FROM OLD.retired_at THEN
        RAISE EXCEPTION USING ERRCODE = '23514', MESSAGE = 'audit export retired_at is immutable once set';
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER tr_nexilabs_auth_audit_export_transition
BEFORE UPDATE OR DELETE
ON nexilabs_auth.audit_export
FOR EACH ROW
EXECUTE FUNCTION nexilabs_auth.validate_audit_export_transition();

COMMENT ON TABLE nexilabs_auth.enrollment_event IS
    'P006.UI.10.2.F immutable Developer-enrollment lifecycle evidence referencing predecessor authority; not a duplicate current-state store.';
COMMENT ON TABLE nexilabs_auth.notification_delivery IS
    'Provider-neutral notification delivery evidence only; rendered message bodies and provider credentials are excluded.';
COMMENT ON COLUMN nexilabs_auth.notification_delivery.recipient_reference IS
    'Opaque logical recipient reference only; never a persisted email address.';
COMMENT ON COLUMN nexilabs_auth.notification_delivery.provider_message_reference IS
    'Optional provider-issued message reference only; never provider credentials or rendered message content.';
COMMENT ON TABLE nexilabs_auth.audit_export IS
    'Governed elevated-Admin audit export artifact metadata; report bytes remain outside PostgreSQL.';
COMMENT ON COLUMN nexilabs_auth.audit_export.filter_reference IS
    'Opaque governed report/filter reference only; never raw SQL or unrestricted query payload.';
COMMENT ON COLUMN nexilabs_auth.audit_export.object_key IS
    'Private object-storage reference only; never a public, permanent or presigned URL.';

REVOKE ALL ON TABLE nexilabs_auth.enrollment_event FROM PUBLIC;
REVOKE ALL ON TABLE nexilabs_auth.notification_delivery FROM PUBLIC;
REVOKE ALL ON TABLE nexilabs_auth.audit_export FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_enrollment_event_authority() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.reject_enrollment_event_mutation() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_notification_event_template() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_notification_delivery_transition() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_audit_export_requester() FROM PUBLIC;
REVOKE ALL ON FUNCTION nexilabs_auth.validate_audit_export_transition() FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA nexilabs_auth FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA nexilabs_auth FROM PUBLIC;

COMMIT;
