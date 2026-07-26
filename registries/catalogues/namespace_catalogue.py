"""
============================================================
Nexa Provider Platform
File: registries/catalogues/namespace_catalogue.py
Layer: Master Registry Foundation
Milestone: NPP-M008.7 — Registry Catalogue
============================================================

Deterministic discovery catalogue for immutable NamespaceDefinition
objects. Cross-object ownership validation remains assigned to the
later Registry Validation milestone.
============================================================
"""

from __future__ import annotations

from registries.core.namespace_definition import NamespaceDefinition
from registries.core.registry_status import RegistryStatus

from ._definition_catalogue import DefinitionCatalogue
from .catalogue_errors import CatalogueValidationError


class NamespaceCatalogue(DefinitionCatalogue[NamespaceDefinition]):
    """Register and discover namespace definitions."""

    def __init__(self, definitions: tuple[NamespaceDefinition, ...] = ()) -> None:
        super().__init__(
            definition_type=NamespaceDefinition,
            id_attribute="namespace_id",
            code_attribute="namespace_code",
            resource_name="Namespace definition",
        )
        for definition in definitions:
            self.register(definition)

    def for_registry(self, registry_id: str) -> tuple[NamespaceDefinition, ...]:
        normalized_id = self._normalize_text(registry_id, field_name="registry_id")
        return self.select(lambda definition: definition.registry_id == normalized_id)

    def for_status(
        self,
        status: RegistryStatus | str,
    ) -> tuple[NamespaceDefinition, ...]:
        try:
            normalized_status = (
                status if isinstance(status, RegistryStatus) else RegistryStatus(status)
            )
        except (TypeError, ValueError) as exc:
            raise CatalogueValidationError(
                "Unsupported namespace status.",
                field="status",
                context={"value": status},
            ) from exc
        return self.select(lambda definition: definition.status is normalized_status)

    def version_for(self, namespace_id: str) -> int:
        return self.get(namespace_id).version


__all__ = ["NamespaceCatalogue"]
