from __future__ import annotations

import pytest

from backend.auth.enrollment_notification_audit_persistence.contracts import (
    ADMIN_OPERATIONS_RECIPIENT_REFERENCE,
    AUDIT_EXPORT_STATES,
    ENROLLMENT_EVENT_TYPES,
    EVENT_AUTHORITY_TYPES,
    NOTIFICATION_DELIVERY_STATES,
    NOTIFICATION_TEMPLATE_CODES,
    AuditExportRecord,
    EnrollmentEventRecord,
    NotificationDeliveryRecord,
)


def _event(**updates: object) -> EnrollmentEventRecord:
    values: dict[str, object] = {
        "event_id": "event-1",
        "request_id": "request-1",
        "event_type": "REQUEST_RECEIVED",
        "authority_type": "DEVELOPER_ACCESS_REQUEST",
        "authority_id": "request-1",
        "occurred_at": "2026-09-08T12:00:00+00:00",
        "source_reference": "receipt:event-1",
        "correlation_id": "correlation-1",
        "causation_event_id": None,
    }
    values.update(updates)
    return EnrollmentEventRecord(**values)  # type: ignore[arg-type]


def _notification(**updates: object) -> NotificationDeliveryRecord:
    values: dict[str, object] = {
        "notification_id": "notification-1",
        "event_id": "event-1",
        "template_code": "ADMIN_DEVELOPER_REQUEST_ALERT",
        "template_version": 1,
        "recipient_reference": ADMIN_OPERATIONS_RECIPIENT_REFERENCE,
        "provider_message_reference": None,
        "delivery_state": "QUEUED",
        "queued_at": "2026-09-08T12:00:00+00:00",
        "sent_at": None,
        "failed_at": None,
        "failure_code": None,
    }
    values.update(updates)
    return NotificationDeliveryRecord(**values)  # type: ignore[arg-type]


def _audit(**updates: object) -> AuditExportRecord:
    values: dict[str, object] = {
        "export_id": "export-1",
        "requested_by_admin_operator_id": "admin-operator-1",
        "report_type": "DEVELOPER_ENROLLMENT_AUDIT",
        "filter_reference": "AUDIT_FILTER:developer-enrollment-1",
        "object_provider_code": "AWS_S3_PRIVATE",
        "object_key": "private/audit/export-1.pdf",
        "content_sha256": "a" * 64,
        "byte_size": 4096,
        "export_state": "AVAILABLE",
        "generated_at": "2026-09-08T12:00:00+00:00",
        "expires_at": "2026-09-09T12:00:00+00:00",
        "retention_until": "2026-10-08T12:00:00+00:00",
        "expired_at": None,
        "retired_at": None,
    }
    values.update(updates)
    return AuditExportRecord(**values)  # type: ignore[arg-type]


def test_f_event_vocabulary_is_exact_and_typed_to_predecessor_authority() -> None:
    assert ENROLLMENT_EVENT_TYPES == (
        "REQUEST_RECEIVED", "UNDER_REVIEW", "APPROVED", "REJECTED",
        "SETUP_ISSUED", "SETUP_VERIFIED", "OTP_ISSUED", "EMAIL_VERIFIED",
        "ENIGMA_PROVISIONED", "BUNDLE_READY", "DELIVERY_ISSUED", "ACCOUNT_ACTIVATED",
    )
    assert set(EVENT_AUTHORITY_TYPES) == set(ENROLLMENT_EVENT_TYPES)
    assert EVENT_AUTHORITY_TYPES["APPROVED"] == "DEVELOPER_ACCESS_DECISION"
    assert EVENT_AUTHORITY_TYPES["OTP_ISSUED"] == "EMAIL_VERIFICATION_CHALLENGE"
    assert EVENT_AUTHORITY_TYPES["DELIVERY_ISSUED"] == "CREDENTIAL_DELIVERY"
    assert EVENT_AUTHORITY_TYPES["ACCOUNT_ACTIVATED"] == "PRINCIPAL_ACCOUNT"


def test_event_rejects_wrong_polymorphic_authority_and_self_causation() -> None:
    with pytest.raises(ValueError, match="requires authority_type"):
        _event(event_type="APPROVED", authority_type="DEVELOPER_ACCESS_REQUEST")
    with pytest.raises(ValueError, match="must not equal"):
        _event(causation_event_id="event-1")


