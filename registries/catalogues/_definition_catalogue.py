"""Internal reusable mechanics for immutable definition catalogues."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

from .catalogue_errors import (
    CatalogueConflictError,
    CatalogueNotFoundError,
    CatalogueValidationError,
)

DefinitionT = TypeVar("DefinitionT")


class DefinitionCatalogue(Generic[DefinitionT]):
    """Store immutable definitions by stable ID and canonical code."""

    def __init__(
        self,
        *,
        definition_type: type[DefinitionT],
        id_attribute: str,
        code_attribute: str,
        resource_name: str,
    ) -> None:
        self._definition_type = definition_type
        self._id_attribute = id_attribute
        self._code_attribute = code_attribute
        self._resource_name = resource_name
        self._by_id: dict[str, DefinitionT] = {}
        self._id_by_code: dict[str, str] = {}

    @staticmethod
    def _normalize_text(value: object, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise CatalogueValidationError(
                f"{field_name} must be text.",
                field=field_name,
                context={"actual_type": type(value).__name__},
            )
        normalized = value.strip()
        if not normalized:
            raise CatalogueValidationError(
                f"{field_name} cannot be empty.",
                field=field_name,
            )
        return normalized

    def register(self, definition: DefinitionT) -> DefinitionT:
        if not isinstance(definition, self._definition_type):
            raise CatalogueValidationError(
                f"definition must be a {self._definition_type.__name__} instance.",
                field="definition",
                context={"actual_type": type(definition).__name__},
            )

        definition_id = getattr(definition, self._id_attribute)
        definition_code = getattr(definition, self._code_attribute)
        canonical_code = definition_code.upper()

        if definition_id in self._by_id:
            existing = self._by_id[definition_id]
            raise CatalogueConflictError(
                f"{self._resource_name} identifier is already registered: "
                f"{definition_id}",
                field=self._id_attribute,
                resource_reference=definition_id,
                context={
                    "existing_code": getattr(existing, self._code_attribute),
                    "incoming_code": definition_code,
                },
            )

        existing_id = self._id_by_code.get(canonical_code)
        if existing_id is not None:
            raise CatalogueConflictError(
                f"{self._resource_name} code is already registered: "
                f"{definition_code}",
                field=self._code_attribute,
                resource_reference=existing_id,
                context={
                    "existing_id": existing_id,
                    "incoming_id": definition_id,
                },
            )

        self._by_id[definition_id] = definition
        self._id_by_code[canonical_code] = definition_id
        return definition

    def get(self, definition_id: str) -> DefinitionT:
        normalized_id = self._normalize_text(
            definition_id,
            field_name=self._id_attribute,
        )
        try:
            return self._by_id[normalized_id]
        except KeyError as exc:
            raise CatalogueNotFoundError(
                f"{self._resource_name} is not registered: {normalized_id}",
                field=self._id_attribute,
                resource_reference=normalized_id,
            ) from exc

    def get_by_code(self, definition_code: str) -> DefinitionT:
        normalized_code = self._normalize_text(
            definition_code,
            field_name=self._code_attribute,
        ).upper()
        try:
            definition_id = self._id_by_code[normalized_code]
        except KeyError as exc:
            raise CatalogueNotFoundError(
                f"{self._resource_name} code is not registered: "
                f"{normalized_code}",
                field=self._code_attribute,
                resource_reference=normalized_code,
            ) from exc
        return self._by_id[definition_id]

    def is_registered(self, definition_id: object) -> bool:
        if not isinstance(definition_id, str):
            return False
        normalized_id = definition_id.strip()
        return bool(normalized_id) and normalized_id in self._by_id

    def is_code_registered(self, definition_code: object) -> bool:
        if not isinstance(definition_code, str):
            return False
        normalized_code = definition_code.strip().upper()
        return bool(normalized_code) and normalized_code in self._id_by_code

    def select(self, predicate: Callable[[DefinitionT], bool]) -> tuple[DefinitionT, ...]:
        return tuple(item for item in self.definitions if predicate(item))

    @property
    def definitions(self) -> tuple[DefinitionT, ...]:
        return tuple(self._by_id[key] for key in sorted(self._by_id))

    @property
    def identifiers(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_id))

    @property
    def codes(self) -> tuple[str, ...]:
        return tuple(sorted(self._id_by_code))

    @property
    def count(self) -> int:
        return len(self._by_id)

    def __contains__(self, definition_id: object) -> bool:
        return self.is_registered(definition_id)

    def __len__(self) -> int:
        return self.count

    def __iter__(self) -> Iterator[DefinitionT]:
        return iter(self.definitions)
