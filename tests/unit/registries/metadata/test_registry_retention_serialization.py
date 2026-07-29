from datetime import datetime, timedelta, timezone

import pytest

from registries.metadata import RegistryRetention, RegistryRetentionError


def make_item():
    return RegistryRetention(
        "event_triggered",
        "Account evidence",
        trigger_event="account.closed",
        retention_period=timedelta(days=30),
        archive_required=True,
        deletion_permitted=True,
        review_at=datetime(2030, 1, 1, tzinfo=timezone.utc),
        policy_reference="BANK-POLICY-1",
        version=2,
        attributes={"scope": {"copies": ["central", "archive"]}},
    )


def test_to_dict_has_stable_complete_shape():
    data = make_item().to_dict()
    assert list(data) == [
        "mode",
        "reason",
        "retention_seconds",
        "retain_until",
        "trigger_event",
        "archive_required",
        "deletion_permitted",
        "legal_hold",
        "review_at",
        "policy_reference",
        "version",
        "attributes",
    ]
    assert data["mode"] == "event_triggered"
    assert data["trigger_event"] == "ACCOUNT.CLOSED"


def test_from_dict_round_trip_is_lossless():
    item = make_item()
    rebuilt = RegistryRetention.from_dict(item.to_dict())
    assert rebuilt == item
    assert rebuilt.to_dict() == item.to_dict()


def test_from_dict_accepts_z_suffix_and_datetime_objects():
    data = {
        "mode": "until_date",
        "reason": "Until expiry",
        "retention_seconds": None,
        "retain_until": "2030-01-01T00:00:00Z",
        "trigger_event": "",
        "archive_required": False,
        "deletion_permitted": False,
        "legal_hold": False,
        "review_at": datetime(2029, 1, 1, tzinfo=timezone.utc),
        "policy_reference": "",
        "version": 1,
        "attributes": {},
    }
    item = RegistryRetention.from_dict(data)
    assert item.retain_until == datetime(2030, 1, 1, tzinfo=timezone.utc)


def test_from_dict_rejects_non_mapping_and_unknown_fields():
    with pytest.raises(TypeError, match="data must be a mapping"):
        RegistryRetention.from_dict([])
    with pytest.raises(TypeError, match="unexpected keyword"):
        RegistryRetention.from_dict({"mode": "permanent", "reason": "History", "extra": 1})


@pytest.mark.parametrize("seconds", [0, -1])
def test_from_dict_rejects_non_positive_seconds(seconds):
    with pytest.raises(RegistryRetentionError, match="must be positive"):
        RegistryRetention.from_dict({
            "mode": "fixed_duration",
            "reason": "Temporary",
            "retention_seconds": seconds,
        })


def test_from_dict_rejects_fractional_or_wrong_seconds():
    with pytest.raises(RegistryRetentionError, match="whole-second precision"):
        RegistryRetention.from_dict({
            "mode": "fixed_duration",
            "reason": "Temporary",
            "retention_seconds": 1.5,
        })
    with pytest.raises(TypeError, match="must be a number"):
        RegistryRetention.from_dict({
            "mode": "fixed_duration",
            "reason": "Temporary",
            "retention_seconds": "30",
        })


def test_invalid_iso_timestamp_is_domain_error():
    with pytest.raises(RegistryRetentionError, match="valid ISO datetime"):
        RegistryRetention.from_dict({
            "mode": "until_date",
            "reason": "Until expiry",
            "retain_until": "not-a-date",
        })


def test_serialized_output_is_detached():
    item = make_item()
    data = item.to_dict()
    data["attributes"]["scope"]["copies"].append("device")
    assert item.to_dict()["attributes"]["scope"]["copies"] == ["central", "archive"]
