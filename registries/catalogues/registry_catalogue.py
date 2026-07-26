"""
============================================================
Nexa Provider Platform
File: registries/catalogues/registry_catalogue.py
Layer: Master Registry Foundation
Milestone: NPP-M008.7 — Registry Catalogue
============================================================

Deterministic in-memory catalogue for immutable RegistryDefinition
objects. It provides registration and discovery only; it is not an
operational record repository, factory, lifecycle engine, validator,
event publisher, audit adapter, or public transport API.
============================================================
"""

from __future__ import annotations

from registries.core.registry_definition import RegistryDefinition
from registries.core.registry_family import RegistryFamily
from registries.core.registry_status import RegistryStatus

from ._definition_catalogue import DefinitionCatalogue


class RegistryCatalogue(DefinitionCatalogue[RegistryDefinition]):
    """Register and discover authoritative registry definitions."""

    def __init__(self, definitions: tuple[RegistryDefinition, ...] = ()) -> None:
        super().__init__(
            definition_type=RegistryDefinition,
            id_attribute="registry_id",
            code_attribute="registry_code",
            resource_name="Registry definition",
        )
        for definition in definitions:
            self.register(definition)

    def for_family(
        self,
        family: RegistryFamily | str,
    ) -> tuple[RegistryDefinition, ...]:
        try:
            normalized_family = (
                family if isinstance(family, RegistryFamily) else RegistryFamily(family)
            )
        except (TypeError, ValueError) as exc:
            from .catalogue_errors import CatalogueValidationError

            raise CatalogueValidationError(
                "Unsupported registry family.",
                field="family",
                context={"value": family},
            ) from exc
        return self.select(lambda definition: definition.family is normalized_family)

    def for_status(
        self,
        status: RegistryStatus | str,
    ) -> tuple[RegistryDefinition, ...]:
        try:
            normalized_status = (
                status if isinstance(status, RegistryStatus) else RegistryStatus(status)
            )
        except (TypeError, ValueError) as exc:
            from .catalogue_errors import CatalogueValidationError

            raise CatalogueValidationError(
                "Unsupported registry status.",
                field="status",
                context={"value": status},
            ) from exc
        return self.select(lambda definition: definition.status is normalized_status)

    def version_for(self, registry_id: str) -> int:
        return self.get(registry_id).version


__all__ = ["RegistryCatalogue"]
