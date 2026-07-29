from registries.metadata import RegistryMetadataProfile
from tests.unit.registries.metadata.metadata_test_support import (
    make_capability,
    make_classification,
    make_profile,
    make_provenance,
    make_retention,
    make_training,
)


def test_rich_metadata_family_round_trip_is_deterministic_and_detached():
    profile = make_profile(
        capabilities=(
            make_capability(attributes={"dependencies": ["country.registry"]}),
        ),
        data_classification=make_classification(
            attributes={"policy_refs": ["privacy.identity.v1"]}
        ),
        training_eligibility=make_training(
            attributes={"approval_refs": ["training.review.v1"]}
        ),
        provenance=make_provenance(
            attributes={"verification": {"authority": "civil-registry"}}
        ),
        retention=make_retention(
            attributes={"archive": {"format": "event-first"}}
        ),
        attributes={"relationships": ["country.registry", "policy.registry"]},
    )
    payload = profile.to_dict()
    restored = RegistryMetadataProfile.from_dict(payload)
    assert restored.to_dict() == payload
    assert restored.to_dict() == restored.to_dict()
