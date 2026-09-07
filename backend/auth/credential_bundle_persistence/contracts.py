"""P006.UI.10.2.E — stable contracts for credential bundle/storage/delivery persistence."""
from __future__ import annotations

from dataclasses import dataclass, field


CREDENTIAL_BUNDLE_STATES = (
    "GENERATED",
    "READY",
    "EXPIRED",
    "RETIRED",
    "INVALIDATED",
)
TERMINAL_CREDENTIAL_BUNDLE_STATES = (
    "EXPIRED",
    "RETIRED",
    "INVALIDATED",
)
CREDENTIAL_DELIVERY_STATES = (
    "ISSUED",
    "CONSUMED",
    "EXPIRED",
    "REVOKED",
)
TERMINAL_CREDENTIAL_DELIVERY_STATES = (
    "CONSUMED",
    "EXPIRED",
    "REVOKED",
)


class CredentialBundlePersistenceError(RuntimeError):
    """Raised when persisted bundle/delivery authority violates its contract."""


class CredentialBundleQualificationError(RuntimeError):
    """Raised when PostgreSQL does not match the P006.UI.10.2.E authority."""


def _nonblank(value: object, name: str, *, maximum: int = 255) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-blank text")
    normalized = value.strip()
    if len(normalized) > maximum:
        raise ValueError(f"{name} must be at most {maximum} characters")
    return normalized


@dataclass(frozen=True, slots=True)
class CredentialBundleRecord:
    bundle_id: str
    principal_id: str
    enigma_profile_id: str
    bundle_state: str
    object_provider_code: str
    object_key: str = field(repr=False)
    content_sha256: str
    byte_size: int
    created_at: str
    integrity_verified_at: str | None
    object_confirmed_at: str | None
    ready_at: str | None
    expires_at: str
    retention_until: str
    invalidated_at: str | None
    retired_at: str | None

    def safe_summary(self) -> dict[str, object]:
        """Return diagnostics without exposing the private object key."""
        return {
            "bundleId": self.bundle_id,
            "principalId": self.principal_id,
            "enigmaProfileId": self.enigma_profile_id,
            "bundleState": self.bundle_state,
            "objectProviderCode": self.object_provider_code,
            "contentSha256": self.content_sha256,
            "byteSize": self.byte_size,
            "createdAt": self.created_at,
            "integrityVerifiedAt": self.integrity_verified_at,
            "objectConfirmedAt": self.object_confirmed_at,
            "readyAt": self.ready_at,
            "expiresAt": self.expires_at,
            "retentionUntil": self.retention_until,
            "invalidatedAt": self.invalidated_at,
            "retiredAt": self.retired_at,
        }


@dataclass(frozen=True, slots=True)
class CredentialBundleSecretRecord:
    bundle_secret_id: str
    bundle_id: str
    escrow_provider_code: str
    encrypted_secret_reference: str = field(repr=False)
    encryption_context_version: str
    created_at: str
    retired_at: str | None

    def safe_summary(self) -> dict[str, object]:
        """Return metadata only; the encrypted-secret reference is intentionally excluded."""
        return {
            "bundleSecretId": self.bundle_secret_id,
            "bundleId": self.bundle_id,
            "escrowProviderCode": self.escrow_provider_code,
            "encryptionContextVersion": self.encryption_context_version,
            "createdAt": self.created_at,
            "retiredAt": self.retired_at,
        }


@dataclass(frozen=True, slots=True)
class CredentialDeliveryRecord:
    delivery_id: str
    bundle_id: str
    token_verifier_scheme: str
    token_verifier_version: int
    token_verifier_payload: str = field(repr=False)
    delivery_state: str = "ISSUED"
    policy_version: str = ""
    logical_delivery_host_code: str = ""
    issued_at: str = ""
    expires_at: str = ""
    consumed_at: str | None = None
    revoked_at: str | None = None
    download_count: int = 0
    first_downloaded_at: str | None = None
    last_downloaded_at: str | None = None

    def __post_init__(self) -> None:
        _nonblank(self.delivery_id, "delivery_id")
        _nonblank(self.bundle_id, "bundle_id")
        _nonblank(self.token_verifier_scheme, "token_verifier_scheme", maximum=80)
        if isinstance(self.token_verifier_version, bool) or not isinstance(
            self.token_verifier_version, int
        ) or self.token_verifier_version <= 0:
            raise ValueError("token_verifier_version must be a positive integer")
        if not isinstance(self.token_verifier_payload, str) or len(self.token_verifier_payload) < 20:
            raise ValueError("token_verifier_payload must contain opaque verifier material")
        if self.delivery_state not in CREDENTIAL_DELIVERY_STATES:
            raise ValueError("unsupported credential delivery state")
        _nonblank(self.policy_version, "policy_version")
        _nonblank(self.logical_delivery_host_code, "logical_delivery_host_code")
        if isinstance(self.download_count, bool) or not isinstance(self.download_count, int) or self.download_count < 0:
            raise ValueError("download_count must be a non-negative integer")

    def safe_summary(self) -> dict[str, object]:
        """Return non-secret diagnostics; verifier payload is intentionally excluded."""
        return {
            "deliveryId": self.delivery_id,
            "bundleId": self.bundle_id,
            "tokenVerifierScheme": self.token_verifier_scheme,
            "tokenVerifierVersion": self.token_verifier_version,
            "deliveryState": self.delivery_state,
            "policyVersion": self.policy_version,
            "logicalDeliveryHostCode": self.logical_delivery_host_code,
            "issuedAt": self.issued_at,
            "expiresAt": self.expires_at,
            "consumedAt": self.consumed_at,
            "revokedAt": self.revoked_at,
            "downloadCount": self.download_count,
            "firstDownloadedAt": self.first_downloaded_at,
            "lastDownloadedAt": self.last_downloaded_at,
        }


