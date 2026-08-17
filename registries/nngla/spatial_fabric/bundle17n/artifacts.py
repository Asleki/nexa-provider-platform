"""Bundle 17N governed artifact catalogue."""
from ._shared import (
    COMMAND_CATALOGUE_PATH, COMMAND_AUTHORIZATION_PATH, BULK_POLICY_PATH,
    IDEMPOTENCY_POLICY_PATH, VALIDATION_RULES_PATH, FOUNDATION_AUTHORITY_MATRIX_PATH, SCHEMA_PATH,
)
def artifact_paths():
    return {
        "command_catalogue": COMMAND_CATALOGUE_PATH,
        "command_authorization": COMMAND_AUTHORIZATION_PATH,
        "bulk_policy": BULK_POLICY_PATH,
        "idempotency_policy": IDEMPOTENCY_POLICY_PATH,
        "validation_rules": VALIDATION_RULES_PATH,
        "foundation_authority_matrix": FOUNDATION_AUTHORITY_MATRIX_PATH,
        "schema": SCHEMA_PATH,
    }
__all__=["artifact_paths"]
