from registries.metadata import RegistryMetadataValidator
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from metadata_validation_test_support import make_profile


def test_highly_restricted_permanent_retention_without_policy_warns():
    r=RegistryMetadataValidator.validate(make_profile(level="highly_restricted", contains_sensitive=True))
    assert "REGISTRY_METADATA_SENSITIVE_PERMANENT_RETENTION_POLICY_MISSING" in [m.code for m in r.warnings]


def test_policy_reference_removes_retention_warning():
    r=RegistryMetadataValidator.validate(make_profile(level="highly_restricted", contains_sensitive=True, retention_policy="NVG-POLICY-1"))
    assert "REGISTRY_METADATA_SENSITIVE_PERMANENT_RETENTION_POLICY_MISSING" not in [m.code for m in r.messages]


def test_public_permanent_retention_is_not_a_conflict():
    r=RegistryMetadataValidator.validate(make_profile(level="public", contains_personal=False, training_status="ineligible", anonymisation=False))
    assert "REGISTRY_METADATA_RETENTION_CONFLICT" not in [m.code for m in r.messages]