@dataclass(frozen=True, slots=True)
class CredentialBundleQualificationReport:
    phase: str
    database_name: str
    tls_active: bool
    repository_migration_count: int
    database_migration_count: int
    migration_tail_sequence: int
    migration_tail_id: str
    nexilabs_auth_tables: tuple[str, ...]
    public_schema_privilege_count: int
    public_table_privilege_count: int
    public_routine_privilege_count: int
    principal_count: int
    credential_count: int
    developer_request_count: int
    admin_operator_count: int
    developer_decision_count: int
    email_challenge_count: int
    enigma_catalogue_count: int
    enigma_catalogue_entry_count: int
    enigma_profile_count: int
    principal_enigma_profile_count: int
    bundle_count: int
    bundle_secret_count: int
    delivery_count: int

    def safe_summary(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "databaseName": self.database_name,
            "tlsActive": self.tls_active,
            "repositoryMigrationCount": self.repository_migration_count,
            "databaseMigrationCount": self.database_migration_count,
            "migrationTailSequence": self.migration_tail_sequence,
            "migrationTailId": self.migration_tail_id,
            "nexilabsAuthTables": list(self.nexilabs_auth_tables),
            "publicSchemaPrivilegeCount": self.public_schema_privilege_count,
            "publicTablePrivilegeCount": self.public_table_privilege_count,
            "publicRoutinePrivilegeCount": self.public_routine_privilege_count,
            "principalCount": self.principal_count,
            "credentialCount": self.credential_count,
            "developerRequestCount": self.developer_request_count,
            "adminOperatorCount": self.admin_operator_count,
            "developerDecisionCount": self.developer_decision_count,
            "emailChallengeCount": self.email_challenge_count,
            "enigmaCatalogueCount": self.enigma_catalogue_count,
            "enigmaCatalogueEntryCount": self.enigma_catalogue_entry_count,
            "enigmaProfileCount": self.enigma_profile_count,
            "principalEnigmaProfileCount": self.principal_enigma_profile_count,
            "bundleCount": self.bundle_count,
            "bundleSecretCount": self.bundle_secret_count,
            "deliveryCount": self.delivery_count,
        }


@dataclass(frozen=True, slots=True)
class CredentialBundleAdapterQualificationReceipt:
    bundle_id: str
    principal_id: str
    enigma_profile_id: str
    bundle_secret_id: str
    delivery_id: str
    bundle_state: str
    delivery_state: str
    rollback_verified: bool

    def safe_summary(self) -> dict[str, object]:
        return {
            "bundleId": self.bundle_id,
            "principalId": self.principal_id,
            "enigmaProfileId": self.enigma_profile_id,
            "bundleSecretId": self.bundle_secret_id,
            "deliveryId": self.delivery_id,
            "bundleState": self.bundle_state,
            "deliveryState": self.delivery_state,
            "rollbackVerified": self.rollback_verified,
        }


__all__ = [
    "CREDENTIAL_BUNDLE_STATES",
    "CREDENTIAL_DELIVERY_STATES",
    "TERMINAL_CREDENTIAL_BUNDLE_STATES",
    "TERMINAL_CREDENTIAL_DELIVERY_STATES",
    "CredentialBundleAdapterQualificationReceipt",
    "CredentialBundlePersistenceError",
    "CredentialBundleQualificationError",
    "CredentialBundleQualificationReport",
    "CredentialBundleRecord",
    "CredentialBundleSecretRecord",
    "CredentialDeliveryRecord",
]
