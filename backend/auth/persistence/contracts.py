"""P006.UI.10.2 — Stable records for governed account persistence reads."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CredentialVerifierRecord:
    credential_id: str
    principal_id: str
    credential_kind: str
    verifier_scheme: str
    verifier_version: int
    verifier_payload: str


@dataclass(frozen=True, slots=True)
class PrimaryEmailRecord:
    email_id: str
    principal_id: str
    email_address: str
    verification_state: str
    verified_at: str | None


@dataclass(frozen=True, slots=True)
class DeveloperSetupVerifierRecord:
    developer_setup_id: str
    request_id: str
    setup_lookup_key: str
    verifier_scheme: str
    verifier_version: int
    verifier_payload: str
    setup_state: str
    issued_at: str
    expires_at: str
    consumed_at: str | None
    revoked_at: str | None
    resulting_principal_id: str | None


@dataclass(frozen=True, slots=True)
class EnigmaCatalogueEntryRecord:
    catalogue_id: str
    profile_id: str
    word_length: int
    day_of_month: int
    period: str
    words: tuple[str, str, str]


__all__ = [
    "CredentialVerifierRecord",
    "DeveloperSetupVerifierRecord",
    "EnigmaCatalogueEntryRecord",
    "PrimaryEmailRecord",
]
