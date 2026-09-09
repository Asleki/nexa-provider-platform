BEGIN;

-- Restore the exact Sequence 35 audit-export filter-reference constraint.
-- This rollback is for disposable/safe qualification targets only.

ALTER TABLE nexilabs_auth.audit_export
    DROP CONSTRAINT ck_nexilabs_auth_audit_export_filter_reference;

ALTER TABLE nexilabs_auth.audit_export
    ADD CONSTRAINT ck_nexilabs_auth_audit_export_filter_reference CHECK (
        length(btrim(filter_reference)) BETWEEN 1 AND 2048
        AND filter_reference = btrim(filter_reference)
        AND filter_reference ~ '^[A-Z][A-Z0-9_]{2,79}:[A-Za-z0-9][A-Za-z0-9._:/=-]{0,1966}$'
        AND filter_reference !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'
    );

COMMIT;
