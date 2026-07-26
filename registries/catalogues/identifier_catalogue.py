"""
============================================================
Nexa Provider Platform
File: registries/catalogues/identifier_catalogue.py
Layer: Master Registry Foundation
Milestone: NPP-M008.7 — Registry Catalogue
============================================================

Deterministic discovery catalogue for immutable IdentifierDefinition
objects. Identifier issuance, format validation, persistence, and
lifecycle transitions remain outside this milestone.
============================================================
"""

from __future__ import annotations

from registries.core.identifier_definition import IdentifierDefinition
from registries.core.registry_status import RegistryStatus

from ._definition_catalogue import DefinitionCatalogue
from .catalogue_errors import CatalogueValidationError


class IdentifierCatalogue(DefinitionCatalogue[IdentifierDefinition]):
    """Register and discover identifier definitions."""

    def __init__(self, definitions: tuple[IdentifierDefinition, ...] = ()) -> None:
        super().__init__(
            definition_type=IdentifierDefinition,
            id_attribute="identifier_id",
            code_attribute="identifier_code",
            resource_name="Identifier definition",
        )
        for definition in definitions:
            self.register(definition)

    def for_registry(self, registry_id: str) -> tuple[IdentifierDefinition, ...]:
        normalized_id = self._normalize_text(registry_id, field_name="registry_id")
        return self.select(lambda definition: definition.registry_id == normalized_id)

    def for_namespace(self, namespace_id: str) -> tuple[IdentifierDefinition, ...]:
        normalized_id = self._normalize_text(namespace_id, field_name="namespace_id")
        return self.select(lambda definition: definition.namespace_id == normalized_id)

    def for_status(
        self,
        status: RegistryStatus | str,
    ) -> tuple[IdentifierDefinition, ...]:
        try:
            normalized_status = (
                status if isinstance(status, RegistryStatus) else RegistryStatus(status)
            )
        except (TypeError, ValueError) as exc:
            raise CatalogueValidationError(
                "Unsupported identifier status.",
                field="status",
                context={"value": status},
            ) from exc
        return self.select(lambda definition: definition.status is normalized_status)

    def version_for(self, identifier_id: str) -> int:
        return self.get(identifier_id).version


__all__ = ["IdentifierCatalogue"]
