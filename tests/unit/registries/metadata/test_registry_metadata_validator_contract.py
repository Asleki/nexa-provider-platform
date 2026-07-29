import pytest
from registries.metadata import RegistryMetadataValidator, InvalidRegistryMetadataError
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from metadata_validation_test_support import make_profile


def test_validator_rejects_wrong_input_type():
    with pytest.raises(TypeError): RegistryMetadataValidator.validate({})


def test_class_and_instance_invocation_are_deterministic():
    profile = make_profile()
    first = RegistryMetadataValidator.validate(profile)
    second = RegistryMetadataValidator().validate(profile)
    assert first.to_dict() == second.to_dict()
    assert first.metadata == {"validator":"registry_metadata","validator_version":1,"registry_id":"registry","profile_version":1,"review_status":"unreviewed"}


def test_validate_does_not_mutate_profile():
    profile = make_profile(); before = profile.to_dict(); RegistryMetadataValidator.validate(profile)
    assert profile.to_dict() == before


def test_validate_or_raise_returns_valid_and_raises_invalid():
    valid = make_profile()
    assert RegistryMetadataValidator.validate_or_raise(valid).valid
    invalid = make_profile(level="confidential", contains_sensitive=True, training_status="eligible", anonymisation=False)
    with pytest.raises(InvalidRegistryMetadataError): RegistryMetadataValidator.validate_or_raise(invalid)