def test_notification_template_namespace_is_exact_and_provider_neutral() -> None:
    assert NOTIFICATION_TEMPLATE_CODES == (
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
    assert NOTIFICATION_DELIVERY_STATES == ("QUEUED", "SENT", "FAILED")


def test_reference_only_admin_alert_cannot_embed_mailbox_or_url() -> None:
    assert _notification().recipient_reference == "NEXILABS_ADMIN_OPERATIONS"
    with pytest.raises(ValueError, match="email address"):
        _notification(recipient_reference="nexatech.core@gmail.com")
    with pytest.raises(ValueError, match="not a URL"):
        _notification(recipient_reference="https://mail.example.invalid/admin")


def test_notification_state_evidence_is_coherent_and_provider_ref_not_in_repr() -> None:
    sent = _notification(
        provider_message_reference="provider-message:opaque-1",
        delivery_state="SENT",
        sent_at="2026-09-08T12:00:01+00:00",
    )
    assert sent.safe_summary()["providerMessageReferencePresent"] is True
    assert "provider-message:opaque-1" not in repr(sent)
    with pytest.raises(ValueError, match="terminal evidence"):
        _notification(sent_at="2026-09-08T12:00:01+00:00")
    with pytest.raises(ValueError, match="failure_code"):
        _notification(
            delivery_state="FAILED",
            failed_at="2026-09-08T12:00:01+00:00",
            failure_code="provider said no",
        )


def test_audit_export_contract_has_integrity_retention_and_private_refs() -> None:
    assert AUDIT_EXPORT_STATES == ("AVAILABLE", "EXPIRED", "RETIRED")
    record = _audit()
    summary = record.safe_summary()
    assert summary["contentSha256"] == "a" * 64
    assert summary["byteSize"] == 4096
    assert "filterReference" not in summary
    assert "objectKey" not in summary
    assert "developer-enrollment-1" not in repr(record)
    assert "private/audit/export-1.pdf" not in repr(record)


@pytest.mark.parametrize(
    "field,value,pattern",
    [
        ("filter_reference", "SELECT * FROM secrets", "opaque governed reference"),
        ("filter_reference", "FILTER:{raw-json}", "unrestricted query payload"),
        ("object_key", "https://bucket.example/export.pdf", "not a URL"),
        ("content_sha256", "A" * 64, "lowercase SHA-256"),
        ("byte_size", 0, "positive integer"),
        ("report_type", "developer audit", "uppercase governed code"),
    ],
)
def test_audit_export_rejects_unsafe_or_malformed_authority(
    field: str, value: object, pattern: str
) -> None:
    with pytest.raises(ValueError, match=pattern):
        _audit(**{field: value})


def test_f_contracts_have_no_rendered_mail_secret_or_public_url_fields() -> None:
    fields = {
        *EnrollmentEventRecord.__dataclass_fields__,
        *NotificationDeliveryRecord.__dataclass_fields__,
        *AuditExportRecord.__dataclass_fields__,
    }
    forbidden = {
        "runtime", "email_address", "mailbox", "message_body", "rendered_body",
        "html_body", "text_body", "password", "otp", "developer_setup_secret",
        "archive_password", "enigma_response", "raw_download_token", "raw_token",
        "provider_credential", "public_url", "presigned_url", "artifact_bytes",
    }
    assert not (fields & forbidden)


def test_event_provenance_and_correlation_references_cannot_embed_pii_or_urls() -> None:
    with pytest.raises(ValueError, match="opaque non-PII reference"):
        _event(source_reference="applicant@example.invalid")
    with pytest.raises(ValueError, match="opaque non-PII reference"):
        _event(correlation_id="contains applicant name")
    with pytest.raises(ValueError, match="not a URL"):
        _event(source_reference="https://example.invalid/receipt/1")


def test_provider_message_reference_is_opaque_evidence_not_mailbox_or_url() -> None:
    with pytest.raises(ValueError, match="opaque non-PII reference"):
        _notification(provider_message_reference="provider@example.invalid")
    with pytest.raises(ValueError, match="not a URL"):
        _notification(provider_message_reference="https://provider.invalid/messages/1")
