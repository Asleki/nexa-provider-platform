import pytest

from registries.catalogues import (
    CatalogueConflictError,
    CatalogueNotFoundError,
    CatalogueValidationError,
    NamespaceCatalogue,
)
from registries.core import NamespaceDefinition, RegistryStatus


def _definition(**overrides):
    values = {
        "namespace_id": "npp.namespace.citizen.identity",
        "registry_id": "npp.registry.citizens",
        "namespace_code": "CITIZEN_IDENTITY",
        "namespace_name": "Citizen Identity",
        "status": RegistryStatus.ACTIVE,
        "version": 1,
    }
    values.update(overrides)
    return NamespaceDefinition(**values)


def test_namespace_registration_lookup_filtering_and_version():
    identity = _definition()
    birth = _definition(
        namespace_id="npp.namespace.birth.records",
        registry_id="npp.registry.births",
        namespace_code="BIRTH_RECORDS",
        namespace_name="Birth Records",
        version=4,
    )
    catalogue = NamespaceCatalogue((identity, birth))

    assert catalogue.get(identity.namespace_id) is identity
    assert catalogue.get_by_code(" birth_records ") is birth
    assert catalogue.for_registry("npp.registry.citizens") == (identity,)
    assert catalogue.for_status("active") == (birth, identity)
    assert catalogue.version_for(birth.namespace_id) == 4


def test_namespace_duplicate_and_missing_behaviour():
    catalogue = NamespaceCatalogue((_definition(),))
    with pytest.raises(CatalogueConflictError):
        catalogue.register(_definition())
    with pytest.raises(CatalogueNotFoundError):
        catalogue.get("npp.namespace.missing")
    with pytest.raises(CatalogueValidationError):
        catalogue.register(object())
    with pytest.raises(CatalogueValidationError):
        catalogue.for_registry(" ")
    with pytest.raises(CatalogueValidationError):
        catalogue.for_status("unsupported")
