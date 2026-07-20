
"""
============================================================
Nexa Provider Platform
File: registries/core/numbering_strategy.py
Layer: Master Registry Foundation
Milestone: NPP-M006.2 — Registry Foundation
============================================================

Immutable definition describing how identifiers should be
generated. This model defines strategy metadata only; it does not
generate identifier values.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


class NumberingMode(str, Enum):
    SEQUENTIAL = "sequential"
    RANDOM = "random"
    UUID = "uuid"
    DATE_PREFIXED = "date_prefixed"
    CUSTOM = "custom"


class NumberingStrategyError(ValueError):
    """Raised when an invalid NumberingStrategy is created."""


@dataclass(frozen=True, slots=True)
class NumberingStrategy:
    strategy_id: str
    registry_id: str
    namespace_id: str
    identifier_id: str
    strategy_code: str
    strategy_name: str
    mode: NumberingMode = NumberingMode.SEQUENTIAL
    prefix: str | None = None
    suffix: str | None = None
    padding_length: int | None = None
    version: int = 1
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "strategy_id",
            "registry_id",
            "namespace_id",
            "identifier_id",
            "strategy_code",
            "strategy_name",
        ):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be text.")
            value = value.strip()
            if not value:
                raise NumberingStrategyError(f"{name} cannot be empty.")
            if name == "strategy_code":
                value = value.upper()
            object.__setattr__(self, name, value)

        for opt in ("prefix", "suffix"):
            value = getattr(self, opt)
            if value is not None:
                if not isinstance(value, str):
                    raise TypeError(f"{opt} must be text or None.")
                value = value.strip() or None
            object.__setattr__(self, opt, value)

        if not isinstance(self.mode, NumberingMode):
            object.__setattr__(self, "mode", NumberingMode(self.mode))

        if self.padding_length is not None:
            if isinstance(self.padding_length, bool) or not isinstance(self.padding_length, int):
                raise TypeError("padding_length must be an integer or None.")
            if self.padding_length < 1:
                raise NumberingStrategyError("padding_length must be greater than zero.")

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < 1:
            raise NumberingStrategyError("version must be >= 1.")

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def qualified_code(self) -> str:
        return f"{self.registry_id}:{self.namespace_id}:{self.strategy_code}"

    @property
    def padded(self) -> bool:
        return self.padding_length is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy_id": self.strategy_id,
            "registry_id": self.registry_id,
            "namespace_id": self.namespace_id,
            "identifier_id": self.identifier_id,
            "strategy_code": self.strategy_code,
            "strategy_name": self.strategy_name,
            "mode": self.mode.value,
            "prefix": self.prefix,
            "suffix": self.suffix,
            "padding_length": self.padding_length,
            "version": self.version,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, values: Mapping[str, object]) -> "NumberingStrategy":
        return cls(**dict(values))


__all__ = (
    "NumberingMode",
    "NumberingStrategy",
    "NumberingStrategyError",
)
