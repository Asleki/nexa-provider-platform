from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from registries.metadata import RegistryMetadataProfile, RegistryMetadataProfileError
from tests.unit.registries.metadata.metadata_test_support import make_profile


def test_profile_round_trip_preserves_complete_aggregate():
    reviewed_at = datetime(2026, 7, 29, 7, 30, tzinfo=timezone.utc)
    original = make_profile(
        profile_version=4,
        review_status="conditional",
        reviewed_at=reviewed_at,
        attributes={
            "country_registry_id": "country.ke",
            "jurisdiction_policy_id": "name-policy.ke.citizen.v1",
            "form_schema_id": "civil-name-form.ke.v1",
        },
    )
    restored = RegistryMetadataProfile.from_dict(original.to_dict())
    assert restored == original
    assert restored.to_dict() == original.to_dict()


def test_from_dict_accepts_z_suffix_and_offset_datetimes():
    payload = make_profile().to_dict()
    payload["effective_from"] = "2026-07-29T10:00:00+02:00"
    restored = RegistryMetadataProfile.from_dict(payload)
    assert restored.effective_from.isoformat() == "2026-07-29T08:00:00+00:00"


def test_from_dict_does_not_retain_caller_owned_values():
    payload = make_profile(attributes={"nested": {"values": [1]}}).to_dict()
    snapshot = deepcopy(payload)
    restored = RegistryMetadataProfile.from_dict(payload)
    payload["attributes"]["nested"]["values"].append(2)
    payload["capabilities"][0]["attributes"]["mutated"] = True
    assert restored.to_dict() == snapshot


def test_from_dict_rejects_unknown_top_level_fields():
    payload = make_profile().to_dict()
    payload["unknown"] = True
    with pytest.raises(RegistryMetadataProfileError, match="unknown profile fields"):
        RegistryMetadataProfile.from_dict(payload)


@pytest.mark.parametrize("value", [None, [], "profile", 1])
def test_from_dict_requires_mapping(value):
    with pytest.raises(TypeError, match="data must be a mapping"):
        RegistryMetadataProfile.from_dict(value)


def test_from_dict_reports_missing_required_fields():
    payload = make_profile().to_dict()
    del payload["provenance"]
    with pytest.raises(RegistryMetadataProfileError, match="missing required profile field"):
        RegistryMetadataProfile.from_dict(payload)


@pytest.mark.parametrize("value", ["", "not-a-date", 123, []])
def test_from_dict_rejects_invalid_effective_from(value):
    payload = make_profile().to_dict()
    payload["effective_from"] = value
    with pytest.raises((TypeError, RegistryMetadataProfileError)):
        RegistryMetadataProfile.from_dict(payload)
