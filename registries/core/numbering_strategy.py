"""
============================================================
Nexa Provider Platform
File: registries/core/numbering_strategy.py
Layer: Master Registry Foundation
Milestone: M008.2 — Registry Identifier Model
============================================================

Immutable, storage-neutral description of an identifier numbering strategy.
This model records strategy metadata only. It never allocates, reserves, or
generates identifier values and never owns sequence state.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Final


DEFAULT_NUMBERING_STRATEGY_VERSION: Final[int] = 1


class NumberingMode(str, Enum):
    """Supported descriptive numbering modes."""

    SEQUENTIAL = "sequential"
    RANDOM = "random"
    UUID = "uuid"
    DATE_PREFIXED = "date_prefixed"
    CUSTOM = "custom"


class NumberingStrategyError(ValueError):
    """Raised when an invalid NumberingStrategy is created."""


@dataclass(frozen=True, slots=True)
class NumberingStrategy:
    """Immutable description of one identifier numbering strategy."""

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
    version: int = DEFAULT_NUMBERING_STRATEGY_VERSION
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "strategy_id", "registry_id", "namespace_id", "identifier_id",
            "strategy_code", "strategy_name",
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

        for name in ("prefix", "suffix"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, str):
                    raise TypeError(f"{name} must be text or None.")
                value = value.strip() or None
            object.__setattr__(self, name, value)

        if not isinstance(self.mode, NumberingMode):
            try:
                object.__setattr__(self, "mode", NumberingMode(self.mode))
            except (TypeError, ValueError) as exc:
                raise NumberingStrategyError(
                    f"Unsupported numbering mode {self.mode!r}."
                ) from exc

        if self.padding_length is not None:
            if isinstance(self.padding_length, bool) or not isinstance(
                self.padding_length, int
            ):
                raise TypeError("padding_length must be an integer or None.")
            if self.padding_length < 1:
                raise NumberingStrategyError(
                    "padding_length must be greater than zero."
                )

        if isinstance(self.version, bool) or not isinstance(self.version, int):
            raise TypeError("version must be an integer.")
        if self.version < DEFAULT_NUMBERING_STRATEGY_VERSION:
            raise NumberingStrategyError(
                "version must be greater than or equal to "
                f"{DEFAULT_NUMBERING_STRATEGY_VERSION}."
            )

        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        normalized: dict[str, object] = {}
        for key, value in self.metadata.items():
            if not isinstance(key, str):
                raise TypeError("metadata keys must be text.")
            key = key.strip()
            if not key:
                raise NumberingStrategyError("metadata keys cannot be empty.")
            normalized[key] = value
        object.__setattr__(self, "metadata", MappingProxyType(normalized))

    @property
    def identity(self) -> tuple[str, str]:
        return self.strategy_id, self.strategy_code

    @property
    def ownership(self) -> tuple[str, str, str]:
        return self.registry_id, self.namespace_id, self.identifier_id

    @property
    def qualified_code(self) -> str:
        return f"{self.registry_id}:{self.namespace_id}:{self.strategy_code}"

    @property
    def padded(self) -> bool:
        return self.padding_length is not None

    def metadata_value(self, key: str, default: object = None) -> object:
        if not isinstance(key, str):
            raise TypeError("key must be text.")
        key = key.strip()
        if not key:
            raise ValueError("key cannot be empty.")
        return self.metadata.get(key, default)

    def has_metadata(self, key: str) -> bool:
        if not isinstance(key, str):
            raise TypeError("key must be text.")
        key = key.strip()
        return bool(key) and key in self.metadata

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
        if not isinstance(values, Mapping):
            raise TypeError("values must be a mapping.")
        return cls(**dict(values))

    def summary(self) -> str:
        return (
            "========================================================\n"
            "Nexa Provider Platform\n"
            "Numbering Strategy\n"
            "--------------------------------------------------------\n"
            f"Strategy ID   : {self.strategy_id}\n"
            f"Registry ID   : {self.registry_id}\n"
            f"Namespace ID  : {self.namespace_id}\n"
            f"Identifier ID : {self.identifier_id}\n"
            f"Code          : {self.strategy_code}\n"
            f"Name          : {self.strategy_name}\n"
            f"Mode          : {self.mode.value}\n"
            f"Version       : {self.version}\n"
            "========================================================"
        )


__all__ = (
    "DEFAULT_NUMBERING_STRATEGY_VERSION",
    "NumberingMode",
    "NumberingStrategy",
    "NumberingStrategyError",
)
