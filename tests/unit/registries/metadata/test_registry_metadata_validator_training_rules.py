from registries.metadata import RegistryMetadataValidator
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from metadata_validation_test_support import make_profile


def codes(profile): return [m.code for m in RegistryMetadataValidator.validate(profile).messages]


def test_confidential_unconditional_training_is_error():
    r=RegistryMetadataValidator.validate(make_profile(level="confidential", contains_sensitive=True, training_status="eligible", anonymisation=False))
    assert r.invalid and "REGISTRY_METADATA_TRAINING_CLASSIFICATION_CONFLICT" in [m.code for m in r.errors]


def test_sensitive_conditional_training_requires_anonymisation_or_aggregation():
    p=make_profile(level="confidential", contains_sensitive=True, anonymisation=False, human_approval=True)
    assert "REGISTRY_METADATA_SENSITIVE_TRAINING_CONDITION_REQUIRED" in codes(p)
    assert "REGISTRY_METADATA_SENSITIVE_TRAINING_CONDITION_REQUIRED" not in codes(make_profile(level="confidential", contains_sensitive=True, aggregation=True, anonymisation=False))


def test_personal_conditional_training_without_safeguard_warns():
    p=make_profile(level="restricted", contains_personal=True, anonymisation=False, simulation_only=True)
    r=RegistryMetadataValidator.validate(p)
    assert "REGISTRY_METADATA_PERSONAL_TRAINING_REVIEW_REQUIRED" in [m.code for m in r.warnings]


def test_production_with_simulation_only_training_is_information():
    p=make_profile(production=True, simulation=True, simulation_only=True)
    r=RegistryMetadataValidator.validate(p)
    assert "REGISTRY_METADATA_PRODUCTION_CAPABILITY_SIMULATION_TRAINING" in [m.code for m in r.information]
