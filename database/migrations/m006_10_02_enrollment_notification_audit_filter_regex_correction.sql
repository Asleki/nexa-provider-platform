BEGIN;

-- P006.UI.10.2.F Sequence 36
-- Audit-export filter-reference PostgreSQL regular-expression correction.
--
-- Sequence 35 remains immutable. PostgreSQL stores the original CHECK
-- expression but rejects row evaluation because its oversized bounded
-- repetition exceeds the engine's supported range. The independent length
-- constraint already governs the 2048-character maximum, so this correction
-- preserves the same accepted character set and prefix contract while using
-- a PostgreSQL-safe tail quantifier.

ALTER TABLE nexilabs_auth.audit_export
    DROP CONSTRAINT ck_nexilabs_auth_audit_export_filter_reference;

ALTER TABLE nexilabs_auth.audit_export
    ADD CONSTRAINT ck_nexilabs_auth_audit_export_filter_reference CHECK (
        length(btrim(filter_reference)) BETWEEN 1 AND 2048
        AND filter_reference = btrim(filter_reference)
        AND filter_reference ~ '^[A-Z][A-Z0-9_]{2,79}:[A-Za-z0-9][A-Za-z0-9._:/=-]*$'
        AND filter_reference !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'
    );

COMMIT;
