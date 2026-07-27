from pathlib import Path

from registries.core import BaseRegistry, RegistryDefinition, RegistryFamily
from registries.validators import RegistryValidator

ROOT = Path(__file__).resolve().parents[3]


def test_m008_9_appends_tests_without_removing_previous_boundaries():
    registry_tests = ROOT / "tests" / "unit" / "registries"
    for milestone in range(1, 9):
        assert list(registry_tests.glob(f"test_m008_{milestone}_*boundaries.py"))


def test_validation_is_repository_event_audit_and_api_neutral():
    validator_dir = ROOT / "registries" / "validators"
    source = "\n".join(path.read_text() for path in validator_dir.glob("*.py"))
    forbidden = (
        "MemoryRegistryRepository",
        "EventRepository",
        "AuditRepository",
        "FastAPI",
        "APIRouter",
        "requests.",
        "httpx.",
    )
    for token in forbidden:
        assert token not in source


def test_validation_does_not_duplicate_lifecycle_transition_policy():
    source = (ROOT / "registries" / "validators" / "registry_validator.py").read_text()
    assert "RegistryLifecyclePolicy" not in source
    assert "transition(" not in source
    assert "dataclasses.replace" not in source


def test_validation_reuses_existing_registry_definition_and_base_registry():
    definition = RegistryDefinition(
        registry_id="npp.registry.school",
        registry_code="SCHOOL",
        registry_name="School Registry",
        family=RegistryFamily.SHARED_INFRASTRUCTURE,
    )
    assert RegistryValidator.validate(definition).valid
    assert RegistryValidator.validate(BaseRegistry(definition)).valid


def test_later_m008_placeholders_remain_unimplemented():
    # M008.10 Registry Events is now implemented.
    #
    # This advancing boundary preserves the original M008.9 validation tests
    # while continuing to guard the still-future M008.11+ registry layers.
    for folder in ("api", "apis", "metadata"):
        path = ROOT / "registries" / folder
        assert not path.exists() or not any(path.glob("*.py"))

    validation_source = "\n".join(
        path.read_text() for path in (ROOT / "registries" / "validators").glob("*.py")
    )

    for token in (
        "training_eligibility",
        "retention_policy",
        "relationship_provenance",
    ):
        assert token not in validation_source