BEGIN;
DROP FUNCTION IF EXISTS geography.nngla_claim_runtime_command(text,text,integer,text,text,text,text,text);
DROP TABLE IF EXISTS geography.nngla_runtime_bulk_operation_receipt;
DROP TABLE IF EXISTS geography.nngla_runtime_command_receipt;
COMMIT;
