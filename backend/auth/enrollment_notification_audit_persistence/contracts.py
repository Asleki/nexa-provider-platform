"""P006.UI.10.2.F — stable enrollment notification/mail/audit persistence contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
import re


ENROLLMENT_EVENT_TYPES = (
    "REQUEST_RECEIVED",
    "UNDER_REVIEW",
    "APPROVED",
    "REJECTED",
    "SETUP_ISSUED",
    "SETUP_VERIFIED",
    "OTP_ISSUED",
    "EMAIL_VERIFIED",
    "ENIGMA_PROVISIONED",
    "BUNDLE_READY",
    "DELIVERY_ISSUED",
    "ACCOUNT_ACTIVATED",
)

ENROLLMENT_AUTHORITY_TYPES = (
    "DEVELOPER_ACCESS_REQUEST",
    "DEVELOPER_ACCESS_DECISION",
    "DEVELOPER_SETUP",
    "EMAIL_VERIFICATION_CHALLENGE",
    "PRINCIPAL_ENIGMA_PROFILE",
    "CREDENTIAL_BUNDLE",
    "CREDENTIAL_DELIVERY",
    "PRINCIPAL_ACCOUNT",
)

EVENT_AUTHORITY_TYPES = {
    "REQUEST_RECEIVED": "DEVELOPER_ACCESS_REQUEST",
    "UNDER_REVIEW": "DEVELOPER_ACCESS_REQUEST",
    "APPROVED": "DEVELOPER_ACCESS_DECISION",
    "REJECTED": "DEVELOPER_ACCESS_DECISION",
    "SETUP_ISSUED": "DEVELOPER_SETUP",
    "SETUP_VERIFIED": "DEVELOPER_SETUP",
    "OTP_ISSUED": "EMAIL_VERIFICATION_CHALLENGE",
    "EMAIL_VERIFIED": "EMAIL_VERIFICATION_CHALLENGE",
    "ENIGMA_PROVISIONED": "PRINCIPAL_ENIGMA_PROFILE",
    "BUNDLE_READY": "CREDENTIAL_BUNDLE",
    "DELIVERY_ISSUED": "CREDENTIAL_DELIVERY",
    "ACCOUNT_ACTIVATED": "PRINCIPAL_ACCOUNT",
}

NOTIFICATION_TEMPLATE_CODES = (
    "DEVELOPER_REQUEST_RECEIVED",
    "ADMIN_DEVELOPER_REQUEST_ALERT",
    "DEVELOPER_REQUEST_APPROVED",
    "DEVELOPER_REQUEST_REJECTED",
    "DEVELOPER_SETUP_ISSUED",
    "EMAIL_VERIFICATION_OTP",
    "CREDENTIAL_BUNDLE_READY",
    "DEVELOPER_WELCOME",
    "SECURITY_ALERT",
)

NOTIFICATION_DELIVERY_STATES = ("QUEUED", "SENT", "FAILED")
TERMINAL_NOTIFICATION_DELIVERY_STATES = ("SENT", "FAILED")
ADMIN_OPERATIONS_RECIPIENT_REFERENCE = "NEXILABS_ADMIN_OPERATIONS"

AUDIT_EXPORT_STATES = ("AVAILABLE", "EXPIRED", "RETIRED")
TERMINAL_AUDIT_EXPORT_STATES = ("RETIRED",)

_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,79}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_URI = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
_FILTER_REFERENCE = re.compile(r"^[A-Z][A-Z0-9_]{2,79}:[A-Za-z0-9][A-Za-z0-9._:/=-]{0,1966}$")


class EnrollmentNotificationAuditPersistenceError(RuntimeError):
    """Raised when persisted F authority violates its stable contract."""


class EnrollmentNotificationAuditQualificationError(RuntimeError):
    """Raised when PostgreSQL does not match the P006.UI.10.2.F authority."""


def _nonblank(value: object, name: str, *, maximum: int = 255) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-blank text")
    normalized = value.strip()
    if len(normalized) > maximum:
        raise ValueError(f"{name} must be at most {maximum} characters")
    if "\n" in normalized or "\r" in normalized:
        raise ValueError(f"{name} must be single-line text")
    return normalized


def _code(value: object, name: str) -> str:
    normalized = _nonblank(value, name, maximum=80)
    if not _CODE.fullmatch(normalized):
        raise ValueError(f"{name} must be an uppercase governed code")
    return normalized


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _sha256(value: object, name: str) -> str:
    normalized = _nonblank(value, name, maximum=64)
    if not _SHA256.fullmatch(normalized):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return normalized


def _reference(value: object, name: str, *, maximum: int = 1024) -> str:
    normalized = _nonblank(value, name, maximum=maximum)
    if _URI.match(normalized):
        raise ValueError(f"{name} must be a private/logical reference, not a URL")
    return normalized


def _recipient_reference(value: object) -> str:
    normalized = _reference(value, "recipient_reference")
    if "@" in normalized:
        raise ValueError("recipient_reference must not embed an email address")
    if any(ch.isspace() for ch in normalized):
        raise ValueError("recipient_reference must be an opaque logical reference")
    return normalized


def _filter_reference(value: object) -> str:
    normalized = _reference(value, "filter_reference", maximum=2048)
    if not _FILTER_REFERENCE.fullmatch(normalized):
        raise ValueError("filter_reference must be an opaque governed reference, not an unrestricted query payload")
    return normalized


def _opaque_reference(value: object, name: str, *, maximum: int = 1024) -> str:
    normalized = _reference(value, name, maximum=maximum)
    if "@" in normalized or any(ch.isspace() for ch in normalized):
        raise ValueError(f"{name} must be an opaque non-PII reference")
    return normalized


@dataclass(frozen=True, slots=True)
class EnrollmentEventRecord:
    event_id: str
    request_id: str
    event_type: str
    authority_type: str
    authority_id: str
    occurred_at: str
    source_reference: str
    correlation_id: str | None = None
    causation_event_id: str | None = None

    def __post_init__(self) -> None:
        _nonblank(self.event_id, "event_id")
        _nonblank(self.request_id, "request_id")
        if self.event_type not in ENROLLMENT_EVENT_TYPES:
            raise ValueError("unsupported enrollment event type")
        if self.authority_type not in ENROLLMENT_AUTHORITY_TYPES:
            raise ValueError("unsupported enrollment authority type")
        expected = EVENT_AUTHORITY_TYPES[self.event_type]
        if self.authority_type != expected:
            raise ValueError(
                f"{self.event_type} requires authority_type {expected}"
            )
        _nonblank(self.authority_id, "authority_id")
        _nonblank(self.occurred_at, "occurred_at")
        _opaque_reference(self.source_reference, "source_reference")
        if self.correlation_id is not None:
            _opaque_reference(self.correlation_id, "correlation_id")
        if self.causation_event_id is not None:
            _nonblank(self.causation_event_id, "causation_event_id")
            if self.causation_event_id == self.event_id:
                raise ValueError("causation_event_id must not equal event_id")

    def safe_summary(self) -> dict[str, object]:
        return {
            "eventId": self.event_id,
            "requestId": self.request_id,
            "eventType": self.event_type,
            "authorityType": self.authority_type,
            "authorityId": self.authority_id,
            "occurredAt": self.occurred_at,
            "sourceReference": self.source_reference,
            "correlationId": self.correlation_id,
            "causationEventId": self.causation_event_id,
        }


@dataclass(frozen=True, slots=True)
class NotificationDeliveryRecord:
    notification_id: str
    event_id: str
    template_code: str
    template_version: int
    recipient_reference: str
    provider_message_reference: str | None = field(default=None, repr=False)
    delivery_state: str = "QUEUED"
    queued_at: str = ""
    sent_at: str | None = None
    failed_at: str | None = None
    failure_code: str | None = None

    def __post_init__(self) -> None:
        _nonblank(self.notification_id, "notification_id")
        _nonblank(self.event_id, "event_id")
        if self.template_code not in NOTIFICATION_TEMPLATE_CODES:
            raise ValueError("unsupported notification template code")
        _positive_int(self.template_version, "template_version")
        _recipient_reference(self.recipient_reference)
        if self.provider_message_reference is not None:
            _opaque_reference(
                self.provider_message_reference,
                "provider_message_reference",
                maximum=1024,
            )
        if self.delivery_state not in NOTIFICATION_DELIVERY_STATES:
            raise ValueError("unsupported notification delivery state")
        _nonblank(self.queued_at, "queued_at")
        if self.delivery_state == "QUEUED":
            if any(value is not None for value in (self.sent_at, self.failed_at, self.failure_code)):
                raise ValueError("QUEUED notification cannot carry terminal evidence")
        elif self.delivery_state == "SENT":
            _nonblank(self.sent_at, "sent_at")
            if self.failed_at is not None or self.failure_code is not None:
                raise ValueError("SENT notification cannot carry failure evidence")
        elif self.delivery_state == "FAILED":
            _nonblank(self.failed_at, "failed_at")
            _code(self.failure_code, "failure_code")
            if self.sent_at is not None:
                raise ValueError("FAILED notification cannot carry sent_at")

    def safe_summary(self) -> dict[str, object]:
        return {
            "notificationId": self.notification_id,
            "eventId": self.event_id,
            "templateCode": self.template_code,
            "templateVersion": self.template_version,
            "recipientReference": self.recipient_reference,
            "providerMessageReferencePresent": self.provider_message_reference is not None,
            "deliveryState": self.delivery_state,
            "queuedAt": self.queued_at,
            "sentAt": self.sent_at,
            "failedAt": self.failed_at,
            "failureCode": self.failure_code,
        }


@dataclass(frozen=True, slots=True)
class AuditExportRecord:
    export_id: str
    requested_by_admin_operator_id: str
    report_type: str
    filter_reference: str = field(repr=False)
    object_provider_code: str = ""
    object_key: str = field(default="", repr=False)
    content_sha256: str = ""
    byte_size: int = 0
    export_state: str = "AVAILABLE"
    generated_at: str = ""
    expires_at: str = ""
    retention_until: str = ""
    expired_at: str | None = None
    retired_at: str | None = None

    def __post_init__(self) -> None:
        _nonblank(self.export_id, "export_id")
        _nonblank(self.requested_by_admin_operator_id, "requested_by_admin_operator_id")
        _code(self.report_type, "report_type")
        _filter_reference(self.filter_reference)
        _code(self.object_provider_code, "object_provider_code")
        _reference(self.object_key, "object_key", maximum=2048)
        _sha256(self.content_sha256, "content_sha256")
        _positive_int(self.byte_size, "byte_size")
        if self.export_state not in AUDIT_EXPORT_STATES:
            raise ValueError("unsupported audit export state")
        _nonblank(self.generated_at, "generated_at")
        _nonblank(self.expires_at, "expires_at")
        _nonblank(self.retention_until, "retention_until")
        if self.export_state == "AVAILABLE":
            if self.expired_at is not None or self.retired_at is not None:
                raise ValueError("AVAILABLE audit export cannot carry terminal timestamps")
        elif self.export_state == "EXPIRED":
            _nonblank(self.expired_at, "expired_at")
            if self.retired_at is not None:
                raise ValueError("EXPIRED audit export cannot carry retired_at")
        elif self.export_state == "RETIRED":
            _nonblank(self.retired_at, "retired_at")

    def safe_summary(self) -> dict[str, object]:
        return {
            "exportId": self.export_id,
            "requestedByAdminOperatorId": self.requested_by_admin_operator_id,
            "reportType": self.report_type,
            "filterReferencePresent": True,
            "objectProviderCode": self.object_provider_code,
            "contentSha256": self.content_sha256,
            "byteSize": self.byte_size,
            "exportState": self.export_state,
            "generatedAt": self.generated_at,
            "expiresAt": self.expires_at,
            "retentionUntil": self.retention_until,
            "expiredAt": self.expired_at,
            "retiredAt": self.retired_at,
        }


@dataclass(frozen=True, slots=True)
class EnrollmentNotificationAuditQualificationReport:
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
    enrollment_event_count: int
    notification_delivery_count: int
    audit_export_count: int

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
            "enrollmentEventCount": self.enrollment_event_count,
            "notificationDeliveryCount": self.notification_delivery_count,
            "auditExportCount": self.audit_export_count,
        }


@dataclass(frozen=True, slots=True)
class EnrollmentNotificationAuditAdapterQualificationReceipt:
    request_id: str
    event_count: int
    notification_id: str
    admin_alert_recipient_reference: str
    audit_export_id: str
    notification_state: str
    audit_export_state: str
    rollback_verified: bool

    def safe_summary(self) -> dict[str, object]:
        return {
            "requestId": self.request_id,
            "eventCount": self.event_count,
            "notificationId": self.notification_id,
            "adminAlertRecipientReference": self.admin_alert_recipient_reference,
            "auditExportId": self.audit_export_id,
            "notificationState": self.notification_state,
            "auditExportState": self.audit_export_state,
            "rollbackVerified": self.rollback_verified,
        }


__all__ = [
    "ADMIN_OPERATIONS_RECIPIENT_REFERENCE",
    "AUDIT_EXPORT_STATES",
    "ENROLLMENT_AUTHORITY_TYPES",
    "ENROLLMENT_EVENT_TYPES",
    "EVENT_AUTHORITY_TYPES",
    "NOTIFICATION_DELIVERY_STATES",
    "NOTIFICATION_TEMPLATE_CODES",
    "TERMINAL_AUDIT_EXPORT_STATES",
    "TERMINAL_NOTIFICATION_DELIVERY_STATES",
    "AuditExportRecord",
    "EnrollmentEventRecord",
    "EnrollmentNotificationAuditAdapterQualificationReceipt",
    "EnrollmentNotificationAuditPersistenceError",
    "EnrollmentNotificationAuditQualificationError",
    "EnrollmentNotificationAuditQualificationReport",
    "NotificationDeliveryRecord",
]
