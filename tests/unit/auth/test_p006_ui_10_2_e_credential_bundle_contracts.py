from __future__ import annotations

import pytest

from backend.auth.credential_bundle_persistence.contracts import (
    CREDENTIAL_BUNDLE_STATES,
    CREDENTIAL_DELIVERY_STATES,
    TERMINAL_CREDENTIAL_BUNDLE_STATES,
    TERMINAL_CREDENTIAL_DELIVERY_STATES,
    CredentialBundleRecord,
    CredentialBundleSecretRecord,
    CredentialDeliveryRecord,
)


def _bundle() -> CredentialBundleRecord:
    return CredentialBundleRecord(
        bundle_id="bundle-1",
        principal_id="principal-1",
        enigma_profile_id="profile-1",
        bundle_state="READY",
        object_provider_code="AWS_S3_PRIVATE",
        object_key="private/credentials/bundle-1.zip",
        content_sha256="a" * 64,
        byte_size=4096,
        created_at="2026-09-06T20:00:00+00:00",
        integrity_verified_at="2026-09-06T20:00:01+00:00",
        object_confirmed_at="2026-09-06T20:00:02+00:00",
        ready_at="2026-09-06T20:00:03+00:00",
        expires_at="2026-09-07T20:00:00+00:00",
        retention_until="2026-10-06T20:00:00+00:00",
        invalidated_at=None,
        retired_at=None,
    )


def _delivery(**updates: object) -> CredentialDeliveryRecord:
    values: dict[str, object] = {
        "delivery_id": "delivery-1",
        "bundle_id": "bundle-1",
        "token_verifier_scheme": "hmac-sha256",
        "token_verifier_version": 1,
        "token_verifier_payload": "v" * 64,
        "delivery_state": "ISSUED",
        "policy_version": "delivery-policy-v1",
        "logical_delivery_host_code": "CREDENTIAL_DELIVERY_SECURE",
        "issued_at": "2026-09-06T20:00:00+00:00",
        "expires_at": "2026-09-06T20:15:00+00:00",
        "consumed_at": None,
        "revoked_at": None,
        "download_count": 0,
        "first_downloaded_at": None,
        "last_downloaded_at": None,
    }
    values.update(updates)
    return CredentialDeliveryRecord(**values)  # type: ignore[arg-type]


def test_states_are_exact_and_terminal_sets_do_not_reopen_authority() -> None:
    assert CREDENTIAL_BUNDLE_STATES == (
        "GENERATED", "READY", "EXPIRED", "RETIRED", "INVALIDATED"
    )
    assert TERMINAL_CREDENTIAL_BUNDLE_STATES == ("EXPIRED", "RETIRED", "INVALIDATED")
    assert CREDENTIAL_DELIVERY_STATES == ("ISSUED", "CONSUMED", "EXPIRED", "REVOKED")
    assert TERMINAL_CREDENTIAL_DELIVERY_STATES == ("CONSUMED", "EXPIRED", "REVOKED")


def test_bundle_safe_summary_excludes_private_object_key() -> None:
    record = _bundle()
    summary = record.safe_summary()
    assert summary["bundleId"] == "bundle-1"
    assert summary["contentSha256"] == "a" * 64
    assert "objectKey" not in summary
    assert "private/credentials" not in repr(summary)
    assert "private/credentials" not in repr(record)


def test_secret_safe_summary_and_repr_exclude_escrow_reference() -> None:
    record = CredentialBundleSecretRecord(
        bundle_secret_id="secret-1",
        bundle_id="bundle-1",
        escrow_provider_code="AWS_KMS_REFERENCE",
        encrypted_secret_reference="kms:opaque:ciphertext-reference",
        encryption_context_version="ctx-v1",
        created_at="2026-09-06T20:00:00+00:00",
        retired_at=None,
    )
    summary = record.safe_summary()
    assert summary["escrowProviderCode"] == "AWS_KMS_REFERENCE"
    assert "encryptedSecretReference" not in summary
    assert "opaque:ciphertext" not in repr(summary)
    assert "opaque:ciphertext" not in repr(record)


def test_delivery_safe_summary_and_repr_exclude_token_verifier_payload() -> None:
    record = _delivery()
    summary = record.safe_summary()
    assert summary["deliveryState"] == "ISSUED"
    assert "tokenVerifierPayload" not in summary
    assert "v" * 32 not in repr(summary)
    assert "v" * 32 not in repr(record)


@pytest.mark.parametrize(
    "field,value,pattern",
    [
        ("token_verifier_scheme", "", "token_verifier_scheme"),
        ("token_verifier_version", 0, "token_verifier_version"),
        ("token_verifier_payload", "short", "token_verifier_payload"),
        ("delivery_state", "READY", "unsupported"),
        ("policy_version", "", "policy_version"),
        ("logical_delivery_host_code", "", "logical_delivery_host_code"),
        ("download_count", -1, "download_count"),
    ],
)
def test_delivery_contract_rejects_malformed_persistent_authority(
    field: str, value: object, pattern: str
) -> None:
    with pytest.raises(ValueError, match=pattern):
        _delivery(**{field: value})


def test_contracts_do_not_claim_runtime_or_public_url_authority() -> None:
    bundle_fields = set(CredentialBundleRecord.__dataclass_fields__)
    delivery_fields = set(CredentialDeliveryRecord.__dataclass_fields__)
    assert "runtime" not in bundle_fields | delivery_fields
    assert "public_url" not in bundle_fields | delivery_fields
    assert "presigned_url" not in bundle_fields | delivery_fields
    assert "raw_token" not in bundle_fields | delivery_fields
    assert "archive_password" not in bundle_fields | delivery_fields
