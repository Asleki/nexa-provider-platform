from registries.metadata import RegistryCapability, RegistryMetadataValidator
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from metadata_validation_test_support import make_profile


def test_empty_capabilities_warn():
    r=RegistryMetadataValidator.validate(make_profile(capabilities=()))
    assert "REGISTRY_METADATA_NO_CAPABILITIES_DECLARED" in [m.code for m in r.warnings]


def test_all_unsupported_capabilities_warn():
    cap=RegistryCapability("cap","IDENTITY.REGISTER","Cap","identity",supported=False,simulation_supported=False,production_supported=False)
    r=RegistryMetadataValidator.validate(make_profile(capabilities=(cap,)))
    assert "REGISTRY_METADATA_NO_SUPPORTED_CAPABILITIES" in [m.code for m in r.warnings]


def test_supported_capability_without_runtime_warns():
    cap=RegistryCapability("cap","IDENTITY.REGISTER","Cap","identity",supported=True,simulation_supported=False,production_supported=False)
    r=RegistryMetadataValidator.validate(make_profile(capabilities=(cap,)))
    assert "REGISTRY_METADATA_NO_RUNTIME_CAPABILITY" in [m.code for m in r.warnings]


def test_restricted_export_is_not_automatically_rejected():
    cap=RegistryCapability("cap","EXPORT.CONTROLLED","Export","export",simulation_supported=True)
    r=RegistryMetadataValidator.validate(make_profile(capabilities=(cap,)))
    assert not any("EXPORT" in m.code for m in r.errors)
