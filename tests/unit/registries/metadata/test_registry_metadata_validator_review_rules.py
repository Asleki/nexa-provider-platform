from registries.metadata import RegistryMetadataValidator
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from metadata_validation_test_support import make_profile


def test_unreviewed_production_profile_warns():
    r=RegistryMetadataValidator.validate(make_profile(production=True, simulation=False, training_status="ineligible", anonymisation=False))
    assert "REGISTRY_METADATA_PRODUCTION_PROFILE_UNREVIEWED" in [m.code for m in r.warnings]


def test_approved_production_profile_removes_unreviewed_warning():
    r=RegistryMetadataValidator.validate(make_profile(production=True, simulation=False, training_status="ineligible", anonymisation=False, review_status="approved"))
    assert "REGISTRY_METADATA_PRODUCTION_PROFILE_UNREVIEWED" not in [m.code for m in r.messages]


def test_rejected_profile_is_information_not_error():
    r=RegistryMetadataValidator.validate(make_profile(review_status="rejected"))
    assert "REGISTRY_METADATA_PROFILE_REJECTED" in [m.code for m in r.information]
