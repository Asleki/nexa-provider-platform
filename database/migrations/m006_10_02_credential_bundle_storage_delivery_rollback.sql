BEGIN;

-- P006.UI.10.2.E rollback for disposable/safe qualification targets only.
-- Live AWS rollback is not a qualification shortcut.

DROP TRIGGER IF EXISTS tr_nexilabs_auth_credential_delivery_transition
    ON nexilabs_auth.credential_delivery;
DROP TRIGGER IF EXISTS tr_nexilabs_auth_credential_delivery_bundle
    ON nexilabs_auth.credential_delivery;
DROP TRIGGER IF EXISTS tr_nexilabs_auth_credential_bundle_secret_transition
    ON nexilabs_auth.credential_bundle_secret;
DROP TRIGGER IF EXISTS tr_nexilabs_auth_credential_bundle_transition
    ON nexilabs_auth.credential_bundle;
DROP TRIGGER IF EXISTS tr_nexilabs_auth_credential_bundle_owner
    ON nexilabs_auth.credential_bundle;

DROP FUNCTION IF EXISTS nexilabs_auth.validate_credential_delivery_transition();
DROP FUNCTION IF EXISTS nexilabs_auth.validate_credential_delivery_bundle();
DROP FUNCTION IF EXISTS nexilabs_auth.validate_credential_bundle_secret_transition();
DROP FUNCTION IF EXISTS nexilabs_auth.validate_credential_bundle_transition();
DROP FUNCTION IF EXISTS nexilabs_auth.validate_credential_bundle_owner();

DROP TABLE IF EXISTS nexilabs_auth.credential_delivery;
DROP TABLE IF EXISTS nexilabs_auth.credential_bundle_secret;
DROP TABLE IF EXISTS nexilabs_auth.credential_bundle;

COMMIT;
