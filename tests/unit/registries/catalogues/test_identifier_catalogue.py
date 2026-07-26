import pytest

from registries.catalogues import (
    CatalogueConflictError,
    CatalogueNotFoundError,
    CatalogueValidationError,
    IdentifierCatalogue,
)
from registries.core import IdentifierDefinition, RegistryStatus


def _definition(**overrides):
    values = {
        "identifier_id": "npp.identifier.citizen_id",
        "registry_id": "npp.registry.citizens",
        "namespace_id": "npp.namespace.citizen.identity",
        "identifier_code": "CITIZEN_ID",
        "identifier_name": "Citizen ID",
        "status": RegistryStatus.ACTIVE,
        "version": 2,
    }
    values.update(overrides)
    return IdentifierDefinition(**values)


def test_identifier_registration_lookup_filtering_and_version():
    citizen = _definition()
    birth = _definition(
        identifier_id="npp.identifier.birth_reference",
        registry_id="npp.registry.births",
        namespace_id="npp.namespace.birth.records",
        identifier_code="BIRTH_REFERENCE",
        identifier_name="Birth Reference",
        version=5,
    )
    catalogue = IdentifierCatalogue((citizen, birth))

    assert catalogue.get(citizen.identifier_id) is citizen
    assert catalogue.get_by_code("birth_reference") is birth
    assert catalogue.for_registry("npp.registry.citizens") == (citizen,)
    assert catalogue.for_namespace("npp.namespace.birth.records") == (birth,)
    assert catalogue.for_status(RegistryStatus.ACTIVE) == (birth, citizen)
    assert catalogue.version_for(birth.identifier_id) == 5


def test_identifier_duplicate_and_missing_behaviour():
    catalogue = IdentifierCatalogue((_definition(),))
    with pytest.raises(CatalogueConflictError):
        catalogue.register(_definition())
    with pytest.raises(CatalogueNotFoundError):
        catalogue.get_by_code("missing")
    with pytest.raises(CatalogueValidationError):
        catalogue.register(object())
    with pytest.raises(CatalogueValidationError):
        catalogue.for_namespace(None)
    with pytest.raises(CatalogueValidationError):
        catalogue.for_status("unsupported")
