from datetime import datetime, timezone

import pytest

from registries.metadata import RegistryMetadataProfileError
from tests.unit.registries.metadata.metadata_test_support import (
    make_capability,
    make_profile,
)


def test_profile_normalises_registry_id_capabilities_and_review_status():
    cap = make_capability()
    reviewed_at = datetime(2026, 7, 28, 8, 0, tzinfo=timezone.utc)
    profile = make_profile(
        registry_id="  citizen.registry  ",
        capabilities=[cap],
        review_status=" APPROVED ",
        reviewed_at=reviewed_at,
    )
    assert profile.registry_id == "citizen.registry"
    assert profile.capabilities == (cap,)
    assert profile.review_status == "approved"


@pytest.mark.parametrize("value", [None, 1, True, object()])
def test_profile_rejects_non_text_registry_ids(value):
    with pytest.raises(TypeError, match="registry_id must be text"):
        make_profile(registry_id=value)


def test_profile_rejects_empty_registry_id():
    with pytest.raises(RegistryMetadataProfileError, match="cannot be empty"):
        make_profile(registry_id="   ")


@pytest.mark.parametrize("value", [0, -1])
def test_profile_rejects_non_positive_profile_versions(value):
    with pytest.raises(RegistryMetadataProfileError, match="at least 1"):
        make_profile(profile_version=value)


@pytest.mark.parametrize("value", [True, 1.5, "2"])
def test_profile_rejects_non_integer_profile_versions(value):
    with pytest.raises(TypeError, match="profile_version must be an integer"):
        make_profile(profile_version=value)


def test_profile_allows_empty_capability_collection():
    assert make_profile(capabilities=()).capabilities == ()


def test_profile_rejects_duplicate_capability_codes_after_capability_normalisation():
    cap_a = make_capability(capability_id="a", capability_code="identity.register")
    cap_b = make_capability(capability_id="b", capability_code="IDENTITY.REGISTER")
    with pytest.raises(RegistryMetadataProfileError, match="must be unique"):
        make_profile(capabilities=(cap_a, cap_b))


@pytest.mark.parametrize("status", ["pending", "reviewed", "active", ""])
def test_profile_rejects_unknown_review_status(status):
    with pytest.raises(RegistryMetadataProfileError, match="unsupported review_status"):
        make_profile(review_status=status)


def test_reviewed_profile_requires_reviewed_at():
    with pytest.raises(RegistryMetadataProfileError, match="require reviewed_at"):
        make_profile(review_status="approved")


def test_unreviewed_profile_rejects_reviewed_at():
    with pytest.raises(RegistryMetadataProfileError, match="cannot have reviewed_at"):
        make_profile(reviewed_at=datetime.now(timezone.utc))
