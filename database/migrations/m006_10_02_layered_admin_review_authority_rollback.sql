BEGIN;

-- P006.UI.10.2.C rollback for disposable/safe qualification targets only.
-- Live AWS rollback is not a qualification shortcut.

ALTER TABLE nexilabs_auth.developer_access_request
    DROP CONSTRAINT IF EXISTS fk_nexilabs_auth_request_terminal_decision;

DROP TRIGGER IF EXISTS tr_nexilabs_auth_developer_access_decision_immutable
    ON nexilabs_auth.developer_access_decision;
DROP TRIGGER IF EXISTS tr_nexilabs_auth_developer_access_decision_reviewer
    ON nexilabs_auth.developer_access_decision;

DROP TABLE IF EXISTS nexilabs_auth.developer_access_decision;

ALTER TABLE nexilabs_auth.developer_access_request
    DROP CONSTRAINT IF EXISTS ck_nexilabs_auth_request_terminal_decision_presence,
    DROP CONSTRAINT IF EXISTS uq_nexilabs_auth_request_terminal_projection,
    DROP COLUMN IF EXISTS terminal_decision_id;

DROP INDEX IF EXISTS nexilabs_auth.ux_nexilabs_auth_active_admin_password;

DROP TRIGGER IF EXISTS tr_nexilabs_auth_admin_operator_binding
    ON nexilabs_auth.admin_operator;

DROP TABLE IF EXISTS nexilabs_auth.admin_operator;

DROP FUNCTION IF EXISTS nexilabs_auth.reject_developer_access_decision_mutation();
DROP FUNCTION IF EXISTS nexilabs_auth.validate_developer_access_decision_reviewer();
DROP FUNCTION IF EXISTS nexilabs_auth.validate_admin_operator_binding();

ALTER TABLE nexilabs_auth.account_email
    DROP CONSTRAINT IF EXISTS uq_nexilabs_auth_email_id_principal;

COMMIT;
