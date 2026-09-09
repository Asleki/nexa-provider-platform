BEGIN;

-- P006.UI.10.2.F rollback.
-- Intended for disposable/safe qualification targets only. Production migration
-- history is forward-only; this rollback must never be used as a production
-- shortcut and deliberately uses only narrow object drops.

DROP TRIGGER IF EXISTS tr_nexilabs_auth_audit_export_transition ON nexilabs_auth.audit_export;
DROP TRIGGER IF EXISTS tr_nexilabs_auth_audit_export_requester ON nexilabs_auth.audit_export;
DROP TRIGGER IF EXISTS tr_nexilabs_auth_notification_delivery_transition ON nexilabs_auth.notification_delivery;
DROP TRIGGER IF EXISTS tr_nexilabs_auth_notification_event_template ON nexilabs_auth.notification_delivery;
DROP TRIGGER IF EXISTS tr_nexilabs_auth_enrollment_event_immutable ON nexilabs_auth.enrollment_event;
DROP TRIGGER IF EXISTS tr_nexilabs_auth_enrollment_event_authority ON nexilabs_auth.enrollment_event;

DROP TABLE IF EXISTS nexilabs_auth.audit_export;
DROP TABLE IF EXISTS nexilabs_auth.notification_delivery;
DROP TABLE IF EXISTS nexilabs_auth.enrollment_event;

DROP FUNCTION IF EXISTS nexilabs_auth.validate_audit_export_transition();
DROP FUNCTION IF EXISTS nexilabs_auth.validate_audit_export_requester();
DROP FUNCTION IF EXISTS nexilabs_auth.validate_notification_delivery_transition();
DROP FUNCTION IF EXISTS nexilabs_auth.validate_notification_event_template();
DROP FUNCTION IF EXISTS nexilabs_auth.reject_enrollment_event_mutation();
DROP FUNCTION IF EXISTS nexilabs_auth.validate_enrollment_event_authority();

COMMIT;
