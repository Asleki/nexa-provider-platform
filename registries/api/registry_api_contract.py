"""Versioned declaration of M008.11 Registry API capabilities."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .registry_api_errors import RegistryApiContractError
from .registry_api_operation import RegistryApiOperation


@dataclass(frozen=True, slots=True)
class RegistryApiContract:
    name: str = "registry"
    version: int = 1
    operations: tuple[RegistryApiOperation, ...] = tuple(RegistryApiOperation)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise RegistryApiContractError("name must be non-empty text.")
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise RegistryApiContractError("version must be a positive integer.")
        if not isinstance(self.operations, tuple):
            raise RegistryApiContractError("operations must be a tuple.")
        try:
            parsed = tuple(RegistryApiOperation.parse(item) for item in self.operations)
        except Exception as exc:
            raise RegistryApiContractError(str(exc)) from exc
        if not parsed or len(parsed) != len(set(parsed)):
            raise RegistryApiContractError("operations must be non-empty and unique.")
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "operations", parsed)

    def supports(self, operation: RegistryApiOperation | str) -> bool:
        try:
            return RegistryApiOperation.parse(operation) in self.operations
        except Exception:
            return False

    def to_dict(self) -> Mapping[str, object]:
        return MappingProxyType({
            "name": self.name,
            "version": self.version,
            "operations": tuple(item.value for item in self.operations),
        })


__all__ = ["RegistryApiContract"]
