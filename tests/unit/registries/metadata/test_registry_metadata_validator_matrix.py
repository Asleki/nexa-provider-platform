from registries.metadata import RegistryMetadataValidator
from tests.unit.registries.metadata.metadata_validation_test_support import make_profile


def test_validator_multi_finding_result_is_deterministic_and_structured():
    profile = make_profile(
        capabilities=(),
        training_status="eligible",
        source_type="unknown",
        retention_mode="permanent",
        review_status="unreviewed",
    )
    first = RegistryMetadataValidator.validate(profile)
    second = RegistryMetadataValidator.validate(profile)
    assert first.to_dict() == second.to_dict()
    assert first.metadata["registry_id"] == profile.registry_id
    assert first.metadata["validator_version"] == RegistryMetadataValidator.VERSION
    assert len(first.messages) >= 2
    assert first.error_count >= 1
    assert first.is_valid is False
    assert len({(message.code, message.field) for message in first.messages}) == len(
        first.messages
    )
