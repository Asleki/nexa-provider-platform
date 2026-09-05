"""P006.UI.10.2 — Governed PostgreSQL account persistence foundation."""

from .contracts import (
    CredentialVerifierRecord,
    DeveloperSetupVerifierRecord,
    EnigmaCatalogueEntryRecord,
    PrimaryEmailRecord,
)
from .postgresql_account_authority import (
    AccountPersistenceError,
    PostgreSQLAccountAuthority,
)

__all__ = [
    "AccountPersistenceError",
    "CredentialVerifierRecord",
    "DeveloperSetupVerifierRecord",
    "EnigmaCatalogueEntryRecord",
    "PostgreSQLAccountAuthority",
    "PrimaryEmailRecord",
]
