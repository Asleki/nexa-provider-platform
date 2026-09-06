from dataclasses import FrozenInstanceError

import pytest

from backend.auth.admin_review_persistence.contracts import (
    ADMIN_PASSWORD_KIND,
    ADMIN_STATES,
    DEVELOPER_ACCESS_DECISIONS,
    DEVELOPER_REJECTION_REASON_CODES,
    TECHNICAL_ENROLLMENT_FAILURE_CODES,
    AdminOperatorRecord,
    DeveloperAccessDecisionRecord,
)


def test_c_contract_preserves_exact_admin_and_decision_vocabularies() -> None:
    assert ADMIN_PASSWORD_KIND == "ADMIN_PASSWORD"
    assert ADMIN_STATES == ("ACTIVE", "DISABLED")
    assert DEVELOPER_ACCESS_DECISIONS == ("APPROVED", "REJECTED")
    assert DEVELOPER_REJECTION_REASON_CODES == (
        "DUPLICATE_ACTIVE_REQUEST",
        "IDENTITY_NOT_CONFIRMED",
        "ACCESS_ELIGIBILITY_NOT_CONFIRMED",
        "SECURITY_REVIEW_FAILED",
        "PREVIOUS_ACCESS_RESTRICTION",
        "REQUEST_INCOMPLETE",
        "POLICY_REQUIREMENTS_NOT_MET",
    )


def test_technical_enrollment_failures_are_disjoint_from_admin_rejection_reasons() -> None:
    assert set(TECHNICAL_ENROLLMENT_FAILURE_CODES) == {
        "INVALID_SETUP",
        "EXPIRED_SETUP",
        "WRONG_OTP",
        "EXPIRED_OTP",
    }
    assert set(TECHNICAL_ENROLLMENT_FAILURE_CODES).isdisjoint(DEVELOPER_REJECTION_REASON_CODES)


def test_admin_operator_record_is_immutable_and_does_not_create_a_runtime_or_identity_type() -> None:
    record = AdminOperatorRecord(
        admin_operator_id="operator:test",
        principal_id="principal:test",
        admin_developer_id="opaque-admin-developer-id",
        bound_admin_email_id="email:test",
        bound_admin_email="admin@example.test",
        admin_state="ACTIVE",
        created_at="2026-09-06T12:00:00+00:00",
        disabled_at=None,
        bootstrap_reference=None,
        audit_reference="audit:test",
    )
    assert not hasattr(record, "runtime")
    assert not hasattr(record, "identity_type")
    with pytest.raises(FrozenInstanceError):
        record.admin_state = "DISABLED"  # type: ignore[misc]


def test_developer_access_decision_record_carries_reviewer_policy_and_receipt_evidence() -> None:
    record = DeveloperAccessDecisionRecord(
        decision_id="decision:test",
        request_id="request:test",
        reviewer_principal_id="principal:reviewer",
        admin_operator_id="operator:reviewer",
        decision="REJECTED",
        reason_code="REQUEST_INCOMPLETE",
        safe_explanation="The request is incomplete.",
        internal_reference="internal:test",
        policy_version="policy-v1",
        receipt_reference="receipt:test",
        decided_at="2026-09-06T12:00:00+00:00",
    )
    assert record.reviewer_principal_id == "principal:reviewer"
    assert record.admin_operator_id == "operator:reviewer"
    assert record.policy_version == "policy-v1"
    assert record.receipt_reference == "receipt:test"
