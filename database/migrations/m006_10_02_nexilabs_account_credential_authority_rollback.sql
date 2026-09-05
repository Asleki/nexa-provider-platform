BEGIN;

DROP TABLE IF EXISTS nexilabs_auth.principal_enigma_profile;
DROP TABLE IF EXISTS nexilabs_auth.enigma_profile_catalogue;
DROP TABLE IF EXISTS nexilabs_auth.enigma_profile;
DROP TABLE IF EXISTS nexilabs_auth.enigma_catalogue_entry;
DROP TABLE IF EXISTS nexilabs_auth.enigma_catalogue;
DROP TABLE IF EXISTS nexilabs_auth.developer_setup;
DROP TABLE IF EXISTS nexilabs_auth.developer_access_request;
DROP TABLE IF EXISTS nexilabs_auth.credential_verifier;
DROP TABLE IF EXISTS nexilabs_auth.account_email;
DROP TABLE IF EXISTS nexilabs_auth.principal_permission;
DROP TABLE IF EXISTS nexilabs_auth.principal_profile;
DROP TABLE IF EXISTS nexilabs_auth.principal_account;
DROP SCHEMA IF EXISTS nexilabs_auth;

COMMIT;
