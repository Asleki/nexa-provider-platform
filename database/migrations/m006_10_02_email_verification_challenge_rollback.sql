BEGIN;

-- P006.UI.10.2.D rollback is for disposable/safe qualification targets only.
-- Live governed AWS authorities are never destructively rolled back as a
-- qualification shortcut.

DROP TRIGGER IF EXISTS tr_nexilabs_auth_email_verification_challenge_transition
    ON nexilabs_auth.email_verification_challenge;
DROP TRIGGER IF EXISTS tr_nexilabs_auth_email_verification_challenge_email
    ON nexilabs_auth.email_verification_challenge;
DROP FUNCTION IF EXISTS nexilabs_auth.validate_email_verification_challenge_transition();
DROP FUNCTION IF EXISTS nexilabs_auth.validate_email_verification_challenge_email();
DROP TABLE IF EXISTS nexilabs_auth.email_verification_challenge;

COMMIT;
