from registries.metadata import RegistryMetadataValidator
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from metadata_validation_test_support import make_profile


def test_unknown_unverified_provenance_blocks_eligible_training():
    r=RegistryMetadataValidator.validate(make_profile(source_type="unknown", training_status="eligible", anonymisation=False))
    assert "REGISTRY_METADATA_UNKNOWN_PROVENANCE_TRAINING_CONFLICT" in [m.code for m in r.errors]


def test_unverified_conditional_training_warns():
    r=RegistryMetadataValidator.validate(make_profile())
    assert "REGISTRY_METADATA_UNVERIFIED_PROVENANCE_TRAINING_REVIEW" in [m.code for m in r.warnings]


def test_simulation_generator_requires_simulation_capability():
    r=RegistryMetadataValidator.validate(make_profile(source_type="simulation_generator", generated=True, simulation=False))
    assert "REGISTRY_METADATA_GENERATED_WITHOUT_SIMULATION_CAPABILITY" in [m.code for m in r.errors]


def test_non_simulation_provenance_does_not_require_simulation_capability():
    r=RegistryMetadataValidator.validate(make_profile(source_type="system", generated=False, simulation=False, training_status="ineligible", anonymisation=False))
    assert "REGISTRY_METADATA_GENERATED_WITHOUT_SIMULATION_CAPABILITY" not in [m.code for m in r.messages]


def test_unknown_provenance_on_production_profile_warns():
    r=RegistryMetadataValidator.validate(make_profile(source_type="unknown", production=True, simulation=False, training_status="ineligible", anonymisation=False))
    assert "REGISTRY_METADATA_PRODUCTION_UNKNOWN_PROVENANCE" in [m.code for m in r.warnings]
