from __future__ import annotations

from dataclasses import fields

import pytest

from backend.auth.email_verification_persistence.contracts import (
    EMAIL_VERIFICATION_CHALLENGE_STATES,
    TERMINAL_EMAIL_VERIFICATION_CHALLENGE_STATES,
    EmailVerificationChallengePolicy,
    EmailVerificationChallengeRecord,
)


def test_d_lifecycle_states_are_exactly_the_controlled_pdf_contract() -> None:
    assert EMAIL_VERIFICATION_CHALLENGE_STATES == (
        "ISSUED", "VERIFIED", "EXPIRED", "LOCKED", "INVALIDATED"
    )
    assert TERMINAL_EMAIL_VERIFICATION_CHALLENGE_STATES == (
        "VERIFIED", "EXPIRED", "LOCKED", "INVALIDATED"
    )


def test_policy_is_explicit_server_configuration_without_silent_defaults() -> None:
    names = tuple(field.name for field in fields(EmailVerificationChallengePolicy))
    assert names == (
        "policy_version", "otp_lifetime_seconds", "max_attempts", "resend_delay_seconds"
    )
    policy = EmailVerificationChallengePolicy("qualification-v1", 600, 5, 60)
    assert policy.safe_summary() == {
        "policyVersion": "qualification-v1",
        "otpLifetimeSeconds": 600,
        "maxAttempts": 5,
        "resendDelaySeconds": 60,
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"policy_version": "", "otp_lifetime_seconds": 600, "max_attempts": 5, "resend_delay_seconds": 60},
        {"policy_version": "v1", "otp_lifetime_seconds": 0, "max_attempts": 5, "resend_delay_seconds": 60},
        {"policy_version": "v1", "otp_lifetime_seconds": 600, "max_attempts": 0, "resend_delay_seconds": 60},
        {"policy_version": "v1", "otp_lifetime_seconds": 600, "max_attempts": 5, "resend_delay_seconds": 0},
        {"policy_version": "v1", "otp_lifetime_seconds": True, "max_attempts": 5, "resend_delay_seconds": 60},
    ],
)
def test_policy_rejects_blank_or_non_positive_values(kwargs) -> None:
    with pytest.raises(ValueError):
        EmailVerificationChallengePolicy(**kwargs)


def test_challenge_record_has_verifier_material_but_no_raw_otp_field() -> None:
    names = {field.name for field in fields(EmailVerificationChallengeRecord)}
    assert {
        "challenge_id", "principal_id", "email_id",
        "otp_verifier_scheme", "otp_verifier_version", "otp_verifier_payload",
        "challenge_state", "policy_version", "issued_at", "expires_at",
        "consumed_at", "invalidated_at", "attempt_count", "max_attempts",
        "resend_count", "last_resend_at",
    } == names
    assert "otp" not in names
    assert "raw_otp" not in names
    assert "otp_plaintext" not in names


def test_safe_summary_never_exposes_verifier_payload() -> None:
    record = EmailVerificationChallengeRecord(
        challenge_id="challenge:d:1",
        principal_id="principal:d:1",
        email_id="email:d:1",
        otp_verifier_scheme="keyed-hmac-sha256",
        otp_verifier_version=1,
        otp_verifier_payload="opaque-keyed-verifier-material-not-an-otp",
        challenge_state="ISSUED",
        policy_version="qualification-v1",
        issued_at="2026-09-06T00:00:00+00:00",
        expires_at="2026-09-06T00:10:00+00:00",
        consumed_at=None,
        invalidated_at=None,
        attempt_count=0,
        max_attempts=5,
        resend_count=0,
        last_resend_at=None,
    )
    summary = record.safe_summary()
    assert "otp_verifier_payload" not in summary
    assert "otpVerifierPayload" not in summary
    assert record.otp_verifier_payload not in repr(summary)
