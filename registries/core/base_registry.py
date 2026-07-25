"""
============================================================
Nexa Provider Platform
File: registries/core/base_registry.py
Layer: Master Registry Foundation
Milestone: NPP-M008.3 — Base Registry
============================================================

Defines the storage-neutral BaseRegistry runtime façade.

BaseRegistry binds one immutable RegistryDefinition to a stable,
read-only runtime object without duplicating registry identity fields.

It does not persist data, issue identifiers, manage lifecycle
transitions, publish events, write audit records, or connect to
external systems. Those responsibilities belong to later milestones.

Import Boundary
---------------
RegistryContract is imported lazily during construction to prevent a
package-level circular import:

registry_contract
→ registries.core.registry_family
→ registries.core.__init__
→ base_registry
→ registry_contract

Type-only imports are kept behind TYPE_CHECKING.
============================================================
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from .registry_definition import RegistryDefinition
from .registry_family import RegistryFamily
from .registry_status import RegistryStatus


if TYPE_CHECKING:
    from registries.contracts.registry_contract import RegistryContract


BASE_REGISTRY_SCHEMA_VERSION: Final[int] = 1


class BaseRegistryError(ValueError):
    """
    Raised when a BaseRegistry cannot be constructed safely.
    """


@dataclass(frozen=True, slots=True)
class BaseRegistry:
    """
    Read-only runtime façade for one registry definition.

    The bound definition must satisfy RegistryContract structurally.

    RegistryContract is checked lazily during construction so importing
    registries.core does not create a circular dependency with
    registries.contracts.registry_contract.
    """

    definition: RegistryContract

    def __post_init__(self) -> None:
        """
        Validate the bound definition against RegistryContract.

        The import is intentionally local. Moving it to module scope
        would reintroduce a circular import through registries.core.
        """

        from registries.contracts.registry_contract import (
            RegistryContract,
            RegistryContractError,
        )

        try:
            normalized_definition = RegistryContract.require(
                self.definition
            )
        except RegistryContractError as exc:
            raise BaseRegistryError(
                "definition must satisfy RegistryContract."
            ) from exc

        object.__setattr__(
            self,
            "definition",
            normalized_definition,
        )

    """
    ============================================================
    SECTION 1 — Delegated Registry Properties
    ============================================================
    """

    @property
    def registry_id(self) -> str:
        """
        Return the stable registry identifier.
        """

        return self.definition.registry_id

    @property
    def registry_code(self) -> str:
        """
        Return the canonical registry code.
        """

        return self.definition.registry_code

    @property
    def registry_name(self) -> str:
        """
        Return the human-readable registry name.
        """

        return self.definition.registry_name

    @property
    def family(self) -> RegistryFamily:
        """
        Return the registry family.
        """

        return self.definition.family

    @property
    def status(self) -> RegistryStatus:
        """
        Return the registry lifecycle status.
        """

        return self.definition.status

    @property
    def description(self) -> str:
        """
        Return the registry description.
        """

        return self.definition.description

    @property
    def version(self) -> int:
        """
        Return the registry-definition version.
        """

        return self.definition.version

    @property
    def metadata(self) -> Mapping[str, object]:
        """
        Return the registry definition's read-only metadata.
        """

        return self.definition.metadata

    """
    ============================================================
    SECTION 2 — Identity and Lifecycle Helpers
    ============================================================
    """

    @property
    def identity(self) -> tuple[str, str]:
        """
        Return the stable registry identity pair.
        """

        return (
            self.registry_id,
            self.registry_code,
        )

    @property
    def qualified_code(self) -> str:
        """
        Return the family-qualified registry code.
        """

        return (
            f"{self.family.value}:"
            f"{self.registry_code}"
        )

    @property
    def active(self) -> bool:
        """
        Return True when the registry definition is active.
        """

        return self.status is RegistryStatus.ACTIVE

    @property
    def inactive(self) -> bool:
        """
        Return True when the registry definition is not active.
        """

        return not self.active

    """
    ============================================================
    SECTION 3 — Metadata Helpers
    ============================================================
    """

    def has_metadata(
        self,
        key: str,
    ) -> bool:
        """
        Return whether a normalized metadata key exists.
        """

        if not isinstance(key, str):
            raise TypeError(
                "key must be text."
            )

        normalized_key = key.strip()

        if not normalized_key:
            return False

        return normalized_key in self.metadata

    def metadata_value(
        self,
        key: str,
        default: object = None,
    ) -> object:
        """
        Return one normalized metadata value.
        """

        if not isinstance(key, str):
            raise TypeError(
                "key must be text."
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise BaseRegistryError(
                "key cannot be empty."
            )

        return self.metadata.get(
            normalized_key,
            default,
        )

    """
    ============================================================
    SECTION 4 — Serialization and Construction
    ============================================================
    """

    def to_dict(self) -> dict[str, object]:
        """
        Serialize using the existing RegistryDefinition shape.
        """

        return dict(
            self.definition.to_dict()
        )

    @classmethod
    def from_definition(
        cls,
        definition: RegistryContract,
    ) -> "BaseRegistry":
        """
        Construct from a RegistryContract-compatible definition.
        """

        return cls(
            definition=definition
        )

    @classmethod
    def from_dict(
        cls,
        values: Mapping[str, object],
    ) -> "BaseRegistry":
        """
        Construct through the existing RegistryDefinition model.
        """

        if not isinstance(values, Mapping):
            raise TypeError(
                "values must be a mapping."
            )

        return cls(
            definition=RegistryDefinition.from_dict(
                values
            )
        )

    """
    ============================================================
    SECTION 5 — Human-Readable Representation
    ============================================================
    """

    def summary(self) -> str:
        """
        Return a deterministic human-readable summary.
        """

        return (
            "========================================================\n"
            "Nexa Provider Platform\n"
            "Base Registry\n"
            "--------------------------------------------------------\n"
            f"Registry ID : {self.registry_id}\n"
            f"Code        : {self.registry_code}\n"
            f"Name        : {self.registry_name}\n"
            f"Family      : {self.family.value}\n"
            f"Status      : {self.status.value}\n"
            f"Version     : {self.version}\n"
            "========================================================"
        )


"""
============================================================
SECTION 6 — Public Exports
============================================================
"""

__all__ = (
    "BASE_REGISTRY_SCHEMA_VERSION",
    "BaseRegistry",
    "BaseRegistryError",
)