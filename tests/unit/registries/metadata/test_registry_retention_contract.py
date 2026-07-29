from datetime import datetime, timedelta, timezone

import pytest

from registries.metadata import (
    RegistryRetention,
    RegistryRetentionError,
    RegistryRetentionMode,
)

NOW = datetime(2030, 1, 1, tzinfo=timezone.utc)


def make(**overrides):
    values = {"mode": "permanent", "reason": "National history"}
    values.update(overrides)
    return RegistryRetention(**values)


def test_reason_and_policy_reference_are_trimmed_and_bounded():
    item = make(reason="  National history  ", policy_reference="  POLICY-1  ")
    assert item.reason == "National history"
    assert item.policy_reference == "POLICY-1"
    with pytest.raises(RegistryRetentionError, match="reason cannot be empty"):
        make(reason=" ")
    with pytest.raises(RegistryRetentionError, match="reason cannot exceed"):
        make(reason="x" * 2001)
    with pytest.raises(RegistryRetentionError, match="policy_reference cannot exceed"):
        make(policy_reference="x" * 513)


def test_invalid_mode_is_translated_to_retention_domain_error():
    with pytest.raises(RegistryRetentionError, match="Unsupported retention mode"):
        make(mode="rebuildable")
    with pytest.raises(TypeError, match="retention mode must be text"):
        make(mode=5)


@pytest.mark.parametrize("name", ["archive_required", "deletion_permitted", "legal_hold"])
def test_boolean_fields_are_strict(name):
    with pytest.raises(TypeError, match=f"{name} must be a boolean"):
        make(**{name: 1})


def test_permanent_mode_rejects_disposition_deadlines_and_holds():
    assert make().mode is RegistryRetentionMode.PERMANENT
    cases = (
        ({"retention_period": timedelta(days=1)}, "duration"),
        ({"retain_until": NOW}, "retain-until"),
        ({"trigger_event": "RECORD.CLOSED"}, "trigger event"),
        ({"legal_hold": True}, "legal_hold"),
        ({"deletion_permitted": True}, "cannot permit deletion"),
    )
    for overrides, message in cases:
        with pytest.raises(RegistryRetentionError, match=message):
            make(**overrides)


def test_fixed_duration_requires_one_unambiguous_duration():
    with pytest.raises(RegistryRetentionError, match="requires retention_period"):
        make(mode="fixed_duration")
    item = make(
        mode="fixed_duration",
        retention_period=timedelta(days=30),
        deletion_permitted=True,
    )
    assert item.retention_period == timedelta(days=30)
    with pytest.raises(RegistryRetentionError, match="cannot declare"):
        make(mode="fixed_duration", retention_period=timedelta(days=1), retain_until=NOW)


def test_until_date_requires_one_unambiguous_absolute_date():
    with pytest.raises(RegistryRetentionError, match="requires retain_until"):
        make(mode="until_date")
    item = make(mode="until_date", retain_until=NOW)
    assert item.retain_until == NOW
    with pytest.raises(RegistryRetentionError, match="cannot declare"):
        make(mode="until_date", retain_until=NOW, trigger_event="ACCOUNT.CLOSED")


def test_event_triggered_requires_semantic_event_code_and_allows_post_trigger_period():
    with pytest.raises(RegistryRetentionError, match="requires trigger_event"):
        make(mode="event_triggered")
    item = make(
        mode="event_triggered",
        trigger_event=" account.closed ",
        retention_period=timedelta(days=365),
    )
    assert item.trigger_event == "ACCOUNT.CLOSED"
    assert item.retention_period == timedelta(days=365)
    with pytest.raises(RegistryRetentionError, match="semantic code"):
        make(mode="event_triggered", trigger_event="after closure")
    with pytest.raises(RegistryRetentionError, match="cannot declare retain_until"):
        make(mode="event_triggered", trigger_event="ACCOUNT.CLOSED", retain_until=NOW)


def test_standalone_legal_hold_requires_traceability():
    with pytest.raises(RegistryRetentionError, match="requires legal_hold=True"):
        make(mode="legal_hold", policy_reference="CASE-1")
    with pytest.raises(RegistryRetentionError, match="requires review_at or policy_reference"):
        make(mode="legal_hold", legal_hold=True)
    item = make(mode="legal_hold", legal_hold=True, policy_reference="CASE-1")
    assert item.legal_hold is True
    assert item.deletion_permitted is False


def test_legal_hold_can_overlay_non_permanent_base_policies():
    item = make(
        mode="fixed_duration",
        retention_period=timedelta(days=30),
        legal_hold=True,
        policy_reference="CASE-1",
    )
    assert item.legal_hold is True
    with pytest.raises(RegistryRetentionError, match="cannot permit deletion"):
        make(
            mode="fixed_duration",
            retention_period=timedelta(days=30),
            legal_hold=True,
            deletion_permitted=True,
        )


def test_policy_review_requires_a_review_date_or_policy_reference():
    with pytest.raises(RegistryRetentionError, match="requires review_at or policy_reference"):
        make(mode="policy_review_required")
    assert make(mode="policy_review_required", review_at=NOW).review_at == NOW
    assert make(mode="policy_review_required", policy_reference="POLICY-1").policy_reference == "POLICY-1"


def test_archive_and_future_deletion_eligibility_can_coexist():
    item = make(
        mode="fixed_duration",
        retention_period=timedelta(days=1),
        archive_required=True,
        deletion_permitted=True,
    )
    assert item.archive_required is True
    assert item.deletion_permitted is True


@pytest.mark.parametrize("version", [0, -1])
def test_version_must_be_positive(version):
    with pytest.raises(RegistryRetentionError, match="at least 1"):
        make(version=version)


@pytest.mark.parametrize("version", [True, 1.5, "1"])
def test_version_requires_a_real_integer(version):
    with pytest.raises(TypeError, match="version must be an integer"):
        make(version=version)
