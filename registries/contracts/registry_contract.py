"""
============================================================
Nexa Provider Platform
File: registries/contracts/registry_contract.py
Layer: Master Registry Foundation
Milestone: NPP-M008.1 — Registry Contracts
============================================================

Purpose
-------
Defines the minimum, storage-neutral structural contract for a
registry definition.

Later registry components may accept this contract without being
coupled to the concrete RegistryDefinition implementation. The
contract describes definition shape only; it does not validate
business policy, persist data, publish events, write audit records,
or manage registry lifecycle transitions.
============================================================
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import ClassVar, Self

from registries.core.registry_family import RegistryFamily
from registries.core.registry_status import RegistryStatus


class RegistryContractError(TypeError):
    """Raised when an object does not satisfy RegistryContract."""


class _RegistryContractMeta(type):
    """Provide a narrow, side-effect-free structural instance check."""

    def __instancecheck__(cls, instance: object) -> bool:
        required_attributes = cls.REQUIRED_ATTRIBUTES
        return all(hasattr(instance, name) for name in required_attributes) and callable(
            getattr(instance, "to_dict", None)
        )


class RegistryContract(metaclass=_RegistryContractMeta):
    """Minimum structural contract for one registry definition.

    This class is not intended to be instantiated. Concrete models
    conform structurally by exposing the required attributes and a
    callable ``to_dict`` method.
    """

    REQUIRED_ATTRIBUTES: ClassVar[tuple[str, ...]] = (
        "registry_id",
        "registry_code",
        "registry_name",
        "family",
        "status",
        "description",
        "version",
        "metadata",
    )

    registry_id: str
    registry_code: str
    registry_name: str
    family: RegistryFamily
    status: RegistryStatus
    description: str
    version: int
    metadata: Mapping[str, object]

    def __new__(cls, *args: object, **kwargs: object) -> Self:
        if cls is RegistryContract:
            raise RegistryContractError(
                "RegistryContract is a structural contract and cannot be instantiated."
            )
        return super().__new__(cls)

    def to_dict(self) -> Mapping[str, object]:
        """Return the registry definition as a mapping."""
        raise NotImplementedError

    @classmethod
    def require(cls, value: object) -> Self:
        """Return *value* when it satisfies this contract."""
        if not isinstance(value, cls):
            raise RegistryContractError(
                "value must satisfy RegistryContract."
            )
        return value  # type: ignore[return-value]


__all__ = [
    "RegistryContract",
    "RegistryContractError",
]
