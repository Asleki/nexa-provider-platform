import pytest

from registries.catalogues import (
    CatalogueConflictError,
    CatalogueNotFoundError,
    CatalogueValidationError,
    RegistryCatalogue,
)
from registries.core import RegistryDefinition, RegistryFamily, RegistryStatus


def _definition(**overrides):
    values = {
        "registry_id": "npp.registry.citizens",
        "registry_code": "CITIZENS",
        "registry_name": "Citizen Registry",
        "family": RegistryFamily.CORE_INFRASTRUCTURE,
        "status": RegistryStatus.ACTIVE,
        "version": 2,
    }
    values.update(overrides)
    return RegistryDefinition(**values)


def test_register_lookup_and_discovery_are_deterministic():
    catalogue = RegistryCatalogue()
    second = _definition(
        registry_id="npp.registry.businesses",
        registry_code="BUSINESSES",
        registry_name="Business Registry",
    )
    first = _definition()
    catalogue.register(first)
    catalogue.register(second)

    assert catalogue.get(" npp.registry.citizens ") is first
    assert catalogue.get_by_code(" citizens ") is first
    assert catalogue.identifiers == (
        "npp.registry.businesses",
        "npp.registry.citizens",
    )
    assert tuple(item.registry_id for item in catalogue) == catalogue.identifiers
    assert catalogue.codes == ("BUSINESSES", "CITIZENS")
    assert len(catalogue) == 2
    assert "npp.registry.citizens" in catalogue


def test_duplicate_identifier_and_code_are_rejected_without_replacement():
    catalogue = RegistryCatalogue((_definition(),))
    with pytest.raises(CatalogueConflictError) as id_error:
        catalogue.register(_definition(registry_code="OTHER"))
    assert id_error.value.field == "registry_id"
    assert id_error.value.code == "NPP-REGISTRY-CATALOGUE-010"

    with pytest.raises(CatalogueConflictError) as code_error:
        catalogue.register(
            _definition(
                registry_id="npp.registry.other",
                registry_code="citizens",
            )
        )
    assert code_error.value.field == "registry_code"


def test_unknown_and_invalid_lookups_are_controlled():
    catalogue = RegistryCatalogue()
    with pytest.raises(CatalogueNotFoundError) as missing:
        catalogue.get("npp.registry.missing")
    assert missing.value.resource_reference == "npp.registry.missing"
    assert missing.value.code == "NPP-REGISTRY-CATALOGUE-020"

    with pytest.raises(CatalogueValidationError):
        catalogue.get("   ")
    with pytest.raises(CatalogueValidationError):
        catalogue.get_by_code(None)


def test_registration_requires_registry_definition():
    with pytest.raises(CatalogueValidationError, match="RegistryDefinition"):
        RegistryCatalogue().register(object())


def test_family_status_and_version_discovery():
    active = _definition()
    draft = _definition(
        registry_id="npp.registry.devices",
        registry_code="DEVICES",
        registry_name="Device Registry",
        family=RegistryFamily.NEXA_ECOSYSTEM,
        status=RegistryStatus.DRAFT,
        version=3,
    )
    catalogue = RegistryCatalogue((draft, active))

    assert catalogue.for_family("core_infrastructure") == (active,)
    assert catalogue.for_status(RegistryStatus.DRAFT) == (draft,)
    assert catalogue.version_for("npp.registry.devices") == 3
    with pytest.raises(CatalogueValidationError):
        catalogue.for_family("unsupported")
    with pytest.raises(CatalogueValidationError):
        catalogue.for_status("unsupported")


def test_membership_checks_do_not_raise_for_invalid_values():
    catalogue = RegistryCatalogue((_definition(),))
    assert catalogue.is_registered(None) is False
    assert catalogue.is_registered("   ") is False
    assert catalogue.is_code_registered(7) is False
    assert object() not in catalogue
